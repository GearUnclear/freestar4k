"""Check real PyAV -> bounded FFmpeg transport -> MediaMTX publication."""
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from broadcast_encoder import BroadcastEncoder
from test_broadcast_encoder import BroadcastEncoderTests


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    config = directory/'mediamtx.yml'
    config.write_text(f'''logLevel: error
rtsp: no
webrtc: no
srt: no
moq: no
hls: no
rtmpAddress: 127.0.0.1:{port}
paths:
  test/live:
    source: publisher
''')
    server = subprocess.Popen(['/usr/local/bin/mediamtx', str(config)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    encoder = None
    receiver = None
    producer = None
    try:
        deadline = time.monotonic()+5
        while True:
            try:
                with socket.create_connection(('127.0.0.1',port), timeout=.2):
                    break
            except OSError:
                if time.monotonic()>deadline:
                    raise RuntimeError('Test media server never started')
                time.sleep(.1)
        url = f'rtmp://127.0.0.1:{port}/test/live'
        encoder = BroadcastEncoder([url],30,(160,120))
        checks = BroadcastEncoderTests()
        producer = threading.Thread(target=checks.produce, args=(encoder,12))
        producer.start()
        recording = directory/'received.flv'
        # RTMP readers are allowed only after the first publisher packet.
        for attempt in range(10):
            receiver = subprocess.Popen(['ffmpeg','-nostdin','-hide_banner','-loglevel','error',
                '-y','-rw_timeout','3000000','-i',url,'-t','6','-c','copy',str(recording)],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(.5)
            if receiver.poll() is None:
                break
        receiver.wait(timeout=15)
        assert receiver.returncode == 0, 'RTMP capture failed'
        producer.join(timeout=15)
        assert not producer.is_alive(), 'Producer did not finish'
        checks.inspect(recording)
        assert not any(thread.is_alive() for thread in encoder.threads), 'Encoder did not close'
        print('Real RTMP transport passed: normal video cadence, keyframes, continuous AAC, clean shutdown')
    finally:
        if encoder:
            encoder.close()
        if receiver and receiver.poll() is None:
            receiver.kill();receiver.wait()
        if producer:
            producer.join(timeout=15)
        server.terminate();server.wait(timeout=5)
