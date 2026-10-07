# Changelog

## CI dependency correction — 2026-10-05

- GitHub repository tests lacked the host sharp dependency required by guided wardrobe-edit tests. Reproduced with a clean Node lookup: 10 of 14 tests fail; with sharp 0.35.4 all 14 pass.
- Install pinned sharp only in the ephemeral CI test directory and pass its module path to the repository test step. Runtime, user dependency gates and image generation behavior remain unchanged. The subsequent GitHub run must establish hosted success before merge.

## Source integration — compact candidate, 2026-10-05

- Integrate published beta.11 and current showcase updates without changing their media; preserve all six upstream pose regression scenarios under existing mapped IDs 127–132. Retain the reviewed compact/model-reuse runtime and remove a duplicate paragraph introduced by merging.
- Align candidate manifest, guide wording and casting eval 93 with the compact interaction flow. Existing public beta.11 download links stay versioned; this source PR does not publish a new archive or repeat image generation. Local installation evidence remains separately scoped in `docs/verification/2026-10-05-compact-live-install.md`.

- Integration verification: 331 tests pass in one run using existing Python image/font dependencies and host sharp; 24-pack lint, trigger checks, source/runtime validation, allowlist build, tree/history privacy scan and diff checks pass. Runtime bytes match the locally installed compact source; gallery bytes match current main. No fresh model run or image generation.

## Unreleased — compact conversation flow, 2026-10-04

- Trigger: repeated menus, confirmations and QA reports obscured the single-image task and its stopping point. Replace default full recognition/style/model menus with one proposal covering identity, a concrete style, purpose and count; optional choices remain available on request.
- A confirmation of a concrete generation proposal binds its choices and stated calls once. Existing authority is reused; process approval and image satisfaction do not grant new image calls. Keep independent technical QA and human evidence while allowing one overall acceptance to close an eligible single-image task or continue an already-authorized six-image set.
- Update the entrypoint, recognition/flow/router/model/QA/prompt references and existing default prompt. Remove mandatory verbose reporting and fixed casting authorization copy; keep source fidelity, failure recovery and budget gates. No command, schema or style-pack change.
- Update source evals and add decision-based scenarios 143–151 for proposal confirmation, direct execution, process-only approval, single completion, person-only acceptance, existing six-image authority, hard failures, unknown calls and unsupported retries. Fixtures describe expected behavior, not live model evidence.
- Validation: all 326 distinct existing local tests have passing results. Initial full run: 300 passed; 16 `test_brand_assets` errors (fontTools unavailable in the selected Python) and 10 `test_wardrobe_edit` failures (host sharp path missing). Using existing dependencies, the affected modules passed 16/16 and 14/14; no dependency was installed. Final repository contracts passed 14/14; skill quick validation, 24-pack lint, routing checks, eval JSON and diff checks passed. New conversation fixtures were reviewed against the rules, not run as fresh model sessions. No generation, live installation or release in this change.

## Local flow2 installed — 2026-10-04

- User-authorized backup, replacement and official plugin activation completed; source/cache byte parity and rollback source retained. Official activation removed the old cache, not the complete source backup.
- Six installed-state checks passed. One fresh installed CLI casting scenario scored 12/13: correct installed-cache reads and no image calls, with a non-blocking first-reply delivery preview retained as a deferred finding. No rerun, source behavior change or new image in this installation batch. See `docs/verification/2026-10-04-flow2-live-install.md`.

## Local flow2 candidate — 2026-10-04

- Close routing-path and process-reporting observations: resolve complete registered style slugs before opening packs, remove misleading historical/short path examples, and separate role-based material summaries from claims about tool execution order.
- First replay exposed truncated registry output before pack access; require the actual matching row to be visible before opening the pack, and retain that failed run.
- Second replay passed registered-pack ordering but omitted the trial-authorization sentence; make all three handoff conditions mandatory and retain that regression before the final bounded replay.
- Split eval 138 authorization/confirmation/tool assertions into independently graded conditions and add French-style eval 142. Existing traces remain unchanged; new candidate and matched baseline evidence are retained separately.
- Package cumulative preparation-status, internal-diagnostic, casting-handoff and first-reply revisions after scoped tests and review. No new images or live installation in this batch; see `docs/verification/2026-10-04-routing-closeout.md`.

