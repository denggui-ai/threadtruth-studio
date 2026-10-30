# Explicit one-call web execution envelope

Scope: source fix for the observed web agent announcing a second corrective generation after the first preview returned. The caller stopped the page; whether the second tool call had started remained unknown. A single Send and a local reservation cannot prove the number of remote image calls. Private originals, browser observations and conversation identifiers stay outside this repository.

The new explicit `export-web-execution` command reads the current canonical export and adds immutable `web-execution-v1/submission.txt` and `execution.json`. The receiving turn is limited to at most one image generation/edit invocation, including any delegated execution, and must return or stop on success, failure or uncertainty. It performs no automatic correction. QA remains the caller's responsibility after the original result is returned.

The existing `reserve` operation can bind the exact execution manifest and submission hash; an already-prepared envelope cannot silently omit that binding. The record remains on the same attempt and survives existing retry history. No new task status, budget, silent task migration, image-model assertion or native execution wrapper is introduced.

The existing canonical renderer and manifest builder were extracted without changing their byte format. Preparation checks the actual prompt, manifest and ordered exported attachments against the current frozen task before writing separate files. Submission rechecks those bindings. Old submitted attempts retain their original artifacts; they are never retroactively rebuilt from a later pixel baseline or revised plan.

Validation performed:

- 14 new deterministic tests cover actual unchanged artifacts, native/web visual prompt equivalence, schema-1 compatibility, preview one-call transport, canonical/manifest/attachment/envelope tampering, stale pending revisions, exact CLI reservation binding, unknown-request blocking and retained retry history. Synthetic colored fixtures only; no provider call.
- 160 existing reference-execution, photography-target, visual-plan, web-ledger, real-face-plan, preview and plan-revision tests passed, covering the shared renderer extraction and recovery paths. After adding the prepared-envelope omission guard, its affected 14-test envelope suite and 21-test legacy web suite passed together; unchanged unrelated suites were not repeated.
- 14 repository/public-data contract tests passed. Source eval definitions `SR-E-WEB-ONE-CALL`, `SR-E-WEB-IMMUTABLE`, `SR-E-WEB-UNCERTAIN` and main cases 224–226 parse, have unique IDs and agree. These definitions have no model-run pass claim.
- Seven old-writer cases from `f531e1a18947ced0901a54b9d872709e089677fa` covered schema 1/2, original prompt contract 0, native/web, standalone/preview and exact/ratio-first canvas behavior. Re-export with the new helper was byte-identical; explicit web-envelope creation left every preexisting byte unchanged.
- The 32 prepared current singles and three old controls were checked read-only against their canonical hashes/manifests. Pending exports matched the extracted renderer; already-submitted originals retained their preparation hashes, without rerendering them against subsequently established pixel baselines. All 35 checks passed; zero retained task writes, re-exports, image calls or browser calls.
- `git diff --check` passed. The system skill creator's `quick_validate.py` initially could not start because the default Python lacks PyYAML (`ModuleNotFoundError: yaml`). Reusing the existing host dependency bundle through `PYTHONPATH` then returned `Skill is valid!`; no dependency was installed.
- An independent read-only review of the scoped runtime, documentation and tests found no blocking defect. It checked byte preservation, exclusive sidecar creation, current reservation binding, retained retry history and unchanged budget/uncertainty gates; it made no external call or visual-quality claim.

The first targeted test run exposed two test-fixture issues: a pending-revision test omitted its existing expected-prompt hash, and a macOS temporary-directory alias differed from its resolved path. Both test fixtures were corrected; no runtime permission or history gate was relaxed.

Finding status: fixed in source for explicit transport and hash binding. Live receiving-agent adherence remains unverified by this patch. No installation, publication, automatic retry or additional image authority follows from these local checks.
