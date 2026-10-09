# ChatGPT web: handoff and host-browser execution

Read when the user selects ChatGPT web. This adapter is designed for macOS Codex Desktop with an authorized dedicated Chrome and host browser tools. Actual availability is checked each session; installation alone does not supply browser tools. Other environments receive the manual package. No API, private endpoints, credentials, main-browser profile or undocumented tool commands.

## Local task contract

Use `scripts/web-task.py` relative to this skill. Store task files under the user's chosen workspace, never inside the installed skill. All helper commands are local; they do not click Send or grant approval. The agent records only approval actually given by the user and observations actually made in the browser. JSON task state is private workflow data, not public evidence.

Create a JSON spec containing `references` (ordered `{path,role}` images: garment-source, identity-reference, aesthetic-reference; accepted model-supplement additionally requires sha256, scope face/full and actual confirmation_note), `prompts` (one single-image prompt for action 2, or six for action 1), `size` (`[width,height]` resolved from the canvas contract), `context` (outfit, style, mode B/C/D, output_form, size, first_pose), `route` (chatgpt_web, or codex_native for the same local native ledger), optional `model` (see model-selection.md) or `model_package` (private package path), and `identity` (true for real/faceless models; false for flat/hanger/mannequin). Compose prompts from the selected style and prompt-build; do not use old comparison prompts with unrelated identity references. Resolve an unspecified exact size to a proposed size matching the user's ratio before submission; preserve any explicit dimensions. Explain the chosen canvas.

