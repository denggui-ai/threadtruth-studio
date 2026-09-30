# beta.9 local candidate closeout — 2026-09-30

Status: **local engineering checks passed; unpublished candidate**. This receipt covers packaging/documentation closeout on `release/caiguang-beta9`, starting at `aa3569b731bfff62b0918c1b436b42d1e94019f8`. It does not supersede the retained [installed-plugin text observation](2026-09-30-beta9-installed-regression.md) or claim a fresh paid/model run.

## Changes and defect closure

- `fixed`: staged `docs/CAPABILITIES.md` linked to excluded `tests/test_web_task.py`. A new staged-document regression reproduced the missing file, then passed when the reference became an explicit online source link.
- Current public/candidate/adoption status is summarized in the existing Beta register; the dated work ledger is labeled historical. File-placement ownership is in CONTRIBUTING, without relocating history or frozen assets.
- Compatibility exposes the retained installed-plugin text result and its limits. The trial guide now names the missing-photo first-reply correction as part of beta.9, while preserving generation permission and review rules.

## Candidate and verification

| Check | Result |
|---|---|
| Candidate | `threadtruth-studio-1.0.0-beta.9.zip`; 33,288,845 bytes; 269 members |
| SHA-256 | `292f921f3bb35d577962de40e615fe079e5c9c2a1622f4ae5441de132e7c7e44` |
| Rebuild | Independently staged second build has identical SHA-256 |
| Actual archive | CRC, unique/safe member paths, manifest version, extracted/source parity passed |
| Package links | Inline relative Markdown document links and HTML href/src targets resolve after staging |
| Isolated install | Actual extracted archive passed installer dry run and source registration in a dedicated recipient directory; all installed payload files matched |
| Repository contracts | 217 tests passed under Python 3.14; includes installer upgrade/rollback and packaging fixtures |
| Browser regression | 11 checks passed in isolated headless Chromium; 320/390/768/1024/1440 widths, Chinese/English, complete images, navigation, storage/clipboard failures and comparison page covered |
| Visual spot-check | Chinese 390px and English 1440px homepage screenshots inspected; no observed overlap or missing primary images |
| Existing CI checks | 24 style packs strict lint; trigger/routing assertions; 73 JSON files parsed; 42 Python files compiled; public tree/history scan passed |
| Preservation | All 40 runtime files and 207 frozen media files match the initial SHA-256 inventory |
| Prior installed artifact | Member set unchanged; five guide documents differ from the retained installed ZIP; runtime/media bytes unchanged |
| Public status | Read-only remote check: beta.8 prerelease assets present; homepage HTTP 200 links beta.8; Issue #1 remains open |

The first baseline suite had 16 errors because the host interpreter lacked the declared `fontTools` dependency. Installing `requirements-dev.txt` in a dedicated virtual environment resolved that environment failure. The first browser invocation could not bind localhost under the sandbox; its approved retry in a separate headless browser passed. Failed logs were retained locally alongside the successful runs.

The isolated registration uses the installer's supported `recipient_home` API. It does not enable the plugin in Codex and is not an independent person's installation. The previously enabled maintainer candidate was not replaced; its eight text probes were not rerun.

## Pending and external gates

- `open`: desktop GUI discovery/display, actual maintainer rollback, and non-maintainer fresh-host lifecycle remain unverified.
- `open`: external adoption and feedback-patch gates remain unchanged. A candidate ZIP, matched checksum, instructions and blank opt-in trial record are prepared locally; no tester was contacted.
- `blocked`: new ecommerce case has only three plausible same-item independent source views. A local source record retains URLs, license snapshots, uncropped downloaded website previews, hashes and visual observations. Four-source acceptance rules remain unchanged; no generation call, retry or new public case was made.
- The already approved one-image test can proceed only after qualified source inputs. Six finals still require test acceptance and separate authorization, followed by final human/publication review.
- No remote push, PR, release, GitHub settings change, global reinstall or public-asset replacement was performed.

Private run logs, source-selection files, screenshots, installer receipts, candidate manifest, tester kit and release draft are stored in the maintainer's dated closeout output folder. The preceding installed-candidate output retains verified beta.8 rollback locations. No private receipts or complete logs are committed here.
