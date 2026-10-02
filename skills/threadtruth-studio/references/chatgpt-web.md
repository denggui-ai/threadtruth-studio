# ChatGPT web: handoff and host-browser execution

Read when the user selects ChatGPT web. This adapter is designed for macOS Codex Desktop with an authorized dedicated Chrome and host browser tools. Actual availability is checked each session; installation alone does not supply browser tools. Other environments receive the manual package. No API, private endpoints, credentials, main-browser profile or undocumented tool commands.

## Local task contract

Use `scripts/web-task.py` relative to this skill. Store task files under the user's chosen workspace, never inside the installed skill. All helper commands are local; they do not click Send or grant approval. The agent records only approval actually given by the user and observations actually made in the browser. JSON task state is private workflow data, not public evidence.

Create a JSON spec containing `references` (ordered `{path,role}` images: garment-source, identity-reference, aesthetic-reference; accepted model-supplement additionally requires sha256, scope face/full and actual confirmation_note), `prompts` (one single-image prompt for action 2, or six for action 1), `size` (`[width,height]` resolved from the canvas contract), `context` (outfit, style, mode B/C/D, output_form, size, first_pose), `route` (chatgpt_web, or codex_native for the same local native ledger), optional `model` (see model-selection.md) or `model_package` (private package path), and `identity` (true for real/faceless models; false for flat/hanger/mannequin). Compose prompts from the selected style and prompt-build; do not use old comparison prompts with unrelated identity references. Resolve an unspecified exact size to a proposed size matching the user's ratio before submission; preserve any explicit dimensions. Explain the chosen canvas.

```sh
python3 scripts/web-task.py init --task <new-task-directory> --spec <spec.json>
python3 scripts/web-task.py export --task <task-directory>
python3 scripts/web-task.py status --task <task-directory>
```

`init` refuses an existing task. Resume through `status`; never create a replacement task to reset an unresolved budget. Snapshot garment files and hashes; inspect actual images before declaring them garment sources. Only the next pending look is exported. Subsequent prompts remain locked until previous QA is recorded. For real/faceless models, accepted look-1 is appended after all garment references and labeled identity-only. Its clothes, lighting and pose never become product authority.

## Authorization and entry setup

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
6. Use `returned --look N --file <downloaded-original.png>`. The helper checks dimensions and duplicate bytes and copies to an immutable numbered output. Non-PNG, wrong size or duplicate means pause; do not convert, crop or generate another image automatically. Then inspect actual content with image tools and apply existing commercial QA, garment facts and identity-anchor gates.
7. Only suitable images receive `accept --look N --qa qa-pass|qa-user-review --note <actual-visible-review>`. `qa-user-review` is allowed only when outstanding issues do not affect hard garment facts, anatomy/safety or anchor suitability. For unsuitable images, record `reject --look N --note <visible-hard-failure>`; explain the issue and stop. In new schema-2 adult portrait tasks, look-1 acceptance still pauses for human model confirmation; record `confirm-model --look 1 --note <actual-user-acceptance>` before the next look. Existing schema-1 tasks retain their original recovery behavior. `complete=true` means all recorded images accepted for progression, not commercial `image-ready`; retain final user approval requirements.

## Manual path

Give the user the exported `handoff` directory and its README. They upload numbered files, paste `prompt.txt` and provide the chat URL (or agree an observed new-chat tab identifier). Before they click Send, reserve that look in the same task. They click once, download the original and return it for `returned` plus visual QA. Do not give six unlocked prompt bundles before look-1 validation. If they already sent outside the ledger, stop and reconcile actual submissions before authorizing more; never claim automated request-count verification for unobserved manual actions.

## Recovery and limits

`reserved` means the Send action may have occurred; count it against budget. `unknown` can import a later recovered original, but cannot reserve again. `failed` records an explicit provider failure and still consumes the reservation. The initial authorization remains limited to six. Failure never increases it automatically. Do not silently create a fresh ledger for the same unresolved group. Explicitly failed provider requests and unknown requests cannot use the visual-QA retry path below; first reconcile the original request.

A stale `.writer-lock` blocks mutation. Inspect the existing process and task before manual recovery; never delete a lock automatically. A crash after output copy but before state persistence requires reconciliation of that exact file and original request, not another generation. Reference/output hash changes stop progression. Preserve private receipts, original files and unresolved statuses.

## Explicit visual-QA retry (candidate, local tool only)

After a returned original fails visual QA, record `reject` with the visible reason. For old schema-1 tasks left `returned` by an earlier version, inspect the original and record that rejection first. Accepted anchors cannot be rejected/replaced through this path; downstream work must remain pending.

