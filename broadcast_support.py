"""Data and timing helpers shared by the weather renderer and its checks."""

import datetime as dt
import math
import re
import textwrap
import threading
import time


def wrap_lines(text, width=32):
    lines = []
    for paragraph in str(text).splitlines() or ['']:
        lines.extend(textwrap.wrap(paragraph, width=width) or [''])
    return lines


def forecast_pages(weather, alerts=(), uppercase=False):
    """Paginate complete forecast paragraphs in feed order, without empty pages."""
    dayparts = ((weather or {}).get('extended') or {}).get('daypart') or []
    advisories = [alert[0] for alert in alerts if alert[1] != 'W']
    lines = []
    if advisories:
        for line in wrap_lines(advisories[0].upper(), 30):
            lines.append('*' + line.center(30) + '*')
        lines.append('')
    for period in dayparts[:4 if advisories else 3]:
        if not period or not period.get('name') or not period.get('narration'):
            continue
        if lines and lines[-1]:
            lines.append('')
        text = period['name'].capitalize() + '...' + period['narration']
        lines.extend(wrap_lines(text.upper() if uppercase else text))
    while lines and not lines[-1]:
        lines.pop()
    if not any(lines):
        return [['Forecast temporarily unavailable']]
    pages = []
    for offset in range(0, len(lines), 7):
        page = lines[offset:offset+7]
        while page and not page[0]:
            page.pop(0)
        if any(page):
            pages.append(page)
    return pages


def validate_weather(data, sections=('current', 'extended')):
    """Reject incomplete responses before replacing the last usable report."""
    if not isinstance(data, dict):
        raise ValueError('Weather response must be an object')
    if 'current' in sections:
        current = data['current']
        info, conditions = current['info'], current['conditions']
        for key in ('temperature', 'feelsLike', 'humidity', 'dewPoint',
                    'pressure', 'windSpeed', 'visibility'):
            value = conditions[key]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'Invalid current condition: {key}')
        for key in ('pressureTendency', 'windCardinal', 'windGusts', 'cloudCeiling'):
            if key not in conditions:
                raise ValueError(f'Missing current condition: {key}')
        if not isinstance(conditions['windCardinal'], str):
            raise ValueError('Invalid wind direction')
        if not isinstance(info['iconCode'], int):
            raise ValueError('Invalid current icon code')
        for key in ('phraseLong', 'phraseMedium', 'phraseShort'):
            if not isinstance(info[key], str):
                raise ValueError(f'Invalid current description: {key}')
        if len(info['geocode']) != 2:
            raise ValueError('Invalid location coordinates')
        # Current-only responses legitimately omit alert data (null).
        if current.get('alerts') is None:
            current['alerts'] = []
        if not isinstance(current['alerts'], list):
            raise ValueError('Invalid alert list')
    if 'extended' in sections:
        periods = data['extended']['daypart']
        if not isinstance(periods, list) or not periods:
            raise ValueError('Forecast has no periods')
        for period in periods:
            for key in ('name', 'narration', 'phraseLong', 'phraseShort', 'windCardinal'):
                if not isinstance(period[key], str):
                    raise ValueError(f'Invalid forecast field: {key}')
            if period['dayOrNight'] not in ('D', 'N'):
                raise ValueError('Invalid forecast day/night')
            for key in ('temperature', 'windSpeed'):
                if not isinstance(period[key], (int, float)) or not math.isfinite(period[key]):
                    raise ValueError(f'Invalid forecast value: {key}')
            if not isinstance(period['iconCode'], int):
                raise ValueError('Invalid forecast icon code')
        if not isinstance(data['extended']['daily'], list):
            raise ValueError('Invalid daily forecast')
        for day in data['extended']['daily']:
            if not isinstance(day['valid'], (int, float)):
                raise ValueError('Invalid daily forecast date')
    return data