For a new `source_type=real` task that reuses a visible human face, inspect the original real references and declare `real_face_plan` as described in [model-selection.md](model-selection.md#真人参考覆盖与本轮朝向计划). It records observed coverage, separate body/head/gaze choices and per-look attachment selection while retaining the complete reference inventory. It does not classify real versus AI from pixels, measure faces or prove fidelity. Uploaded AI models and `new` models keep the existing workflow and prompt defaults; aesthetic-only, faceless and non-human tasks do not enter this branch. Resume older tasks without rewriting their history, and do not claim coverage was checked when it was not recorded.

```sh
python3 scripts/web-task.py init --task <new-task-directory> --spec <spec.json>
python3 scripts/web-task.py export --task <task-directory>
python3 scripts/web-task.py status --task <task-directory>
```

`init` refuses an existing task. Resume through `status`; never create a replacement task to reset an unresolved budget. Snapshot garment files and hashes; inspect actual images before declaring them garment sources. Only the next pending look is exported. Subsequent prompts remain locked until previous QA is recorded. In schema 2, a resolved visual rejection after look-1 does not block the next authorized ordinal; it remains rejected for final delivery. The first anchor, unresolved requests and retained provider/canvas failures still block. Schema 1 retains its strict accepted-predecessor rule. For real/faceless models, accepted look-1 is appended after all garment references and labeled identity-only. Its clothes, lighting and pose never become product authority.

## Authorization and entry setup

For an explicitly requested custom single-image presentation, set `context.first_pose="custom"` and `pose_description` to the actual user-selected action/framing; do not pretend it is one of the six masters. For correction of an existing person's failed output, set `context.purpose="correction-edit"` and include exactly one `edit-target`, original identity and current garment sources. This is a single-image task, not a continuation to six; all original reference/hash/approval checks remain. The target is never exported as an original identity or accepted supplement.

For `codex_native`, `export` also writes `handoff/look-N/request.json` with the exact prompt and ordered frozen local attachments. Read that file directly as the built-in tool arguments, compare its prompt/reference hashes to the adjacent `manifest.json`, then reserve and call once. Do not independently rewrite the request and omit model conditions. The exported file grants no authorization and does not prove visual fidelity; returned originals still undergo the same QA and human acceptance.

For newly prepared style tasks, record 2–4 task-specific photography targets in optional `context.photography_targets` (nonempty single-line strings, at most 240 characters each), following prompt-build §4.1. This extends schema 2 without changing model/package fields. The existing context hash freezes the targets; continuation keeps them unchanged. Export inserts the canonical target block once, or checks an existing block exactly matches the context. A malformed, duplicated or conflicting block must be corrected before submission. Legacy tasks without the field keep their previous behavior and are not silently migrated or certified against new targets. Retry wording may change how the same targets are met, not the frozen targets or the consumed budget. The helper validates transport, not the semantics of arbitrary hand-written prose or actual visual quality.

For an adopted real-face plan, compose the frozen prompt with its supported per-look head/gaze direction instead of conflicting unrestricted-head or mandatory-glance wording. Verify the selected attachments and selection record, including space for the accepted first-image anchor on later looks. A six-look plan must fit the five-attachment limit for each look; never upload the entire inventory by habit. Genuine garment back coverage and genuine face-angle coverage remain separate checks.

Confirm the existing user instruction covers this outfit, upload to ChatGPT, the selected action and request limit. Inherit sufficient authorization without asking again. Before approval, recognition, prompt preparation and export are allowed, but upload/submission are not.

Record the exact approval in `authorize --note <user-approval-summary> --limit <1-or-6>`. The helper never infers approval from a mode selection. Set `mode --mode automatic` only after browser capabilities are confirmed; changing mode preserves all reservations.

For automatic mode, read the available host browser tool documentation. Confirm a dedicated Chrome session can be identified/created without the main profile, and that the tool supports attachment upload and original-file download. Do not install an unnamed tool or ask users to copy credentials. If these capabilities are absent, explain the missing capability and export the manual package. On this maintainer's host, follow the user-authorized dedicated-browser configuration; do not embed that machine's CDP port or paths in portable instructions.

The user signs into ChatGPT themselves. Login required, quota restriction, loading failure or no attachment support means pause before submission, not permission to fall back to another service. Persistent chat history must be enabled; do not use temporary chats.

## Automatic loop: one image at a time

1. Read task status. If any reserved/unknown request exists, recover it first. Otherwise export the next look and open a new persistent ChatGPT chat in the dedicated session.
2. Upload the numbered references and wait for each upload to finish. Verify thumbnail count/order against the exported files; paste the exact exported prompt. Do not click Send until login, attachments and prompt are verified. Record visible model wording only; keep image model unverified unless explicit image-model evidence exists.
3. Immediately before clicking Send, execute `reserve --look N --ready --refs <ordered SHA256 values> --conversation <observed-url>`. For a new chat that does not yet have a `/c/` URL, also supply `--tab <observed-stable-tab-handle>` with the observed ChatGPT root URL. `--ready` attests all UI checks above, not merely that a tab exists. A successful reservation is required. Click Send exactly once. On failure or uncertainty do not repeat the click.
4. When a persistent `/c/` URL appears, use `bind --look N --conversation <observed-url>` on the same reservation. Poll only the existing request, with bounded observations and user updates. After 30 minutes without a verified result, record `unknown --look N` and pause. This stops observation, not remote generation.
5. Download the original through the supported browser download mechanism into the task's workspace. Do not scrape private image URLs, save a screenshot as the result, or invent a download path. If download is unavailable, ask the user to download and provide that exact original; retain the existing reservation.
6. Use `returned --look N --file <downloaded-original.png>`. The helper checks dimensions and duplicate bytes and copies to an immutable numbered output. Under failure recovery v1, a non-PNG, corrupt, wrong-size or duplicate result is retained byte-for-byte as failed evidence; the command exits unsuccessfully after saving the failure. Stop and reconcile; do not convert, crop or generate another image automatically. If no readable original was provided, the existing reservation remains unresolved. For a valid result, inspect actual content with image tools and apply existing commercial QA, garment facts and identity-anchor gates.
7. Only suitable images receive `accept --look N --qa qa-pass|qa-user-review --note <actual-visible-review>`. `qa-user-review` is allowed only when outstanding issues do not affect hard garment facts, anatomy/safety or anchor suitability. For unsuitable images, record `reject --look N --note <visible-hard-failure>`. Stop for look-1, unresolved requests or provider/canvas failures. A resolved non-anchor visual reject remains outside accepted delivery, but schema 2 can continue other already authorized ordinals with the original accepted look-1; never auto-retry. In new schema-2 adult portrait tasks, look-1 acceptance still pauses for human model confirmation; record `confirm-model --look 1 --note <actual-user-acceptance>` before the next look. Existing schema-1 tasks retain their original recovery behavior. `complete=true` means all recorded images accepted for progression, not commercial `image-ready`; retain final user approval requirements.

## Manual path

Give the user the exported `handoff` directory and its README. They upload numbered files, paste `prompt.txt` and provide the chat URL (or agree an observed new-chat tab identifier). Before they click Send, reserve that look in the same task. They click once, download the original and return it for `returned` plus visual QA. Do not give six unlocked prompt bundles before look-1 validation. If they already sent outside the ledger, stop and reconcile actual submissions before authorizing more; never claim automated request-count verification for unobserved manual actions.

## Recovery and limits

`reserved` means the Send action may have occurred; count it against budget. `unknown` can import a later recovered original, but cannot reserve again, reconcile as failed or obtain retry authority. Check that original request first. A verified terminal provider error can then be recorded as `failed`; an observed original can be imported with `returned`. A timeout alone is not a terminal failure. The initial authorization stays unchanged; failure never adds calls automatically. Never create a fresh ledger to reset the same group's used requests.

New schema-2 tasks declare `failure_recovery_version=1`. Existing schema-2 tasks without that field retain their previous failure behavior until explicit local adoption using `enable-failure-recovery --task <task> --note <reason-for-adopting-v1>`. Adoption records its note/time without changing prior states, files, authorization or consumed calls. It grants no generation authority. For an already-failed legacy task, supply its actual terminal receipt using `failed` after adoption. For an old wrong-canvas task still reserved, import its existing original again after adoption to retain the failure. Schema-1 tasks keep their existing recovery interface and cannot adopt this extension; preserve their evidence and do not reset them.

Recovery v1 requires a nonempty local terminal receipt and a reason for an explicit provider failure. Receipts can be an observed provider/tool error record saved locally; do not invent one. The helper retains exact receipt bytes/hash. Wrong-canvas/corrupt originals are retained automatically with their failure reason. Both still consume the original reservation. When the original-request check has completed and there is no pending original request or recoverable usable result, record that check against the exact failed attempt:

```sh
python3 scripts/web-task.py failed --task <task> --look 1 --reason <observed-terminal-error> --failure-receipt <local-receipt>
python3 scripts/web-task.py reconcile-failure --task <task> --look 1 --expected-attempt 1 --request-check-completed --note <completed-original-request-check>
```

For automatically retained invalid results, skip `failed` and start with the original-request check. Reconciliation does not submit or grant calls. Only a separate, explicit new one-image generation/upload approval allows the `retry-authorize` command below. It adds exactly one slot and preserves the failed attempt, receipt/original, error, check record and cumulative count in history. A new failed attempt needs a new check and new approval. These local records bind declared facts to retained bytes; they cannot authenticate provider terminal status or human authorization.

A stale `.writer-lock` blocks mutation. Inspect the existing process and task before manual recovery; never delete a lock automatically. A crash after output copy but before state persistence requires reconciliation of that exact file and original request, not another generation. Reference/output hash changes stop progression. Preserve private receipts, original files and unresolved statuses.

## Explicit one-image retry (candidate, local tool only)

After a returned original fails visual QA, record `reject` with the visible reason. For old schema-1 tasks left `returned` by an earlier version, inspect the original and record that rejection first. Accepted anchors cannot be rejected/replaced through this path; downstream work must remain pending.

For a rejected visual result or a reconciled recovery-v1 failure, prepare a corrected single-image prompt and show the user the failed facts, change, exact additional request count and overall budget. Preparation/development approval does not authorize image generation. Only after an explicit retry/upload approval, record a unique approval identifier and the current rejected/failed attempt number (1 for legacy tasks):

```sh
python3 scripts/web-task.py retry-authorize --task <existing-task> --look 1 --expected-attempt 1 --approval-id <unique-user-approval-id> --note <actual-user-approval> --prompt-file <corrected-prompt.txt>
python3 scripts/web-task.py export --task <existing-task>
```

Each grant adds exactly one request to the initial limit; it never resets used requests, creates images or authorizes an automatic retry loop. Repeating an approval ID or targeting an obsolete attempt is rejected. A new rejected attempt requires another explicit approval. Unused initial slots retain their original scope; if the user withdraws continuation authorization, stop regardless of numerical availability.

The previous attempt's prompt, source hashes, conversation, QA/output or retained failure and request check remain in `history`, with original files intact. A retry uses a new `look-N-attempt-M` output and handoff directory. Follow the current README; older handoff folders are evidence, never a queue to resubmit. All recorded outputs and failure files remain hash-checked; accepted/rejected output bytes cannot be imported as new results. Do not edit JSON to reset state or use old handoff files for the new request.

Resume the same reserve → one Send → bind → returned → visual QA loop. A corrected look-1 must be technically accepted and, for new adult portrait tasks, human-confirmed before any later look is unlocked. A grant records human authority; the local script cannot verify a human actually gave it, so agents must never fabricate approval receipts.

## Model confirmation, portable reference and continuation (schema 2)

New adult-model and non-portrait tasks use schema 2; explicit legacy specifications can use schema_version=1 without new model/context fields; never silently migrate schema 1 or invent its missing model approval. For native generation use route codex_native and the same reserve/returned/accept/confirm ledger with actual ordered tool attachments; no browser URL is required, and do not run the web upload loop.

```sh
python3 scripts/web-task.py confirm-model --task <task> --look 1 --note <actual-human-model-acceptance>
python3 scripts/web-task.py export-model --task <task> --destination <new-private-package> --name <model-name>
python3 scripts/web-task.py continue-authorize --task <single-test-task> --spec <five-prompts-and-identical-context.json> --approval-id <unique-id> --note <actual-five-more-approval>
```

Existing identity exports the original source(s) and previously selected accepted supplements, without automatically promoting the latest outfit image. An explicit `export-model --include-accepted-reference --accepted-scope face|full` adds the current technically accepted and human-confirmed first image as a scoped supplement; originals remain unchanged. Hash checks bind the declared acceptance to bytes; they do not prove consent or likeness. Package schema 1 remains readable; schema 2 stores supplements separately, never as garment sources. New AI identity exports the accepted first image. `model_package` imports verified relative paths and hashes as identity-only evidence; it never supplies garment facts, consent to generate/upload, or first-output acceptance on another SKU. Continuation adds exactly five slots after a confirmed mother-pose-1 trial, preserving its output, history and consumed budget; no reset or regeneration of look-1. A changed product/style/mode/output/canvas is a new task with its own authorization. The agent must verify trial pose1; the helper cannot infer pose from pixels or natural-language prompt.

When that real trial already carries `real_face_plan`, continuation additionally supplies `real_face_looks` for the five remaining looks using the same observed coverage and reference inventory; see model-selection.md for its single maintained format. This does not change continuation or confirmation behavior for `ai`/`new`. A real source plus accepted AI supplements remains real, and no accepted generated view supplies missing authentic real-face coverage.

## User declines the technically accepted model

Before model confirmation and downstream work, record actual user feedback with `reject-model --look 1 --note <feedback>`. This changes progression eligibility, not the recorded technical QA. Export preserves the original result. Nothing is regenerated by rejection.

On explicit one-image retry authority use the existing `retry-authorize` with current attempt number and unique approval ID. If the user revised proposed model conditions, add `--model-spec <private-json-containing-model>` and a matching corrected prompt. The helper preserves old model conditions in attempt history and adds exactly one request; no budget reset. Original identity attachments, subject, source and scope stay fixed. Selecting an entirely different person requires an explicitly declared new model version/task with new original references; keep the original task and consumed calls, and never use this as automatic budget recovery. Once the model is human-confirmed, this in-task replacement path is blocked.


Optional close/half-frame model diagnostics require their own explicit call authority and `context.purpose=model-check`. They are single portrait tasks and cannot be continued as delivery look-1, even when first_pose=1 and the person is accepted. They do not change the six production poses; maintain the cumulative budget across diagnostic and delivery tasks. Existing contexts without purpose retain delivery behavior. Original-face fidelity, accepted-candidate continuity and garment QA must be reported separately. A product-failed candidate cannot be exported or propagated simply because its face is liked. The tool freezes supplied prompts/roles; it does not measure faces, infer framing from pixels or enforce provider identity weights.

## Auditable review correction and pending shot revisions (schema 2)

These local actions make no generation calls, grant no budget and preserve original image bytes, accepted identity and task context.

- `review-output --look N --expected-output-sha256 <existing-hash> --qa qa-pass|qa-user-review|qa-retry --note <fresh-review-reason>`: only an already reviewed non-anchor output. Read the actual original and product requirements before correction. Saves old QA/state/output hash in `qa_history`; never use it to hide a known hard error. First-image rejection/recovery keeps its existing stronger rules.
- `revise-pending --look N --expected-prompt-sha256 <current-hash> --prompt-file <new-text> --note <actual-user-approved-plan-change>`: only a never-submitted ordinal, no unresolved request. Keep outfit, style, canvas, identity and references; material context changes require the existing new-task rules. Saves old prompt/hash and approval note in `prompt_history`, increments `plan_revision`, leaves counts/authorization unchanged. Retry-pending ordinals use retry authorization instead.
- Exported revised plans use `look-N-plan-R` (with attempt suffix where applicable), preserving old handoffs. `manifest.json` carries both the frozen prompt and actual tool-prompt hashes plus ordered reference hashes. For a revised plan, reserve with `--expected-prompt-sha256 <manifest.frozen_prompt_sha256>`; stale revisions must not be submitted. A plan note records user authority; the helper cannot authenticate that the user actually supplied it.
- `export` and `reserve` share the same progression checks. `complete` continues to require every image accepted and the actual first-image human confirmation; neither a resolved rejection nor six returned files confers `image-ready`.
