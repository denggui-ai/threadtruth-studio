# Face fidelity stabilization — 2026-10-02

Conclusion: conditional. Mode: authorized development stabilization and regression evaluation. Platform: Codex. Status: candidate; local contracts verified within the checks below, provider image capability and release not claimed.

Runtime target: `skills/threadtruth-studio/`. Evidence root: this development checkout. Base: `34c8b28`, branch `feat/model-reference-reuse`. Source editing and local tests only; no generation, uploads, live install, merge, push or publication. Frozen style packs, poses, media, historical prompts and image evidence remain unchanged.

## Implemented and verified contract

- Original identity, explicitly selected accepted generated supplements and current garment sources retain separate roles. Supplements carry exact SHA256, actual human-acceptance summary and face/full presentation scope; face-only scope never supplies unknown body facts. Original identity remains primary in the actual emitted prompts and attachments. Acceptance notes remain data, not prompt instructions.
- Portable package schema 2 stores supplements separately; schema 1 remains readable. Existing models retain original images. Default task export keeps prior selected supplements without promoting the latest image; explicit opt-in can add the current QA-accepted and human-confirmed first image. New AI first images become originals without duplicate supplements.
- New task reference metadata is hash-checked. Supplements require this metadata hash even if it was removed; existing schema-2 tasks without supplements can still recover without silent migration. Model confirmation must bind the current first output. Invalid acceptance, scope, changed images, traversal, duplicates, native capacity and failed first anchors stop progression/export. Snapshot copying also checks the declared accepted hash and removes only its own incomplete new task on failure.
- Optional single `purpose=model-check` diagnostics cannot create or continue into a delivery six-pose set. Existing contexts keep their previous delivery behavior. Original production poses and authorization accounting remain unchanged; cross-task cumulative accounting remains an agent responsibility, not a new global ledger.
- Runtime rules separately report original-face fidelity, accepted-candidate continuity and product QA. Diagnostic framing is optional and requires corresponding call authority. User person acceptance cannot override product failures.

## Regression and independent review

Initial test-first run: 49 focused methods, with 13 failed assertions/subtests exposing missing supplement, diagnostic and export behavior. The first implementation passed all 49. Additional regressions exposed stale first-confirmation hashes and the missing reference-metadata hash compatibility bypass. These now pass, alongside explicit pre-extension schema-2 recovery.

A copied-file race regression uses resolved paths and asserts its mutation hook actually ran. Its red state was reverified in memory by removing only the snapshot hash comparison; changed accepted bytes were then allowed. With the comparison present it passes and the partial task is removed. The initial macOS path-alias fixture error was corrected rather than counted as valid evidence.

Fresh independent read-only review ran **56 model + 16 legacy tests (72 total), all passed**. Findings closed:

| ID | Finding | Closure |
|---|---|---|
| FF-1 | Removing reference metadata hash bypassed new supplement checks | fixed — hash mandatory whenever supplements exist; shape/scope/acceptance/files/original checked on read/export/mutation; old non-supplement tasks recover unchanged |
| FF-2 | Race fixture compared unresolved and resolved macOS temporary paths, so mutation did not fire | fixed — resolve both paths, assert hook invocation, independently rerun red/green |
| FF-3 | Human confirmation could name a different first-output hash | fixed — actual first-output hash required before export or later-reference use |
| FF-4 | Supplement could change between declared acceptance validation and snapshot copy | fixed — copied bytes checked against accepted SHA; incomplete new directory removed |

Full review retained privately outside the repository; review SHA256: `2bdc82dd09d60e912b31d555ee19f5b7b4e3728252d2d38e2e4c41efda07512a`. No remaining code blocker was reported within local contracts. This is not an independent visual or provider identity assessment.

Final complete suite: **275 tests passed in 241.808 seconds** after the integrity fixes. Earlier intermediate full suite passed 272 tests; final run includes the additional race and compatibility cases. A first attempt selected an incomplete temporary dependency environment and was stopped after setup errors. The final run uses existing fontTools dependencies; no dependency installation or global changes.

Creator/governor quick validation, strict source standard (111 declarative scenarios), public scan and whitespace check passed. The initial runtime-tree check found an ignored local bytecode cache; the tracked-file allowlist stage excludes it. Final tracked-file stage contains 43 byte-matched runtime files and passes strict runtime validation. Staged CLI smoke passes for supplement-bearing native handoff, schema-2 package export, explicit current-result export with face scope, original-image preservation, unchanged consumed attempts and rejection of export-only flags on unrelated commands. All smoke images are synthetic; no provider call. Scenarios 106–111 are designed regressions, not observed implicit-trigger or fresh installed-plugin evidence.

## Image evidence and unresolved scope

The prior separately authorized four-stage experiment returned exactly four distinct 1024×1536 images: AI half-body, real half-body, real full-body and real cross-product full-body. Prior returns were 22, cumulative returns 26. No fifth call or automatic retry. User acceptance exists for the real half-body and first real full-body candidates, not for the final cross-product output.

Independent visual observations support limited accepted-candidate continuity under the tested near-front studio conditions. They do not prove strict original-person facial fidelity, generalize across people/styles/angles, or identify the provider's internal failure cause. Multiple reference/framing/prompt changes occurred together, so causality is unisolated. The experiment preceded these runtime edits; the revised runtime has not been tested with new provider images.

`open(REAL-STRICT-FIDELITY)`: exact original facial preservation remains unproven. `open(PRODUCT-A-DENIM-COLOR)`: final denim is visibly lighter and washed versus the declared deep-indigo source; qa-retry, never propagate/export as an accepted product anchor. `open(FINAL-RESULT-USER-ACCEPTANCE)`: final candidate not human accepted. Prior AI accessory and final commercial source-review findings retain their historical states. No image-ready or real-person six-pose claim.

Private portraits, full prompts, raw generation receipts and image-review logs remain in the user output workspace, outside source/runtime. Full library/search/cloud sync remains accepted backlog. Installation/publication and further paid validation need their corresponding authority. Retain this candidate branch; rollback is a local revert of the stabilization commit, without rewriting historical outputs or earlier task records.
