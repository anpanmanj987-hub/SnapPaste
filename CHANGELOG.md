# Changelog

## 0.1.0a5 — 2026-10-06

- English interface. The phone page follows the browser language (Japanese when it comes first, English otherwise), with a toggle that is remembered and a `?lang=ja|en` override. Replies from the host, including image-validation errors, follow the page's `Accept-Language`.
- The command line speaks English or Japanese: `SNAPPASTE_LANG`, then `LC_ALL`/`LC_MESSAGES`/`LANG`, then the Windows display language.
- Fix: the page did not load when its URL carried a query string such as `?lang=en`; static assets are now matched on the path only.
- Tests check that both languages define the same keys, that every key used by the page and the host exists, and the language rules.

## 0.1.0a4 — 2026-10-06

- Fix: rejected uploads on Windows (wrong token after a restart, wrong Origin, busy, too large) could reach the phone as a connection reset, so the page said it could not reach the PC instead of showing the reason. The host now discards a bounded remainder of the unread body before closing.
- When the clipboard cannot be opened, the message now says the PC may be locked: Windows refuses clipboard access to desktop apps while the session is locked.
- The page footer no longer shows a stale version number.
- Verified on real Windows 11: the image reaches the native clipboard with orientation applied, stays there after SnapPaste exits, and is readable through the formats Windows synthesizes. See [docs/VALIDATION.md](docs/VALIDATION.md).
- README rewritten with screenshots and a no-clone install; internal working notes removed from `docs/`.

## 0.1.0a3 — 2026-10-05

- Fix `--help` and status output crashing under CP1252 or ASCII console encodings, including redirected Windows output. Unsupported characters are escaped; UTF-8 output keeps Japanese text.

## 0.1.0a2 — 2026-10-05

- Revalidated release of 0.1.0a1 with no behaviour change.

## 0.1.0a1 — 2026-10-03

- First alpha: phone page with camera and library pickers, preview before sending, EXIF orientation, metadata stripping, 24-bit `CF_DIB` clipboard output, explicit `--dry-run` mode, token/Host/Origin checks and upload limits.
