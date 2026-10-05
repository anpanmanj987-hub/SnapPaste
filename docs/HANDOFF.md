# Handoff / 引継ぎ

`snappaste/` is a self-contained Python source project. Native Windows mode and explicit cross-platform dry-run share the same normalization and DIB pipeline. Default port: 8766. Runtime dependencies: Pillow and qrcode. Version: 0.1.0a2. License: MIT.

## Commands

```sh
python -m pip install .
python -m snappaste --help
python -m unittest discover -s tests -v
python -m snappaste --dry-run --host 127.0.0.1 --port 8766
```

Native Windows removes `--dry-run`. For a phone, choose the PC's IPv4 with `--host`; wildcard binding additionally needs `--advertise`. Use the printed URL including its token fragment. The exact advertised authority must be used even for a local browser; substituting `localhost` for the printed IPv4 is rejected deliberately.

## HTTP contract

`GET /api/status`: `X-SnapPaste-Token` required, exact Host required. Returns `ok`, `version`, `mode`, `max_bytes`, `max_edge`.

`POST /api/upload`: raw photo bytes, a single positive Content-Length, `X-SnapPaste-Token`, exact Host and Origin. Browser requests use `Content-Type: application/octet-stream`; the decoder detects the real format. No multipart or chunked upload. Successful responses contain `ok`, `dry_run`, `clipboard_updated`, `width`, `height`, `message`. Dry-run always sets `clipboard_updated:false`. Errors contain `ok:false` and a safe Japanese message.

Status codes: 401 token, 403 Host/Origin/preflight, 400 invalid/incomplete length/body, 411 missing length/chunked, 413 size/pixels, 415 format/animation, 422 corrupt decode, 408 timeout, 429 processing busy, 503 clipboard/connection capacity, 500 unexpected processing failure. Assets come from a fixed route allowlist. There is no endpoint that returns the join token or any uploaded original.

## Verification ownership

The controller's final full run passed all 46 tests, including actual HTTP. Browser preview, explicit send, dry-run completion and cancellation passed. Wheel/sdist builds, separate-directory installs and installed real HTTP assets/status/image upload passed. The independent reviewer approved the deadline/auth fixes. See `VALIDATION.md` for confirmed evidence and `IMPLEMENTATION-REPORT.md` for test-first history. Fake-native tests and dry-run are not Windows validation.

## Remaining work before broad release

- Real Windows native HWND lifecycle, clipboard contention and paste-target compatibility.
- Physical iPhone/Android capture and gallery over LAN HTTP, including HEIC handling.
- Real GitHub CI across the declared matrix.
- Optional faithful ICC-to-sRGB conversion and CF_DIBV5 transparency would require new acceptance tests and an explicit feature change.

The source agent performed no git operations, remote publication, installation outside this workspace or native clipboard changes. Plain HTTP and the in-flight-native-call timeout limitation are documented in `DESIGN.md`.
