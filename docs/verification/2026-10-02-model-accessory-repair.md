# Authorized AI outfit accessory correction

Status: `candidate`, `image-draft`, group `qa-retry`. This is a scoped follow-up to the retained [native test](2026-10-02-model-reference-reuse-native.md), not replacement evidence or a release.

The user authorized continuing the correction. Before generation the agent disclosed a new retained version, six calls maximum, one attempt per image, serial QA, and no automatic retry after a hard failure. The original first image already had downstream work, so the previous task/files were preserved and a new correction task was created. The original confirmed AI person remained the identity source; prior user delegation covers test-person acceptance, not commercial signoff or real-person consent.

## Actual result

Six new native images returned, all unique 1024×1536 PNGs. Prior returned images: 13; cumulative returned images: 19. One earlier local attachment validation rejection produced no image and remains separately recorded. The new task consumed exactly its six-call cap, with no retry or budget reset. First actual call attached garment source and original person; later calls attached those plus this corrected first, counts `[2,3,3,3,3,3]`. Actual handoff prompt hashes, ordered attachment hashes and output hashes were verified in private evidence. Exported handoff prompts include role/anchor instructions in addition to the frozen base prompts; both hashes are retained separately. Original person hash and previous task bytes remain unchanged.

| Image | Final technical disposition | Actual visual observations |
|---|---|---|
| 1 | `qa-user-review` | Original person continuous; necklace, left brown-strap pale-dial watch and both front buttons visible |
| 2 | `qa-user-review` | Wall lean; necklace/watch retained; both front buttons assessable; shoes/bag/hem uncropped |
| 3 | `qa-user-review` | Upright seated; necklace/watch retained; lower button naturally occluded, not independently countable in this view |
| 4 | `qa-user-review` | Walking; necklace/watch and two front buttons visible |
| 5 | `qa-user-review` | Forward lean seated; necklace/watch retained; lower button naturally occluded |
| 6 | `qa-retry` | Detached pale-gold bright oval in background near pixel `(427,313)`, with no visible chain/physical connection |

The primary agent and a read-only independent reviewer actually viewed all six images against the original product/person. No obvious identity switch or blocking anatomy/canvas issue was observed. The reviewer separately confirmed the first image before continuation. The final review explicitly inspected the primary agent's suspected artifact location: it is an independent visual recheck, not a blinded discovery experiment. Object category is uncertain, but the floating artifact is clear. Back-turn occlusion of the chest necklace is natural and is not the rejection reason.

Known necklace/watch presence was explicitly strengthened in the correction prompts, with garment source authority over the person reference's previous accessory omission. Two small circular gold source pieces were recorded as provisional hoop-earring styling, not confirmed SKU facts. Their category, exact jewelry/watch hardware, subtle garment color/material and unprovided rear construction remain source-owner checks. All images remain drafts.

## Closure and remaining scope

- `MODEL-IMG-A-ACCESSORIES`: fixed within the five assessable front/seated outputs; the complete six-image correction is still incomplete.
- `MODEL-IMG-A-REPAIR-6`: `open` for the detached-object artifact. The failed image/file/budget is retained and the task is not complete. A further correction needs a separately authorized targeted retry; none was performed.
- `MODEL-REAL-2`: `blocked(input)`; two real-person trials remain unexecuted without an explicitly consented likeness reference and necessary rights. Generation approval does not supply that missing input.
- Commercial acceptance, broader person/product/style evidence, fresh-host behavior, installation and publication remain unverified. No live changes, merge or push.

Private run artifacts are outside the runtime/source tree in the parent workspace's `outputs/caiguang-model-reference-reuse-20261002/ai-outfit-a-accessory-repair/`: task, exact calls, frozen sources, native-output copies, integrity record and readable report. Prior evidence and long-term person reference were not rewritten. This follow-up changes evidence and candidate status documentation only; runtime code and its previously passing 257-test verification are unchanged. The full suite was not rerun for these evidence-only changes.

Follow-up checks: source strict validation passes (105 declarative evals), public tree scan and diff whitespace checks pass, final task states/cap/no-retry assertions pass. All seven release-builder regressions pass in 106.114 seconds, including allowlist exclusions and shipped offline-link resolution. Temporary test archives are not a publication. The package-facing guide states the incomplete result without linking to excluded source-only evidence.
