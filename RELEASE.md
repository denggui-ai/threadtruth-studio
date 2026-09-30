# Release Readiness

## Local candidate — beta.9

Status: `candidate`, not published. Public brand and displayed plugin name become **裁光 · Caiguang**; technical IDs and invocation remain unchanged. Missing-photo discovery and response handling are revised for Issue #1; image-generation rules are unchanged. The candidate ships a version-matched [trial guide](docs/BETA9-TRYOUT.md) and offline guide, while the public beta.8 download below stays immutable.

Scope: metadata, onboarding, missing-photo handling and a narrower recipient-document allowlist. Development audits, changelog, application draft and work register stay in source; authorized public demo provenance remains with its images. `guide-required`.

Before public beta.9: verify the candidate package and isolated registration, obtain a non-maintainer installation/name/recognition trial, record the optional one-image outcome separately, fix and retest reported issues, then review final archive/checksum and release notes. The scoped maintainer CLI retest is recorded in [Issue #1 verification](docs/verification/2026-09-30-issue1-missing-photo.md). It does not establish candidate plugin installation, fresh-host or GUI discovery, image-generation behavior, or stable-release readiness.

## Current prerelease — beta.8

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
- Historical Beta acceptance retained [Issue #1](https://github.com/denggui-ai/threadtruth-studio/issues/1) as a documented limitation after an explicit real-image workflow; it did not close the issue. The beta.9 project-scoped fix candidate still requires installed-plugin and fresh-host retesting before closure.
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
