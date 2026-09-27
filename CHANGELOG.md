# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## 2026-09-28 — 1.0.0-beta.6 (local candidate)

- Trigger: the maintainer accepted an entry recommendation policy after a 24-style local comparison (48 attempts, 43 saved originals, 19 complete pairs). Rendering votes favored ChatGPT web in 11 pairs, Codex in 7, with 1 tie; five missing pairs are not ties.
### Behavior before

- Before: the skill described native generation availability but had no bounded entry preference guidance.
### Behavior after

- After: retains Codex as the default and preserves explicit user selection. Rendering requests receive a style-specific sample recommendation; ties, missing pairs and unmeasured styles retain the default. Rendering preference is not a fidelity, identity or style guarantee. No automatic browser upload, route switch, retry, API fallback, or new generation authorization is introduced.
### Eval coverage

- Adds a dependency-free local advisory helper and a single runtime evidence table. Source regressions cover defaults, manual override, all 24 styles, missing/tied/unknown evidence and non-rendering goals. The comparison does not verify an image model version or the revised six-image workflow.
### Verification

- The recommendation change was committed on 2026-09-27; on 2026-09-28 the maintainer authorized continuation into local candidate packaging and installation. No new image generation or public release is included.
- Scoped checks and limitations: [verification record](docs/verification/2026-09-27-entry-recommendations.md).

## 2026-09-21 — 1.0.0-beta.5 (prerelease)

### Trigger

- The maintainer authorized integration, regression validation, packaging and local installation after closing the head/gaze review. The active local Plugin was still beta.1.

### Behavior before

- Shared natural head/gaze relations and the ecommerce photography pilot existed only on an experiment branch. Current-rule validation also rejected the immutable, previously accepted beta.4 outfit gallery after runtime prompts changed.

### Behavior after

- Integrates shared head/body relations across the existing six poses and 24 styles, preserving style-specific expression and the ecommerce lighting/scene pilot. It adds no fixed left/right quotas or new head rules.
- Preserves the exact published beta.3 white-vest and beta.4 outfit collections as hash-checked historical evidence. New previews still require current reproducible prompts and all existing authorization, source-rights and human-review gates.
- Updates the Plugin version and matching installation/offline guides. After local installation passed, the maintainer authorized GitHub prerelease publication. Public packaging changes distribution documentation only; runtime bytes match local beta.5. The local archive remains immutable with its own checksum. Stable v1.0.0 remains pending.

### Eval coverage

- Existing shared-rule tests cover 24 grid prompts and 144 single-pose prompts; source evals cover expression and face-obscured precedence. Frozen-collection regressions reject changed bytes and preserve strict current-rule checks for new runs. Installer regressions cover dry-run, replacement backups and unrelated marketplace entries.

### Verification

- See [local integration verification](docs/verification/2026-09-21-beta.5-local.md) for actual checks and installation scope. Historical galleries do not verify beta.5 image quality. The latest ecommerce V2 remains a locally corrected candidate, not a universal quality pass; no new image call was made for this integration.
- External clean-host discovery, Beta exit criteria and stable release remain pending. Earlier experimental plans below are historical; the maintainer closed further head-rule expansion and additional preview generation for this task.

## Pre-integration development history

#### Experimental candidate — shared head/gaze relations across 24 styles (not visually verified)

- Replaces the inherited Korean head/gaze instructions and the ecommerce fixed-left/right override with one six-pose body-relation table. Head direction, tilt and eye contact follow action and existing scene; expression remains in each pack's `model_persona`. No gaze quotas, new props, style categories or schema/CLI changes.
- Action-0 and action-2 prompt builders read the same head/gaze table and one shared guidance paragraph. Removed the ecommerce head override parser and repeated per-cell expression note. Existing ecommerce photography additions remain scoped independently; lighting, scenes, identity and framing behavior are preserved.
- Face-obscured and nonportrait instructions retain §1a precedence. Automated coverage exercises 24 grid prompts and all 144 single-pose prompts, including propagation of a shared-rule edit; declarative evals 79–80 cover style expression and output-form precedence. These checks do not establish image quality.
- Prior accepted images retain their original prompts, hashes and acceptance. Current-rule publication checks are unchanged and historical public evidence is expected to remain stale. This candidate is experimental; planned visual comparison is ecommerce, Korean cold editorial, Japanese lifestyle and athleisure with the same outfit/identity, one grid each under separate generation authorization. No native generation or promotion in this change.

