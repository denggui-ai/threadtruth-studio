# beta.8 controlled retry candidate — 2026-09-28

Status: candidate. Runtime: `skills/threadtruth-studio`; development evidence: repository root. This round implements local retry bookkeeping only. No provider submission, browser operation, live installation or GitHub publication.

## Behavior and evidence

- Added visual rejection and an explicitly approved one-request retry grant. Grant records bind a unique user-approval ID, rejected attempt number, corrected prompt hash and reason. Initial authorization and cumulative attempts are not reset.
- Archived prompt, conversation, QA and original output remain intact; retry output/handoff paths are versioned. Hash checks and duplicate prevention include historical outputs. Unknown requests and accepted anchors cannot enter this retry path.
- Three new regression scenarios failed with the expected missing-event error before implementation. All 16 ledger tests then passed; full repository suite passed 173 tests in 82.183 seconds.
- Independent read-only reviewer found no blocking issue; additional initial-limit-one/two-grant/mode-switch testing preserved three cumulative attempts and blocked a further look when exhausted.
- Local simulation copied the existing schema-1 failed task, recorded rejection and simulated a grant, and exported attempt-2. The real task file was byte-identical afterward, actual generation count remained zero and later looks remained locked. Simulated authorization is not usable human approval.
- This is deterministic bookkeeping evidence, not successful provider retry or six-image acceptance. Corrected output may still fail visual QA and must stop again.

## Remaining approval boundary

The user approved implementation and review preparation only. The proposed next provider scope is up to six automatic calls (one corrected look-1, followed by five only if accepted), plus the pending one manual call. Overall proposed ceiling is 18, compared with 11 already used. Do not execute until the user explicitly approves this scope and corresponding uploads. Each further failed retry needs a fresh approval; no automatic loop.

Existing beta.6 install and immutable beta.7 archives remain untouched. The first-image watch/button correction belongs to this specific outfit prompt, not a global wardrobe rule.