## Unreleased — casting handoff and early discovery text, 2026-10-04

- Trigger: CLI new-casting replay omitted trial authorization and actual first-image model confirmation; its pre-load reply promised later deliverables while skill descriptions were shortened by the host.
- Front-load a short apparel-specific input-check sentence in discovery metadata; preserve the body gates and non-apparel/API exclusions. This targets pre-load visibility rather than adding more late body rules.
- Add one direction-card closing sentence distinguishing choice, applicable generation authorization, and actual model confirmation. Existing valid generation authority is reused; text-only tasks do not acquire a new approval question.
- Independent review caught a fixed-Chinese ambiguity in the short example; preserve the user’s language explicitly. Extend eval 138 and trigger boundaries; add near-miss eval 140 and English first-reply/missing-photo eval 141. Retain real catalog/first-message/tool evidence for the declared CLI test only; no installation, image generation or universal discovery claim.
- Verification: final candidate scenarios passed 14/14 assertions and repository contracts 14/14; matched casting baseline scored 6/7. Both first replies passed this round, so no general reliability improvement is claimed. Independent review closed the language issue; three non-blocking observations are explicitly backlogged in `docs/verification/2026-10-04-casting-flow-followup.md`.

## Unreleased — automation evidence and preparation status, 2026-10-04

- Trigger: prepared local tasks reported `image-draft` before any returned image, and routing instructions required exposing debug weights to users. Source changes distinguish `prepared` from returned/retained image evidence and keep routing diagnostics internal unless requested.
- Normalize schema-1/2 legacy delivery labels on read without rewriting files; persisted mutations derive the label from current and retained retry outputs. Budget, failure evidence, user model confirmation and commercial QA remain separate.
- Add local regressions and eval 139; extend eval 138 to cover user-facing diagnostics. Repeat the two earlier process-evidence gaps with retained real CLI JSONL events. Candidate evidence does not update the installed plugin or establish image quality.

## Local appearance1 handoff — 2026-10-04

- Package the reviewed `3354de4` appearance-default correction as `1.0.0-beta.11+model-reuse.20261004.appearance1`; update the existing installation guides without changing schema or installer behavior.
- The user accepted visible face presentation in both authorized diagnostic images. Retain original identity plus the accepted candidate as a private face-only supplement; comparative visual improvement remains inconclusive and garment acceptance remains separate.
- Release checks and actual installation outcome are recorded in `docs/verification/2026-10-04-appearance-release.md`; no extra image requests or public publication.

## Unreleased — preserve default appearance for existing identities, 2026-10-04

- Trigger: an existing AI/real identity card that only requests a friendly smile still receives the Korean pack’s eye makeup, lip colour and flyaway-hair targets because the mood filter activates only literal condition keywords. This contradicts the existing default to retain reference hair/makeup. It is a reproducible prompt conflict, not proof of the cause of earlier visual drift.
- Treat hair/makeup as retained axes for existing identities even when the card omits them; state the same default in shared native/web prompt guidance. Explicit declared changes still reach the prompt. New casting keeps unoverridden pack styling, and photographic/garment/safety instructions remain intact. No new schema, style pack or generation route.
- Add preview/single-image regressions across AI/real and face/full scopes, explicit-restyling coverage, and source eval 135. Update the old test that incorrectly treated a reused identity like unspecified new casting.
- Empty adjustable conditions now honor explicit fixed styling targets; new casting no longer defaults to retaining a nonexistent identity reference. Two additional regressions cover both cases.
- Verification: 89 model tests and 14 repository contracts passed; deterministic failing baseline and interim failures retained privately. Source/runtime static checks and independent scoped review recorded in `docs/verification/2026-10-04-model-appearance-defaults.md`. No new image, live installation or visual-fidelity claim.

