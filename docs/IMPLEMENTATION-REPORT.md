# SnapPaste implementation report

Date: 2026-10-03. Implementer scope: only `snappaste/**`. Version `0.1.0a1`, MIT. This report records the implementation agent's observed results and labels controller-reported evidence separately. The controller owns the final privileged HTTP suite and package verification.

## Delivered

- Independent src-layout package with `python -m snappaste` and `snappaste` console entry point; loopback default, port 8766, explicit IPv4 LAN binding/advertised address, local terminal QR and per-launch capability.
- Mobile Japanese UI with camera and gallery file inputs, local blob preview, explicit Send, processing/error state, reconnect and reset controls, and persistent dry-run disclosure. No camera stream API, CDN, font service or external processing.
- JPEG/PNG/static-WebP decoder allowlist; compressed-size, input-pixel and decompression-bomb safeguards; animation rejection; EXIF orientation; no enlargement; white transparency flattening; fresh RGB pixels; metadata-free 24-bit bottom-up BGR DIB with DWORD padding.
- Windows worker creates a nonzero message-only HWND, pumps its message queue and uses pointer-width ctypes declarations. Memory is allocated before clearing; clipboard-open contention is bounded; only a successful SetClipboardData transfers ownership; untransferred handles are freed. Close failure is surfaced without freeing transferred memory.
- Fixed asset routes, exact single Host, API token and mutation Origin validation, non-ASCII/duplicate rejection, no CORS, no request logs, no automatic input-image disk storage. Raw-body uploads have a single positive Content-Length, bounded clients, one processing lock, socket timeout and an absolute monotonic body deadline checked before and after each `read1`, including the final read.
- MIT, `.gitignore`, pyproject/MANIFEST static inclusion, GitHub Actions matrix/build artifact workflow, Japanese and English README, design, validation, publishing and handoff documentation.

## TDD and command evidence

Process used: test-driven-development and its writing-good-tests reference. Expectations for all eight orientations and widths 1–5 are independent literals/hand-derived row bytes. Image and HTTP tests exercise Pillow and actual HTTP respectively; fake Win32 is confined to the external OS boundary. Deadline tests use actual reader behavior with a deterministic clock/chunked IO boundary.

Commands below ran from `snappaste/` using the workspace Python, which reported **Python 3.12.14**. Pillow was **12.3.0**. Node syntax verification used **Node 24.19.0**.

| Stage | Command | Observed result |
|---|---|---|
| Initial RED | `PYTHONPATH=src ../.venv/bin/python -m unittest discover -s tests -v` | 34 tests, 34 explicit FAILs for missing image/HTTP/native features, before production code |
| Initial implementation | Same full command | Image12/native8 passed; 14 HTTP cases errored at `socket.bind` with sandbox `Operation not permitted`. No HTTP success claimed |
| CLI RED | `PYTHONPATH=src ../.venv/bin/python -m unittest discover -s tests -p test_cli.py -v` | 5 cases, 7 failures including subtests while `__main__` was absent |
| CLI GREEN | Same CLI command | 5 passed |
| Native-close RED/GREEN | `... -p test_clipboard.py -v` | New close-failure case failed because no error was raised; after fix, all 9 passed and transferred memory remained unfreed |
| Upload-deadline RED/GREEN | `... -p test_reads.py -v` | Initial 3 missing-feature FAILs, then 3 passed; final-chunk deadline regression separately failed before post-read check, then all 4 passed |
| Auth RED/GREEN | `... -p test_auth.py -v` | Non-ASCII header caused real `compare_digest` TypeError, converted to a failing assertion; after ASCII guard, passed |
| Final implementer GREEN | `PYTHONPATH=src ../.venv/bin/python -m unittest discover -s tests -p 'test_[acir]*.py' -v` | **31 tests passed, 0 failures/errors/warnings**, HTTP intentionally excluded because controller owns privileged sockets |
| JavaScript syntax | `node --input-type=module --check < src/snappaste/static/app.js`; `node --check src/snappaste/static/api.mjs` | Both exit 0. An accidental invalid first line in api.mjs was caught by an earlier syntax check and removed before handoff |

The controller additionally reported observing the actual HTTP non-ASCII regression as TypeError/RemoteDisconnected before the guard was fixed. The implementer did not independently run the privileged HTTP GREEN afterward.

Current complete suite: **46 unittest cases** = 12 image/DIB + 9 native boundary + 5 CLI + 4 read-deadline + 1 malformed-auth + 15 real HTTP. On Windows, the other-OS-default CLI case is intentionally skipped.

## Review response

The independent code review identified a body-timeout bypass in buffered `rfile.read(length)`. The implementation now reads available progress with `read1`, resets the socket timeout to the remaining monotonic deadline, checks elapsed time before each read and immediately after every read, and releases the processing lock in the handler's `finally`. The added final-read regression proves a complete body arriving after the deadline cannot enter decoding/clipboard work. Socket-level trickle reproduction and successful next-upload recovery are part of the controller's integration run, not inferred from the clock-boundary test.

The review found no important native ABI/ownership defect and independently reported image12/native9 tests passing. The implementer retains the real-Windows verification limitation.

## Limits and remaining evidence

- **Windows clipboard, hidden-window message pumping and actual paste into Paint/Office/other apps are not verified on this macOS machine.** Boundary tests do not change that status.
- **Physical smartphone capture/gallery flows are unverified.** Browser preview and raw upload are implemented; actual picker behavior is browser-specific.
- Final full HTTP, real browser walkthrough, wheel/sdist build, bundled-asset inventory and separate-directory installed startup are controller-owned. No package-build or independently observed browser-success claim is made by the implementer.
- Controller-reported browser walkthrough succeeded: current token URL, connection/dry-run state, synthetic 960×640 PNG gallery selection, local preview, explicit real-HTTP Send, 960×640 completion with clipboard-not-updated message; mobile viewport had no horizontal overflow. This was not a physical-phone or Windows-native test. Details are in `VALIDATION.md`.
- LAN HTTP is unencrypted. Original metadata is present in the upload until normalization on the host. Default image bytes are not written to disk.
- Transparency is flattened onto white; ICC profiles are stripped without sRGB color conversion. HEIC, animation, IPv6, DNS names and Internet deployment are outside this alpha.
- A native failure after EmptyClipboard can lose previous clipboard contents. A timed-out native API already in progress cannot be forcibly cancelled and may complete later; the UI reports uncertainty/error, never copy success.
- GitHub CI exists but has not been run remotely. No git, remote publication or Windows clipboard action was performed by this agent.

See [VALIDATION.md](VALIDATION.md) for manual acceptance checklists and [HANDOFF.md](HANDOFF.md) for API/startup contracts.
