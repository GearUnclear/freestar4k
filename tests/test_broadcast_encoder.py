import tempfile
import threading
import time
import unittest
from pathlib import Path

import av
import numpy as np

from broadcast_encoder import BroadcastEncoder
from broadcast_support import FrameClock


class BroadcastEncoderTests(unittest.TestCase):
    def produce(self, encoder, seconds):
        stop = threading.Event()
        def mix():
            next_callback = time.monotonic()
            pcm = bytes(8192*4)
            while not stop.is_set():
                encoder.submit_audio(pcm)
                next_callback += 8192/44100
                stop.wait(max(0, next_callback-time.monotonic()))
        audio = threading.Thread(target=mix)
        audio.start()
        clock = FrameClock()
        start = time.monotonic()
        frame = np.zeros((120,160,3), dtype=np.uint8)
        while time.monotonic()-start < seconds:
            clock.tick(30)
            frame = np.full_like(frame, int((time.monotonic()-start)*25)%255)
            encoder.submit_video(frame)
        stop.set();audio.join();encoder.close()

    def inspect(self, path):
        with av.open(str(path)) as recording:
            video = list(recording.decode(video=0))
        with av.open(str(path)) as recording:
            audio = list(recording.decode(audio=0))
        timestamps = [float(frame.pts*frame.time_base) for frame in video]
        keys = [float(frame.pts*frame.time_base) for frame in video if frame.key_frame]
        self.assertGreater(len(video), 100)
        self.assertTrue(all(b>a for a,b in zip(timestamps,timestamps[1:])))
        fps = (len(video)-1)/(timestamps[-1]-timestamps[0])
        self.assertGreater(fps, 27)
        self.assertLess(fps, 32)
        self.assertTrue(all(b-a<=2.15 for a,b in zip(keys,keys[1:])))
        self.assertTrue(all(abs(float(b.pts*b.time_base)-float(a.pts*a.time_base)-a.samples/44100)<0.002
                            for a,b in zip(audio,audio[1:])))
        self.assertLess(abs(float(audio[-1].pts*audio[-1].time_base)-timestamps[-1]),0.3)

    def test_real_h264_aac_has_normal_frame_rate_and_continuous_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'stream.flv'
            encoder = BroadcastEncoder([str(path)],30,(160,120))
            self.produce(encoder,6)
            self.inspect(path)

    def test_failed_initial_connection_retries_without_losing_audio_or_thread(self):
        class InterruptedEncoder(BroadcastEncoder):
            attempts = 0
            def _open(self,url):
                self.attempts += 1
                if self.attempts == 1:
                    raise OSError('Injected unavailable media server')
                return super()._open(url)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'reconnected.flv'
            encoder = InterruptedEncoder([str(path)],30,(160,120))
            self.produce(encoder,7)
            self.assertGreaterEqual(encoder.attempts,2)
            self.inspect(path)


if __name__ == '__main__':
    unittest.main()
