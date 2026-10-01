# Model selection/reuse candidate verification — 2026-10-02

Conclusion: conditional. Mode: authorized development implementation plus independent read-only review. Platform: Codex, existing native generation and explicitly chosen ChatGPT web adapter. Status: candidate implementation; visual capability unverified.

Runtime target: `skills/threadtruth-studio/`. Development/evidence root: this repository. Base: release/caiguang-beta10, `f7323aa2dff320ebbd4bb2fef3629c025b12dfa6`. Branch: `feat/model-reference-reuse`. No live install or frozen public asset was modified. No external message, image-provider call, merge, push or publication occurred.

## Implemented boundary

Adult single-person existing authorized real/AI identity, or new casting; separate original identity, aesthetic-only, current-first-image and garment roles. Technical first-image acceptance and human model acceptance are distinct. Direction cards, image confirmation and portable factor/reference cards deliver fixed/adjustable/unknown conditions with provenance. Proposed targets become fixed only at accepted package export. New garments remain authoritative; original identity references are never automatically replaced by later outfit results.

Schema-2 local native/web tasks preserve hashes, request counts and failed-attempt history. A confirmed pose-1 trial can add five explicitly authorized slots without another first-image generation. Old schema-1 recovery remains unchanged. Unconfirmed first-model rejection supports a separately authorized corrected trial and preserves the rejected result plus old model conditions. Confirmed identity anchors cannot be replaced through that path.

## Independent review and closure

A fresh-context read-only reviewer inspected the working-tree changes and new files against the approved brief, and independently ran 24 model tests plus 16 legacy web tests. No Critical finding. Initial merge assessment: With fixes.

| ID | Finding and observed failure | Closure |
|---|---|---|
| MR-1 | Cold-editorial mood still injected detached expression, forbidden smile and old makeup despite friendly-smile model override | fixed — full preview/single-prompt regression failed before mood-clause filtering; passes after. Photographic lighting, retouching and safety clauses retained. |
| MR-2 | Unknown body value could also occur in locked prompt conditions; duplicate factor names could disagree | fixed — negative regressions failed before validation; unknown values/confirmation, same-name states and fixed/adjustable overlap rejected. |
| MR-3 | Technically accepted but disliked first model had no rejection/retry path | fixed — user-rejection workflow failed before reject-model; explicit retry now retains old output/model/budget and optionally updates proposed conditions. Method and native CLI end-to-end tests pass. |
| MR-4 | Existing web Markdown/HTML tutorials described technical pass as sufficient to continue | fixed — regraded as recipient-flow correctness; all three entry guides distinguish candidate human confirmation and released legacy behavior, and link to the new guide. |

Reviewer set aside actual image quality/likeness, account-bound uploads/downloads, first-host discovery and live installation; these remain outside local verification. Library/database/search/cloud and child reference packages are accepted backlog, outside this implementation.

## Verification

- Focused runtime/prompt/legacy tests: 50 passed after reviewer fixes. Synthetic fixtures only; this is not a generated-image benchmark.
- Complete suite: 246 tests passed after reviewer fixes (247.764 seconds). Initial default-Python attempt encountered 16 missing-fontTools setup errors; rerun uses the existing complete project dependency environment. No dependency install or global configuration change.
- All 24 pack lints and registry agreement passed; route checks passed (132 ownership, 22 query, 3 score, 47 style-target, 13 conflict and 1 core conflict assertions).
- System skill-creator quick validation passed in the existing PyYAML environment. Governor source and staged-runtime strict checks passed; source has 101 declarative evals. New evals 92–101 are scenarios, not retained native trigger evidence.
- Public tree scan and diff whitespace check passed. No diff under frozen demo/media and style-pack directories.
- Temporary allowlist package built locally outside the repository. All 43 runtime files match source bytes; archive integrity, new tools/guide inclusion and development-evidence exclusion verified. Stage is smoke-tested only, not installed or released. It retains beta.10 metadata for internal packaging verification; do not distribute this modified artifact as the released beta.10.

## Outstanding validation

`deferred(MODEL-IMG-14)`: needs separate user authority and input assets. Planned calls: new AI model, two outfits × six images = 12; authorized real model, two outfits × one image = 2. Failures never add automatic calls. Independently compare each original identity and new garment, then obtain user acceptance. Two real single-image trials cannot support a real-person six-image claim.

Actual native/browser tool invocation, attachment submission, fresh-host discovery and installed-plugin user flow were not run for this candidate. No production-ready, released, image-ready or closed-loop visual/self-evolution claim is made. The existing installation remains beta.10. Retain the development branch and worktree for final image validation and a separately authorized release.