Prepare a corrected single-image prompt and show the user the failed facts, change, exact additional request count and overall budget. Preparation/development approval does not authorize image generation. Only after an explicit retry/upload approval, record a unique approval identifier and the current rejected attempt number (1 for legacy tasks):

```sh
python3 scripts/web-task.py retry-authorize --task <existing-task> --look 1 --expected-attempt 1 --approval-id <unique-user-approval-id> --note <actual-user-approval> --prompt-file <corrected-prompt.txt>
python3 scripts/web-task.py export --task <existing-task>
```

Each grant adds exactly one request to the initial limit; it never resets used requests, creates images or authorizes an automatic retry loop. Repeating an approval ID or targeting an obsolete attempt is rejected. A new rejected attempt requires another explicit approval. Unused initial slots retain their original scope; if the user withdraws continuation authorization, stop regardless of numerical availability.

The previous attempt's prompt, source hashes, conversation, QA and output remain in `history`, with the original file intact. A retry uses a new `look-N-attempt-M` output and handoff directory. Follow the current README; older handoff folders are evidence, never a queue to resubmit. All recorded outputs, including rejected attempts, remain hash-checked and cannot be imported as duplicate results. Do not edit JSON to reset state or use old handoff files for the new request.

Resume the same reserve → one Send → bind → returned → visual QA loop. A corrected look-1 must be technically accepted and, for new adult portrait tasks, human-confirmed before any later look is unlocked. A grant records human authority; the local script cannot verify a human actually gave it, so agents must never fabricate approval receipts.

## Model confirmation, portable reference and continuation (schema 2)

New adult-model and non-portrait tasks use schema 2; explicit legacy specifications can use schema_version=1 without new model/context fields; never silently migrate schema 1 or invent its missing model approval. For native generation use route codex_native and the same reserve/returned/accept/confirm ledger with actual ordered tool attachments; no browser URL is required, and do not run the web upload loop.

```sh
python3 scripts/web-task.py confirm-model --task <task> --look 1 --note <actual-human-model-acceptance>
python3 scripts/web-task.py export-model --task <task> --destination <new-private-package> --name <model-name>
python3 scripts/web-task.py continue-authorize --task <single-test-task> --spec <five-prompts-and-identical-context.json> --approval-id <unique-id> --note <actual-five-more-approval>
```

Existing identity exports the original source(s) and previously selected accepted supplements, without automatically promoting the latest outfit image. An explicit `export-model --include-accepted-reference --accepted-scope face|full` adds the current technically accepted and human-confirmed first image as a scoped supplement; originals remain unchanged. Hash checks bind the declared acceptance to bytes; they do not prove consent or likeness. Package schema 1 remains readable; schema 2 stores supplements separately, never as garment sources. New AI identity exports the accepted first image. `model_package` imports verified relative paths and hashes as identity-only evidence; it never supplies garment facts, consent to generate/upload, or first-output acceptance on another SKU. Continuation adds exactly five slots after a confirmed mother-pose-1 trial, preserving its output, history and consumed budget; no reset or regeneration of look-1. A changed product/style/mode/output/canvas is a new task with its own authorization. The agent must verify trial pose1; the helper cannot infer pose from pixels or natural-language prompt.

## User declines the technically accepted model

Before model confirmation and downstream work, record actual user feedback with `reject-model --look 1 --note <feedback>`. This changes progression eligibility, not the recorded technical QA. Export preserves the original result. Nothing is regenerated by rejection.

On explicit one-image retry authority use the existing `retry-authorize` with current attempt number and unique approval ID. If the user revised proposed model conditions, add `--model-spec <private-json-containing-model>` and a matching corrected prompt. The helper preserves old model conditions in attempt history and adds exactly one request; no budget reset. Original identity attachments, subject, source and scope stay fixed. Selecting an entirely different person requires an explicitly declared new model version/task with new original references; keep the original task and consumed calls, and never use this as automatic budget recovery. Once the model is human-confirmed, this in-task replacement path is blocked.


Optional close/half-frame model diagnostics require their own explicit call authority and `context.purpose=model-check`. They are single portrait tasks and cannot be continued as delivery look-1, even when first_pose=1 and the person is accepted. They do not change the six production poses; maintain the cumulative budget across diagnostic and delivery tasks. Existing contexts without purpose retain delivery behavior. Original-face fidelity, accepted-candidate continuity and garment QA must be reported separately. A product-failed candidate cannot be exported or propagated simply because its face is liked. The tool freezes supplied prompts/roles; it does not measure faces, infer framing from pixels or enforce provider identity weights.
