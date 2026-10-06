"""CLI contracts catch unsafe implicit LAN/native startup and invalid limits."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

from snappaste import __version__


class CLITests(unittest.TestCase):
    def run_cli(self, *args, encoding=None, lang="ja"):
        root = Path(__file__).resolve().parents[1]
        environment = dict(os.environ, PYTHONPATH=str(root / "src"), SNAPPASTE_LANG=lang)
        if encoding is not None:
            environment["PYTHONIOENCODING"] = encoding
        return subprocess.run([sys.executable, "-m", "snappaste", *args],
                              capture_output=True, text=True, encoding=encoding,
                              env=environment, timeout=5)

    def test_help_describes_explicit_dry_run_and_lan_options(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--advertise", result.stdout)

    def test_help_succeeds_with_legacy_or_ascii_output(self):
        for encoding in ("cp1252", "ascii"):
            with self.subTest(encoding=encoding):
                result = self.run_cli("--help", encoding=encoding)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--dry-run", result.stdout)
                self.assertIn("--advertise", result.stdout)
                self.assertNotIn("UnicodeEncodeError", result.stderr)

    def test_utf8_help_preserves_japanese(self):
        result = self.run_cli("--help", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("スマホの写真", result.stdout)

    def test_english_help_when_requested(self):
        result = self.run_cli("--help", encoding="utf-8", lang="en")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("send phone photos to the Windows image clipboard", result.stdout)
        self.assertNotIn("スマホ", result.stdout)

    def test_version_is_available_without_server(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn(__version__, result.stdout)

    @unittest.skipIf(sys.platform == "win32", "native mode is valid on Windows")
    def test_other_platform_requires_explicit_dry_run(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("--dry-run", result.stderr)

    def test_wildcard_bind_requires_usable_advertised_ip(self):
        result = self.run_cli("--dry-run", "--host", "0.0.0.0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--advertise", result.stderr)

    def test_limits_rejected_before_server_creation(self):
        for args in [("--max-edge", "0"), ("--port", "70000"), ("--timeout", "nan")]:
            with self.subTest(args=args):
                result = self.run_cli("--dry-run", *args)
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
