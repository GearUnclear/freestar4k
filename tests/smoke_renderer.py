"""Exercise the real renderer with recorded weather and injected feed failures."""
import copy
import io
import json
import os
from pathlib import Path
import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['TZ'] = 'America/Los_Angeles'
import time
time.tzset()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
case = sys.argv[1] if len(sys.argv)>1 else 'normal'
destination = ROOT/'output/hardening'/('renderer-'+case)
destination.mkdir(parents=True, exist_ok=True)

import conf
conf.outputs = []
conf.mute = True
conf.musicdir = ''
conf.flavor_times = [1]*len(conf.flavor)

import weather_http
import pygame as pg
weather = json.loads((ROOT/'tests/fixtures/weather.json').read_text())
if case == 'partial':
    weather['extended']['daypart'] = weather['extended']['daypart'][:2]
    weather['extended']['daily'] = weather['extended']['daily'][:2]
    for period in weather['extended']['daypart']:
        period['iconCode'] = 999
    weather['current']['info']['iconCode'] = 999
tides = json.loads((ROOT/'tests/fixtures/tacoma-tides.json').read_text())
image = pg.Surface((4200,1920));image.fill((60,100,80))
buffer = io.BytesIO();pg.image.save(image,buffer,'radar.png');radar = buffer.getvalue()

class Reply:
    content = radar
    text = (ROOT/'tests/fixtures/climate.txt').read_text()
    def json(self):
        return copy.deepcopy(tides if '/tides' in self.url else weather)

calls = []
refreshes = 0
def request(url, **kwargs):
    global refreshes
    calls.append(url)
    if case == 'offline':
        raise OSError('Injected unavailable weather provider')
    if case == 'recovery' and kwargs.get('params',{}).get('extendeddays'):
        refreshes += 1
        if 2 <= refreshes <= 4:
            raise OSError('Injected weather refresh outage')
        weather['current']['conditions']['temperature'] = 59 if refreshes < 5 else 61
    reply = Reply();reply.url = url
    return reply
weather_http.response = request

source = (ROOT/'main.py').read_text()
if case == 'recovery':
    source = source.replace('tm.sleep(300)', 'tm.sleep(0.75)')
source = source.replace('    frame_idx_actual += 1', '''    if frame_idx_actual % 8 == 0:
        marker = f'{slide}-{subpage}'
        if marker not in smoke_seen:
            smoke_seen.add(marker)
            pg.image.save(win, str(smoke_destination/(marker+'.png')))
    if frame_idx_actual >= 980:
        working = False
    frame_idx_actual += 1''')
namespace = {'__file__': str(ROOT/'main.py'), '__name__': '__main__',
             'smoke_seen': set(), 'smoke_destination': destination}
exec(compile(source,str(ROOT/'main.py'),'exec'),namespace)
seen = sorted(namespace['smoke_seen'])
expected = set(conf.flavor)
observed = {marker.rsplit('-',1)[0] for marker in seen}
assert expected <= observed, (expected-observed,seen)
assert namespace['render_error_time'] == -float('inf'), 'Renderer used its last-resort exception fallback'
if case != 'offline':
    assert namespace['wxdata'], 'Weather never loaded'
    assert namespace['aldata']['tidal'][1], 'Tides never loaded'
    if case == 'recovery':
        assert refreshes >= 5, 'Weather worker stopped retrying'
        assert namespace['wxdata']['current']['conditions']['temperature'] == 61, 'Weather did not recover'
else:
    assert namespace['wxdata'] is None
(destination/'summary.json').write_text(json.dumps({'screens': seen, 'requests':len(calls)},indent=2)+'\n')
print('Renderer passed:',case,seen)