## Unreleased — local FLOW-1 candidate handoff, 2026-10-04

- Package the previously reviewed `41aaa2b` first-response correction as `1.0.0-beta.11+model-reuse.20261004.flow1`; update manifest and both candidate guides to avoid collision with the earlier package. No additional runtime behavior or data schema change.
- Verify all 318 distinct current tests: 308 passed the full run; ten environment failures were closed by a 14/14 affected-module rerun using the existing host sharp path. Preserve both logs; no dependency installation or skipped tests.
- Clean 278-file archive, 45-file runtime parity, separate runtime checksums, isolated replacement/backup/rollback, helper smoke, synthetic local recovery and desktop/mobile guide checks passed. Independent review found no actionable new regression. See `docs/verification/2026-10-04-flow1-release-candidate.md`.
- Candidate handoff only: real installation, new installed-chat discovery, image generation and public release are not performed or implied.

## Unreleased — scoped first-response correction, 2026-10-04

- Trigger: current prompt-only model-reuse evaluation again promised local preparation before reading the skill. Providing the complete existing discovery description still produced a later-preparation clause in the first visible reply. Host-normalized visible messages retain both observations.
- Replace abstract discovery wording with a concrete standalone input-check sentence and a stop point. Consolidate the repetitive first-reply body block into one example and the existing downstream gate sequence; preserve actual input classification, generation authorization, model/garment facts and all 24 style packs.
- Update source evals 91/113 to cover generic local-preparation promises and require ordered visible-message evidence; update the existing metadata contract. No new scripts, schema, model library or image calls.
- Verification: two old-rule runs scored 4/5 (first-reply failure); the revised explicit-path, metadata-visible run scored 5/5 under independent review. Each configuration has one run; the old metadata control read extra workspace context. All 14 repository contracts and source/runtime static checks passed; 45-file snapshots show only SKILL.md changed. No actionable finding remained in the narrow source review. See `docs/verification/2026-10-04-first-response-flow.md`. No installed-runtime change or universal trigger/reliability claim.

## Unreleased — local beta.11 model-reuse integration, 2026-10-04

- Trigger: takeover found the reviewed model-reuse branch still based on beta.10, while the active plugin had beta.11 source-supported six-pose rules. Direct replacement would regress those published rules.
- Port the runtime changes from published `5c568c8` and the applicable release-envelope changes from `656cdb6`; retain model confirmation, original references, failure reconciliation and frozen-call checks. No public showcase media or frozen style packs changed.
- Resolve the QA and retry overlaps by preserving both source-supported slot-6 substitution and model-reuse source/identity safeguards. Clarify that new-set substitution does not replace a user-selected fixed-pose mother or authorize an unsupported garment view.
- Preserve existing eval IDs; import beta.11 cases as 127–132, update structural-drift case 89, and add integration cases 133–134. Local build metadata identifies the candidate separately from the public beta.11 archive; the installer already accepts SemVer build metadata.
- Add candidate installation/rollback guidance and a matching local offline guide. No new workflow engine, pose generator, or automatic fallback was introduced.
- Verification: 318 current unit tests passed using pre-existing dependencies; sanitized 278-file ZIP, exact 45-file runtime parity, isolated registration/backup/restore and installed-copy synthetic recovery passed. Independent review closed 3 guide findings (open=0); desktop/mobile offline-guide checks passed. See `docs/verification/2026-10-04-model-reuse-install-candidate.md`. No live plugin replacement, public release, push or generation.

All notable changes are documented here. Versions follow Semantic Versioning.

## Unreleased — reverse-audit recovery and reference fixes, 2026-10-03

