# ChatGPT web: handoff and host-browser execution

Read when the user selects ChatGPT web. This adapter is designed for macOS Codex Desktop with an authorized dedicated Chrome and host browser tools. Actual availability is checked each session; installation alone does not supply browser tools. Other environments receive the manual package. No API, private endpoints, credentials, main-browser profile or undocumented tool commands.

## Local task contract

Use `scripts/web-task.py` relative to this skill. Store task files under the user's chosen workspace, never inside the installed skill. All helper commands are local; they do not click Send or grant approval. The agent records only approval actually given by the user and observations actually made in the browser. JSON task state is private workflow data, not public evidence.

Create a JSON spec containing `references` (absolute garment paths, in user-confirmed order), `prompts` (one single-image prompt for action 2, or six for action 1), `size` (`[width,height]` resolved from the canvas contract), and `identity` (true for real/faceless models; false for flat/hanger/mannequin). Compose prompts from the selected style and prompt-build; do not use old comparison prompts with unrelated identity references. Resolve an unspecified exact size to a proposed size matching the user's ratio before submission; preserve any explicit dimensions. Explain the chosen canvas.

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
7. Only suitable images receive `accept --look N --qa qa-pass|qa-user-review --note <actual-visible-review>`. `qa-user-review` is allowed only when outstanding issues do not affect hard garment facts, anatomy/safety or anchor suitability. Unsuitable images stay returned; explain the issue and stop. Successful acceptance unlocks the next look. `complete=true` means all recorded images accepted for progression, not commercial `image-ready`; retain final user approval requirements.

## Manual path

Give the user the exported `handoff` directory and its README. They upload numbered files, paste `prompt.txt` and provide the chat URL (or agree an observed new-chat tab identifier). Before they click Send, reserve that look in the same task. They click once, download the original and return it for `returned` plus visual QA. Do not give six unlocked prompt bundles before look-1 validation. If they already sent outside the ledger, stop and reconcile actual submissions before authorizing more; never claim automated request-count verification for unobserved manual actions.

## Recovery and limits

`reserved` means the Send action may have occurred; count it against budget. `unknown` can import a later recovered original, but cannot reserve again. `failed` records an explicit provider failure and still consumes the reservation. No failure increases the maximum of six. The v1 helper intentionally has no retry/reset command: report remaining budget and obtain a separately reviewed retry/continuation instruction before extending this adapter. Do not silently create a fresh ledger for the same unresolved group.

A stale `.writer-lock` blocks mutation. Inspect the existing process and task before manual recovery; never delete a lock automatically. A crash after output copy but before state persistence requires reconciliation of that exact file and original request, not another generation. Reference/output hash changes stop progression. Preserve private receipts, original files and unresolved statuses.
