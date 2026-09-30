# beta.9 installed-plugin regression

Scope: the user authorized a backed-up upgrade in their existing Codex environment and fresh text-only tests of the original missing-photo prompt, explicit invocation, complete catalog and non-apparel isolation. No image generation, external-user contact, push, merge, tag or public release is included.

Target runtime: `skills/threadtruth-studio`. Evidence root: repository root, outside the runtime envelope. Overall release status remains `candidate`; no change to the skill's `DRAFT` maturity.

## Installation and rollback

- Host: maintainer macOS 26.6.2; `codex-cli 0.155.1`.
- Verified candidate ZIP, extracted to a fresh directory, ran installer dry-run, applied `--replace`, then used the installer's exact `threadtruth-studio@personal` selector to enable it.
- The original beta.8 source backup matches the complete pre-upgrade file-hash record. Marketplace backup matches its previous JSON; current marketplace entries are unchanged. Other installed plugin versions and enabled states match the saved pre-upgrade list.
- Final enabled version: `1.0.0-beta.9+codex.20260930T132722-e74ab7a4`; the suffix is the installer's cache refresh marker.
- Installed plugin display metadata is `裁光 · Caiguang`. The computer-use tool refuses access to the Codex app itself, so actual desktop UI rendering remains `not-observable`; it is not inferred from metadata. A manual check was requested separately.
- All 269 extracted, source and active-cache files match, allowing only the expected manifest version suffix. CLI refresh may retire old cache directories; rollback relies on the verified source backup, not an old cache path.
- Recovery instructions with the exact backup locations are retained privately with the installation receipts. Rollback was not executed; the verified final beta.9 remains active.

## Forward-test finding and correction

The first installed candidate used the prior project-scoped fix unchanged. All three original-prompt sessions read the complete skill, but **two of three had already forecast later image generation in their pre-read commentary**. Their final replies correctly requested photos. Checking only the final reply would have missed the failure.

The correction front-loads the existing first-visible-reply boundary in discovery metadata: “Apparel model images: first reply only checks inputs, never promises later generation.” The missing-photo scope and exclusions remain. The runtime body, generation authorization, style packs, helpers and technical IDs are unchanged relative to the previously tested candidate. Source evals now explicitly include commentary before the skill read.

An intermediate revision used an unquoted colon in YAML description metadata. Official plugin validation rejected it; the owned probe runner and its children were stopped, and these runs were marked invalidated rather than counted as successes. The same description string was properly quoted, source and staged official validation passed, and the corrected archive was installed before all final probes were restarted. Failed/incomplete intermediate outputs and receipts remain private; they are not behavioral pass evidence.

## Fresh installed-plugin probes

Both valid batches use enabled installed-plugin discovery in isolated empty working directories, **without project skill copies or target-plugin disable overrides**. Each is a fresh ephemeral read-only Codex session. Image generation, hooks and multi-agent execution are disabled per process. No configured model override; model identity is not exposed by CLI events.

Complete loading is counted only when the read tool's returned text contains the full frozen `SKILL.md`. Skill names, read commands alone and partial excerpts do not count. Earlier runtime text is retained in verified extracted archives even when the CLI refresh removes its cache directory.

The initial valid batch has six sessions: original prompt ×3, explicit, catalog and coffee machine. The final valid batch has eight: the same six plus Chinese shirt and English dress paraphrases. Invalidated format-error runs are excluded.

| Final probe | Complete skill read | Reply/content result |
|---|---|---|
| Original minimal prompt, three fresh sessions | 3/3 observed | First pre-read commentary and final reply stay at material checking |
| Explicit invocation | Observed | Requests actual photos; no generation forecast |
| Full 24-style catalog | Observed, plus registry read | All 24 slugs each once; no invented garment-specific recommendation |
| Coffee-machine negative control | No apparel read observed | Remains in product-photo scope |
| Chinese shirt / English dress paraphrases | 2/2 observed | Material preparation only |

Independent blind grading: all 8 final outputs pass; 2 of the 6 initial outputs fail because their pre-read commentary forecasts generation. [Sanitized output extracts and complete-read facts](evidence/2026-09-30-installed-beta9/runs.json) and [independent grades](evidence/2026-09-30-installed-beta9/grading.json) retain both failures and successes. Configuration labels were revealed only after grading. Read facts and content grading are separate, and no paid-action safety or image quality is inferred from unavailable image tools.

## Artifact and static checks

- Final archive: `threadtruth-studio-1.0.0-beta.9.zip`, 269 files, 33,286,349 bytes.
- SHA-256: `0d852f15f8043edaed2176d159084d5d97d48c34c32e2d6c76eb7148ea983208`.
- Final runtime SHA-256: `6c97b2098a4bec4a01f45d0aeecd7372249557df6c4d052f29d49ded8d53c98c`.
- Actual SHA sidecar check, CRC, safe extraction, exact archive/source/cache file sets and byte parity: pass.
- Official plugin validation of corrected source and stage, runtime strict validation and all 14 existing repository-contract tests: pass. The only test fixture change tracks the intended description; no unrelated runtime code or browser UI changed.
- This separately stored build supersedes the earlier local candidate for further installation trials. Previous archives and public beta.8 assets remain unchanged.

## Finding closure

- `fixed`: installed pre-read commentary gap; final original-prompt repetitions and independent grading pass.
- `fixed`: YAML description syntax; invalidated intermediate probes were stopped and excluded, corrected source/stage validation and installed regression pass.
- `deferred(issue #1)`: desktop UI observation, non-maintainer trial and public distribution remain outstanding as detailed below.

## Remaining gates

- Desktop UI display: manual check pending; metadata check passed.
- Non-maintainer fresh-host installation, actual-photo recognition and optional separately authorized one-image trial: not tested.
- Public Issue #1 remains open until fresh-host verification and fix distribution. This record establishes a narrow maintainer installed-CLI result, not general automatic-invocation reliability or stable-release readiness.
- Human review remains available separately; no feedback or broad self-evolution claim is inferred from a blank review form.