- Trigger/target: four reproducible local counterexamples on the model-reference development branch: terminal failures and wrong canvases could not recover, person filtering deleted photographic mood, byte hashes accepted fake images, and changed tool parameters escaped wardrobe verification.
- F1: retain terminal failure receipts or rejected raw returns, reasons and cumulative request history. Add an explicit completed-request reconciliation before a newly authorized single retry. Unknown requests still require recovery first. New schema-2 tasks declare the recovery protocol; old schema-2 tasks opt in explicitly, while the schema-1 recovery interface remains unchanged. No task reset or automatic request/budget increase.
- F2: replace broad semicolon/person-word deletion with local explicit-condition filtering; preserve real style-pack photography, lighting, backgrounds and texture. No frozen style pack or six-pose definition changed.
- F3: require real supported encoding and full decoding of original/supplement/pose-mother and current-product references at export/read/pre-call boundaries. Existing host Pillow/sharp only; unavailable decoders block without installation. Hashes remain byte-integrity checks, not content/consent authentication.
- F4: new wardrobe contracts bind the prompt digest and ordered attachment roles/paths/hashes to frozen copies. Local preflight compares and records the actual proposed tool parameters. Legacy contracts stay explicitly unverified for call binding; pixel verification is separate from provider execution, original identity fidelity and authorization authenticity.
- Clarify long-term adjustable factors versus the current protected pixels: hair, makeup, expression and head angle inside the guard remain fixed; hats, makeup changes and neckline/scarf conflicts must be resolved before a call without dropping requirements or shrinking protection.
- Files/coverage: model/task helpers, native prompt preflight, fixed-pose and recovery references, user model guide, source regression tests and evals 121–126. Avoided a new model library, automatic masks or workflow engine; live installs and historical media/evidence remain unchanged.
- Verification: 162 distinct relevant regressions covered across the integrated run and final task rerun; complete synthetic recovery/confirmation/continuation rehearsal passed (7 virtual reservations, 6 accepted synthetic outputs, 0 real calls). Independent review closed F1–F4 with no open findings; two fresh matched forward tasks passed 8/8 outcome assertions per configuration. Creator/governor source/runtime checks passed. Preserve the 16 historical font-dependency blocks and image-fidelity/product-review limitations. [Scope and evidence](docs/verification/2026-10-03-reverse-audit-repairs.md). No provider image, external API, install, publication or production-readiness claim.

## Unreleased — guided fixed-pose wardrobe reuse, 2026-10-03

- Trigger: localized wardrobe tests preserved each existing pose mother while full-frame generation still changed face pixels. The six-output upper-garment case received qualified usability acceptance; precise original-real-person fidelity and exact shoulder construction remain unresolved.
- Before: portable packages carried original identity and optional generated supplements, but did not distinguish pose editing targets or retain qualified pose acceptance/QA. Per-image protection used private one-off scripts.
- After: optional schema3 pose-mothers store explicit actual poses, image hashes, accepted/qualified feedback and separate original/continuity/garment QA. Originals remain separate; schema1/2 still read. Ordinary new-product tasks do not automatically attach mothers or inherit model confirmation.
- Add a guided local Node/sharp prepare/apply/verify helper with pre-call spatial head protection, feathered whole-garment region, fixed canvas and immutable result versions. Local boundary refinement keeps the same head guard; no generation, network or dependency installation. Manual boundary review and subjective/product QA remain required.
- Files: model reference helper, fixed-pose runtime reference and compositor, narrow SKILL/model-selection/QA routes, user model guide, source tests and evals 116–120. No frozen style packs, production pose definitions, historical evidence/images or installed files changed; no model database, automatic segmentation or hard identity claim added.
- Verification: 61 model + 8 wardrobe regressions passed; six retained-donor replays are pixel-equivalent to the previous final outputs. Independent review closed an actual attachment/frozen-base mismatch; a fresh explicit-path planning run preserved scope/QA/permission boundaries. Source/runtime static checks passed. Sixteen historical font tests remain environment-blocked (fontTools/Brotli), not counted as passes. [Verification and limits](docs/verification/2026-10-03-fixed-pose-wardrobe-reuse.md). Development candidate; no install or new-image verification.

## Unreleased — model selection and portable reuse, 2026-10-02

- Retain scoped human selection of K3 from the controlled diagnostic and K3/M8 pair preferences. K3 acceptance binds its output without promoting originals or granting new calls/commercial use; the frozen independent result remains inconclusive and strict original-face fidelity remains open.

