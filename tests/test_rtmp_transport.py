import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from rtmp_transport import RTMPTransport


class RTMPTransportTests(unittest.TestCase):
    def test_unresponsive_receiver_times_out_and_is_reaped(self):
        # A real process that never reads its input models a wedged output.
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                                   stdin=subprocess.PIPE, bufsize=0)
        with patch('rtmp_transport.subprocess.Popen', return_value=process):
            transport = RTMPTransport('rtmp://example.invalid/stream', timeout=0.2)
        start = time.monotonic()
        try:
            with self.assertRaises(TimeoutError):
                transport.write(bytes(1_000_000))
            self.assertLess(time.monotonic()-start, 1)
        finally:
            transport.close()
        self.assertIsNotNone(process.poll())
        with self.assertRaises(OSError):
            transport.write(b'closed')

    def test_successful_write_preserves_every_byte(self):
        process = subprocess.Popen([sys.executable, '-c',
                                    'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        with patch('rtmp_transport.subprocess.Popen', return_value=process):
            transport = RTMPTransport('rtmp://example.invalid/stream')
        payload = b'encoded stream'*100
        self.assertEqual(transport.write(payload), len(payload))
        transport.close()
        self.assertEqual(process.stdout.read(), payload)
        process.stdout.close()


if __name__ == '__main__':
    unittest.main()
