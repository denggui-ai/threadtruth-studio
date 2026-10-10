# Release Readiness

## Current release — beta.13 (GitHub prerelease)

Version `1.0.0-beta.13` is cut on `main` from the real-person face-lock branch: strict directional off-lens gaze rejection for frontal-only real coverage, knee-up default for a single real-person visible look, full-body real faces delivered as product images with face `qa-user-review`, `unknown` coverage excluded from the frontal-only test, and the new `references/real-face-material-guide.md` (recommended 4+2 capture set, delivery boundary, graded evidence). Evidence is a private user-judged ablation (97 native calls); likeness is a human judgement, not a biometric score. Published as [v1.0.0-beta.13](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.13) on 2026-10-10. The ZIP has 284 files with SHA256 `b9b83fcd…43ff85`. No new tryout document was written. See [verification](docs/verification/2026-10-10-beta13-source-cut.md). The maintainer host runs these runtime bytes as a `+codex` local install.

## Published prerelease — beta.12

Channel: GitHub prerelease; `guide-required`. Includes portable adult model references, guarded first-image confirmation, recoverable cumulative task accounting, guided fixed-pose wardrobe editing and compact proposal/confirmation/image-review flow. Runtime files are unchanged from the locally installed compact source. PR #31 and hosted CI passed; this release updates version and distribution documentation without new image calls.

The existing offline HTML guide and version-matched [beta.12 trial](docs/BETA12-TRYOUT.md) cover installation, privacy, optional dependencies, backup and rollback. Fresh-host discovery, strict real-person reproduction and general garment fidelity remain unverified; broad production-readiness and stable-release gates are not promoted.

## Historical prerelease — beta.9

Channel: public GitHub prerelease, `guide-required`. Public brand and displayed plugin name are **裁光 · Caiguang**; technical IDs and invocation remain unchanged. Missing-photo discovery and first-visible replies are corrected for Issue #1; generation approval, budget and review rules are unchanged. Use the version-matched [trial guide](docs/BETA9-TRYOUT.md) or offline HTML guide.

Scope: metadata, onboarding, missing-photo handling, packaged links and a narrower recipient-document allowlist. Development audits, changelog, application draft and work register stay in source; authorized public demo provenance remains with its images. The publication archive updates current-version download instructions relative to the retained local candidate; runtime and frozen media are identical.

Maintainer decision: after reviewing the local closeout and its explicit missing evidence, the owner authorized pushing and publishing beta.9 as a prerelease. The earlier candidate plan's non-maintainer trial prerequisite is deferred to continued Beta validation. This is an authorization decision, not evidence of successful external installation. Desktop display/discovery, non-maintainer installation/recognition, actual rollback and optional new-image results remain unverified. External counts do not increase and Issue #1 is not closed.

