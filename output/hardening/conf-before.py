# FreeStar 4000 configuration for Everett, WA
# Headless streaming setup -> wagenhoffer.dev/weather
# Generated for server-side rendering (no audio, no built-in stream output;
# an external ffmpeg process captures the Xvfb display and produces HLS).

# --- Presentation ---
textpos = 0            # post-1993 time text position
timedrawing = False
ldldrawing = True
veryuppercase = False
pressuretrend = True

# --- Main location ---
mainloc = "Everett, WA"        # search name for wx.lewolfyt.cc
mainloc2 = "Everett"           # display name
efname = "Everett Metro"       # extended forecast header name

# --- Audio / music ---
# Drop .mp3/.ogg/.wav/.flac files into this folder and they will start
# playing on the stream within seconds (folder is rescanned between tracks).
musicdir = "music"
musicsetting = 0

# --- Mesonet climate product (NWS Seattle CLI) ---
mesoid = "CLISEA"

# --- LDL (lower display line) ---
extra = ""
ldlbg = ""                     # no LDL-only background (ldlmode is off)
ldlmode = False
ldllf = False
forever = True                 # loop the slideshow endlessly; False ends the show into magenta ldlmode
foreverldl = False
ldlfeed = None                 # no video feed input

# --- Crawl messages ---
crawls = []                    # list of [text, enabled] pairs
crawlint = 0                   # index into [15m,30m,1h,2h,3h,4h,6h,8h,12h,24h]
crawllen = 40

# --- Local observations (Latest Observations page) ---
obsloc = [
    ["Seattle, WA", "Seattle"],
    ["Boeing Field, Seattle, WA", "Boeing Field"],
    ["Renton, WA", "Renton"],
    ["Tacoma, WA", "Tacoma"],
    ["Bellingham, WA", "Bellingham"],
    ["Olympia, WA", "Olympia"],
    ["Everett, WA", "Everett"],
]

# --- Regional observations (unused: "ro" not in flavor) ---
reglocs = []
regnames = []

# --- Stream I/O ---
# Built-in PyAV encoder publishes RTMP to local mediamtx, which serves HLS
# on 127.0.0.1:8888; Apache proxies wagenhoffer.dev/weather/hls/ to it.
outputs = ["rtmp://127.0.0.1:1935/weather/hls"]

# --- Schedule (empty = no auto local forecast times) ---
schedule = ""

# --- Radar timing ---
radarint = 0.26
radarhold = 2.74
radarsetting = False

# --- Logos (classic TWC look) ---
mainlogo = "logos/twclogo.png"
radarlogo = "logos/twcradar.png"

# --- Misc ---
extensions = []
audiodevice = "Default"
metric = False
borderless = False
vencoder = "libx264"
widescreen = False           # 768x480 (8:5) native render
compress = False
lsort = 0
smoothscale = True
tidal = ("9447130", "9446484", "SEATTLE", "TACOMA")   # NOAA CO-OPS station IDs (verified live)
efullscreen = False

# --- Headless streaming tweaks ---
mute = False                 # stream carries an AAC track (SDL dummy audio device)
framerate = 30               # halves CPU vs 60
aspect = True
socket = False
smode = 0
old = set()

# --- Flavor: slide sequence and durations (seconds) ---
# Classic WeatherStar 4000 lineup for Everett.
# Added 2026-07-07: ol (30-day outlook), df (daypart forecast), cr (color radar),
# ti (tides) — all on data already fetched; tide IDs verified live.
flavor = ["cc", "lo", "lf", "xf", "lr", "al", "ol", "df", "cr", "ti", "tcf"]
flavor_times = [30, 20, 60, 40, 40, 30, 20, 30, 15, 30, 40]
