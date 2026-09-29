"""Bounded, reconnecting H.264/AAC output for the headless broadcast."""

from fractions import Fraction
import logging
import queue
import threading
import time

import av
from av.video.frame import PictureType

from broadcast_support import AudioClock
from rtmp_transport import RTMPTransport

log = logging.getLogger(__name__)


class BroadcastEncoder:
    def __init__(self, outputs, fps, size, audio_rate=44100, mute=False, codec='libx264'):
        self.fps, self.size = fps, size
        self.audio_rate, self.mute, self.codec = audio_rate, mute, codec
        self.clock = AudioClock(audio_rate)
        self.started = time.monotonic()
        self.stop = threading.Event()
        self.queues = {url: queue.Queue(maxsize=max(32, fps*2)) for url in outputs}
        self.resets = {url: threading.Event() for url in outputs}
        self.threads = []
        self.transports = {}
        self.last_video_pts = -1
        for url in outputs:
            thread = threading.Thread(target=self._run, args=(url,),
                                      name='weather-encoder', daemon=True)
            thread.start()
            self.threads.append(thread)

    def _enqueue(self, item):
        for url, pending in self.queues.items():
            if self.resets[url].is_set():
                continue
            try:
                pending.put_nowait(item)
            except queue.Full:
                # Reconnect both tracks together instead of accumulating latency
                # or dropping audio in the middle of an otherwise intact stream.
                self.resets[url].set()

    def submit_audio(self, memory):
        pcm = bytes(memory)
        samples = len(pcm)//4
        if not samples:
            return
        pts = self.clock.feed(samples)
        self._enqueue(('audio', pts, pcm))

    def submit_video(self, pixels):
        seconds = (time.monotonic()-self.started) if self.mute else self.clock.seconds()
        if seconds is None:
            return
        pts = round(seconds*self.fps)
        if pts <= self.last_video_pts:
            return
        self.last_video_pts = pts
        self._enqueue(('video', pts, pixels))

    def _open(self, url):
        target = url
        if url.startswith(('rtmp://', 'rtmps://')):
            target = RTMPTransport(url)
            self.transports[url] = target
        container = av.open(target, mode='w', format='flv')
        video = container.add_stream(self.codec, rate=self.fps)
        video.width, video.height = self.size
        video.pix_fmt = 'yuv420p'
        video.codec_context.thread_count = 2
        video.codec_context.gop_size = self.fps*2
        if self.codec == 'libx264':
            video.options = {'preset': 'veryfast', 'tune': 'zerolatency',
                             'x264-params': f'keyint={self.fps*2}:min-keyint={self.fps*2}:scenecut=0',
                             'bf': '0'}
        audio = None
        if not self.mute:
            audio = container.add_stream('aac', rate=self.audio_rate)
            audio.layout = 'stereo'
            audio.bit_rate = 128000
        return container, video, audio

    def _clear(self, pending):
        while True:
            try:
                pending.get_nowait()
            except queue.Empty:
                return

    def _run(self, url):
        pending = self.queues[url]
        reset = self.resets[url]
        while not self.stop.is_set():
            container = None
            try:
                container, video, audio = self._open(url)
                self._clear(pending)
                reset.clear()
                origin = None
                last_keyframe = -self.fps*2
                while not self.stop.is_set() and not reset.is_set():
                    try:
                        kind, pts, payload = pending.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    rate = self.fps if kind == 'video' else self.audio_rate
                    if origin is None:
                        origin = Fraction(pts, rate)
                    local_pts = pts-round(origin*rate)
                    if local_pts < 0:
                        continue
                    if kind == 'video':
                        frame = av.VideoFrame.from_ndarray(payload, format='rgb24')
                        frame = frame.reformat(width=self.size[0], height=self.size[1], format='yuv420p')
                        frame.pts, frame.time_base = local_pts, Fraction(1, self.fps)
                        if local_pts-last_keyframe >= self.fps*2:
                            frame.pict_type = PictureType.I
                            last_keyframe = local_pts
                        encoder = video
                    else:
                        frame = av.AudioFrame(format='s16', layout='stereo', samples=len(payload)//4)
                        frame.planes[0].update(payload)
                        frame.sample_rate = self.audio_rate
                        frame.pts, frame.time_base = local_pts, Fraction(1, self.audio_rate)
                        encoder = audio
                    for packet in encoder.encode(frame):
                        container.mux(packet)
                if self.stop.is_set():
                    for encoder in (video, audio):
                        if encoder:
                            for packet in encoder.encode(None):
                                container.mux(packet)
            except Exception:
                log.exception('Weather output interrupted; reconnecting')
                # Close the pipe first so writing a trailer cannot block on
                # the same broken connection that interrupted publication.
                transport = self.transports.pop(url, None)
                if transport:
                    transport.close()
            finally:
                if container:
                    try:
                        container.close()
                    except Exception:
                        log.warning('Could not close interrupted weather output')
                transport = self.transports.pop(url, None)
                if transport:
                    transport.close()
            self._clear(pending)
            if not self.stop.is_set():
                self.stop.wait(2)

    def close(self):
        self.stop.set()
        for thread in self.threads:
            thread.join(timeout=6)