- Execute the separately authorized four-request original/supplement A/B diagnostic: four unique 1024×1536 returns, 31 cumulative, no retries. Fresh anonymous original-feature review yields two ties under the frozen rule; supplement harm/no-effect and strict face-lock remain unproven. Separate continuity/product review retains fine accessory uncertainty and corrects an overstrong pendant-drift premise. Original references/runtime/history are unchanged; new-image human confirmation remains absent. [Scoped results and limitations](docs/verification/2026-10-02-face-supplement-image-results.md).

- Investigate retained original-face transport records and prepare a four-request A/B supplement diagnostic with unchanged common prompt/model/source inputs, frozen anonymous paired review and explicit inconclusive outcomes. Four revision-2 task/handoff preflights pass; no image calls or authority consumed. Supplement causality and strict original-face fidelity remain unproven. [Investigation and prepared scope](docs/verification/2026-10-02-face-supplement-preflight.md).

- Record subsequent scoped human acceptance of the current runtime person candidate as basically usable; the original-face fidelity gap remains explicitly open. Confirmation binds the returned output without granting further generation, commercial readiness or replacement of original references.

- Execute the separately authorized current-runtime single-image packet: one native return, 27 cumulative, no retry. Actual ordered original/supplement/product references and frozen prompt were checked. Two independent visual reviews support major candidate continuity and visible product retention; fine original-face fidelity and small/obscured product details remain `qa-user-review`. Human model confirmation remains absent; no anchor export, install or release. [Scope and remaining checks](docs/verification/2026-10-02-model-runtime-single-image.md).

- Retain three fresh explicit-path workflow dry runs and independent grading for model directions/factor delivery, portable AI prompt delivery and post-image status/QA: 12 scoped assertions pass. Preserve the prompt run's recorded first-reply violation as open, rather than counting overall gates as passed. Actual provider transport, implicit invocation and strict real-face fidelity remain unverified.
- Fix a reproduced runtime-side bytecode write from local model/task CLI imports. Both entrypoints disable bytecode before loading local helpers, so help/read commands do not require caller environment setup to leave runtime bytes unchanged. The isolated regression failed for both commands before the fix. Source evals 112–115 cover the follow-up scope; 276 full tests and independent 73-test review pass, alongside static/runtime checks. [Fresh-flow verification and findings](docs/verification/2026-10-02-model-fresh-flow.md).

- Stabilize accepted generated supplements as an explicit role with image-hash-bound human acceptance and face/full scope. Preserve original identity priority; package schema 2 carries supplements separately while schema 1 remains readable. Task export retains existing selected supplements and only includes the current accepted first image on opt-in; failed or mismatched-confirmation anchors cannot export.
- Add optional single `context.purpose=model-check` diagnostics; prevent them from becoming delivery look-1 or six-pose sets. Preserve legacy contexts, budgets and production poses. Actual prompt/handoff attachments carry supplemental roles and scope without treating acceptance notes as instructions.
- Separate original-face fidelity, accepted-candidate continuity and garment QA. The separately authorized four-stage experiment returned four images (26 cumulative returns); candidate continuity is supported within its tested scope, strict original-face fidelity is unproven, and final denim-color failure remains open. No additional image calls, live changes or publication in this stabilization. Source evals 106–111 and deterministic regressions cover the new boundary. Final 275-test suite, independent 72-test review, creator/governor source/runtime checks and staged CLI smoke pass. [Verification and unresolved image scope](docs/verification/2026-10-02-face-fidelity-stabilization.md).

