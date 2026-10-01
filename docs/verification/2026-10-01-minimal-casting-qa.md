# 2026-10-01 minimal casting / QA repair verification

Current status: source candidate; original Japanese hem-label repairs are complete. The green-shirt home case's visual direction has been accepted. Fine garment/source review remains separate; no release/install authorization. Base `0ee5788`, branch `fix/caiguang-casting-qa`.

## Latest closeout

- A1/A2 fixed in retained `look-1-v3` / `look-3-v3`: flat rectangular hem labels, no hanging component or pocket opening. The latest local repair record includes subsequent authorized rounds; the failed first round below is historical.
- Source commits `cf5b712` and `fc89940` retain the six poses and 24 packs, add optional casting/first-image comparison and one sentence translating an aesthetic reference into visible casting targets. No model library, scoring system or configuration framework.
- The retained green-shirt home case contains six independent 1024×1536 images, four garment references and a first-image identity anchor. User feedback accepts the visual direction. Wider seated framing and obscured garment details remain explicitly recorded; visual approval is not substituted for source-fact verification or public-use consent.
- The earlier eight-button conclusion was a false positive caused by counting a pale-edged buttonhole. Corrected records and original images are retained. No new image calls are needed for this closeout.
- Development source and local case records are synchronized; installed/public versions and frozen previews remain unchanged. No L3 self-evolution, release maturity upgrade or commercial `image-ready` claim.

## First-round verification (historical)

- Runtime target: `skills/threadtruth-studio/`; evidence root: repository root. Four instruction files, three source evals (87–89) and changelog updated. No new config/model library. No style-pack or fixed-pose edits.
- Static: quick_validate PASS; strict source standard PASS (89 evals); strict runtime profile PASS on a clean temporary copy excluding pre-existing Python caches; all 24 packs PASS; trigger-route assertions PASS. The raw checkout runtime profile detects pre-existing ignored `scripts/__pycache__`, dated before this task; it was preserved rather than silently deleting history.
- Affected suite: 66 tests PASS (`test_preview_rules_equivalence`, `test_pilot_ecommerce_lighting`, `test_style_preview`, `test_generation_entry`, `test_repository_contract`). Frozen prompt equivalence remains intact.
- Full-suite baseline: 217 tests, 16 setup errors from absent fontTools; remaining 201 passed. Test dependencies from requirements-dev.txt were installed into `/tmp/caiguang-test-deps` only. Final full suite PASS: 217 tests in the temporary dependency environment.
- Fresh text forward probe: an isolated subagent read the candidate skill and needed references, without seeing eval expectations, changelog or diff. Three synthetic tasks: specified age/body/hair/makeup/temperament, unspecified casting, and confirmed structural drift plus missing back view. Raw responses retained in the parent workspace output folder. Review grading: 3/3 satisfy the scenario expectations (explicit short target / existing defaults without questionnaire / qa-retry stop with supplement/hold); no generation call, no actual casting-image quality claim, no baseline pair or L3 self-evolution claim.
- Native repair: planned max 2 calls; actual 1; automatic retries 0. Japanese look-1-v2 retained same fictional identity/pose and actual 1024x1536 canvas, but still had the extra dangling lower hem structure. QA failed (`qa-retry`), so look-3 was not called, as required by the accepted stop-on-failure plan. No repaired image accepted, no original replaced.
- All 12 original PNG hashes/dimensions checked unchanged. Per-call exact ordered references/roles/hashes, identity target, prompt hash, output path/hash/size and itemized QA saved in `repair-run.json`; missing historic invocation facts are `unknown`.
- Findings A3/A4/A5 fixed for the declared source/record scope; A1/A2 remain open; Japanese look-5 remains deferred(manual-review). Original group remains image-draft.

External retained local artifacts: parent workspace `outputs/caiguang-fixed-poses-20261001/{REVERSE-AUDIT.md,REPAIR.md,repair-run.json,casting-forward-probe.md,repair-review.html,japanese-lifestyle/look-1-v2.png}`. Originals, historical run/gallery/zip and frozen public previews retained. Full tool logs/user private data are not committed.