def tide_report(events, format_time, today=None):
    report = {'lows': [], 'highs': []}
    for event in events:
        if event.get('type') not in ('L', 'H'):
            continue
        timestamp = int(event['valid'])
        if today is not None and dt.datetime.fromtimestamp(timestamp).date() != today:
            continue
        bucket = report['highs' if event['type'] == 'H' else 'lows']
        if len(bucket) < 2:
            bucket.append((format_time(timestamp), timestamp))
    for bucket in report.values():
        while len(bucket) < 2:
            bucket.append(('--', None))
    return report


def sun_report(first, second, today):
    report = {'date': today.isoformat()}
    for index, response in enumerate((first, second), 1):
        expected = (today + dt.timedelta(days=index-1)).isoformat()
        if response.get('status') != 'OK' or response['results']['date'] != expected:
            raise ValueError('Sunrise response date/status does not match requested day')
        for field in ('sunrise', 'sunset'):
            value = response['results'].get(field)
            report[f'{field}{index}'] = int(value) if value is not None else None
    return report


def forecast_sun_report(weather, today):
    daily = weather['extended']['daily']
    report = {'date': today.isoformat()}
    for index in (1, 2):
        day = daily[index-1]
        expected = today + dt.timedelta(days=index-1)
        for name in ('sunrise', 'sunset'):
            timestamp = day.get(name)
            if timestamp is not None:
                timestamp = int(timestamp)
                if dt.datetime.fromtimestamp(timestamp).date() != expected:
                    raise ValueError('Forecast solar times are for a different date')
            report[f'{name}{index}'] = timestamp
    return report


def climate_report(text):
    def month_row(section):
        row = next(line for line in section.splitlines() if 'MONTH TO DATE' in line)
        values = row.split('MONTH TO DATE', 1)[1].split()
        if len(values) < 3:
            raise ValueError('Incomplete monthly climate report')
        return [value if re.fullmatch(r'[+-]?\d+(?:\.\d+)?|T', value) else '--'
                for value in values[:3]]

    precipitation = month_row(text.split('PRECIPITATION (', 1)[1])
    heating = month_row(text.split('DEGREE DAYS', 1)[1].split('COOLING', 1)[0])
    date = re.search(r'CLIMATE SUMMARY FOR ([A-Z]+)\s+(\d{1,2})\s+(\d{4})', text)
    observed = dt.datetime.strptime(' '.join(date.groups()), '%B %d %Y').date() if date else None
    return {'month': observed.strftime('%B') if observed else 'Month to date',
            'date': observed.isoformat() if observed else None,
            'month_precip': precipitation[0], 'precip_normal': precipitation[1],
            'precip_departure': precipitation[2], 'heating': heating[0],
            'heating_normal': heating[1], 'heating_departure': heating[2]}


class AudioClock:
    """Interpolate the sample clock between mixer callbacks instead of dropping frames."""

    def __init__(self, rate, now=time.monotonic):
        self.rate = rate
        self.now = now
        self.samples = 0
        self.anchor = None
        self.lock = threading.Lock()

    def feed(self, samples):
        with self.lock:
            start = self.samples
            self.anchor = (start, self.now())
            self.samples += samples
            return start

    def seconds(self):
        with self.lock:
            if self.anchor is None:
                return None
            samples, timestamp = self.anchor
            # Never extrapolate past audio we actually have. A stalled mixer
            # must not leave video running arbitrarily far ahead of the sound.
            interpolated = samples + max(0, self.now()-timestamp)*self.rate
            return min(interpolated, self.samples) / self.rate


class FrameClock:
    """Pace rendering while returning elapsed time, including slow frames."""

    def __init__(self, now=time.monotonic, sleep=time.sleep):
        self.now, self.sleep = now, sleep
        self.last = now()

    def tick(self, fps):
        remaining = 1/fps - (self.now()-self.last)
        if remaining > 0:
            self.sleep(remaining)
        current = self.now()
        elapsed = current-self.last
        self.last = current
        return elapsed*1000