Retained records: [project-scoped Issue #1 retest](docs/verification/2026-09-30-issue1-missing-photo.md), [installed-plugin text regression](docs/verification/2026-09-30-beta9-installed-regression.md), and [local closeout](docs/verification/2026-09-30-beta9-closeout.md). Stable-release acceptance and style maturity remain separate.

## Historical prerelease — beta.8

Download: https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.8

Publishes the approved 290-file archive from source commit `2450e14`, unchanged SHA256 `815529f52ddf8e0b317fba8f36cb291214c56be041ace42cbd31872e2879c174`. Post-build website documentation clarifies publication; frozen archive wording remains historical. Includes ChatGPT web handoff and bounded retry accounting. Browser capability comes from the host; image model and fresh-host behavior remain unverified. No new comparison gallery or private test records are included.

## Local candidate — beta.6

Version `1.0.0-beta.6` contains bounded entry recommendations, with Codex as default and manual choice preserved. Local packaging and installation only; no public beta.6 download or tag is claimed. See [local verification](docs/verification/2026-09-28-beta.6-local.md). The public beta.5 release below remains unchanged.

## Historical release — beta.5

- Version: `1.0.0-beta.5`
- Scope: publishes the integrated beta.5 runtime already validated and installed on the maintainer host.
- Channel: [GitHub prerelease](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.5). Stable v1.0.0 and external Beta exit gates remain pending.
- Runtime: shared natural head/body relations, style-owned expression and the scoped ecommerce photography pilot. Historical galleries remain immutable and do not establish current-version visual quality.
- Verification and limitations: [beta.5 local record](docs/verification/2026-09-21-beta.5-local.md). `guide-required`; the version-matched offline guide is outside the runtime skill.

## Previous public Beta (historical)

- Version: `1.0.0-beta.4`
- Status: [`v1.0.0-beta.4`](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.4) published as a GitHub prerelease at `2026-09-15T00:18:31Z` from merge commit `f80b4c4`. beta.1–beta.3 remain available and immutable.
- License: Apache-2.0
- Distribution: Codex Plugin repository plus allowlist-built archive
- Runtime telemetry: none
- External connectors/MCP/API fallback: none
- Guide decision: guide-required; offline guide is in the release envelope, outside runtime

## Required gates before publishing the Beta tag

- All repository tests, 24/24 pack lint, trigger eval, Plugin validation, production strict validation, runtime-stage validation, JSON/YAML/Python checks, privacy/history scans, and release staging checks pass.
- A rights-cleared source garment and full demo chain have a completed rights manifest.
- Maintainer-machine installation proves explicit invocation, substantive implicit discovery, negative isolation, uninstall, upgrade, and rollback.
- Historical Beta acceptance retained [Issue #1](https://github.com/denggui-ai/threadtruth-studio/issues/1) as a documented limitation after an explicit real-image workflow; it did not close the issue. The beta.9 installed-plugin fix has a scoped maintainer CLI record; fresh-host retesting and distribution are still required before closure.
- A non-maintainer clean environment repeats installation and discovery before the Beta exits.
- The maintainer reviews the final artifact names, checksums, and release notes before publication.

For beta.4, runtime bytes remain unchanged. The release adds a second 24-style, hash-bound, human-accepted direction-preview collection for one coordinated outfit. It does not raise independent-final coverage above 1/24 or complete-case coverage above 1/3. Local failure and replacement records remain private; the public record retains their hashes. Fresh-host CLI activation and external lifecycle evidence remain pending.

## Known limitations

This project does not provide virtual-fit simulation, CAD accuracy, text/logo guarantees, unattended commercial approval, third-party integrations, or platform-performance guarantees. Native image behavior varies by host and must be evidenced in the release compatibility record.

## Public artifact versus local beta.5

The public beta.5 package updates distribution documentation only relative to the installed local beta.5. Runtime bytes are identical. The earlier local archive, checksum and backup receipt remain unchanged; the public archive has its own checksum. This release adds no new image calls, visual acceptance, external installations or maturity promotion. Source tests and public-source privacy checks apply before publication; the merged commit, published assets and fresh download are verified in the release handoff.

## Release artifacts

Build the allowlisted Plugin archive:

```bash
python3 tools/build-release.py
```

Build the original-resolution primary-case media archive:

```bash
python3 tools/primary-demo.py build-media \
  --staging .threadtruth/primary-demo/white-hooded-puffer-vest \
  --case-id white-hooded-puffer-vest-korean-cold \
  --version 1.0.0-beta.1 \
  --output dist
```

Both commands create a versioned ZIP and a separate SHA-256 sidecar under `dist/`. The Plugin ZIP excludes development tools and full-resolution PNGs; the media ZIP contains four metadata-stripped authorized sources, six metadata-stripped full-resolution PNG results, allowlisted rights/run evidence, a README, and an internal checksum manifest. Raw prompts, private logs, previews, and staging records are excluded.

The beta.1 media archive remains the authoritative unchanged original six-image package; later Betas do not duplicate it. beta.4 carries both accepted 24-style preview collections, including optimized native sheets, layout derivatives, thumbnails and sanitized evidence. Raw native PNGs, local receipts, rejected drafts and private lineage paths never enter the Plugin envelope.
