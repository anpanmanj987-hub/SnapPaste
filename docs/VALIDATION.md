# Validation / 検証

## 0.1.0a3 console-encoding fix on 2026-10-05

The new regression reproduced `UnicodeEncodeError` under CP1252 and ASCII before the fix. CLI startup now preserves each output encoding and escapes characters it cannot represent; UTF-8 retains Japanese text. This applies to both stdout and stderr.

On macOS arm64, Python 3.12.14, Pillow 12.3.0 and qrcode 8.2, all **48 unittest cases passed with zero skips** after installing into a fresh virtual environment. GitHub CI results are available in [Actions](https://github.com/anpanmanj987-hub/SnapPaste/actions/workflows/ci.yml). Native Windows clipboard and physical-phone/LAN checks below remain open. Earlier records are historical.

## 0.1.0a2 post-review checks on 2026-10-05

Observed in the fix session: Linux x86_64, Python 3.12.14, Pillow 12.3.0 (PanelPop/SnapPaste), qrcode 8.2, Node 24.19.0 (RoomPing), setuptools 84.0.0, build 1.6.1. **46 Python unittest cases passed, zero failures and zero skips.** Across all three projects: 120 tests.

- No image-processing, HTTP or native clipboard behaviour changed from reviewed 0.1.0a1. The version and release documentation identify the revalidated release.
- The full 46-case suite and separate wheel/sdist installations were checked again. Dry-run and fake Win32 results remain distinct from real clipboard validation.

Wheel and sdist builds succeeded. Each distribution was installed separately into a newly created virtual environment without system site packages, from a working directory outside the checkout and with PYTHONPATH removed. Import location, version, module and console-script help/version, pip check, every bundled static route and authenticated loopback HTTP operations passed. PanelPop used only synthetic demo input; SnapPaste used only dry-run normalization; RoomPing checked QR, run start/end and exact 1,024-byte transfers. These checks do not verify native Windows or physical LAN/phone performance.

No Windows desktop is available in this environment. Physical Windows capture/input/clipboard, phones and LAN remain unverified. The local Playwright package has no installed browser executable, so the changed UI was not run in a real browser during this fix session. JSON/CSV native browser save/reopen remains unconfirmed; JSON generation/round-trip is tested in Node. GitHub CI and publication have not run. The original macOS evidence below is historical 0.1.0a1 evidence supplied with the source, not work performed in this fix session.

## Historical 0.1.0a1 record

Record date: 2026-10-03. The implementer used macOS, Python 3.12.14 and Pillow 12.3.0. The first automated run intentionally preceded production modules and failed 34 tests with explicit missing-feature assertions. CLI, native-close and body-deadline/auth regressions also had observed RED/GREEN cycles. See [implementation report](IMPLEMENTATION-REPORT.md) for the command record.

## Automated coverage

Run from the project directory after `python -m pip install .`:

```sh
python -m unittest discover -s tests -v
```

From the source checkout without installation:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite currently has 48 unittest cases; subtests add orientation, format, width and invalid-value variations.

| Area | Cases | Observable contract |
|---|---:|---|
| Image processing | 12 | All eight EXIF orientations, metadata absence in normalized/encoded output, resize/no enlargement, RGBA/palette transparency, JPEG grayscale/CMYK/WebP, corruption/truncation, size/pixel limits, animation |
| DIB | Included above | Widths 1–5, independently expected BGR rows/padding/header, decoded top-row color |
| Win32 writer boundary | 9 | High-bit handles, valid HWND, preallocation, ownership transfer, bounded contention retry, allocation/lock/empty/set/close failure |
| CLI | 7 | Help/version, explicit other-OS dry-run, explicit wildcard advertised IPv4, invalid numeric/NaN settings rejected before bind |
| Upload IO deadline | 4 | Exact body bytes, premature EOF, trickle deadline and final-read overrun using a deterministic clock and stream boundary |
| Malformed auth | 1 | Non-ASCII header causes 401, not a handler exception |
| Real HTTP | 15 | Raw upload, dry-run dimensions/flags, token/Host/Origin rejection, preflight refusal, capacity/length/timeout, busy/clipboard error, fixed local assets/security headers, traversal |

The controller's final full run on 2026-10-03 passed **46/46 cases**, with no skips, including all 15 real HTTP cases. The earlier sandbox bind restriction was resolved by the controller's privileged local test run. CI defines Windows/macOS/Linux with Python 3.10/3.12/3.14, but CI has not been run on GitHub yet.

The controller built the wheel/sdist and checked source ZIP integrity and SHA-256. Both distributions were installed into separate temporary site directories outside the checkout. Real HTTP HTML/JS/CSS/status and a 9×7 PNG upload passed, with correct dimensions and dry-run/clipboard-not-updated flags. Wheel import path, version, all assets and CLI help passed. Existing Python validation dependencies were used; this does not establish Windows native installation/paste.

Win32 tests use an isolated fake OS boundary because the machine is macOS. The real memory-copy and ownership transaction executes; the hidden-window creation and native message loop cannot be proven by those tests. Synthetic images are test fixtures, not actual phone-camera verification.

## Controller browser evidence

On 2026-10-03 the controller reported a real in-app browser walkthrough against the latest loopback host on port 8766: open the token URL, observe connection and dry-run disclosure, choose a synthetic 960×640 PNG through the gallery chooser, see the preview before explicit Send, send via the real HTTP API, and see processing completion at 960×640 with clipboard-not-updated text. At a 390px viewport, the controller observed `clientWidth=scrollWidth=375` and visually checked the mobile stacking. An old browser-tab navigation abort resolved by using a fresh tab; no product workaround was required. This is desktop-browser/mobile-viewport evidence, not physical-phone or Windows-native verification.

## Browser and device checklist

- [x] Open the join URL in a desktop browser; connection shows the correct backend (controller).
- [x] At a mobile viewport, visually inspect the camera, gallery, preview and Send layout (controller). Keyboard/device accessibility still needs a full check.
- [x] Selecting a photo shows a preview before sending; cancellation clears the preview and disables Send (controller). Replacement remains a manual follow-up.
- [x] Clicking Send transfers the selected synthetic photo (controller). Double-click stress remains a manual follow-up.
- [x] Dry-run remains visible and completion explicitly says the clipboard was not updated (controller).
- [ ] Disconnect or stop the host, send again, and verify an error without a success claim.
- [ ] On physical iPhone Safari and Android Chrome, exercise capture and library selection over LAN HTTP.
- [ ] Exercise HEIC and unsupported/animated inputs; confirm actionable rejection.

## Windows clipboard checklist

- [ ] Run without `--dry-run` in the interactive desktop session; scan QR and send.
- [ ] Paste into Paint and an intended destination such as Word/PowerPoint/ChatGPT; verify upright RGB color, dimensions and white alpha background.
- [ ] Stop SnapPaste, then paste again to check OS ownership persists after the host exits.
- [ ] Temporarily hold the clipboard open from another process and verify bounded failure/recovery.
- [ ] Send repeatedly and from two phones; inspect process memory/handle counts for leaks.
- [ ] Confirm that decode/auth/limit failures leave the prior clipboard unchanged; native failures after clearing may not preserve it.

Windows native paste and physical-phone flows remain unverified until these checks are executed. A macOS dry-run success is not a native Windows result.
