(function () {
  'use strict';
  var source = '/weather/hls/index.m3u8';
  var video = document.getElementById('tv');
  var button = document.getElementById('tunein');
  var status = document.getElementById('status');
  var active = false;
  var hls = null;
  var retry = null;
  var generation = 0;
  var lastTime = 0;
  var lastProgress = Date.now();
  var lastSeek = 0;
  var failures = 0;
  var mediaRecovery = false;

  function label(text) {
    status.textContent = text;
    status.style.color = text === 'live' ? '#CC0000' : '';
    status.style.fontWeight = text === 'live' ? 'bold' : '';
  }

  function release() {
    generation += 1;
    clearTimeout(retry);
    retry = null;
    if (hls) { hls.destroy(); hls = null; }
    video.pause();
    video.removeAttribute('src');
    video.load();
  }

  function stop() {
    active = false;
    release();
    button.value = '\u25B6 Play (with sound)';
    label('offline');
  }

  function reconnect() {
    if (!active || retry !== null) return;
    release();
    label('reconnecting');
    var attempt = generation;
    retry = setTimeout(function () {
      retry = null;
      if (active && generation === attempt) connect();
    }, Math.min(15000, 2000 * Math.pow(2, failures++)));
  }

  function play(attempt) {
    video.play().catch(function (error) {
      if (!active || attempt !== generation) return;
      if (error.name === 'NotAllowedError') stop();
      else reconnect();
    });
  }

  function connect() {
    release();
    var attempt = generation;
    lastProgress = Date.now();
    lastTime = 0;
    lastSeek = 0;
    mediaRecovery = false;
    label('connecting');
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = source;
      play(attempt);
    } else if (window.Hls && Hls.isSupported()) {
      hls = new Hls({ liveSyncDurationCount: 2, liveMaxLatencyDurationCount: 4,
                      maxBufferLength: 10, backBufferLength: 15 });
      hls.on(Hls.Events.MANIFEST_PARSED, function () {
        if (active && attempt === generation) play(attempt);
      });
      hls.on(Hls.Events.ERROR, function (_event, data) {
        if (!active || attempt !== generation || !data.fatal) return;
        if (data.type === Hls.ErrorTypes.MEDIA_ERROR && !mediaRecovery) {
          mediaRecovery = true;
          label('buffering');
          hls.recoverMediaError();
        } else reconnect();
      });
      hls.loadSource(source);
      hls.attachMedia(video);
    } else stop();
  }

  button.onclick = function () {
    if (active) { stop(); return; }
    active = true;
    failures = 0;
    button.value = '\u25A0 Stop';
    connect();
  };

  video.addEventListener('timeupdate', function () {
    if (!active || retry !== null) return;
    if (video.currentTime !== lastTime) {
      lastTime = video.currentTime;
      lastProgress = Date.now();
      failures = 0;
      label('live');
    }
  });
  video.addEventListener('waiting', function () {
    if (active && retry === null) label('buffering');
  });
  video.addEventListener('error', function () { if (active) reconnect(); });

  setInterval(function () {
    if (!active || retry !== null || document.hidden || Date.now()-lastProgress < 12000) return;
    // Both native HLS and hls.js can stop advancing without a fatal error.
    // Try the newest buffered picture once, then rebuild the player if needed.
    if (video.buffered.length && !lastSeek) {
      var edge = video.buffered.end(video.buffered.length-1);
      if (edge > video.currentTime+1) {
        lastSeek = Date.now();
        video.currentTime = Math.max(0, edge-0.5);
        lastProgress = lastSeek;
        play(generation);
        return;
      }
    }
    reconnect();
  }, 1000);

  document.getElementById('fslink').onclick = function () {
    var wrap = document.getElementById('tvwrap');
    if (wrap.requestFullscreen) {
      var result = wrap.requestFullscreen();
      if (result && result.catch) result.catch(function () {});
    } else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
    return false;
  };
  window.addEventListener('pagehide', stop);
})();
