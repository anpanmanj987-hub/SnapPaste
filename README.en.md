# SnapPaste

Send a photo from your phone browser to the Windows image clipboard. Take or select a photo, check the local preview, press Send, then paste in your PC application with `Ctrl+V`. No phone app or external image processing service is required.

**0.1.0a2 / MIT / alpha.** [日本語](README.md)

Version 0.1.0a2 is the post-review source release. [Validation](docs/VALIDATION.md) separates the current Linux checks from historical 0.1.0a1 macOS evidence.

## Install and run

Requires Python 3.10 or newer. From this source directory on Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python -m snappaste --help
```

The default listener is `127.0.0.1:8766`. To receive from a phone on the same network, explicitly select your PC's LAN IPv4 address (find it with `ipconfig`):

```powershell
.venv\Scripts\python -m snappaste --host 192.168.1.20
```

Replace the example address with your PC's address. A wildcard listener requires an explicit address for the QR URL:

```powershell
.venv\Scripts\python -m snappaste --host 0.0.0.0 --advertise 192.168.1.20
```

Open the printed QR or join URL on your phone. Select a photo and send it after checking the preview. Paste on the PC **after the clipboard confirmation appears**. Stop the host with `Ctrl+C`. The QR/URL grants permission to overwrite the clipboard during that run: keep it private. Restarting generates a new capability.

## Dry run

Other operating systems require explicit `--dry-run`; Windows can use it too. It exercises transfer, orientation, resizing and DIB generation, but **does not update any clipboard or save the image**. The UI and response identify dry-run operation.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m snappaste --dry-run
```

## Image processing

JPEG, PNG and static WebP are supported. Convert HEIC to JPEG first. Animated, unsupported and corrupt images are rejected. Defaults: 25 MiB compressed upload, 50 million input pixels, and a 1920px output long edge. Aspect ratio is preserved and small images are never enlarged. EXIF orientation is applied; transparency is flattened onto white.

Windows receives opaque 24-bit RGB `CF_DIB` data. A fresh pixel image prevents source EXIF/GPS/XMP/ICC/comments from reaching the clipboard. No ICC color conversion is performed, so wide-gamut photos may change appearance. The original file reaches the host before metadata is stripped; uploads are not saved to disk by default.

`--max-edge`, `--max-mib` and `--max-pixels` adjust the limits. Upload/pixel limits cannot exceed the safety ceilings above. `--no-qr` prints only the URL.

## Network scope

This is unencrypted LAN HTTP. Use a trusted network and do not expose the port to the Internet. Photos and the capability are visible to a network observer. No CDN, analytics, cloud or external processing calls are required.

Each run uses a new random token. The host checks exact Host/Origin, allows one processing job and at most eight connections, and uses a default ten-second socket read timeout. Camera capture uses a file input, so `getUserMedia` is unnecessary. The actual picker/camera behavior depends on the phone browser.

For connectivity issues, check the PC IPv4 address, same-network access, receiver process, and Windows private-network firewall settings. Guest-network client isolation or a VPN may prevent communication.

## Development and evidence

```sh
python -m pip install .
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

Tests cover pixels/DIB, real HTTP authentication/limits, CLI validation, and Win32 ownership failure branches using a fake OS boundary. These tests do not prove real Windows clipboard behavior. **Windows paste targets and physical phone camera flows remain unverified.** See [validation](docs/VALIDATION.md), [implementation report](docs/IMPLEMENTATION-REPORT.md), [design](docs/DESIGN.md), [publishing](docs/PUBLISHING.md), and [handoff](docs/HANDOFF.md).
