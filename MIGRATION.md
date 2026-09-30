# Migration from `clothing-portrait-studio`

The technical identity is `threadtruth-studio`; the public brand is 裁光 / Caiguang. The legacy name exists here only to explain migration and is not an active trigger or second installed Skill.

## Safe migration sequence

1. Keep the legacy installation unchanged as a rollback source.
2. Install the new Plugin in a controlled test environment.
3. Temporarily disable, but do not delete, the legacy Skill.
4. Run explicit invocation, positive implicit trigger, negative isolation, paid-gate, clean uninstall, and rollback tests.
5. If the new version fails, disable it and restore the legacy installation.
6. If all checks pass, archive the legacy directory without deleting it.

Changing global Skill state is intentionally not performed by the repository tooling and requires separate user authorization.

## Behavior continuity

The migration preserves the real-garment input gate, 24-style routing, explicit action authorization, serial six-image closed set, identity-only look-1 anchor, canvas validation, commercial QA, state vocabulary, and no-fallback rule. Model-specific runtime wording was removed; the Plugin uses whatever native image capability the host provides.

## beta.8 → beta.9 display-name update

The beta.9 prerelease changes the Codex display name to **裁光 · Caiguang**. The plugin/skill ID, `$threadtruth-studio` invocation, personal-marketplace selector and `plugins/threadtruth-studio` directory remain unchanged. No user-image, output or task-ledger migration is required. Do not rename an existing folder or ZIP to upgrade.

Use the verified beta.9 release ZIP and [beta.9 trial guide](docs/BETA9-TRYOUT.md). Preview with `--replace`, apply only after reviewing the paths, retain the printed backups, re-enable with the printed selector and start a new task. The public beta.8 archive and checksum remain immutable. Fresh-host GUI display and invocation require recipient verification; a source metadata change alone does not prove discovery.
