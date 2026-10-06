# Validation record

This page separates what has been observed on real hardware from what is only covered by automated tests with fixtures.

## Real Windows clipboard check — 2026-10-06 (0.1.0a4)

Environment: Windows 11 (build 26200), Python 3.14.8, Pillow 12.3.0, native mode (no `--dry-run`).

A 400×300 JPEG tagged with EXIF orientation 6, red on the left half and blue on the right, was uploaded over real loopback HTTP with the join token, exactly as the phone page sends it.

| Check | Result |
|---|---|
| HTTP response | 200, `clipboard_updated: true`, 300×400 |
| `CF_DIB` on the clipboard | Present |
| Read back with Pillow `ImageGrab.grabclipboard()` | 300×400, red at the top and blue at the bottom (orientation applied) |
| Read back with .NET `Clipboard.GetImage()` after the SnapPaste process had exited | 300×400, same pixels; formats `DeviceIndependentBitmap`, `Bitmap`, `Format17` (CF_DIBV5) synthesized by Windows |
| Clipboard unavailable (session locked) | Bounded retries, then a 503 failure; no success message, clipboard unchanged |
| Edge (headless), phone-sized viewport | Connects, shows "PCに接続しました", previews a selected photo and enables Send |

The second reader shows the image outlives the host process and is visible to ordinary Windows applications through the formats Windows synthesizes from `CF_DIB`.

The same session found that rejections (wrong token after a restart, wrong Origin, busy, too large) intermittently reached the client as a connection reset on Windows instead of the error reply: 4 of 5 full test runs failed before the fix. The host now discards a bounded remainder of the unread body before closing. 5 of 5 runs passed afterwards.

## English interface — 2026-10-06 (0.1.0a5)

Headless Edge 154 on Windows 11 at a phone-sized viewport: connected, selected a photo and previewed it in English and Japanese. In English no Japanese text remained apart from the language toggle; no script errors. The toggle switched the page in place and a reload without `?lang` kept the choice. This check found that the page returned 404 when its URL carried `?lang=en`; fixed and covered by a test.

## Earlier checks (0.1.0a1–a3, macOS and Linux)

A desktop browser at a 390 px viewport connected to a dry-run host, previewed a selected 960×640 PNG before sending, sent it over real HTTP and showed completion with "clipboard not updated". Wheel and sdist builds were installed outside the checkout and served every static route. 0.1.0a3 fixed `--help` crashing under CP1252 and ASCII console encodings.

## Automated tests

```sh
python -m unittest discover -s tests -v
```

59 cases (one is skipped on Windows because it checks the non-Windows `--dry-run` requirement):

| Area | Cases | What they check |
|---|---:|---|
| Image processing | 12 | All eight EXIF orientations, no metadata in the output, resize without enlarging, transparency on white, grayscale/CMYK/WebP, corrupt and truncated files, size and pixel limits, animation |
| DIB | (in the above) | Widths 1–5, BGR rows and padding, header fields |
| Win32 writer | 9 | High-bit handles, preallocation, ownership transfer, bounded contention retries, every native failure path |
| CLI | 8 | Help/version in Japanese and English, legacy console encodings, explicit dry-run off Windows, wildcard bind needs `--advertise`, invalid limits |
| Upload deadline | 4 | Exact bytes, premature EOF, trickling peers, a last chunk after the deadline |
| Language | 9 | Matching Japanese/English keys, every used key defined, replies follow `Accept-Language`, CLI language rules, pages with a query string |
| Real HTTP | 17 | Upload, dry-run flags, token/Host/Origin rejection, reset-free rejections, preflight, limits, timeouts, busy and clipboard errors, static assets and security headers, path traversal |

GitHub Actions runs the suite on Ubuntu, Windows and macOS with Python 3.10, 3.12 and 3.14 and builds the wheel and sdist. The Win32 writer tests use a fake OS boundary; the real clipboard path is covered by the hardware check above.

## Not yet verified

- [ ] iPhone Safari and Android Chrome over a real LAN: scan the QR code, take a photo, choose from the library, send, and paste.
- [ ] Pasting into Paint, Word, PowerPoint and a browser text box.
- [ ] HEIC from iPhone (Safari usually converts to JPEG on upload), animated and unsupported files: clear rejection messages.
- [ ] Stopping the host mid-send and sending again: an error, never a success claim.
- [ ] Repeated sends and two phones at once: no handle or memory growth.

When you check one of these, please record the Windows build, phone OS and browser, the destination app and the exact result.
