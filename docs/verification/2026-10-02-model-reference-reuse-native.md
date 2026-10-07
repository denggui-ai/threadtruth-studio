# Model reference reuse: authorized native test and follow-up audit

Conclusion: conditional. Mode: eval and forward-test, followed by authorized stabilization. Status: candidate overall; limited AI identity continuity observed, not production-ready or released.

Runtime: `skills/threadtruth-studio/`. Evidence root: this development checkout. Base candidate: `b91d421`, branch `feat/model-reference-reuse`, based on released beta.10. Current installed plugin remains unchanged. Test images and full actual arguments are retained in the parent's private output directory `outputs/caiguang-model-reference-reuse-20261002/`; they are not shipped or copied into this source tree.

## Authority and retained calls

The user authorized the planned 14-image test (two AI outfits × six, two authorized-real single trials). The initial AI trial failed the source blazer's two-button requirement. Generation stopped. One separately authorized targeted retry restored the two buttons. The user then confirmed the displayed corrected AI person and delegated subsequent test-person acceptance; this did not confer product commercial acceptance.

Returned native images: 13, comprising one rejected original, the separately authorized corrected first, five A continuation images and six B images. All returned PNGs are 1024×1536 and have unique hashes. No generated image was used to silently replace the original long-term person reference. The B first has delegated test-only acceptance, not fabricated direct user commercial signoff. Actual provider model, independent raw invocation telemetry and implicit-trigger facts are unavailable; no estimates are made.

One attempted B handoff had six attachments. The host rejected its arguments immediately with `referenced_image_paths must contain at most 5 paths`, producing no image. The original task remained untouched. A private recovery version retained the accepted B first, its confirmation, the reserved look-2 and cumulative budget. Future source views were explicitly reduced to front, hood/collar detail and rear; the redundant zipper-pull close-up was omitted, with reason recorded. Both original identity and the current first remained actual attachments. There was no new first generation or additional request grant.

Real-person trials: zero. No face reference with explicit likeness consent and necessary rights has been supplied. Source-photo display rights were not reinterpreted as identity-replication consent. Two outstanding real trials cannot be repurposed as automatic correction calls.

## Independent visual grade and corrected disposition

A fresh-context read-only reviewer actually viewed all twelve selected outputs, the original person image and relevant garment photographs. Facial shape, eyes/brows, nose/lips, age impression and shoulder-length brown waves remain visibly continuous in this two-product sample. B contains no obvious old A blazer, white top, olive tote or brown gold-bit shoes. B's unprovided underlayer neckline, full jeans silhouette and plain white sneakers were explicitly declared low-presence styling suggestions before generation.

The reviewer identified source accessories missing from A: no visible original necklace or wristwatch in the six outputs. There was no authorization to exclude them. The primary agent had overused “tiny details need review” and continued the group. That was an incorrect source-QA disposition, not a passing garment result. The A full-outfit grade is now `qa-retry`; original technical acceptance and human person choice remain in history. All six A acceptances were revoked with actual audit reasons, without modifying their images or performing another generation. A cannot export or propagate its failed first as a technically valid product anchor.

B retains `qa-user-review`: no obvious blocking identity, anatomy, pose, canvas or main garment drift was observed, but zipper geometry, subtle material/color, actual fit and final source acceptance remain human checks. A's earrings and unseen rear blazer construction are uncertain, not claimed as confirmed failures or faithful reconstructions. All outputs remain `image-draft`. The private person package retains the confirmed original image only for person comparison; it is not a product approval or generation grant.

## Findings and closure

| ID | Finding | Disposition |
|---|---|---|
| MR-5 | Native first accepted five inputs but later first-anchor addition exceeded the host limit | fixed: batch-create, continuation, actual handoff/reservation and preview attachment preflight; sufficient sources selected explicitly, never silently dropped |
| MR-6 | Known A source accessory omission was treated as generic detail uncertainty | fixed: QA records/report corrected and old evidence retained; open `MODEL-IMG-A-ACCESSORIES`: image correction requires corresponding explicit authority, no automatic calls |
| MR-7 | Duplicate identity count could conservatively reject an otherwise normalized plan | fixed: schema2 explicitly requires identity deduplication before freezing and prompt numbering |
| MR-8 | Late independent failure could not revoke prior technical acceptance | fixed: schema2 audit-reject retains previous QA, output, confirmation and budget, blocks failed anchor export/propagation; a new authorized first retry requires fresh confirmation |
| MR-9 | Nonfirst late correction was blocked by the first-anchor downstream rule | fixed: schema2 look-2…6 can be individually repaired with explicit authority while later accepted files remain; first anchor with downstream work is protected; schema1 unchanged |
| MR-10 | Backward nonfirst repair could reserve while a later request was reserved/unknown | fixed: schema2 checks all unresolved requests before a new reservation; recovery precedes submission |
| MODEL-REAL-2 | No authorized real identity inputs | blocked(input): two single-image real tests not executed |

Final independent code review reports no remaining Critical/Important issues in this diff; it independently ran 38 model tests and 16 legacy task tests. Code review acceptance does not close the garment-image failures.

## Deterministic verification

The new behavior regressions were observed failing before implementation and passing afterward: five attachment-cap cases, duplicate identity input, late first-audit rejection, fresh confirmation after first retry, complete-set nonfirst repair, and reserved/unknown later-request recovery. Focused model tests: 38 passed. Final complete suite: **257 tests passed in 354.702 seconds**. Prior intermediate complete runs: 251 and 254 passed. Tests use synthetic local images, not additional generation. The existing temporary fontTools dependency environment was reused; system creator validation was rerun in the existing PyYAML authoring environment after default Python lacked PyYAML. No dependency installation or global changes.

Source strict validation passes with 105 declarative evals; runtime quick validation and public tree scan pass. An internal allowlist archive was rebuilt and extracted outside the source tree: 43 runtime files match source bytes, archive integrity passes, new guide/tools are present and tests/evals/changelog are excluded. Extracted runtime strict validation passes. This smoke archive retains beta.10 metadata only for internal verification and must not be distributed as the published beta.10. No installation, merge, push or publication was performed.

## Unverified boundary

The image test is one AI person, two products, one studio style, with manual/independent QA. It cannot support arbitrary products/styles, real-person six-image workflows, true body measurements, accurate sizing, long-term repeated drift guarantees, fresh-host/plugin discovery or commercial readiness. A's accessory failure also shows that a prompt/ledger gate does not ensure correct visual judgment. The overall approved plan is not finally accepted until its outstanding image/source and authorized-real checks are resolved.
