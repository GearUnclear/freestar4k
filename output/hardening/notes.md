# Stream hardening and live checks — September 29, 2026

The fixes are deployed to https://wagenhoffer.dev/weather/. Source changes are in the worktree; no Git commit was created. The original observation remains in `output/playwright/weather-watch-20260929/notes.md`.

## Problems corrected

- Local Forecast scheduled a third page even when its text list had only two pages. Pagination now follows the actual wrapped content, with complete forecast periods in feed order and a visible fallback for unavailable forecasts.
- Advisory handling selected the last forecast period in place of Tonight. The live sequence now contains Today, Tonight, Tomorrow, and Tomorrow night in that order.
- Video time advanced only at 8,192-sample audio callbacks, dropping delivery to approximately 5.38 fps. The interpolated sample clock now delivers approximately 30 fps, with two-second keyframes instead of roughly eleven seconds between keyframes.
- Tacoma tide parsing reused Seattle event metadata. Each station now uses its own predictions, filtered to the local calendar day; yesterday evening in the API's UTC range no longer displaces today's second high tide.
- Solar responses could contain the wrong date. Solar timestamps are taken from the dated forecast or checked against explicitly requested local dates.
- The old 30 Day Outlook treated observed month-to-date heating degree days as a temperature prediction and could divide by zero. Monthly Climate now displays actual observed values, normals, and departures, with the month taken from the report.
- Failed requests, unsupported icons, partial forecasts, and missing radar frames could interrupt updates or rendering. HTTP calls have timeouts/status checks, usable weather is retained across outages, independent feed failures do not end the refresh loop, and missing data has visible placeholders. A stale-data ticker identifies conditions older than 15 minutes.
- The browser lacked reliable recovery from errors and silent stalls. Native HLS and hls.js now retry with bounded backoff and cancel retries on Stop.
- PyAV's output path ignored the supplied network timeout. RTMP transport now passes the already encoded FLV through FFmpeg without re-encoding, with a protocol timeout and bounded pipe writes. A failed receiver cannot leave rendering blocked or create an unlimited output queue.
- The bundled TWC logo's full-screen transparent canvas placed its visible mark too low and close to the title. The renderer crops that padding and places the visible logo near the top-left at the proportions in the user's supplied reference. The separately drawn radar logo receives the same left margin so it cannot cover its title; custom logos keep their original placement behavior.
- A provider-specific validation issue discovered in live logs rejected `null` alerts on current-only responses. These valid observation reports now normalize the missing alert data to an empty list.
- The requirements file contained a control character after `av`; it was removed, and NumPy is explicitly declared.

## Verification completed

- 17 Python checks passed, including actual H264/AAC encoding, failed initial connection recovery, forecast chronology/pagination, dated solar/climate handling, local-day tide selection, and a real process that stops reading its input.
- Browser logic checks passed for native HLS and hls.js, including error/stall recovery, retry cancellation, and repeated media errors.
- All 11 configured screen types passed in the real renderer with normal, unavailable, and partial feed data. A simulated weather outage retained the previous report and recovered fresh data. These supported cases did not invoke the last-resort render exception panel.
- An isolated real MediaMTX test verified PyAV → bounded FFmpeg transport → RTMP, normal video cadence, keyframe spacing, continuous AAC, and clean shutdown.
- Public `index.html` and `player.js` match the tested sources. Python syntax checks, dependency checks, and `git diff --check` passed.

## Timestamped live observations (UTC)

