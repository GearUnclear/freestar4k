import copy
import datetime as dt
import json
from pathlib import Path
import unittest

from broadcast_support import AudioClock, FrameClock, forecast_pages, tide_report, sun_report, climate_report, validate_weather


class ClockStub:
    def __init__(self):
        self.time = 0
    def now(self):
        return self.time
    def sleep(self, seconds):
        self.time += seconds


class BroadcastSupportTests(unittest.TestCase):
    def test_current_provider_schema_and_partial_data_validation(self):
        fixture = json.loads((Path(__file__).parent/'fixtures/weather.json').read_text())
        self.assertIs(validate_weather(fixture), fixture)
        invalid = copy.deepcopy(fixture)
        invalid['current']['conditions']['temperature'] = None
        with self.assertRaises(ValueError):
            validate_weather(invalid)
        forecast_only = {'extended': fixture['extended']}
        validate_weather(forecast_only, ('extended',))

    def test_advisory_forecast_preserves_every_period_and_never_schedules_empty_page(self):
        periods = [{'name': name, 'narration': 'Cloudy. High around 60F. Winds light and variable.'}
                   for name in ('Today', 'Tonight', 'Tomorrow', 'Tomorrow night')]
        pages = forecast_pages({'extended': {'daypart': periods}}, [('Small craft advisory until 5 PM', 'Y')])
        self.assertTrue(all(1 <= len(page) <= 7 and any(page) for page in pages))
        lines = '\n'.join(line for page in pages for line in page)
        positions = [lines.index(name+'...') for name in ('Today', 'Tonight', 'Tomorrow', 'Tomorrow night')]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(all(len(line) <= 32 for page in pages for line in page))

    def test_current_only_null_alerts_keep_observations_usable(self):
        fixture = json.loads((Path(__file__).parent/'fixtures/weather.json').read_text())
        fixture['current']['alerts'] = None
        validate_weather(fixture, ('current',))
        self.assertEqual(fixture['current']['alerts'], [])
        fixture['current']['alerts'] = 'invalid'
        with self.assertRaises(ValueError):
            validate_weather(fixture, ('current',))

    def test_long_forecast_is_not_silently_truncated(self):
        text = ('A very long weather discussion with unusuallylongunbreakablewords ')*20
        pages = forecast_pages({'extended': {'daypart': [{'name': 'Today', 'narration': text}]}})
        self.assertGreater(len(pages), 3)
        self.assertEqual(''.join(''.join(page) for page in pages).replace(' ', ''),
                         ('Today...'+text).replace(' ', ''))

    def test_absent_forecast_has_visible_fallback(self):
        self.assertIn('unavailable', forecast_pages(None)[0][0])

    def test_tides_use_their_own_events_and_pad_missing_predictions(self):
        seattle = [{'type': 'H', 'valid': 10}, {'type': 'L', 'valid': 20}]
        tacoma = [{'type': 'L', 'valid': 11}, {'type': 'H', 'valid': 21}]
        a, b = [tide_report(events, str) for events in (seattle, tacoma)]
        self.assertEqual(b['lows'][0], ('11', 11))
        self.assertEqual(b['highs'][0], ('21', 21))
        self.assertEqual(b['highs'][1], ('--', None))
        self.assertNotEqual(a['highs'][0], b['highs'][0])

    def test_solar_response_for_wrong_date_is_rejected(self):
        today = dt.date(2026, 9, 29)
        first = {'status': 'OK', 'results': {'date': '2026-09-29', 'sunrise': '1', 'sunset': '2'}}
        second = {'status': 'OK', 'results': {'date': '2026-09-30', 'sunrise': None, 'sunset': None}}
        self.assertIsNone(sun_report(first, second, today)['sunrise2'])
        stale = copy.deepcopy(second);stale['results']['date'] = '2026-09-20'
        with self.assertRaises(ValueError):
            sun_report(first, stale, today)

    def test_tides_skip_previous_utc_day_events_that_are_yesterday_locally(self):
        today = dt.date(2026,9,29)
        yesterday = int(dt.datetime(2026,9,28,18,18).timestamp())
        morning = int(dt.datetime(2026,9,29,7,39).timestamp())
        evening = int(dt.datetime(2026,9,29,18,49).timestamp())
        report = tide_report([{'type':'H','valid':ts} for ts in (yesterday,morning,evening)], str, today)
        self.assertEqual([t[1] for t in report['highs']], [morning,evening])

    def test_video_clock_advances_between_large_audio_callbacks(self):
        time = ClockStub();clock = AudioClock(44100, time.now)
        callback = 8192/44100
        frames = []
        next_callback = 0
        for i in range(300):
            render_time = i/30
            while render_time >= next_callback:
                time.time = next_callback
                clock.feed(8192);next_callback += callback
            time.time = render_time
            frames.append(round(clock.seconds()*30))
        self.assertGreater(len(set(frames)), 285)
        self.assertLess(abs(clock.seconds()-time.time), callback)

    def test_audio_clock_does_not_run_past_available_audio(self):
        time = ClockStub();clock = AudioClock(44100, time.now)
        self.assertIsNone(clock.seconds());clock.feed(8192);time.time = 60
        self.assertEqual(clock.seconds(), 8192/44100)

    def test_slide_clock_includes_slow_frames(self):
        time = ClockStub();clock = FrameClock(time.now, time.sleep)
        self.assertAlmostEqual(clock.tick(30), 1000/30)
        time.time += 1.5
        self.assertAlmostEqual(clock.tick(30), 1500)

    def test_zero_normals_and_trace_precipitation_do_not_divide_by_zero(self):
        report = climate_report('PRECIPITATION (IN)\n MONTH TO DATE T 0.00 0.00\nDEGREE DAYS\n HEATING\n MONTH TO DATE 0 0 0\n COOLING\n')
        self.assertEqual(report['month_precip'], 'T')
        self.assertEqual(report['heating_normal'], '0')

    def test_retained_monthly_climate_keeps_its_observed_date(self):
        report = climate_report((Path(__file__).parent/'fixtures/climate.txt').read_text())
        self.assertEqual(report['month'], 'September')
        self.assertEqual(report['date'], '2026-09-28')


if __name__ == '__main__':
    unittest.main()
