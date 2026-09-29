"""Send an encoded FLV stream through FFmpeg with bounded network writes."""

import os
import select
import subprocess
import time


class RTMPTransport:
    # PyAV 18 uses avio_open for output, which does not receive its options
    # or timeout argument. FFmpeg's protocol options do reach avio_open2.
    def __init__(self, url, timeout=5):
        self.name = url
        self.timeout = timeout
        self.closed = False
        self.process = subprocess.Popen([
            'ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
            '-probesize', '32768', '-analyzeduration', '0',
            '-f', 'flv', '-i', 'pipe:0', '-c', 'copy',
            '-rw_timeout', str(int(timeout*1_000_000)),
            '-flvflags', 'no_duration_filesize', '-flush_packets', '1',
            '-f', 'flv', url,
        ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
           stderr=subprocess.DEVNULL, bufsize=0)
        os.set_blocking(self.process.stdin.fileno(), False)

    def writable(self):
        return True

    def seekable(self):
        return False

    def write(self, data):
        if self.closed:
            raise OSError('RTMP transport is closed')
        pending = memoryview(data)
        deadline = time.monotonic()+self.timeout
        fd = self.process.stdin.fileno()
        while pending:
            remaining = deadline-time.monotonic()
            if remaining <= 0 or not select.select([], [fd], [], max(0, remaining))[1]:
                raise TimeoutError('RTMP output stopped accepting data')
            try:
                pending = pending[os.write(fd, pending):]
            except BlockingIOError:
                continue
        return len(data)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.process.stdin.close()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
