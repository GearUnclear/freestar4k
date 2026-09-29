# Weather stream observation — September 29, 2026

Stream: https://wagenhoffer.dev/weather/

Observed approximately **20:33:52–20:45:10 UTC** (13:33:52–13:45:10 PDT), about **11 minutes 18 seconds**. The broadcast's own clock runs roughly 27–39 seconds behind receipt time in the screenshots. Entries below use the observation computer's UTC time; where legible, the displayed broadcast time is also given. Screenshots show the actual browser playback. A separate HLS recording preserves ten minutes of the broadcast.

**Main finding:** the third Local Forecast page is completely empty for approximately a minute. It was blank when viewing began and repeated after two populated forecast pages. The player remains live, with an advancing clock and ticker. No fully black video or playback freeze lasting at least one second was found in the monitored interval. Other populated screens, and a few text/data details to review, are recorded below.

This is an observation log; no application or deployment changes were made.

| Observation time (UTC) | Broadcast clock (PDT) | Observation |
| --- | --- | --- |
| 20:33:59.863 | 13:33:21 | **Local Forecast main panel completely empty.** Logo, title, clock, background frame, and lower ticker are present. Ticker reads “Visib: 3 mi. Ceiling: 800ft.” Player says live. This is missing slide content, rather than a fully black player. Evidence: `initial.png`. |
| 20:35:37–20:35:54 | 13:35:00–13:35:17 | Almanac renders sunrise/sunset values and all four moon illustrations/dates. Clock and ticker advance normally. |
| 20:35:37–20:35:54 | 13:35:00–13:35:17 | **Almanac values warrant review:** Tuesday sunrise 7:05 AM / sunset 6:51 PM; Wednesday sunrise 6:58 AM / sunset 7:02 PM. This is an observation of the displayed values; their correctness has not been independently checked. |
| 20:35:56–20:36:13 | 13:35:20–13:35:37 | 30 Day Outlook renders “SEPTEMBER,” “Temperatures: Above normal,” and “Precipitation: Normal.” No empty content panel in these samples. |
| 20:36:15–20:36:21 | 13:35:39–13:35:45 | Daypart Forecast renders four rows (Thursday through Friday night), temperatures, winds, and icons. |
| 20:36:51–20:37:42 | 13:36:15–13:37:08 | Daypart Forecast advances to later forecast periods through Tuesday night; content remains populated. |
| 20:37:44–20:37:57 | No clock on this layout | Current Radar renders a map with precipitation around Puget Sound. No blank map in these samples. |
| 20:37:59–20:38:24 | 13:37:25–13:37:51 | Tides renders Seattle and Tacoma low/high tide times and sunrise/sunset. No blank content panel. |
| 20:38:39–20:39:05 | 13:38:06–13:38:32 | Travel Forecast scrolls populated city rows with icons and low/high temperatures. Rows are partially clipped at the top and bottom during scrolling; this appears to be the scrolling layout. |
| 20:39:07–20:39:28 | 13:38:34–13:38:56 | Current Conditions renders Everett temperature, condition/icon, humidity, dewpoint, ceiling, visibility, pressure, wind, and wind chill. |
| 20:39:43–20:39:54 | 13:39:11–13:39:22 | Latest Observations renders all seven city rows, weather, temperature, and wind. |
| 20:39:56–20:40:28 | 13:39:24–13:39:56 | Local Forecast returns **populated**, showing a small craft advisory until 5:00 PM PDT and today's forecast. The blank panel seen at the beginning is not present in these samples. |
| 20:40:30–20:40:32 | 13:39:58–13:40:01 | Local Forecast text changes while still headed “Today”; temperature changes from 59°F to around 60°F, and the ticker's humidity changes from 96% to 95%. Possible live data refresh; no blank during these sampled updates. |
| 20:40:55–20:41:33 | 13:40:25–13:41:03 | Second Local Forecast page has text. **Ordering/label to review:** it begins “Tomorrow night...Mostly cloudy. Low around 50F...” and then “Tomorrow...Cloudy skies early, then partly cloudy in the afternoon. High 63F...”. No independent check of whether the first label should be “Tonight.” |
| 20:41:53.010 | 13:41:23 | Last captured populated second Local Forecast page before the blank. |
| **20:41:55.139–20:42:51.951** | **13:41:24–13:42:22** | **Blank Local Forecast recurs on the third page for approximately one minute.** All forecast/advisory text disappears from the central panel while the title, logo, clock, frame, and changing ticker continue normally. It remains empty in every two-second screenshot in this interval. First blank evidence: `frame-2026-09-29T20-41-55-139Z.png`; last blank screenshot: `frame-2026-09-29T20-42-51-951Z.png`. The populated-to-blank boundary lies between 20:41:53.010 and 20:41:55.139; the switch to Extended Forecast lies between 20:42:51.951 and 20:42:54.053. |
| 20:42:54–20:43:32 | 13:42:25–13:43:03 | Extended Forecast renders Thursday, Friday, and Saturday icons/conditions/low/high temperatures. |
| 20:43:34 | No clock on this layout | Local Radar renders the map and precipitation; no blank map. |
| 20:43:59–20:44:10 | No clock on this layout | Local Radar precipitation image changes across samples; animation is running. |
| 20:44:12–20:44:40 | 13:43:44–13:44:12 | Almanac repeats with the same Tuesday/Wednesday sunrise/sunset values noted earlier. |
| 20:44:42–20:44:48 | 13:44:15–13:44:21 | 30 Day Outlook repeats, populated. |
| 20:45:03–20:45:07 | 13:44:36–13:44:40 | Daypart Forecast repeats with populated rows/icons/temperatures/winds; observation ends shortly afterward. |

## Method and evidence

- Desktop Chrome browser at 1024×900, playing the public page after pressing Play.
- Browser screenshots approximately every two seconds during capture batches; not every individual frame was manually inspected.
- Browser video state and image statistics sampled four times per second from 20:35:26 UTC onward to distinguish black frames and playback pauses from missing slide content.
- Native `stalled` events occur periodically while video time continues advancing; those events alone are not proof of a visible playback freeze.
- Public page heading says “SEATTLE WEATHER”; the bottom ticker identifies conditions at Everett. This naming difference is visible, but not classified as a playback failure.

## Playback checks and saved evidence

- 2,335 browser samples from **20:35:26.107 to 20:45:09.860 UTC**: zero fully black samples, zero paused/offline samples, zero samples below video ready state 3, and no unchanged video-time interval lasting at least one second.
- 52 browser `stalled` events occurred without a measured playback freeze. Browser console contained no errors or warnings on the weather page.
- Ten-minute H.264/AAC recording: `broadcast.mp4` (600.248 seconds, approximately 17 MB). A decoded full-recording black-frame check found no black intervals lasting at least 0.1 seconds at a 98% black-pixel threshold. This check does not classify a blue panel with missing text as a black frame.
- The recording averages approximately **5.38 video frames per second**. This is a delivery/recording measurement; the cause has not been investigated. It may be useful when reviewing animation smoothness.
- `blank-page-sequence.jpg` shows the populated page, blank onset, last blank sample, and subsequent Extended Forecast, with observation timestamps.
- `initial.png` and 257 timestamped `frame-*.png` files preserve the visual samples.
- `telemetry.json`, `playback-summary.json`, and `blackdetect.log` preserve the measurements.

The task was observation only. No source edits, service restarts, or deployments were performed. Audio was not assessed by listening.
