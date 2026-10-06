"""Real sockets catch auth bypass, missing body caps, and false success on backend failure."""
import http.client
import io
import json
import socket
import threading
import unittest
from PIL import Image

try:
    from snappaste.server import ServerConfig, make_server
    from snappaste.clipboard import DryRunClipboard, ClipboardError
except ImportError:
    make_server = None


def photo():
    output = io.BytesIO()
    Image.new("RGBA", (4, 2), (255, 0, 0, 0)).save(output, "PNG")
    return output.getvalue()


class BrokenClipboard:
    mode = "windows"
    def write(self, data):
        raise ClipboardError("clipboard busy")
    def close(self):
        pass


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(make_server, "HTTP service is not implemented")
        self.server = make_server(ServerConfig(port=0, max_bytes=1024, max_pixels=100,
                                               max_edge=2, socket_timeout=0.2),
                                  DryRunClipboard(), token="t" * 43)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.port = self.server.server_address[1]
        self.origin = f"http://127.0.0.1:{self.port}"

    def request(self, path="/api/upload", body=None, method="POST", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        supplied = {"Host": f"127.0.0.1:{self.port}", "Origin": self.origin,
                    "X-SnapPaste-Token": "t" * 43, "Content-Type": "application/octet-stream"}
        if headers:
            for key, value in headers.items():
                if value is None:
                    supplied.pop(key, None)
                else:
                    supplied[key] = value
        connection.request(method, path, body=body, headers=supplied)
        response = connection.getresponse()
        content = response.read()
        result = (response.status, dict(response.getheaders()), content)
        connection.close()
        return result

    def test_authenticated_upload_returns_dry_run_and_normalized_dimensions(self):
        status, headers, body = self.request(body=photo())
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["clipboard_updated"])
        self.assertEqual((result["width"], result["height"]), (2, 1))
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_status_requires_token(self):
        self.assertEqual(self.request("/api/status", method="GET", headers={"X-SnapPaste-Token": None})[0], 401)
        self.assertEqual(self.request("/api/status", method="GET")[0], 200)

    def test_wrong_token_rejected(self):
        self.assertEqual(self.request(body=photo(), headers={"X-SnapPaste-Token": "wrong"})[0], 401)

    def test_non_ascii_token_is_rejected_without_disconnect(self):
        self.assertEqual(self.request(body=photo(), headers={"X-SnapPaste-Token": "caf\u00e9"})[0], 401)

    def test_wrong_host_rejected_for_static_and_api(self):
        for path, method in [("/", "GET"), ("/api/upload", "POST")]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path, photo(), method, {"Host": "attacker.test"})[0], 403)

    def test_mutation_origin_is_exact_and_required(self):
        for origin in [None, "null", "https://attacker.test", self.origin + "/", self.origin + ".evil"]:
            with self.subTest(origin=origin):
                self.assertEqual(self.request(body=photo(), headers={"Origin": origin})[0], 403)

    def test_preflight_is_not_allowed(self):
        status, headers, _ = self.request(method="OPTIONS")
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_invalid_and_unsupported_image_do_not_return_success(self):
        self.assertGreaterEqual(self.request(body=b"broken")[0], 400)

    def test_oversized_body_is_rejected_before_reading(self):
        self.assertEqual(self.request(body=b"x" * 1025)[0], 413)

    def test_missing_length_and_chunked_are_rejected(self):
        for extra in ["", "Transfer-Encoding: chunked\r\n"]:
            with self.subTest(extra=extra):
                sock = socket.create_connection(("127.0.0.1", self.port), timeout=2)
                sock.sendall((f"POST /api/upload HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n"
                              f"Origin: {self.origin}\r\nX-SnapPaste-Token: {'t' * 43}\r\n"
                              f"{extra}\r\n").encode())
                self.assertIn(b" 411 ", sock.recv(4096))
                sock.close()

    def test_slow_or_truncated_body_times_out(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=2)
        sock.sendall((f"POST /api/upload HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n"
                      f"Origin: {self.origin}\r\nX-SnapPaste-Token: {'t' * 43}\r\n"
                      "Content-Length: 10\r\n\r\nx").encode())
        self.assertIn(b" 408 ", sock.recv(4096))
        sock.close()

    def test_rejection_reply_survives_unread_photo(self):
        # Windows resets a socket closed with unread data; the reply must still arrive.
        for _ in range(10):
            self.assertEqual(self.request(body=b"x" * 1000, headers={"X-SnapPaste-Token": "old"})[0], 401)

    def test_busy_processing_is_rejected(self):
        self.server.processing.acquire()
        try:
            self.assertEqual(self.request(body=photo())[0], 429)
        finally:
            self.server.processing.release()

    def test_clipboard_failure_returns_503(self):
        self.server.clipboard = BrokenClipboard()
        status, _, content = self.request(body=photo())
        self.assertEqual(status, 503)
        self.assertFalse(json.loads(content)["ok"])

    def test_static_assets_are_served_with_security_headers(self):
        for path, mime in [("/", "text/html"), ("/app.js", "text/javascript"),
                           ("/style.css", "text/css"), ("/api.mjs", "text/javascript")]:
            with self.subTest(path=path):
                status, headers, body = self.request(path, method="GET")
                self.assertEqual(status, 200)
                self.assertTrue(headers["Content-Type"].startswith(mime))
                self.assertGreater(len(body), 20)
                self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_path_traversal_cannot_read_files(self):
        self.assertEqual(self.request("/../pyproject.toml", method="GET")[0], 404)


if __name__ == "__main__":
    unittest.main()
