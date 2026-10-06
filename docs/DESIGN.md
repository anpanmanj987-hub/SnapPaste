# SnapPaste design / 設計

Python 3.10+, Pillow 12.3, qrcode 8.2, standard-library HTTP server, local HTML/CSS/JavaScript.

## Data flow

```text
phone file input → local blob preview → explicit Send
  → raw binary POST /api/upload
  → authenticate token + exact Host + exact Origin
  → bounded decode → EXIF transpose → white alpha composite
  → aspect-preserving thumbnail → fresh RGB pixels
  → 24-bit DIB → Windows native worker / explicit dry-run
  → JSON confirmation or error → phone status
```

`images.py` knows image formats and DIB bytes. `clipboard.py` owns Windows resources. `server.py` owns HTTP policy and limits. `__main__.py` owns startup, backend selection and local QR display. The UI is served from a fixed allowlist of four resources; uploaded originals are never served back.

## Image contract

Only JPEG, PNG and WebP decoders are enabled with `Image.open(formats=...)`. Image MIME names or filenames are not trusted. Animated images are rejected. Compressed size is checked before decoding; pixel count is checked before loading. Pillow decompression-bomb warnings are promoted to errors and its built-in safety limit remains enabled. Decode errors return an error response, not partial success.

EXIF orientation is applied before output resizing. The resulting RGBA pixels are composited onto opaque white, then reduced with LANCZOS to the configured long edge. Small inputs remain their original size. A new `Image.frombytes("RGB", ...)` prevents original metadata dictionaries, EXIF/GPS, XMP, ICC, text/comments or thumbnails from being copied into output.

This alpha version strips rather than applies ICC profiles. Wide-gamut color accuracy remains a known limitation. Orientation handling does not imply metadata stripping by itself; the fresh-pixel step enforces that separate contract.

The DIB contains a 40-byte `BITMAPINFOHEADER`, positive height, 24 bits/pixel, `BI_RGB=0`, zero resolution/color-table fields, and bottom-up BGR rows. Each row is padded with zeros to a multiple of four bytes. No 14-byte BMP file header is included. Source metadata cannot be represented in this deliberately minimal header/pixel payload. Transparency preservation with CF_DIBV5 is outside this version.

## Clipboard lifetime

One Windows worker creates a message-only native `STATIC` window and pumps messages on the same thread. Its nonzero HWND is passed to `OpenClipboard`. Win32 calls declare pointer-width handle returns, `SIZE_T`, WPARAM/LPARAM and argument signatures explicitly.

The writer allocates movable global memory, locks/copies/unlocks it, and only then attempts to open/empty/write the clipboard. Open contention retries at most 15 times with 50ms pauses (14 pauses maximum). A successful `SetClipboardData(CF_DIB, handle)` transfers ownership to the OS. The application frees only handles that did not transfer; it always attempts to close an opened clipboard. Zero from `GlobalUnlock` with last error zero is treated as a successful final unlock.

While the Windows session is locked, `OpenClipboard` fails with `ERROR_ACCESS_DENIED` for desktop applications. After the bounded retries this surfaces as a "clipboard unavailable" failure that names the lock screen as a likely cause; it is never reported as a copy.

If `EmptyClipboard` succeeds and a subsequent native call fails, the previous clipboard contents can be lost. If closing fails after a successful transfer, the response reports failure but the transferred memory is still owned by Windows. A five-second worker wait limits how long the HTTP request waits; an already-running native API call cannot be forcibly cancelled and may complete later. The timeout message directs users to inspect the PC. These cases do not display a copy-success message.

Dry-run produces the same normalized DIB and discards it. It neither writes any OS clipboard nor saves a processed image. Both `/api/status` and upload success responses identify dry-run.

## Languages

Every message people see is keyed in `messages.py` (Japanese/English pairs) for the host and the command line, and in `static/i18n.mjs` for the page. `ImageValidationError` carries a key, so the same rejection is worded in each client's language. The host reads the first `ja` or `en` tag of `Accept-Language` and defaults to English; the page sends its own language. The command line uses `SNAPPASTE_LANG`, then the POSIX locale variables, then the Windows display language.

## HTTP policy and bounds

The CLI defaults to loopback IPv4 and port 8766. LAN listening is explicit. Binding `0.0.0.0` requires a usable `--advertise` IPv4 for the exact accepted authority. No network discovery uses an external service. IPv6 and DNS names are outside the first version.

A fresh `secrets.token_urlsafe(32)` capability is generated per run. The printed join URL uses `#token=...`, so the token is absent from HTTP request paths. JavaScript sends it in `X-SnapPaste-Token`; comparison uses constant-time comparison after rejecting non-ASCII values. No request logging prints paths, headers, or images. Startup deliberately displays the join capability locally to the person operating the host.

Static content and APIs require one exact Host header. APIs require one valid token. Mutations additionally require one exact Origin header; missing/`null`, cross-origin and duplicate values are rejected. Cross-origin OPTIONS requests are rejected and no CORS response grants access. The UI uses fetch's default `cors` mode: explicitly setting `same-origin` mode together with `no-referrer` can make a POST Origin header `null`.

Only raw-body POST uploads are accepted. Content-Length must be a single positive ASCII integer and Transfer-Encoding is refused. Default bounds are 25MiB compressed upload, 50 million input pixels, 1920px output edge, 8 simultaneous connections and 1 processing job. A socket inactivity timeout covers request parsing; a monotonic total deadline covers the complete upload body. Default timeout is 10 seconds. Rejected unread bodies cannot become later requests because every response closes the connection. Before closing, the host discards what remains of a rejected body (up to the upload limit, for at most two seconds); closing a socket with unread data makes Windows send a reset, and the phone would then see a network error instead of the reply. There is no multipart parser, input filename path, or automatic image disk storage.

Assets are local. CSP restricts scripts/styles/connections to the same origin, permits blob images for preview, disables framing and forms, and sets a fixed base policy. Responses use no-store, no-referrer and nosniff. This does not provide network encryption: original photo bytes and capabilities traverse plain HTTP, including original metadata before host normalization.

## Primary references

- [Microsoft OpenClipboard](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard)
- [Microsoft SetClipboardData and memory ownership](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata)
- [Microsoft GlobalUnlock](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-globalunlock)
- [Microsoft BITMAPINFOHEADER / row stride](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapinfoheader)
- [Python ctypes](https://docs.python.org/3/library/ctypes.html)
- [Python secrets](https://docs.python.org/3/library/secrets.html)
- [Pillow ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html)
- [Pillow security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html)
- [W3C HTML Media Capture](https://www.w3.org/TR/html-media-capture/)
- [Fetch Origin header](https://fetch.spec.whatwg.org/#origin-header)
