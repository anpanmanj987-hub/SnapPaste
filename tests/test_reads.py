"""IO boundary tests catch trickle uploads extending the total read deadline."""
import io
import unittest
from unittest.mock import patch

try:
    from snappaste.server import read_upload
except ImportError:
    read_upload = None


class Connection:
    def settimeout(self, seconds):
        pass


class ChunkedBytes(io.BytesIO):
    def read1(self, size):
        return super().read1(min(size, 1))


class ReadTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(read_upload, "total upload deadline is not implemented")

    def test_read_returns_exact_image_bytes(self):
        self.assertEqual(read_upload(io.BytesIO(b"photoignored"), Connection(), 5, 1), b"photo")

    def test_premature_eof_is_rejected(self):
        with self.assertRaises(EOFError):
            read_upload(io.BytesIO(b"ab"), Connection(), 3, 1)

    def test_trickle_cannot_extend_total_deadline(self):
        with patch("snappaste.server.time.monotonic", side_effect=[0, 0.05, 0.10, 0.15, 0.25]):
            with self.assertRaises(TimeoutError):
                read_upload(ChunkedBytes(b"abc"), Connection(), 3, 0.2)

    def test_last_chunk_cannot_finish_after_deadline(self):
        with patch("snappaste.server.time.monotonic", side_effect=[0, 0.05, 0.25]):
            with self.assertRaises(TimeoutError):
                read_upload(io.BytesIO(b"abc"), Connection(), 3, 0.2)
