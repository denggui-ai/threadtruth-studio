# beta.13 source cut — 2026-10-10

Mode: version bump and merge; the prerelease was published later the same day (see "Publication" below). Owner authorized merging `fix/shared-style-photography-targets` into `main` and bumping to `1.0.0-beta.13` after a final review of f8159aa..48c7c29 passed (one non-blocking finding fixed in 37a9d61: `unknown` coverage no longer unlocks directional off-lens gaze; regression test added).

- Runtime change set since beta.12: real-person gaze/knee-up guards (57b1929, 5fa202b, 37a9d61), real-person material guide and RF-13/RF-14 evals (48c7c29), photography baselines/planning and persona scoping (earlier Unreleased entries).
- Validation on this cut: targeted real-face/model-reference/photography/web-task tests 119 passed; release, repository-contract and installer tests pass (see commit); quick_validate passes; `check_skill_standard --strict` reports the two pre-existing layout items (evals/CHANGELOG at repository root).
- Local install: maintainer host upgraded on 2026-10-10 from 37a9d61 (`1.0.0-beta.12+codex.20261010T124045-d8c3845c`, backup `threadtruth-studio.backup-20261010T124045-d8c3845c`); runtime bytes identical to this cut.
- Not included in the source cut (tag, ZIP and SHA256 were added the same day, see below): tryout document, README/offline-guide refresh, fresh-host installation, any image call or visual-quality claim. The public prerelease remains beta.12.

## Publication (same day)

Owner authorized external publication. Gates run on e12d7f6: CI validate passed; 151 targeted, release, contract and installer tests passed; 24/24 strict pack lint; trigger eval passed with 132 ownership, 22 route, 3 score, 47 style target, 13 style-conflict and 1 core-conflict assertions; public scan passed for tree and history. The full local suite has 13 failures, all environment-only: 10 need host Node sharp and 3 hit a module path. The same failures occur without this change, and CI provisions sharp.

- Artifact: `threadtruth-studio-1.0.0-beta.13.zip`, 284 files, SHA256 `b9b83fcd2dad31e56d620faa57256659023196aaa011c6cc26534183b143ff85`, with a matching sidecar. An allowlist entry check found no private paths. The downloaded asset re-verified against the sidecar.
- Published: [v1.0.0-beta.13](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.13), prerelease, 2026-10-10T13:28:23Z, target e12d7f6.
- Not refreshed: the tryout document, README and offline guide. Fresh-host installation is not verified. `guide-required`; maturity is not promoted.
