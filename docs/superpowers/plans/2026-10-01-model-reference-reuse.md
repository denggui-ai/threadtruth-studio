# Model selection and reuse implementation

Approved brief: two entry paths (existing real/AI, new casting), first-image human confirmation, portable private references, no model library. Base: beta.10 f7323aa.

Tasks:
1. Portable model-reference validator/exporter and shared prompt assembly; test invalid cards, face scope, consent, tampering and style overrides.
2. Version-2 local task ledger: explicit reference roles, first-output confirmation, unchanged budget and one-to-six continuation; preserve schema-1 behavior. Both native and web routes use local records, never auto-generate.
3. Connect optional casting/reference input to new development preview/single prompts without changing frozen public evidence.
4. Align runtime gates, QA, safety, permissions, recipient guide, source evals and packaging.
5. Run focused/full checks, independent review, commit locally. Paid 14-call image verification, install, publication and push remain separately authorized.

Reverse-audit rulings:
- Classify mixed attachments per role; only actual garment images can satisfy the garment gate. A person image/card alone never authorizes garment generation.
- Likeness consent and first-output visual approval are distinct; neither implies generation authorization.
- Keep original identity references and the current outfit anchor separate. Aesthetic references never become identity assets.
- Continuation requires identical frozen context; no replacement of first output, authorization reset or unresolved request duplication.
- Native route needs local recording too; extend the existing local helper rather than add another ledger.
- Identity scope is face-only unless body evidence or an explicitly confirmed body target exists; no measured fit promise.

Progress:
- Baseline: 23 focused tests passed.

- Tasks 1–4 implemented; focused suite passed 50 tests after reviewer fixes. Full suite before fixes passed 242 tests; final reviewed candidate passed all 246 tests in the existing complete dependency environment.
- Task 5 independent review: three Important findings (mood conflicts, unknown/duplicate factor contradictions, no user-rejection path) reproduced RED and fixed GREEN; existing tutorial drift was regraded as required recipient-flow documentation and corrected in Markdown/HTML.
- Ruling: record first_pose in frozen task context — a test at another pose cannot truthfully become look-1 — cost if wrong: the user needs a separately authorized group instead of direct continuation.
- Ruling: proposed factors use target until actual first-image acceptance; package export promotes them while retaining recommendation provenance — cost if wrong: a misleading fixed-condition card; covered by tests.
- Ruling: user decline uses a distinct reject-model event and explicit retry with optional revised candidate conditions before confirmation; original identity/source/scope stay fixed — cost if wrong: a changed person needs an explicitly authorized new model version rather than in-place replacement.
- No model library, child reuse expansion, paid image generation, installation, merge, push or publication performed.

- Task 5 local closure: 246 full tests, 50 focused tests, all pack/router checks, source/staged strict standards, system creator validation, public scan, package integrity and diff checks passed. Independent reviewer findings MR-1…MR-4 closed fixed in the verification record. Candidate remains uninstalled/unpublished; MODEL-IMG-14 deferred pending separate authorization. Branch/worktree retained as required by the isolated development scope.