- User supplied the authorized real portrait for the two previously approved single-image trials. Both returned unique 1024×1536 images with the same original face reference, explicit unknown-body scope and retained factors; no additional calls or result-person acceptance inferred. Independent review grades A `qa-retry` for explicit two-button visibility and B `qa-user-review`; smoother/narrower face presentation still needs user likeness acceptance. Missing-input blocker closed, real-person six-image behavior and overall plan acceptance remain unverified. [Scoped real-person evidence](docs/verification/2026-10-02-real-model-single-trials.md).
- Separately authorized accessory correction retained six new unique native outputs (19 cumulative), original person/task bytes and actual prompt/reference hashes. Independent visual recheck accepts five as `qa-user-review` but rejects the back-turn image's detached bright object as `qa-retry`; the six-call cap is exhausted with no automatic retry. Overall candidate remains incomplete; runtime code and prior 257-test verification are unchanged. [Correction evidence and remaining scope](docs/verification/2026-10-02-model-accessory-repair.md).
- Native test found a five-attachment tool limit: four garment views plus original identity worked for look-1 but exceeded the limit after adding the current first image. Add preflight checks at batch creation, continuation, handoff/reservation and explicit-model prompt delivery; never silently omit source/identity inputs. Five deterministic regressions cover early blocking, exact-five success, unchanged continuation budget, old overfull tasks and prompt side effects. Source eval 102 covers selection before freezing.
- Authorized native test retained 13 returned images: two six-image sets plus one rejected initial trial, with a separately authorized correction. Independent visual review supports limited AI-person continuity and no old-clothing leakage in outfit B, but finds outfit A's original necklace/watch not retained; revise its full-outfit QA to retry rather than claiming 12 product passes. Add schema-2 audit-reject with retained prior QA/confirmation/files/budget, stop invalid first-anchor export/propagation, and require fresh confirmation after an explicitly authorized single-first retry. One local attachment-validation rejection produced no image. Original master remained unchanged; outfit B resumed in a retained version with sufficient three-view sources and original budget/history. Real-person trials, commercial source review, installation and publication remain pending.
- Independent follow-up review also closed duplicate-identity normalization, authorized nonfirst repair after a complete set, and all-task reserved/unknown recovery before submission. Schema1 remains unchanged. New source evals 102–105 and eleven deterministic regressions cover these findings. [Native test scope and remaining image checks](docs/verification/2026-10-02-model-reference-reuse-native.md).
- Final local verification: 257 tests passed; independent reviewer ran 38 model and 16 legacy tests with no remaining Critical/Important code findings. System creator, governor source/runtime strict, public scan, diff checks and internal allowlist archive integrity/runtime parity passed. Visual A accessory correction and real-model tests remain open; no install or publication.

- Add two adult-model paths: existing authorized real/AI identity or editable casting recommendations, with a technical first-image gate followed by separate human model acceptance.
- Deliver direction cards, image confirmation and a portable private reference package. Fixed, adjustable, proposed and unknown factors retain their origins and match actual prompt conditions; face-only references do not imply the person's body measurements.
- Add explicit garment/identity/aesthetic roles and schema-2 local native/web accounting. A pose-1 single trial can continue as the same look-1 plus five authorized images without resetting requests, failure history or original files; schema-1 remains unchanged.
- Keep original identity references across products, override conflicting person style terms while retaining safety/product constraints, and accept optional explicit model inputs in development prompts. No model database; no frozen packs, poses, media or historic prompts changed.
- Initial verification: 246 local tests passed; independent review findings closed with regressions (mood person conflicts, unknown-factor contradictions and first-model refusal). Static runtime/source and package smoke checks passed. New source evals cover reference completeness, factor delivery, confirmation, continuation, tampering, native/web parity and prompt/attachment roles. Follow-up native test and reference-limit verification are recorded separately below; this is not a released or production-ready claim.
## 1.0.0-beta.11 — source-supported sixth pose, 2026-10-02

