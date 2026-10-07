# FLOW-1 authorized local installation — 2026-10-04

Conclusion: **installed and enabled on the maintainer's local Codex host**. The user explicitly approved backing up and replacing the current plugin after reviewing the completed candidate.

- Candidate source commit: `580feb8`; behavior commit: `41aaa2b`. Candidate checksum and prior release gates remain in [candidate verification](2026-10-04-flow1-release-candidate.md).
- Actual installed version: `1.0.0-beta.11+codex.20261004T050220-2bd3b1d9`; plugin: `threadtruth-studio@personal`. The installer rewrites build metadata; version alone was not used as proof of payload identity.
- Applied the verified candidate installer with backed-up replacement, then ran its printed Codex activation command. No dependency installation, generation or public publication.
- Source and new Codex cache both contain the exact expected 278-file set. All 45 runtime files and all 277 non-manifest envelope files match the candidate; manifest changes are limited to the installer-generated version.
- Prior source backup is an exact 278-file match to the pre-write hash snapshot. Marketplace backup matches its pre-write digest; existing plugin entries are preserved. Exact backup locations are retained in private `outputs/caiguang-flow1-release-20261004/live-install/RESULT.json` outside source.
- Five installed helper help commands pass and runtime bytes remain unchanged. CLI returned `installed=true`, `enabled=true` and the new version. Remote marketplace listing warned of network failure, which does not negate the returned local plugin state; remote catalog health is not claimed.

`fixed(live-candidate-replacement)`: authorized replacement and post-write verification complete. Restart discovery context by opening a new Codex chat; this existing chat may retain old loaded instructions. `DISCOVERY-1` remains deferred because a new installed-chat invocation was not tested. No previous image tests are repeated or scheduled. Original likeness and garment-quality limitations retain their existing status.

Rollback uses the retained pre-install source backup through the documented installer, preserves later marketplace entries and keeps private model packages, images and task ledgers. Previous candidate evidence is historical and is not rewritten to imply it included installation.
