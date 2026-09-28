# beta.7 web delivery candidate — 2026-09-28

Status: candidate; implementation and deterministic checks verified, actual browser generation and publication pending. Runtime root is `skills/threadtruth-studio`; development evidence root is the repository.

## Implemented

- Local shared manual/automatic ChatGPT task ledger, one/six-image budget, immutable ordered reference snapshots and prompt hashes, durable submission reservations, original-result recovery and staged handoff export.
- First-image QA and identity-only anchor gates, exact dimensions, duplicate-output checks, complete PNG chunk/checksum/pixel-stream checks, output integrity checks and completion distinct from image-ready.
- Host-browser execution instructions for dedicated Chrome on macOS, including capability/login/upload checks, original downloads, bounded observations, ambiguous-state stop and manual handoff. This is an agent-operated browser workflow, not a standalone browser driver.
- Product-first local landing page plus historical comparison appendix. English multiword/hyphen search and hidden-result leakage fixed. New comparison media is outside plugin payload; source execution plans are excluded from the delivery envelope.

## Actual checks and review

- First targeted run failed because the task helper did not exist. Initial tests passed after implementation.
- Independent review identified directory fsync, non-anchor output integrity and truncated-PNG handling gaps. Three regressions reproduced those gaps before fixes; all twelve ledger tests now pass. Independent re-review marked all three fixed, with no new blocking findings.
- Full source suite: 169 tests passed in 241.868 seconds. The later packaging-only exclusion is covered by a targeted release regression rerun.
- Browser regression reproduced `old money` returning zero results before the fix. Afterward English space/hyphen and Chinese search, result filtering, hidden conclusions, 43 image loads and 1440/390 px layouts passed.
- Official skill validation, strict source standard, 24 pack lint, trigger assertions and public text scan passed.
- Candidate archive was extracted and the local six-step state machine exercised with synthetic fixtures. This is NOT six real generated images. Source references, reservations, progression and complete-but-image-draft behavior passed.
- The first extracted smoke check created a bytecode cache because its harness omitted the no-bytecode environment flag. The cache was removed from that disposable extraction and strict runtime validation passed; the ZIP never contained it.
- The first candidate archive included the newly added source plan because the inherited envelope copied all docs. Added a release regression and excluded that source-only directory before the final build.

## Media and execution boundary

All 24 historical styles are inventoried locally. The female identity reference matches the hash of a previously published generated primary-case look-1. Three garment inputs have no verified reuse license; proposed replacements use the project's previously approved beige outfit and generated female identity reference, preserving the originals and labeling changed-input pairs. The new source is a contemporary outfit; cultural motifs are not invented to force a style match.

Pexels licensing was rechecked against its official license page. Source credits and contextual/no-endorsement restrictions remain required; this record does not certify all future uses or relicense these assets as CC0. Final publication-context review remains pending. Private rights inventories, exact source URLs, prompts, chat addresses and local recovery records remain outside the public payload.

Proposed new-call budget: six calls for three replacement pairs, four missing-side calls, one manual workflow call and six automatic workflow calls = maximum 17. No new generation or upload is authorized by the implementation acceptance itself. The exact proposal and frozen replacement files were presented for approval. No automatic retries.

## Pending acceptance

- User approval of replacement materials, 17-call scope and ChatGPT upload destination.
- New-task manual single-image and automatic six-image provider verification.
- Recovery/supplementation, all 24 complete eligible pairs and new blinded reviews.
- Final human review of the public media, site, candidate artifact and upload file list.
- Separate GitHub push/release approval. Current live installation remains beta.6; this candidate is not installed or publicly released.

## Final local artifact and recovery receipt

- Final candidate archive: 287 files; SHA-256 `78d54b22646211a430e89cac66ab8967c8ea66b84a6d01352148fc8ce74a96cb`. Clean extraction passed official plugin and strict runtime validation; new media and source execution plans are excluded. The later receipt-only source change does not modify the immutable archive.
- All six targeted release tests passed after the packaging exclusion change (67.931 seconds).
- The original Guochao web conversation became accessible during bounded read-only recovery. Its image-viewer Download button returned an original 1024×1536 PNG, full integrity checked. SHA-256 `6e2c8882e62a4f6421402211adf78fe6cbfa5833df09622d568e756fd1e75216`. Zero new generation calls. This is a recovered historical result, not a newly scored pair or publication approval. The original 43-image/19-reviewed-pair snapshot remains unchanged; one recovered original is recorded separately.
- Recovery does not reduce the proposed 17-call budget: Guochao still needs both sides regenerated with the replacement source for the public candidate. Four other missing-side calls remain in that proposal.
- Local review media is a separate archive, marked review-only; no media is newly published or relicensed.
