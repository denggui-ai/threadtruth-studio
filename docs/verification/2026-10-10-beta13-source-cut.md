# beta.13 source cut — 2026-10-10

Mode: version bump and merge only; no prerelease publication. Owner authorized merging `fix/shared-style-photography-targets` into `main` and bumping to `1.0.0-beta.13` after a final review of f8159aa..48c7c29 passed (one non-blocking finding fixed in 37a9d61: `unknown` coverage no longer unlocks directional off-lens gaze; regression test added).

- Runtime change set since beta.12: real-person gaze/knee-up guards (57b1929, 5fa202b, 37a9d61), real-person material guide and RF-13/RF-14 evals (48c7c29), photography baselines/planning and persona scoping (earlier Unreleased entries).
- Validation on this cut: targeted real-face/model-reference/photography/web-task tests 119 passed; release, repository-contract and installer tests pass (see commit); quick_validate passes; `check_skill_standard --strict` reports the two pre-existing layout items (evals/CHANGELOG at repository root).
- Local install: maintainer host upgraded on 2026-10-10 from 37a9d61 (`1.0.0-beta.12+codex.20261010T124045-d8c3845c`, backup `threadtruth-studio.backup-20261010T124045-d8c3845c`); runtime bytes identical to this cut.
- Not included: GitHub prerelease tag, ZIP artifact and SHA256, tryout document, README/offline-guide refresh, fresh-host installation, any image call or visual-quality claim. The public prerelease remains beta.12.
