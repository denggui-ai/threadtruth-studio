# Source-supported six-pose verification — 2026-10-02

Conclusion: **static checks passed; scoped text regression passed**. Source implementation only; no release, installed-plugin change, new native image call or image-ready claim.

- Target: `skills/threadtruth-studio`; evidence root: repository root.
- Scope: **Core Gap**. Clear front-only garment inputs previously could not safely complete the default six-photo workflow.
- Done: keep the default six when real rear coverage exists; otherwise disclose only slot 6 as stationary frontal standing, preserve slots 1–5 and source truth, and fail duplicate actions. Explicit original-pose/rear-detail demands still require real rear material or acceptance of substitution.

| Check | Result |
|---|---|
| System skill-creator quick validation | Pass, using existing local PyYAML dependency |
| Runtime and source standard; eval/changelog | Pass, `STANDARD_PASS` |
| Existing repository suite | 221 tests passed |
| Pack lint | 24 unchanged packs passed |
| Trigger/route suite | Existing deterministic assertions passed |
| Default preview compatibility | All 24 beige-outfit prompt hashes and pose mappings match pre-change HEAD; canonical six pose/gaze/preview-negative data unchanged |
| New scoped text regression | 92–97 passed; eval 89 retains known-structure-drift blocking |
| Final default/frozen preview recheck | 9 tests passed after the detail-shot wording clarification |
| Public source scan / diff whitespace | Pass |
| Native generation / image QA | Not run for this skill change |
| HTML rendering | N/A; no HTML changed |

[Text output excerpts and grading](2026-10-02-source-supported-six-poses-text.json) bind the final source files by SHA-256. One independent fresh agent received six supplied-fact scenarios without expected answers and returned actual plans/QA decisions/six prompts. This is one text probe, not six isolated image sessions; tool-loading traces and model/token telemetry are unavailable. It does not prove native generation, visual uniqueness or implicit installed-plugin discovery. Final detail-shot precedence wording was clarified following the probe and passed static checks.

Initial validation on the system Python lacked PyYAML/fontTools; reuse of existing local authoring/test dependencies resolved this without installation or network. Runtime validation also found an ignored `scripts/__pycache__`; it was moved outside the runtime source, preserved locally, and validation rerun passed. No tracked runtime script changed.

Limits: actual pose differences and garment source coverage still require per-image visual QA. Unsupported side structure may require a supplementary photo. This exception covers human/faceless styling; nonportrait rear views still need real rear material. Six-file delivery never overrides source truth, image failure, paid-call limits or retry approval.

No pose library, model library, new runtime script/configuration, style-pack edits, frozen-preview regeneration or historical evidence rewriting was added.
