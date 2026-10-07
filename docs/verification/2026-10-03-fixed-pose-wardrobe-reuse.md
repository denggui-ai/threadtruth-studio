# Guided fixed-pose wardrobe reuse — 2026-10-03

Conclusion: conditional, development candidate. Mode: narrow stabilization of an existing, manually reviewed fixed-pose workflow. Runtime target: `skills/threadtruth-studio`; evidence root: repository root. Private portraits, reference packages, local traces and retained-image replay are kept outside the repository. No installation, external publication, generation or dependency installation in this change.

## Implemented scope

- Existing original-identity/supplement paths and first-image gates already existed. Add only explicit pose editing targets and a reusable local protection helper; preserve original six-pose definitions and 24 style packs.
- Optional package schema3 stores original references separately from selected pose mothers, per-pose accepted/qualified feedback, image hashes and independent original-fidelity/candidate-continuity/garment QA. Failed or unreviewed mothers cannot export. Missing/changed/escaping files, duplicate image roles and unavailable poses block reuse. Schema1/2 remain readable.
- Ordinary new-product task import does not attach pose mothers, inherit old clothes or grant current-product model confirmation/authorization. Fixed-pose editing explicitly selects one mother; originals remain independent review inputs.
- `wardrobe-edit.cjs` requires already-available host Node/sharp. It freezes mother and product attachments, a manually reviewed head/face guard and feathered clothing region before a call. It performs no calls. Local composition rejects canvas mismatch, EXIF rotation, transparency and overwritten result versions. Region refinements retain the original head guard and all prior outputs.
- Runtime routes and the user guide explain first-result confirmation, garment-source limits, independent original/continuity/product checks and the distinction between a protected existing pose and new head/pose generation. No automated masking, model database, hard identity constraint or commercial acceptance added.

## Evidence

- Final relevant deterministic regression: **61 model tests + 8 wardrobe tests passed**. Test fixtures are synthetic, not private customer images. Source evals 116–120 cover happy path, scoped acceptance, missing pose/dependency, boundary repair and completion claims.
- Six retained native donors were replayed through the reusable helper without new generation. Read-only Pillow independently confirmed each replay equals the previous final output in RGB pixels and each own-mother head/face region remains unchanged: **6/6**. Replaying reviewed final regions is retrospective deterministic verification, not proof that new automatic masks or future provider edits will pass.
- Fresh explicit-path workflow check actually validated/read the schema3 private package, selected the seated image and viewed mother/original/product. Its answer and attachment plan preserved scoped acceptance, retained current-source truth and stopped before generation/editing/upload. Planning paths are not provider invocation evidence; actual generated-call attachments would use newly frozen private-run copies.
- Independent code review reproduced a P2 mismatch: initial prepare used external mother path for the planned attachment while composition verified a frozen copy. Fixed by snapshotting mother **and garment** attachments and planning those exact copies; regression changes external sources after prepare. Reviewer rechecked the final helper, passed seven tests and independently tested opaque/transparent/rotated images; finding **fixed**. The final suite adds the eighth orientation/transparency regression.
- System creator validation, governor source strict, governor runtime-stage strict, public tree scan and diff checks pass. Runtime-only stage contains 45 source-identical files; no source evals, tests, private data or caches. Model-package ZIP clean extraction validates all seven image hashes and remains portable.

## Full-suite environment limitation

A broader run executed 286 tests: 270 passed, 16 historical brand-font tests failed at missing `fontTools` import. A local cached fontTools retry exposed absent Brotli as the remaining font dependency. These are recorded as **deferred(environment-font-dependencies)**; no dependency installation, font/brand code changes or fake skip-to-pass result. Relevant final regressions passed after subsequent small fixes. Do not claim final all-suite pass.

## Boundaries and findings closure

- **fixed**: actual attachment/frozen-base mismatch; local boundary/version/canvas/guard regressions.
- **deferred(environment-font-dependencies)**: 16 brand-font regressions cannot run in this host environment.
- **deferred(original-real-face-fidelity)**: existing mothers retain differences from original portrait; own-mother zero pixels does not eliminate them.
- **deferred(product-source-review)**: source knit/shoulder construction and commercial details remain uncertain; scoped user usability acceptance does not close them.
- **backlog**: automatic segmentation, new head angles, new pose generation, multiple people, model search/library, cloud sync and fresh-host automatic discovery. Outside this change.

This is a guided development workflow with retained deterministic replay and one fresh planning check. No new provider image test, installed-version upgrade, blanket six-pose original-real-person verification, automatic masking claim or self-evolution maturity upgrade. Runtime and private-reference deployment are separate; the private package is data and confers no call authority.
