# SnapPaste 0.1.0a3 release notes

MIT-licensed alpha release.

- Fix Japanese help and status output crashing under CP1252 or ASCII, including redirected Windows output. Unsupported characters are escaped without changing the output encoding. UTF-8 output keeps Japanese text.
- Add legacy/ASCII and UTF-8 CLI regression coverage. All 48 local tests pass.
- Version metadata and installation examples now identify 0.1.0a3.

See [validation](VALIDATION.md) and [GitHub Actions](https://github.com/anpanmanj987-hub/SnapPaste/actions/workflows/ci.yml). Physical Windows clipboard, phones and LAN remain unverified.

# Snappaste 0.1.0a2 release notes

MIT-licensed alpha source release. See README and VALIDATION.md for operating assumptions and evidence.

- No image-processing, HTTP or native clipboard behaviour changed from reviewed 0.1.0a1. The version and release documentation identify the revalidated release.
- The full 46-case suite and separate wheel/sdist installations were checked again. Dry-run and fake Win32 results remain distinct from real clipboard validation.

Physical Windows, phones and LAN remain unverified. Do not describe fixture tests, demo or dry-run as native hardware success. RoomPing native browser JSON/CSV saving remains unconfirmed. GitHub publication is a separate owner action.
