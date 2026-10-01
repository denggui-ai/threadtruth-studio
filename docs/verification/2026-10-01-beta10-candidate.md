# beta.10 candidate verification — 2026-10-01

Status: **candidate / publication held**. Public beta.9 and installed-plugin state are unchanged.

## Scope and result

The candidate packages already approved optional casting, aesthetic-reference translation, first-image casting QA and garment-first priorities. The six fixed poses, style packs and generation process are unchanged. No model library or new configuration framework was added.

- 219 source Python tests passed after the candidate-status edits. The final wording was additionally checked by 14 repository-contract tests and the release-build tests. Source and clean-unpacked runtime static validation passed.
- Two fresh-context agents loaded the clean-unpacked candidate, with real garment references and either explicit casting or defaults. Neither generated images.
- Both subsequent preparations honored casting, source roles, fixed pose 1, no nationality inference and the explicit no-generation instruction.
- **Both actual first replies failed the gate-only wording requirement**: they mentioned preparing the first test prompt. No paid call or image promise occurred. Keep this `open`; do not report 2/2 overall pass.
- The parent performed exactly one authorized native image call after reviewing sources. The explicit prompt was retained, with only its button-arrangement phrase expanded to the observed seven buttons (collar 1 + placket 6). No retry occurred.
- Native PNG metadata: **1024×1536, 2:3**, SHA-256 `6e158f9e8ff42f4fd69deb52a1386a8bf81dbc14ad77ab429882570b64500fa4`.
- Casting appearance and first side-turn pose were broadly consistent. Exact apparent age and temperament remain subjective review items.
- **Garment QA: qa-retry / open**. The rendered sleeve adds unsupported overlapping button-cuff and sleeve-placket structure. Hands obscure the middle/lower front placket, so all seven front/collar buttons cannot be verified. Hair also obscures some collar/shoulder details. Unknown hidden facts do not authorize invented construction.
- The image remains `image-draft`, is not an accepted identity anchor, is not added to the public gallery, and does not establish a six-image workflow.

## Retained evidence and limits

Original forward responses, exact final prompt, ordered source roles/hashes, null identity reference, output hash and QA remain in the local release evidence directory. No original source photos, private prompts or full logs are included in the repository or distribution.

An independent agent reviewed both text outputs and the generated image against the four sources. Its review confirmed the first-reply and sleeve/occlusion findings. First-reply correctness and model rendering are separate findings; adding a model library would not fix either.

The existing full-plugin builder and repository tests verify the Codex plugin layout. The governor's legacy single-skill ZIP checker expects root `SKILL.md` and is not applicable to the full-plugin layout; runtime-directory auditing, ZIP metadata safety and offline-guide checks are applied separately. Do not relabel that format mismatch a full-plugin checker pass.

Fresh-host installation, GUI automatic discovery, current installed-plugin behavior and full six-image casting consistency are **not tested** here. No stable-release or closed-loop self-evolution claim is made.

## Release decision

Final local bundle SHA-256: `8792c071fcda0fd62346520d8bdea82fe46ba9e45a0366b33022eb6148fd4cb8`. Its 40 runtime files match the source byte-for-byte after excluding non-distributable bytecode caches. ZIP metadata, offline-guide sections/links/anchors, runtime safety and isolated source registration passed. Desktop guide content was previewed; a new-host installation was not performed.

**Do not merge a download switch or publish beta.10 based on this failed garment smoke.** Keep the candidate locally reviewable and public links on beta.9. The next image test requires a new bounded authorization; retain this failed attempt. Prepare a narrow correction for source-only simple cuff construction and hands clear of the placket; do not modify poses or add automatic retries.