- Trigger: a clear front-only outfit could produce only five supported default poses; the previous rule required supplement/hold and prohibited every substitution.
- After: retain all six default poses with adequate real rear references. For human/faceless styling images with supported front/front-side coverage, disclose only slot 6 as `FRONT_RELAXED_STANDING`; preserve slots 1–5, six independent files, garment truth, identity, canvas and paid-call gates. Explicit original-pose/rear-detail requirements still need real rear material or user-approved substitution.
- QA compares body action, support and visible direction, not gaze/background/crop or unique hashes. Duplicate walking/leaning/turning is `qa-retry`; substitution cannot hide known structural drift or certify unseen rear construction. Preview, prompt-only, generation and retry use the same declared actual pose.
- Files: runtime entrypoint and existing recognition/flow/prompt/QA references; source eval 89 clarified and regressions 92–97 added. No pose library, new runtime script, style-pack edits or case regeneration. Version-matched user guides and release links updated for the authorized beta.11 publication and local upgrade.
- Verification: see [scoped source verification](docs/verification/2026-10-02-source-supported-six-poses.md). Text scenarios and static/default-preview checks do not prove native image generation or commercial readiness.

## 1.0.0-beta.10 — casting and first-image QA prerelease, 2026-10-01

- Distribute the approved optional casting, aesthetic-reference translation, garment-first priorities and first-image QA changes that were previously available only in source. Keep fixed poses, style packs and the generation process.
- Clarify the discovery description and existing gate sentence so prompt-only requests also begin with input checks; add source eval 91 and update the description contract.
- Ship version-matched offline and installation/tryout guides, update current download links, and preserve older release assets and installed state.
- Verification: 219 local tests, source/runtime checks, isolated registration and two scoped metadata-supplied fresh-context rechecks passed. Retain initial first-reply failures. One native first image failed cuff/occlusion QA; one separately authorized edit closed those visible failures and preserved the AI appearance/pose at 1024×1536. No automatic retry or new six-image case.
- Image remains a draft pending user source review; no fresh-host, automatic installed-plugin discovery or style-maturity upgrade is claimed. [Verification scope and retained findings](docs/verification/2026-10-01-beta10-candidate.md).

## Showcase update — 2026-10-01

- Publish four fixed-six-pose AI styling examples (24 unchanged 1024×1536 PNGs): red floral dress, sage-shirt home outfit, and American/Japanese contrast-trim T-shirt sets. Separate accepted visual direction from remaining human garment/action review.
- Add bilingual case pages, homepage cards and README previews with source credits and sanitized image integrity records. Preserve historical previews and the beta.9 release/installed version.
- Extend the existing Pages allowlist check for the fixed 24-image publication set, including corrupted/missing images and private-path/extra-file rejection regressions.

## Source change — 2026-10-01 aesthetic-reference casting (included in beta.10)

- Before: a declared age/makeup target could miss the visible styling and temperament explicitly requested through an aesthetic reference.
- After: translate those visible features into a short casting target and compare look-1 before propagating identity; retain garment truth, fixed poses and the existing no-identity-copy/no-nationality-inference boundary. One instruction sentence; no model library or scoring framework.
- Source eval 90 covers the reference-to-casting case. No installed-version change or release.

## Source change — 2026-10-01 minimal casting and QA repair (included in beta.10)

- Before: identity consistency did not explicitly check user-declared casting goals; the priority chain contradicted garment-first guidance, and known hem-label drift was recorded as user review in the local example.
- After: capture optional user-stated apparent age, body presentation, hair/makeup and temperament without a questionnaire or nationality/customer inference; check them at look-1. Safety/authorization and garment truth precede fixed poses and style. Confirmed structural drift requires `qa-retry`; missing source views require supplement/hold, not a pose substitution.
- Retain per-image actual ordered references/roles/hashes, identity reference, prompt/output hashes and QA in the existing run record; historic missing invocation facts remain unknown.
- Source regressions: evals 87–89 cover explicit/default casting and structural-drift blocking. These are text scenarios, not new casting-image benchmarks. Local two-image repair evidence is kept separately in `outputs/caiguang-fixed-poses-20261001/repair-run.json` in the parent workspace. No release or installed-version update.

## 1.0.0-beta.9 — Caiguang onboarding prerelease

- Closeout: repair a source-only test link in the packaged capability guide and add a staged-document reference regression. Summarize current public/candidate/evidence status in the existing Beta register; label the older work ledger as historical and surface the retained installed-plugin text result in compatibility. Runtime files and frozen demo media are unchanged; public beta.8 assets remain immutable.

