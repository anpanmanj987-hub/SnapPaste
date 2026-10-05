"""Malformed header values must produce an auth rejection, not a handler crash."""
from http.client import HTTPMessage
from types import SimpleNamespace
import unittest
from snappaste.server import RequestHandler


class Probe(RequestHandler):
    def _error(self, status, message):
        self.rejection = status


class AuthTests(unittest.TestCase):
    def test_non_ascii_capability_returns_401(self):
        handler = Probe.__new__(Probe)
        handler.server = SimpleNamespace(authority="127.0.0.1:8766", token="a" * 43)
        handler.headers = HTTPMessage()
        handler.headers.add_header("Host", "127.0.0.1:8766")
        handler.headers.add_header("X-SnapPaste-Token", "caf\u00e9")
        try:
            accepted = handler._authorized()
        except TypeError as error:
            self.fail(f"malformed header crashed authentication instead of rejecting: {error}")
        self.assertFalse(accepted)
        self.assertEqual(handler.rejection, 401)
