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

- The app's built-in PyAV encoder (`outputs` in `conf.py`) publishes
  H264 + AAC over RTMP. No Xvfb or external ffmpeg involved.
- mediamtx converts that to HLS. Its path is named `weather/hls` on purpose:
  the public URL prefix matches the internal one, so mediamtx's
  `?cookieCheck=1` redirect survives the reverse proxy unchanged.
- The player page (vendored hls.js + the Star 4000 font) is static HTML.

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
