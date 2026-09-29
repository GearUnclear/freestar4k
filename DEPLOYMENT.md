# wagenhoffer.dev/weather deployment

FreeStar 4000 runs headless on this server and broadcasts to
**https://wagenhoffer.dev/weather** as a live HLS stream.

## Architecture

```
freestar-weather.service          mediamtx.service               Apache (wagenhoffer.dev)
python main.py (SDL dummy)  --->  RTMP 127.0.0.1:1935  --->  HLS  ProxyPass /weather/hls/
video: pygame render 30fps        remux to fMP4 HLS               -> 127.0.0.1:8888/weather/hls/
audio: pygame mixer post-mix      127.0.0.1:8888                  player page: /var/www/wagenhoffer-dev/weather/
```

- `broadcast_encoder.py` encodes H264 + AAC with PyAV. The video clock
  interpolates between audio callbacks, and keyframes are two seconds apart.
  `rtmp_transport.py` passes the encoded FLV through FFmpeg (`-c copy`, no
  second encode) to apply a five-second network timeout. PyAV 18 ignores
  output protocol timeout options. A bounded queue and separate worker for
  each output keep a failed connection from blocking rendering or building
  an unlimited backlog. Interrupted outputs reconnect automatically.
  FFmpeg must be available on `PATH`; Xvfb is not used.
- mediamtx converts that to HLS. Its path is named `weather/hls` on purpose:
  the public URL prefix matches the internal one, so mediamtx's
  `?cookieCheck=1` redirect survives the reverse proxy unchanged.
- `web/index.html` and `web/player.js` are the deployable player sources.
  The deployed folder also contains vendored hls.js and the Star 4000 font.
  Both native HLS and hls.js paths retry failed connections and check for
  stalled playback. Stop cancels pending retries and releases the player.

## Pieces

| Piece | Where |
|---|---|
| venv | `/opt/FreeStar/venv` (pygame-ce, requests, av, numpy) |
| App config | `/opt/FreeStar/conf.py` (gitignored, server-local) |
| App service | `/etc/systemd/system/freestar-weather.service` |
| mediamtx | `/usr/local/bin/mediamtx`, config `/etc/mediamtx/mediamtx.yml`, `mediamtx.service` |
| Apache vhost | `/etc/apache2/sites-available/wagenhoffer-dev-le-ssl.conf` |
| Player page | `/var/www/wagenhoffer-dev/weather/` |

Both services are enabled at boot. The app service sets
`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` and `TZ=America/Los_Angeles`
(the on-screen clock uses system local time).

## Changing location

Edit `/opt/FreeStar/conf.py`:

- `mainloc` / `mainloc2` / `efname` — main city (search name, display name,
  extended-forecast region name)
- `obsloc` — the Latest Observations city list
- `mesoid` — NWS climate product id (e.g. `CLISEA` for Seattle)
- `flavor` / `flavor_times` — the screen rotation and per-screen seconds

Then `systemctl restart freestar-weather`. Also update `TZ=` in the unit if
the new location is in a different timezone.

## Weather refresh and screen behavior

`weather_http.py` applies connection/read timeouts and checks HTTP status.
`broadcast_support.py` validates incoming reports before replacing the last
usable weather data. Independent tide, solar, radar, and climate failures
do not stop the polling loop. Missing data produces visible placeholders;
conditions older than 15 minutes produce a stale-data ticker message.

Forecast pages follow feed order and are scheduled from their actual content,
so short reports do not produce an empty third page. Tacoma tide times use
Tacoma events; both stations select the displayed local calendar day's
predictions rather than a preceding evening in the API's UTC range.
Solar times are checked against the requested local dates.
The Monthly Climate screen shows observed heating degree days and rainfall
with normals/departures; it is not a 30-day weather prediction. Its month
label comes from the report, including while retaining an older report.

The bundled TWC logo's transparent canvas is cropped in the renderer and its
visible mark placed at `(12, 4)` with size `160 × 88`, matching the reference
placement. The bundled radar logo uses its separate artwork at `(12, 10)`
with the same size, leaving clearance beside the radar title. Custom logos
retain their original canvas placement.

## Deploying changes

Python files are read from `/opt/FreeStar`; restart `freestar-weather` after
changing the app or its helpers. Copy `web/index.html` and `web/player.js` to
`/var/www/wagenhoffer-dev/weather/` when changing the player. Bump the player
script query string in the HTML when publishing a new player version.

## Verification

Run from `/opt/FreeStar`:

```sh
venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node tests/test_player.cjs
venv/bin/python tests/smoke_renderer.py normal
venv/bin/python tests/smoke_renderer.py offline
venv/bin/python tests/smoke_renderer.py partial
venv/bin/python tests/smoke_renderer.py recovery
venv/bin/python tests/smoke_rtmp.py
```

Renderer checks use recorded provider responses and simulated outages; their
screenshots are saved under `output/hardening/renderer-*`. The RTMP check
starts a temporary MediaMTX instance on an unused local port, publishes real
H264/AAC, and checks the received video cadence, keyframe spacing, audio
continuity, and shutdown. It requires FFmpeg and `/usr/local/bin/mediamtx`.
Tests do not publish to the public stream.

## Music

Drop audio files (`.mp3 .ogg .wav .flac .xm .mod`) into `/opt/FreeStar/music/`.
The folder is rescanned between tracks, so no restart is needed. Tracks are
shuffled without immediate repeats and mixed into the stream's AAC track.

## Watching / debugging

```
systemctl status freestar-weather mediamtx
journalctl -u freestar-weather -f
curl -sL http://127.0.0.1:8888/weather/hls/index.m3u8   # HLS at the source
```
