"""Both languages are complete, used keys exist, and replies follow the page language."""
import http.client
import json
import os
import re
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from snappaste.clipboard import DryRunClipboard
from snappaste.messages import MESSAGES, cli_language, language, text
from snappaste.server import ServerConfig, make_server

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "snappaste"
STATIC = PACKAGE / "static"
JAPANESE = re.compile("[぀-ヿ一-鿿]")


def interface_text():
    module = (STATIC / "i18n.mjs").read_text(encoding="utf-8")
    start = module.index("Object.freeze(") + len("Object.freeze(")
    return json.loads(module[start:module.index(");\n", start)])


class InterfaceTextTests(unittest.TestCase):
    def test_both_languages_have_the_same_keys(self):
        table = interface_text()
        self.assertEqual(set(table["ja"]), set(table["en"]))
        for key, value in table["en"].items():
            with self.subTest(key=key):
                self.assertTrue(value.strip())
                if key != "switch_language":  # names the other language in its own script
                    self.assertIsNone(JAPANESE.search(value))

    def test_every_key_used_by_the_page_exists(self):
        keys, used = set(interface_text()["en"]), set()
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        used |= set(re.findall(r'data-i18n="([^"]+)"', html))
        for pairs in re.findall(r'data-i18n-attr="([^"]+)"', html):
            used |= {pair.split(":")[1] for pair in pairs.split(";")}
        for name in ("app.js", "api.mjs"):
            script = (STATIC / name).read_text(encoding="utf-8")
            used |= set(re.findall(r'\bt\("([a-z_]+)"', script))
            used |= set(re.findall(r'message\("([a-z_]+)"', script))
            used |= set(re.findall(r'(?:title|detail): "([a-z_]+)"', script))
            self.assertIsNone(JAPANESE.search(script), name)
        self.assertGreater(len(used), 30)
        self.assertEqual(used - keys, set())


class ServerTextTests(unittest.TestCase):
    def test_every_message_has_both_languages(self):
        for key, (ja, en) in MESSAGES.items():
            with self.subTest(key=key):
                self.assertRegex(ja, JAPANESE)
                self.assertIsNone(JAPANESE.search(en))

    def test_every_key_used_in_python_exists(self):
        used = set()
        for path in PACKAGE.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            used |= set(re.findall(r'(?:\btext|say|_error\(\d+,|ImageValidationError)\(?\s*"([a-z_]+)"', source))
            if path.name != "messages.py":
                self.assertIsNone(JAPANESE.search(source), path.name)
        self.assertGreater(len(used), 30)
        self.assertEqual(used - set(MESSAGES), set())

    def test_language_follows_the_first_ja_or_en_tag(self):
        for header, expected in (("ja-JP,en;q=0.5", "ja"), ("en-US,ja;q=0.5", "en"), ("fr,ja", "ja"), ("de", "en"), (None, "en")):
            with self.subTest(header=header):
                self.assertEqual(language(header), expected)

    def test_cli_language_prefers_explicit_setting_then_locale(self):
        with patch.dict(os.environ, {"SNAPPASTE_LANG": "en", "LANG": "ja_JP.UTF-8"}):
            self.assertEqual(cli_language(), "en")
        with patch.dict(os.environ, {"SNAPPASTE_LANG": "", "LC_ALL": "", "LC_MESSAGES": "", "LANG": "ja_JP.UTF-8"}):
            self.assertEqual(cli_language(), "ja")
        with patch.dict(os.environ, {"SNAPPASTE_LANG": "", "LC_ALL": "en_US.UTF-8"}):
            self.assertEqual(cli_language(), "en")

    def test_details_are_appended_in_the_language(self):
        self.assertEqual(text("cli_start_failed", "en", "port in use"), "Could not start: port in use")
        self.assertEqual(text("cli_start_failed", "ja", "port in use"), "起動できませんでした：port in use")


class LocalizedHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(ServerConfig(port=0), DryRunClipboard(), token="t" * 43)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def status(self, token, language=None):
        port = self.server.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        headers = {"Host": f"127.0.0.1:{port}", "X-SnapPaste-Token": token}
        if language:
            headers["Accept-Language"] = language
        connection.request("GET", "/api/status", headers=headers)
        response = connection.getresponse()
        result = json.loads(response.read())
        connection.close()
        return result

    def test_page_accepts_a_language_query(self):
        port = self.server.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", "/?lang=en", headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b"/app.js", response.read())
        connection.close()

    def test_replies_follow_accept_language(self):
        self.assertEqual(self.status("old", "ja")["message"], MESSAGES["bad_token"][0])
        self.assertEqual(self.status("old", "en-GB")["message"], MESSAGES["bad_token"][1])
        self.assertEqual(self.status("old")["message"], MESSAGES["bad_token"][1])
        self.assertTrue(self.status("t" * 43, "ja")["ok"])


if __name__ == "__main__":
    unittest.main()
