# Photography planning implementation plan

Goal: preserve the six body-action categories while compiling coherent scene, framing, support and eye-gaze choices; retain original person conditions and distinguish product components/views before export.

Authoring: system skill-creator. Verification: Superpowers TDD, fresh independent source/request review, then production-governor. Runtime target is `skills/threadtruth-studio/`; development evidence root is this repository. Work starts at `11a2d94`.

## Constraints

- No style-pack changes, task-level shot_plan, live installation, publication, generation or automatic retries.
- Original real-person expression and angle coverage remain authoritative; AI/new preserve default head behavior.
- Existing frozen tasks and public examples remain historical evidence. New compilation reflects corrected rules.
- Private source images, request text and full logs stay outside tracked source. One later image calibration requires separate explicit authorization.

## Task 1: coherent compiler

- [x] Add failing regressions for scene/framing selection, B/D studio guards, preview/single equivalence, real-plan authority and default AI/new behavior.
- [x] Add optional `--photography-spec` with mode, D studio_prefix (2/3), and unique shots keyed by pose 1–6, allowing scene_index, framing, support and gaze. Share resolution between preview and independent prompt; retain six categories/order and actual-framing visibility/crop rules.
- [x] Run the targeted tests, plus all24 compiled helper-to-task exports, without external calls.

Produces resolved per-shot values for the private preparation stage. Frozen prompt/hash remains the task transport contract. No second runtime planning schema.

## Task 2: reusable rules and source evals

- [x] Update photography assembly, numbered vs custom boundary, actual-framing QA, and product component/view/current-appearance recognition.
- [x] Add source-side scenarios and CHANGELOG without claiming fresh model runs or visual success.
- [x] Check rule/helper agreement and existing custom/fixed-mother/continuation gates.

Consumes Task 1's compiler choices. Runtime prose owns semantic review of handwritten prompts; the helper cannot understand all free text conflicts.

## Task 3: actual-material preparation and closeout

- [x] Prepare a new private single-image task for master3 full-body seated, including three product facts, the original person and an explicitly labeled aesthetic case (five attachments). Do not mutate earlier failures or authorization ledgers.
- [x] Review the proposed light hierarchy, low-chroma color, spatial depth, asymmetric hand support, near-front face and original expression; check distinct motifs, component attribution and closed front vs supported rear slit.
- [x] Run full suite, 24pack byte/lint/router checks, creator/governor static gates, fresh independent review and exact exported request/attachment checks.
- [x] Commit source changes and update current handoff/roadmap with verified source scope, private prepared request and unverified visual scope.

Shared interface rulings: Task 1 resolves actual shot choices before Task 3 binds them to the existing real_face_plan. Task 2 must describe precisely this boundary. Support/gaze must never silently override an existing frozen real plan. No new first-pose continuation permission is introduced.
