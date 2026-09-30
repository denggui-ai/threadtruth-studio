# Issue #1 — missing-photo discovery and reply regression

Conclusion: **candidate fix verified for the scoped maintainer CLI text probes; public Issue remains open pending packaged-plugin/fresh-host verification.**

Mode: eval + forward regression. Target runtime: `skills/threadtruth-studio`; development evidence root: repository root. This work does not promote the skill's overall `DRAFT` maturity or validate image generation. User authorized fresh text probes, necessary fixes and an Issue update; no image generation, global installation or release publication was performed.

## Reproduction and changes

The exact original prompt was retained:

> 帮我把一件外套做成电商模特图。目前还没有上传图片，也没有授权生图。请简短回应。

Installed beta.8 reproduced the defect: no full runtime read was observed, and its first visible reply ended with “等你明确授权后再生图”. Frozen project-scoped old instructions reproduced the same failure in both matched iterations.

Two small changes were evaluated separately:

1. Front-load apparel model-image requests and preparation before photos are uploaded in the description. Replace the broad “text-only concepts” exclusion with fictional text-only garment design, preserving non-apparel and virtual-try-on/API exclusions. This candidate loaded the full skill on the original prompt, but still forecast generation in its final reply.
2. Extend the existing missing-photo rule with a concrete material-preparation endpoint: request a real source photo and stop there; do not turn the closing sentence into a conditional generation promise. An explicitly requested style catalog remains allowed, without pretending to recognize the unseen garment or recommending a style for it.

Only those two lines of `SKILL.md` changed relative to `08df9a6`. Technical IDs, implicit policy, image-generation authorization, six-image delivery, reference files, styles, scripts and tools are unchanged. Source evals 81–86 and matching trigger cases retain the exact prompt, explicit control, full catalog, coffee-machine negative control and Chinese/English garment paraphrases. Beta.9 recipient trial instructions now distinguish implicit and explicit fresh-task checks.

## Method and evidence

- `codex-cli 0.155.1`, maintainer host, fresh `codex exec --ephemeral --json` sessions in isolated temporary working directories; no prompt contained expected answers or evaluation criteria.
- Read-only sandbox; `image_generation`, hooks and multi-agent execution disabled per process. No model override. The model identity was not exposed by the exec JSON and is recorded as unavailable.
- Installed baseline: enabled beta.8. Matched candidates: project-scoped `.agents/skills` copies, with only `threadtruth-studio@personal` disabled per process. No persistent config, installed plugin or authentication files were edited. Other installed skills remained available; the host warned that skill descriptions were shortened to fit its catalog budget.
- Baseline and candidates were frozen separately; matches ran in balanced pairs. Total 24 text sessions: 4 installed baseline controls, 8 first-iteration runs, 8 second-iteration runs, and 4 final confirmation runs.
- Full runtime loading means the complete expected `SKILL.md` text appeared in a successful read's returned content, not merely a skill name or a read command. Partial reads and unobservable explicit loading remain separate.
- [Sanitized output extracts and deterministic read facts](evidence/2026-09-30-issue1/issue1-runs.json) retain exact synthetic prompts, assistant outputs, runtime hashes and exposed usage/time. Private raw logs, reasoning, plugin inventory and auth data are excluded. Local runtime paths are normalized.
- A fresh grader received opaque specimen labels, actual replies and trace facts, without configuration labels or expected winners. [Independent grades](evidence/2026-09-30-issue1/issue1-grading.json) were unblinded only after grading. Aggregate/viewer files are retained with the local review artifact; their percentages describe text assertions in this small sample, not general reliability or image safety.

## Final candidate results

| Probe | Content | Full skill read | Other observed facts |
|---|---|---|---|
| Original minimal prompt, 3 fresh runs | 3/3 pass | 3/3 observed | Stops at real-photo/material request; no conditional generation forecast |
| Chinese shirt and English dress paraphrases | 2/2 pass | 2/2 observed | No invented recognition or garment-specific style recommendation |
| Full 24-style catalog request | Pass | Observed | Registry read; 24 slugs each once; no garment-specific recommendation |
| Explicit `$threadtruth-studio` control | Pass | Not observable | No tool-read event; do not count the named skill or correct reply as proof of full loading |
| Coffee-machine negative control | Pass | No read observed | Remains in non-apparel product scope |

All 8 final-candidate outputs passed independent content grading. Five catalog outputs across the experiment contained all 24 slugs exactly once; all five coffee-machine controls remained outside apparel scope. The grader found conditional-generation wording failures in six earlier outputs, including the first candidate's minimal reply. These failures remain retained rather than being discarded. One earlier catalog tail was a semantic boundary case and its grading rationale is preserved.

## Static and package verification

- Full existing Python suite: 216 ran; 215 initially passed and the old exact-description fixture failed as expected after the wording change. Updated that existing fixture; all 14 repository-contract tests then passed. No runtime code or additional unrelated tests changed.
- Skill quick validation, source strict and staged-runtime strict validation: pass. Official plugin validation of source and stage: pass.
- 24/24 style packs and existing deterministic routing assertions: pass (132 ownership, 22 query, 3 scoring, 47 style targets, 13 style conflict, 1 core conflict). These deterministic checks do not measure model discovery.
- Refreshed beta.9 archive: 269 files, 33,286,314 bytes; SHA-256 `fe972ef2dc4ec1dda90ba31dfff99cc13d535ff822c13996a69211d58755d43a`.
- Actual `shasum -a 256 -c` check, CRC, path/duplicate/symlink/size/compression bounds and byte-for-byte archive/stage/source parity: pass. Development evals, outputs and reviews remain outside the release envelope.
- Prior candidate archive and frozen public beta.8 assets remain unchanged. This artifact is a separate local candidate build, not a published replacement.

## Finding closure and remaining limits

- `fixed` within scoped candidate: original minimal implicit trigger and conditional missing-photo reply; retained fresh runs and independent grading support this narrow conclusion.
- `fixed`: source eval and recipient trial coverage now include the original Issue entry.
- `deferred(issue #1)`: validate the packaged candidate through installed-plugin discovery in a new task, including a non-maintainer host; publish/integrate the fix before closing the public issue. Project-scoped local discovery does not prove plugin installation or GUI behavior.
- `deferred(issue #1)`: explicit full loading was unobservable in one candidate run. It was not counted as a loading pass.
- No image tools were available in these probes, and no image or alternative-service calls were observed. This is not evidence of paid-action authorization enforcement with image tools enabled, image quality, real-image recognition, all-style workflows or external adoption.
- Human review of the retained outputs is available; no human feedback or general self-evolution level is inferred from an empty review form. No push, merge, tag, Release or live plugin update is part of this round.