#### Experimental candidate v2 — pilot slimming, anchor isolation and single-image validation entry (not visually verified)

- Trigger: the 2026-09-16 blind re-distillation (`docs/verification/2026-09-16-independent-distillation.md`) found that the v1 pilot lighting block named garment parts (sleeves, lapels, pocket flaps), that the persona implied pockets and a direct gaze, that the preview anchor line lacked the §4.0a "ignore its garment, lighting, background" clause (the public ecommerce preview shows the anchor's lighter denim wash), and that a six-cell grid at ~390 px per cell cannot show contact shadows. The maintainer voided the pending B0 authorization (`ecom-b0-pilot-01`) on 2026-09-16 so these fixes could land before the next native call.
- Behavior before: `ecommerce-studio.lighting_palette` (~95 words) named garment parts; persona said `in a pocket` / `calm direct … gaze` / unconditional `weight settled on one leg`; the action-0 anchor line only said "identity-only"; framing was the bare token `full-body`; no runtime entry could produce a single-image (action 2) prompt.
- Behavior after: the pack's `lighting_palette` is ~60 words in the same §4.1 order with no garment-part words; persona is conditional (`when standing`, hands at the side or on an accessory already in the reference, gaze per pose line). For slugs in prompt-build §2a only, the real action-0 prompt adds the §4.0a ignore clause to the anchor line, writes full-body framing as `full body visible, feet and shoes fully inside the frame …`, and adds one `Photorealistic photograph …` line; the other 23 preview prompts stay byte-identical. New `tools/style-preview.py single-prompt --run-id … --style … --pose N [--ratio W:H]` writes one final-stage (§3a negatives, §4.0b exact canvas) single-pose prompt into the run's `prompts/` without touching `evidence.json`, registering a batch, or generating.
- Eval coverage: `evals/styles/ecommerce-studio.json#ec-single-validation-9`; `tests/test_pilot_ecommerce_lighting.py` (slimming assertions, pilot-only prompt lines, single-prompt shape).
- Verification: static and dry-run only; no native generation was run and no visual improvement is claimed. Execution plan: `docs/verification/2026-09-16-execution-plan-after-b0.md`.

#### Experimental candidate — ecommerce-studio lighting and expression pilot (not visually verified)

- Trigger: the accepted coordinated-outfit previews show the `ecommerce-studio` board lit flat (no visible key direction, no contact shadow under the shoes, no separation from the white backdrop) and every style inheriting the Korean-baseline "cold detached" head/gaze mood, which contradicts the ecommerce pack's own approachable persona.
- Behavior before: `ecommerce-studio.lighting_palette` was a single line of adjectives (`even soft-box lighting … low shadow`); prompt-build §2 injected mood adjectives into all 24 packs.
- Behavior after: the pack's `lighting_palette` is written as visible relations in the core §4.1 order (key direction, fill ratio, shadow transition, contact shadow and backdrop separation, exposure, identical light in all six images); its persona describes weight, hands and gaze without cold detachment. New prompt-build §2a keeps only head/gaze geometry for the slugs listed in `pilot_persona_expression_slugs` (currently only `ecommerce-studio`) and takes expression from `pack.model_persona`; the canonical §2 table and the other 23 packs are unchanged. `tools/style_preview.py` reads §2a so the real action-0 prompt carries the change. `commercial-qa.md` §2/§3 route locatable lighting/expression deviations for the pilot slug to `qa-user-review` with reasons (human decision, no automatic retry, no extra call authorization).
- Eval coverage: `evals/styles/ecommerce-studio.json#ec-lighting-pilot-8`; `tests/test_pilot_ecommerce_lighting.py` proves the method enters the real preview prompt and that non-pilot packs keep the canonical head/gaze text.
- Verification: static and dry-run only; no native generation was run and no visual improvement is claimed.

#### Preview evidence binds by prompt equivalence (maintainer decision 2026-09-15)

- Trigger: the public preview collection was bound to the sha256 of the rule files and packs, so any rule edit invalidated all 24 previews even when 23 prompts were byte-identical.
- Behavior before: `style_preview._check_plan` required `rules` and each preview `pack.sha256` to equal the current files.
- Behavior after: the recorded `rules`/`pack` hashes are kept as provenance and only checked for shape; every preview must still be reproducible byte for byte under the current rules (`prompt_sha256` equality), and a failure names the style (`<slug>: prompt is not reproducible under the current rules`). Nothing else in the validator was relaxed.
- Eval coverage: `tests/test_preview_rules_equivalence.py` (failing on the previous validator, passing now).
- Verification: with the pilot pack change applied, public validation now reports exactly one stale preview (`ecommerce-studio`), which must be regenerated under the new rules and approved before release.

### Trigger

- The maintainer noted that the README hero and capability wording still presented only the single-garment white-vest case after the coordinated-outfit gallery shipped.

### Behavior before

- The runtime already governed a locked outfit/SKU and its item relationships, but the public hero and discovery metadata described only a singular garment photo.

### Behavior after

- The README now leads with a left-to-right coordinated-outfit source/result comparison—real source on the left, accepted six-pose preview on the right—while retaining the white vest as the distinct six-independent-final case.
- Skill and Plugin discovery metadata now explicitly cover both real single-garment and coordinated-outfit photos. Outfit fidelity means preserving every visible item, layering, proportions and shoe/bag/accessory relationships; it does not add virtual try-on or automatic restyling.

### Eval coverage

- Updated the exact Skill description contract; existing recognition and prompt rules continue to cover complete-outfit fact locking.

### Verification

- Repository contracts, Skill validation, public link/privacy checks and bilingual README rendering are rerun before publication.

## 2026-09-15 — 1.0.0-beta.4

### Trigger

- The maintainer accepted all 24 coordinated-outfit previews, accepted the two corrected pose boards, authorized public GitHub synchronization, and selected PR merge plus a beta.4 prerelease.

### Behavior before

- The accepted coordinated-outfit collection and its complete local failure/replacement lineage existed only under ignored local state; the public repository and latest Release contained only the white-vest gallery.

### Behavior after

- Added the authorized beige-blazer coordinated outfit as a second public 24-style direction-preview collection: 24 optimized native sheets, 24 fixed-card display boards and 24 thumbnails.
- Bound maintainer acceptance to all 24 current sheets, including the corrected Athleisure and Korean Cold Editorial pose-5 boards. Local failed-call and replacement records remain retained while public evidence exposes hashes without private paths.
- Runtime Skill behavior is unchanged. The release adds no independent finals, complete primary cases, external installations or automatic retries.

- Added hash-bound replacement of an already composed local preview after a separately authorized targeted correction. The prior native image, receipt, layout, display, thumbnail, review template and full preview record are retained under an immutable revision manifest; any earlier failed-call retry remains in that archived lineage.
- Corrected batch accounting so separately authorized corrections do not consume another slot in the original immutable six-style batch, while the active correction still requires its own authorization and acceptance hashes.
- Added hash-bound, single-target retry evidence for recorded prompt-binding failures and native timeouts with no output. The retry must use a new post-failure authorization, the exact planned prompt, and the next attempt number; it does not consume a successful-style slot in the original immutable batch.

### Eval coverage

- Added regression coverage for retry receipt bindings, full six-style batch completion after one authorized failed-call retry, and rejection of missing or mismatched retry authorization.
- Added regression coverage proving that public projection retains lineage hashes, removes private lineage paths, rebinds the public human-review hash, selects the two accepted v3 sheets, and registers exactly 72 coordinated-outfit JPEGs.

### Verification

- Full repository, 24-pack lint, trigger, Plugin/Skill production, privacy, archive, CI and post-publication download results are recorded in the beta.4 candidate verification report and GitHub prerelease checks.

## 2026-09-14 — 1.0.0-beta.3

### Trigger

- The maintainer accepted all24 displayed previews, authorized gallery inclusion and rights-index updates, then separately authorized the GitHub push and beta.3 Release.

### Behavior before

- The public collector could package only the original fixed-prompt sheet for each style. Six accepted correction drafts lived outside the canonical collection, so direct promotion would have selected rejected first drafts.

### Behavior after

- Added the same authorized white vest across all 24 registered styles, with one native six-pose sheet, one disclosed fixed-card display derivative and one whole-board thumbnail per style.
- Bound 24 maintainer visual acceptances to exact display hashes. Six targeted corrections explicitly replace their rejected first drafts and retain the replaced call/image hashes plus actual correction call and prompt hash.
- Updated the 24-style index, per-style pages, bilingual README gallery and generated rights index. Preview coverage is 24/24; independent six-final coverage remains 1/24 and complete primary cases remain 1/3.
- Kept the runtime Skill and global installation unchanged. Existing beta.1/beta.2 assets remain immutable; beta.3 was published from commit `ee7a92f` with a separate ZIP and checksum.
- Added correction-lineage validation so the public builder cannot silently package an old rejected draft or mis-bind a corrected image to the initial prompt.

### Eval coverage

- Added a correction-ingest regression for replaced-asset lineage, actual correction prompt binding, receipt binding, composition and hash-bound human approval. The release archive test requires all72 registered preview JPEGs.

### Verification

- Full repository, Plugin, Skill, production, privacy, archive and browser results are recorded in the beta.3 candidate verification report. The published assets were downloaded again and their SHA-256/ZIP integrity verified after publication.

## 2026-09-14 — Fixed-card preview delivery

### Behavior before

- Trigger: three native single-style attempts did not establish exact equal 3:4 panels. The maintainer explicitly selected disclosed local card layout instead of further prompt-only retries.

### Behavior after

- New development-only schema4 separates retained native content from fixed1200×1200 display boards, six360×480 cards and whole-board thumbnails. Explicit compose uses observed source rectangles, uniform downscaling/padding, local bilingual labels and an AI/layout/non-final footer; no generative repair, stretch, upscale or subject cropping.
- Source originals, actual prompts/calls, historical geometry failures and pending human review are retained. New display records bind extraction/fit/font/derivative hashes; old approvals do not transfer. Reusing a real original does not create a native call.
- Rights index, style pages, README thumbnail slots and promotion allowlists distinguish native/display/thumbnail assets. All24human approvals still gate public promotion; previews never enter six-final records. Extra independent-final representatives are now explicitly optional.
- Primary-case validation adds consistent C1/C support alongside B1/B; keeps2:3, six distinct finals, source rights and human acceptance. Issue1 remains open/needs-reproduction because retained summaries cannot attribute the host-load boundary.
### Eval coverage

- Regression work covers compose success/idempotence, malformed or overlapping source rectangles, tampered evidence/assets, missing composition/approval, original preservation, public projection and C1/mode/action mismatch. CI explicitly requires a development-only CJK font so rendering tests cannot silently skip on its Linux runner; no font is redistributed.

### Verification

- Final120/120 repository tests and source/runtime/Plugin checks pass; the reused Korean C layout passes machine checks but awaits human review. See [the delivery verification report](docs/verification/2026-09-14-card-preview-delivery.md). Local development is not a beta.3 release.
- Runtime, existing beta.1/beta.2 assets, global installation and external systems are unchanged. No new native generation or automatic retry is authorized by this software change.

## 2026-09-13 — Unreleased preview layout and label contract

### Trigger

- The maintainer found that the corrected single-style collector still lacked explicit acceptance checks for the whole-board ratio, per-cell ratio, full registered style label, native subtitle/footer, and text-to-subject overlap.

### Behavior before

- Schema `2.0` bound one style and six poses but could accept a non-square native board, omitted observed cell/text-band geometry and framing attestations, and did not bind the layout/label contracts into the native receipt. Its earlier narrow machine result therefore did not qualify the real Korean C attempt. The beta.2 mixed-style board was already a separate wrong-format draft.

### Behavior after

- Schema `3.0` now requires a native and retained `1:1` board containing independent title, subtitle, two rows of three `3:4` cells, and footer bands. Poses 1/2/4/6 require full-body framing; 3/5 permit half-body. Native dimensions plus layout and label hashes are bound into each receipt and review evidence.
- Prompts require the full registered bilingual style name, exact mode subtitle and exact bilingual AI preview footer to be rendered natively. Original output is preserved before validation; there is no crop, stretch, padding, enlargement or scripted text repair.
- Human review now records six observed cell rectangles plus observed title/subtitle/footer rectangles in retained-image pixels, allowing only one-pixel size/alignment/raster-ratio rounding. Explicit boundary, text correctness/readability, non-overlap and per-pose framing checks default to pending; missing/pending/fail fields or `public_use_approved: false` are not consent.
- Schema `1.0` and `2.0` runs remain read-only history and cannot be prepared, ingested, approved or promoted. Current evidence requires a new run ID. Style-scoped audit can report file evidence without claiming human visual approval; full audit and promotion require all 24 current-schema sheets and reviews.
- Operator, bilingual, offline, Beta, growth, application and work-status wording now separates local software closure from image readiness. Current counts are one unqualified native single-style attempt, 0/24 qualified, 0/24 human-approved and 0/24 public; the prior mixed-style board is separate. The next Korean C retry and the remaining 23 styles require new explicit native authorization.

### Eval coverage

- Added regressions for non-square native output, bad cell ratio/size/alignment/order, out-of-bounds and overlapping rectangles, malformed numeric fields, missing or pending label/framing attestations, receipt/review/image hash tampering, and direct old-schema promotion.
- Retained transactional promotion, historical-gallery accessibility, scoped/full audit, whole-sheet no-upscale, public projection and six-independent-final isolation coverage. Synthetic `900x900` geometry and all-pass attestations remain disposable test fixtures only; they do not count as real review evidence.

### Verification

- Task 1 reports 24/24 focused preview tests and 108/108 repository tests passing at implementation commit `0922c61`; its independent task spec/quality review reported no findings. Final combined tests and guide rendering are recorded separately in [the controller verification report](docs/verification/2026-09-13-preview-layout-label-contract.md) and must not be inferred before that report is closed.
- This static change does not certify the existing real image or the full project. No native call, human approval, promotion, release, network action, installation or runtime change was performed. External lifecycle remains 0/1, non-maintainer installations 0/5, complete primary cases 1/3, and external-feedback fixes 0/1.

## 2026-09-13 — 1.0.0-beta.2

### Trigger and behavior

The maintainer requested the same authorized white vest in all24 styles, four six-style preview boards, DENGGUI attribution and clearer Beta onboarding. Previously the style index only accepted independent-final representatives and the download lacked a reproducible personal-source registration entry.

- Added a development-only prepare/ingest/audit/gallery/approve/promote preview pipeline binding all24 actual packs, source rights, native-output receipts and per-tile human review. Four boards are previews, never six-final cases. The runtime Skill and its six-image/safety boundaries are unchanged.
- Separated preview coverage (0/24 approved at this release) from independently generated case coverage (1/24). No unapproved preview image is packaged.
- Added a dry-run-first local-source installer with explicit apply/replace, preserved marketplace metadata and rollback copies. It never enables the Plugin by itself.
- Changed public display attribution to DENGGUI, with authorized WeChat contact Lvmusic0930; existing GitHub namespace, reviewer identities and provenance are preserved.
- Updated bilingual entry points, installation, security and offline documentation. Added opt-in installation feedback and read-only, local-only Beta metric summaries.
- Kept the2026-09-13 Beta start and immutable beta.1 artifacts.30days/5installers/3workflows remain project goals, not official admission requirements.

### Verification and limitations

New refusal/success tests cover source and pack drift, preview attestation/approval/hash tampering, orphan media, installer preservation/rollback, consented deduplication and distinct download categories. Public scans include tracked files even if force-added from ignored directories; private ignored review workspaces are not public source. No scanning rule was weakened. Full release evidence is recorded in [beta.2 verification](docs/verification/2026-09-13-beta.2.md).

Native preview generation and human acceptance are separate later gates. New-host CLI activation, an external installation and real operation recording remain pending; mock-home source registration is not fresh-host functional verification. No new runtime rules, API fallback or telemetry were added.

## 2026-09-13 — 1.0.0-beta.1

### Trigger

The active identity is `$threadtruth-studio`; explicit, positive apparel, negative adjacent-domain, conflict, and authorization paths are covered by public fixtures.

### Behavior before

The private predecessor used a legacy active name, mentioned specific image models, and mixed runtime and development evidence in one Skill tree.

### Behavior after

The public Plugin has one active identity, model-agnostic host-native generation, an allowlisted runtime payload, and explicit publication/installation/application authorization gates.

### Eval coverage

The repository carries behavior evals, 24 per-style suites, deterministic route cases, repository contracts, and an allowlist packaging test.

### Verification

System Skill validation, official Plugin validation, production strict/runtime checks, 24/24 pack lint, trigger regression, privacy scanning, release staging, public CI, and the maintainer-machine Plugin lifecycle passed. The first authorized source-to-six-image primary case and one auxiliary CC0 rights case are public. External clean-environment evidence remains pending. Minimal implicit missing-image behavior is tracked in [Issue #1](https://github.com/2278091160dg-rgb/threadtruth-studio/issues/1).

#### Added

- Clean Codex Plugin repository and Apache-2.0 licensing.
- Public identity `threadtruth-studio` and bilingual user documentation.
- Allowlist release builder, repository contract tests, CI, community files, and Beta evidence templates.
- Competitive boundary and Codex for Open Source readiness packet.
- Public GitHub repository, passing GitHub Actions, and a privacy-safe local lifecycle verification record.
- Development-only The Met Open Access CC0 evidence pipeline with quarantine, machine audit, offline human-review gallery, governed promotion, schemas, and release-time rights validation.
- A rights-cleared primary white-vest case with four sources, six accepted results, hashes, canvas checks, human QA review, and AI-generated-media disclosure.
- A 24-style evidence index with three primary-case targets, eight featured styles, six source families, and honest planned placeholders.
- A 1280×640 source-to-results social preview and a privacy-preserving, telemetry-free GitHub growth cadence.

#### Changed

- Migrated the private `clothing-portrait-studio` runtime from commit `1eb29ad` without its Git history or private evidence.
- Replaced specific image-model wording with the host's native image generation capability.
- Reset public maturity to `DRAFT` until rights-cleared Beta evidence is complete.
- Archived the legacy live Skill after verifying rollback, then restored and enabled Plugin version `1.0.0-beta.1`.

#### Security

- Preserved the R1–R7 safety boundary, explicit paid-action consent, six-call cap, and no API/CLI/third-party fallback.
- Release validation rejects unregistered demo media, stale rights indexes, incomplete human review evidence, undersized or oversized files, malformed JPEGs, metadata drift, and hash mismatch.
- Candidate paths and redirects are fail-closed; expired approvals cannot be promoted but may be explicitly rejected and pruned.