- Unify plugin and skill display names as 裁光 / Caiguang, update public metadata URLs and describe the AI Fashion Studio. Preserve the `threadtruth-studio` IDs, invocation, install path and implicit policy.
- Fix Issue #1 in the local candidate: include preparation before photo upload in discovery, distinguish missing photos from fictional text-only design, and end missing-photo replies with a source-photo request rather than a conditional generation promise. Add six source evals, matched fresh CLI runs and sanitized output grading; installed beta.8 remains unchanged.
- Installed-plugin forward test exposed a pre-read commentary gap not seen in project-scoped confirmation: 2/3 original prompts forecast generation before reading the skill, although final replies passed. Front-load the first-reply boundary in discovery metadata, quote it as valid YAML, and retain failures. The final installed candidate passed 8 fresh text probes including pre-read commentary; beta.8 backups and other plugin states were preserved. Desktop UI and fresh-host verification remain pending.
- Add version-matched candidate installation, upgrade/rollback and first-use trial instructions; keep public beta.8 download links and frozen assets unchanged.
- Narrow the package document allowlist to recipient material; exclude development changelog, verification records, work register, release-readiness notes and application drafts. Retain public demo media and its required rights/provenance records.
- Regression coverage checks excluded development files and the existing manifest identity contract. No image-provider call, external user adoption or fresh-host discovery is claimed.

## Unreleased — complete product guide

- Explain garment and coordinated-outfit AI model portraits, the six default poses, six independent images and a choice of 24 styles across both READMEs and the homepage.
- Add a bilingual input guide with minimum versus recommended photos, variant grouping, unseen-detail limits and common questions; connect installation and web tutorials to copyable generation prompts.
- Surface both frozen 24-style preview collections and distinguish them from independent finals; retain the explicit gap in public complete outfit-set evidence.
- Refresh sharing copy and its cover through the existing brand-asset process. No runtime behavior, frozen demo evidence or published beta.8 archive is changed.

## Unreleased — first-use and gallery clarity

- Clarify the tested installation environment, download location, dry-run review, first-use checks and troubleshooting in both languages. Copied verification commands stop before extraction if changing directory or checksum verification fails.
- Add bilingual gallery controls, English per-style prompts, a direct case jump and text-only sharing metadata; preserve the paired images, source credits and review records.
- Expand bilingual installation feedback and bug-report forms, link to troubleshooting and support, and update current support links to the renamed repository.
- This is a documentation and gallery update; published beta.8 archives, tags and checksums remain unchanged.

## Unreleased — beta.8 controlled retry candidate

- Add explicit visual rejection and one-request retry grants bound to an approval ID and rejected attempt number; preserve initial authorization and cumulative request count.
- Retain failed prompts, conversations, QA and immutable originals; version retry outputs and handoffs, and validate historical evidence.
- Reject unknown-request retries, approval replay, duplicate old results and accepted-anchor replacement. No automatic retries, new live generation, installation or publication in this implementation round.

## Unreleased — beta.7 web delivery candidate

### Behavior before

- Entry recommendations existed, but no shared submission ledger or staged handoff package existed. Comparison search failed for multiword English labels, and hiding conclusions left visible advice.

### Behavior after

- Adds a local task ledger and staged manual handoff plus host-browser execution instructions. One/six-image budgets, durable reservations, recovery, frozen ordered references, accepted look-1 identity anchor, complete PNG validation and output checks gate progression. No network or browser calls occur in the helper.
- Fixes comparison search and hidden-result leaks, separates the product-first local landing page from the research gallery. New gallery files are not included in the plugin allowlist.

### Eval coverage

- Adds request/authorization, recovery, anchor, order, canvas, duplicate/truncated image, changed output and durability regressions. Browser checks exercise English/Chinese searches and hidden conclusion visibility.

### Verification

- Candidate only. No provider call, new-task real workflow, install or publication is claimed. Supplementary comparison and workflow requests require separately approved material list and exact budget. Existing beta.6 and historical evidence remain immutable.

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
