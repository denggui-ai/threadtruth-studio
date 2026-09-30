# Contributing to Caiguang

Thank you for improving source-faithful fashion portrait production.

## Before opening a change

1. Open an [Issue](https://github.com/denggui-ai/threadtruth-studio/issues) describing the user problem, trigger boundary, and expected state transition, or use [Discussions](https://github.com/denggui-ai/threadtruth-studio/discussions) for exploratory proposals.
2. Keep runtime code under `skills/threadtruth-studio/`; keep evals, audit tools, CI, and evidence at repository root.
3. Do not add external connectors, API-key flows, telemetry, network fallback, or paid actions without a separately reviewed design.
4. Never commit customer content, secrets, private logs, personal paths, or media without documented publication rights.

## Development loop

Install `requirements-dev.txt` for development tools. Card-rendering tests also need a local CJK font: STHeiti Light on macOS or `fonts-noto-cjk` on Ubuntu. CI explicitly requires the Linux font before testing; font files are never included in the plugin or public media package. These are development prerequisites, not Skill runtime dependencies.

Behavior changes require a failing regression fixture first, then the smallest runtime change, then the full suite:

```bash
python3 -m unittest discover -s tests -v
python3 tools/pack-lint.py --strict skills/threadtruth-studio/references/styles/*.pack.yaml
python3 tools/trigger-eval.py
python3 tools/build-release.py
```

Contributions must also pass the repository CI.

## File placement and current information

- README holds the introduction and start links; installation guides own the version-specific lifecycle steps; `docs/COMPATIBILITY.md` owns verification boundaries; `docs/BETA.md` owns current Beta status and opt-in adoption counts.
- Keep dated plans and verification receipts in the development tree. `docs/WORK-STATUS.md` is a historical work ledger; preserve its dated facts and link to current status from its introduction. Frozen case records, originals and hashes remain unchanged.
- Source, website and plugin ZIP are separate distribution scopes. Update the existing release allowlist only when a recipient needs a file. Keep local evidence, build outputs and unpublished candidate media outside the package. The package link regression checks that inline relative document links and HTML media references resolve after staging; source-only references must use clearly labeled online URLs.
- Before moving a file, inspect its references and retain necessary public entrypoints. Do not delete by filename, copy whole development directories into the ZIP, or introduce a second governance handbook.

## Pull requests

Include:

- what changed and why;
- new or updated regression coverage;
- affected statuses and permission gates;
- validation commands and results an independent reviewer can rerun;
- rights information for every added image;
- a `CHANGELOG.md` entry for user-visible behavior.

Reviews resolve each finding as `open`, `fixed`, `deferred(issue)`, or `wontfix(reason)`. A passing checker does not replace human review of safety, source fidelity, or trigger scope.

By submitting a contribution, you agree that it is licensed under Apache-2.0.

Maintainer: [DENGGUI](https://github.com/denggui-ai) · WeChat: `Lvmusic0930`. Never send secrets or private customer media through public channels; security reports belong in the private channel described by [SECURITY.md](SECURITY.md).
