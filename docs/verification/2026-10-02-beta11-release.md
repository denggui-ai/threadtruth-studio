# beta.11 prerelease verification — 2026-10-02

Mode: release. Scope: Codex plugin beta.11, GitHub synchronization and a backed-up maintainer macOS upgrade. User authorized this cutover and publication. No image calls were made for release verification. Guide decision: `guide-required`; `USER-GUIDE.html` is bundled.

The behavior change is [source-supported six poses](2026-10-02-source-supported-six-poses.md), implemented in `5c568c8`. With sufficiently supported front/front-side material and no rear source, portrait slot 6 is disclosed as stationary frontal standing. Slots 1–5 remain; duplicate actions fail QA. Explicit original-six or accurate rear-construction demands require real rear material or explicit acceptance of substitution. Nonportrait rear compositions retain their source requirement.

## Verified scope

- Full repository suite: 221 tests passed, 89.294 seconds. Source and staged/unpacked runtime validation passed. Existing source text probe covers six scenarios; no native-generation claim follows from it.
- Independent read-only release review and final documentation delta review: pass, no blocker. Older capability-page wording was corrected to distinguish the bundled white-vest case from five online reviewed groups.
- Existing homepage browser regression: all 11 checks passed. Offline HTML guide rendered at 1280px desktop, 390px mobile and desktop dark mode: no horizontal overflow or browser errors; local links, keyboard skip focus, reduced motion and body-text contrast passed. Guide content and structure are unchanged by the final capability-document delta.
- Allowlist ZIP: 271 files, 34,765,070 uncompressed bytes, 33,312,457 archive bytes. Source-only tests/evals/changelog/verification, caches, private state and symlinks are excluded. Final clean extraction matches source bytes for every file.
- SHA-256: `d9c1f140b0106c16a71841414ce795df6fccf4f11d4b986c56d019de255c646b`; matching sidecar verified locally. Archive: `threadtruth-studio-1.0.0-beta.11.zip`.
- Maintainer upgrade used the verified clean extraction and existing installer, with old source and personal marketplace backups retained. Native `codex plugin add` installed beta.11 with the expected cache-refresh suffix; plugin list shows installed and enabled. All 40 runtime files match archive, source and active cache. Personal marketplace entries are unchanged; other plugins observable in both CLI snapshots are unchanged. The initial remote-catalog snapshot was unavailable, so remote-catalog before/after parity is not claimed.
- Fresh read-only installed-path text smoke: normal front-only prompts use the six supported poses without generation; an explicit accurate-rear request requires real rear material or acceptance of the replacement. The agent read the actual beta.11 cached skill and relevant references. This does not prove automatic GUI triggering.
- Six existing black-outfit images were visually reviewed for pose distinction only: side-turn, wall support, sitting, stepping, forward lean and stationary front standing are distinguishable. Six originals remain 1024×1536. This is historical-image review, not a new beta.11 provider run or garment/back-detail acceptance.

## Limits and recovery

Fresh-host installation, automatic desktop triggering, new native image quality, paid/provider calls, and actual rollback/uninstall cutovers were not exercised. They remain unverified. No `production-ready`, all-style verification, or L3 native-quality claim is made.

Old public releases and historical previews remain unchanged. Local source and marketplace backups, archive verification, browser screenshots and install receipts are retained outside the public repository; private machine paths and full logs are not included here. Rollback follows the bundled guide using the reported source backup and native enable command, preserving later unrelated marketplace changes.

Release readiness: pass for this narrow prerelease scope. Publication receipts are verified separately after upload; this report records prepublication gates and the completed local upgrade.