| Time | Observation |
| --- | --- |
| 20:41:55–20:42:52 | Original blank third Local Forecast page, with moving clock and ticker. Preserved in the original observation folder. |
| 21:30:58 | First logo adjustment visible in public playback. |
| 21:34:59 | Reference-matched logo visible near the top-left, with clear space beside the title. |
| 21:41:21–21:41:29 | Deliberately stopped and restored MediaMTX for a recovery check. The publisher process remained PID 1447451 throughout. A brief black/buffering interval in this part of the capture is caused by this test. |
| 21:41:30–21:41:35 | Publisher reconnected; both H264 and AAC tracks became available, and HLS playback resumed automatically. |
| 21:41:47 | Current Conditions populated with the adjusted logo. |
| 21:42:03 | Latest Observations populated, including refreshed city rows. |
| 21:42:18–21:43:04 | First Local Forecast page populated with advisory and Today. |
| 21:43:20–21:44:06 | Second Local Forecast page populated with Tonight followed by Tomorrow. |
| 21:44:21–21:45:07 | Third Local Forecast page populated with Tomorrow night; the former empty-panel defect did not recur. |
| 21:45:23–21:45:38 | Extended Forecast populated. |
| 21:45:53–21:46:24 | Local Radar populated and precipitation animation advances. |
| 21:46:39–21:46:55 | Almanac populated: Tuesday sunrise 7:05 AM/set 6:51 PM; Wednesday sunrise 7:06 AM/set 6:49 PM; moon phases populated. |
| 21:47:10 | Monthly Climate populated with September observed HDD 118 vs normal 91 and precipitation 1.45 in vs normal 1.46 in. |
| 21:47:25–21:48:32 | Daypart Forecast populated and advances through all three pages. |
| 21:48:53 | Current Radar populated. Final visual review found its separately drawn logo crowds the title; that logo placement was corrected and checked in the real renderer afterward. |
| 21:49:13 | Tides populated with each station's own Tuesday events: Seattle highs 7:38 AM / 6:45 PM, Tacoma highs 7:39 AM / 6:49 PM. |
| 21:49:39–21:50:09 | Travel Forecast populated and scrolling, correctly labeled For Wednesday. |
| 21:50:30 onward | Current Conditions returns, followed by Latest Observations and Local Forecast; a complete 11-screen rotation has been captured. |

A final 45-second public recording measured **29.933 fps**, maximum video-frame spacing **0.067 s**, keyframe spacing **2.000 s**, maximum AAC timestamp continuity error **0.000794 s**, and final audio/video timestamp difference **0.000993 s**. Audio is non-silent and has no clipped samples; this is a signal check, not a listening assessment. These results are in `live-final-encoding-summary.json` and `live-audio-summary.json`.

Separate browser tests deliberately disabled networking for 24 seconds. Native HLS resumed automatically in **9.282 seconds** after network restoration; hls.js resumed in **12.438 seconds**. Both resumed advancing video. See `native-recovery.json` and `hlsjs-recovery.json`.

The final full rotation capture ran **21:41:17–21:51:31 UTC**. Its deliberately interrupted startup is recorded above. From **21:41:45 UTC** onward, **2,347 samples** showed zero black samples, zero paused samples, zero low-readiness samples, no unchanged-video interval of at least one second, and status continuously live. There were **11 dropped frames out of 17,148** decoded frames in this stable interval. The browser's delivered-frame count can reset on reconnect; these counts use only the uninterrupted stable interval.

Screenshots are sampled approximately every five seconds; telemetry is sampled four times per second. This does not prove the absence of every possible defect between samples. The full screen set, timeline, raw telemetry, and playback summary are under `output/playwright/weather-final-20260929/`. The final small radar logo placement change was verified with the real renderer after this full-rotation capture; it does not change playback, weather processing, or slide scheduling.

The real Stop check confirmed the hls.js player remains offline beyond its maximum retry delay, with no source attribute, empty media/network state, reset video time, and its object URL revoked. Chrome retains the historical `currentSrc` string, which alone is not evidence of retained playback resources. See `player-stop.log`.

Live publisher logs had no unplanned errors after the controlled media-server interruption. The publisher remained PID 1447451 through the entire full-rotation capture. Deployment notes and repeatable verification commands are in `DEPLOYMENT.md`.

Final radar logo correction deployed at **21:54:28 UTC** (publisher PID 1542647). The revised Current/Local Radar layouts passed the real renderer check. MediaMTX confirmed H264/AAC publication at **21:54:31 UTC**, with no publisher errors after startup; the final browser check confirmed live, advancing 640×480 playback. See `final-deployment-player.log`, `renderer-normal/cr-0.png`, and `renderer-normal/lr-0.png`.
