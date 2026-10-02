# Authorized real-person single-image trials

Status: `candidate`, `image-draft`; limited face-reference test, not real-person six-image verification or commercial acceptance. Follow-up to the retained [native AI run](2026-10-02-model-reference-reuse-native.md) and [accessory correction](2026-10-02-model-accessory-repair.md).

## Scope and authority

The approved test plan already included two real-person trials, one image per product. The user supplied the missing portrait expressly as authorized real-person material, in response to the request for本人明确同意及必要使用权的人物参考. Existing generation approval and this session declaration were recorded; consent was not inferred merely from a silent upload. This is reliance on the user's declaration, not independent adjudication of rights or permission to publish the portrait/results. No identifying name, raw portrait or full prompt was added to this repository.

The provided portrait supports visible face, apparent age/skin, long brown hair and makeup. It does not establish full-body measurements or proportions. Both tasks use `source_type=real`, `scope=face`: preserve visible identity/hair/makeup, with a separately disclosed provisional natural adult body presentation. Precise age, measurements, sizing and nationality remain unknown. Result-person acceptance is separate from the source's authorization and remains pending.

## Execution and evidence

Two native calls returned two unique 1024×1536 PNGs. Each task consumed its one planned call; no retries or five-image continuation. Prior returned images: 19; cumulative returned images: 21. Both calls actually attached the same original authorized portrait. A attached one outfit source plus portrait; B attached sufficient front, collar-detail and rear product views plus portrait, counts `[2,4]`. The pictured person in B's rear garment source is explicitly not an identity reference. No generated A image was substituted as B's original face source.

Retained private checks verify full PNG decoding, exact canvas, actual handoff prompt hashes, base prompt hashes, ordered attachment hashes, frozen model/context and output hashes. Both result model-confirmation fields remain null; no package was exported as already confirmed. Actual provider model and independent raw invocation telemetry are unavailable, not estimated. Runtime code is unchanged; no new 257-test claim is made.

## Visual disposition

A is `qa-retry`: only the upper front blazer button is assessable. Hand/pocket overlap covers the lower-button region, contrary to the explicit prompt requirement that both buttons remain assessable and not be obscured by the hand/bag. This is a concrete visibility/verification failure; it does not prove that the hidden button was deleted. Source necklace/watch and the other major outfit items appear. The read-only independent reviewer actually viewed portrait, garment, output and exact arguments and confirmed this failure.

B is `qa-user-review`, confirmed by the read-only independent visual recheck. White hooded quilted vest, gold zipper hardware, brown knit underlayer, jeans and plain white shoes follow the declared product/styling scope; no obvious A outfit or portrait necklace/room leakage is observed. Far-side pocket construction is partly angle/hair occluded; precise hardware, quilt channel count and material/color need source-owner checks. The generated face is somewhat smoother and narrower in outline than the portrait; likeness remains a user acceptance question, not a biometric proof.

Both results show visible facial/hair continuity with the provided portrait in this sample, subject to selfie perspective and camera-distance differences; no claim of exact本人还原 or actual-body reconstruction. The generated body's acceptance as a future visual target has not been fabricated.

## Remaining work

- `MODEL-REAL-2`: planned execution complete; original missing-input blocker resolved. Limited two-single-image review is not a passing real-person full workflow.
- `MODEL-REAL-A-BUTTON-VISIBILITY`: `open`, image correction needs corresponding separately authorized single retry; none was performed.
- `MODEL-REAL-RESULT-CONFIRMATION`: pending user acceptance of the generated person/body presentation before a confirmed reference package or continuation.
- The earlier AI correction's look-6 floating artifact, commercial source acceptance, broader person/product/style coverage, fresh-host checks, installation and publication remain unresolved.

Private files remain under the parent's `outputs/caiguang-model-reference-reuse-20261002/real-person-input/`, `real-outfit-a/` and `real-outfit-b/`: original authorized portrait, consent scope, factor sheet, two exact calls, native-output copies, integrity and readable report. Source changes here document evidence only; prior run evidence and original AI master are retained unchanged.

Independent closeout actually viewed the portrait, both outputs, all corresponding garment sources and exact call arguments. Both PNG/call hashes and scoped dispositions were checked independently. Source strict validation (105 declarative evals), public tree scan, changed-document local links and diff whitespace checks pass. These are evidence/documentation changes; runtime code and the earlier passing 257-test suite are unchanged, so the full suite and generation were not repeated. The package-facing guide does not link to excluded source-only verification files.
