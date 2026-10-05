# Publishing / 公開手順

This alpha is source-ready; creating a remote repository, publishing a release or uploading to PyPI is a separate external action. No remote is assumed in this project. Publish this directory as its own repository so `.github/workflows/ci.yml` is at the repository root.

## Before a source release

1. Run the complete unittest suite and record machine, Python/dependency versions and output in `VALIDATION.md`.
2. Run the browser and actual-device checklist, or keep the remaining unverified items clearly visible in the release description.
3. Inspect the package for accidental join tokens, personal photos, machine paths and private data. Tests contain synthetic pixels only.
4. Confirm MIT rights/attribution and the version in `pyproject.toml` and `src/snappaste/__init__.py` agree.
5. Build distributions and test an installation from the wheel outside the source folder.

```sh
python -m pip install build
python -m build
python -m venv /tmp/snappaste-release-check
/tmp/snappaste-release-check/bin/python -m pip install dist/snappaste-0.1.0a3-py3-none-any.whl
cd /tmp
/tmp/snappaste-release-check/bin/python -m snappaste --help
```

Use an equivalent separate path and `Scripts\python` on Windows. Installing normally may download Pillow and qrcode from the package index; using `--no-deps` is only appropriate when the separate environment already has those dependencies.

Check that the wheel contains `index.html`, `style.css`, `app.js` and `api.mjs`, then start its dry-run host from outside the repository and exercise authenticated HTTP. Check both wheel and source distribution archives. A packaging build alone does not verify browser assets or native clipboard operations.

## GitHub

Create the intended repository using the owner's chosen account/name. Push the source and wait for the CI matrix/package job. Keep the first release labelled prerelease `0.1.0a3` and summarize supported formats, explicit LAN/dry-run setup and the remaining Windows/device checks. Attach built distributions only after the installed-package check succeeds.

## PyPI

GitHub source publication does not require PyPI. The name `snappaste` has not been checked or reserved. If PyPI publication is requested, verify naming/ownership, use the appropriate account and trusted publishing configuration, and test through TestPyPI before production. Do not place credentials or live join URLs in source. Dependency/version changes require fresh full-suite and packaging verification.
