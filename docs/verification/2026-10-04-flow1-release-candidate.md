# FLOW-1 incremental local candidate — 2026-10-04

Conclusion: **local candidate checks passed; live replacement pending authorization**. Scope is the reviewed first-response correction and local Codex plugin handoff. This is not public release, fresh-host discovery, implicit invocation, provider or image-quality verification.

## Identity and scope

- Candidate: `1.0.0-beta.11+model-reuse.20261004.flow1`; distinct from the previously installed model-reuse candidate. Runtime source: `41aaa2b`; previous runtime: `e1364a3`.
- Runtime target: `skills/threadtruth-studio/`; evidence root: this development repository. Private package, logs, lifecycle outputs and reviewer report remain under workstation `outputs/caiguang-flow1-release-20261004/`.
- Mode: production-governor `release`; guide-required, macOS/local Codex target. The envelope includes the updated offline guide and candidate installation/rollback instructions.
- Runtime consists of the same 45 files; only `SKILL.md` differs from the preceding model-reuse runtime. All helper scripts and 24 style packs are unchanged. No schema/data migration.
- Scoped behavior evidence is retained in [the first-response report](2026-10-04-first-response-flow.md). No new behavioral or image run was launched for this packaging batch.

## Validation

- Full suite executed 318 tests: initial 308 passed and 10 failed because the test process lacked the path to existing host `sharp`. The affected wardrobe module was rerun with that existing path: 14/14 passed. Test-ID reconciliation establishes all 318 distinct cases now have a passing result; this is not a claim that the initial full run passed. No source change, dependency install, skipped test or synthetic replacement result was used to close the environment failure.
- Creator frontmatter validation, production source strict (134 definitions), clean-extracted runtime strict, public-tree scan, 24-pack lint and deterministic route checks passed. Route assertions do not prove model implicit invocation.
- ZIP: **278 files, 33372490 bytes**, SHA-256 `ce67336d5a5d6148d6147e3124ee584e2218aec85728c6f5d96b43dc8527d4eb`. CRC, portable names, size/compression bounds, symlink/cache/source-evidence exclusion and private-path scan passed. Exact stage/source/extracted runtime parity passed.
- Actual checksum command passed. A separate `.runtime.sha256` sidecar contains all 45 runtime paths and digests; tested with `shasum -a 256 -c` from the unpacked root. Final provenance binds the committed source, archive digest and sidecars; source-only evidence is not copied into runtime.
- Isolated source registration verified dry-run immutability, explicit replace, exact previous-runtime source backup, marketplace backup, unrelated entries, version cache invalidation, rollback and retained synthetic task data. Baseline is the previous model-reuse runtime, not the older public beta.11 runtime.
- Cleanly unpacked and registered candidate passed five helper entry checks and the existing synthetic local failure/recovery/continuation rehearsal, with no provider calls. Runtime hashes were unchanged after smoke. Synthetic reservations are not real generation or user visual approval.
- Updated guide rendered at 1280×900 and 390×844; no overflow, page errors, remote requests or broken anchors; keyboard skip navigation and reduced motion passed. Chromium required sandbox approval and used a temporary empty profile. Print rendering was not tested.
- Independent release review found no actionable new regression. Final gate closure, including the supplied runtime hash sidecar and environment recovery, is retained in the private `REVIEW.md`.

## Installation and rollback boundary

Read-only preflight found the live source at version `1.0.0-beta.11+codex.20261004T030643-6aef5325`; its 45 runtime files still match `e1364a3`. This batch did not change the real source, cache, enabled-plugin state or marketplace configuration.

Replacing that live plugin requires explicit authorization for this candidate. The installer must back up the then-current source and marketplace, preserve other entries, register the new candidate and print its activation command. After activation, verify exact runtime hashes as well as the rewritten `+codex` version. Keep the new backup; rollback uses the documented installer on that backup and does not remove or downgrade private model packages, images or task records.

## Closure

- `fixed(D4-local-candidate)`: sanitized artifact, current regression coverage, guide checks, hash handoff and isolated lifecycle complete.
- `fixed(test-environment-sharp-path)`: affected tests pass using the existing dependency path; original failure log retained.
- `deferred(live-candidate-replacement)`: await explicit installation decision for this new candidate.
- `deferred(D4-discovery)`: actual new installed-chat invocation remains unverified; no routine repeat of eval 113 or image trial is scheduled.
- `deferred(D3-fidelity/product)`: original-real-person fidelity and existing garment quality limits remain unchanged.

Status: **verified for local candidate handoff; not installed or production-ready**. No network publication, image generation, API fallback, new library or automatic segmentation was introduced.
