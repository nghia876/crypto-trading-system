# Project Settings Attachment Audit and Replacement Recommendation

**Reviewed:** 2026-10-27. These five synced files are read-only references in this workspace. This recommendation and prepared replacement do not modify Project settings.

## Recommended final attachment set

| Current attachment | Recommendation | Reason |
|---|---|---|
| `MASTER_PROMPT.md` | **KEEP; update §24 Current starting point** | Its evidence hierarchy and operating rules remain useful. Section 24 still says Phase 0 is current and asks the next agent to finish the repository audit, which is stale. |
| `PRODUCT_BLUEPRINT.md` | **KEEP; correct the Phase 0 status and add current Phase 2 status** | It is the canonical architecture and roadmap, and its Phase 2 scope/exit criteria are clear. Its Phase 0 status says “IN PROGRESS / NOT COMPLETE,” conflicting with the Phase 0 handoff's “VERIFIED COMPLETE.” |
| `RESOURCE_MANIFEST.md` | **KEEP; update R01 and §8 resource status** | Resource acquisition policy remains useful. R01 and §8 still say the repository and project docs are required next, and public collectors are to be built during Phase 1, although the repository is connected and those collectors now exist. |
| `PHASE_0_AUDIT_HANDOFF.md` | **REPLACE** with `docs/project-settings/PROJECT_STATUS_AND_PHASE_2_HANDOFF.md` | The current attachment says Phase 1 is next. The replacement records Phase 2 evidence, exact local/remote commits, limitations, the storage gate, and the Phase 3 master-chat prompt in the same settings slot. |
| `PHASE_0_AUDIT_FINDINGS_AND_PHASE_1_ARCHITECTURE.md` | **REMOVE from active Project attachments after archiving a copy** | It preserves valuable historical detail but overlaps the Phase 0 handoff and is not the current entry point. Keep an archival copy outside active settings; do not delete the synced source file from this workspace. |

The resulting active set has four attachments: Master Prompt, Product Blueprint, Resource Manifest, and the replacement status/handoff. This stays under the five-file limit and puts the Phase 2 handoff into an existing attachment slot rather than adding a sixth file.

## Conflict and staleness findings

- **Authority:** The Master Prompt correctly ranks code and executable tests above documents and conversation history. Keep this rule.
- **Master Prompt:** §24 still says the project is at Phase 0 and directs agents to complete the initial TradingAgents audit.
- **Blueprint:** §7 marks Phase 0 “IN PROGRESS / NOT COMPLETE,” while `PHASE_0_AUDIT_HANDOFF.md` marks it verified complete. Phase 2 has scope/exits but no current status row.
- **Resource Manifest:** R01 and §8 still say the repository/codebase is required next; §8 also says public market/event collectors belong to future Phase 1 work. These status statements are stale. Its no-paid-API, no-credentials, and source-acquisition policies remain useful.
- **Phase 0 files:** Both direct the reader to Phase 1. The 1,334-line findings document and 400-line handoff repeat architecture, audit scope, and next-phase instructions. Archive the detailed findings; use one current handoff.
- **Evidence boundary:** The project docs define Phase 2 exits but do not name the current branch/SHAs or disclose live-source limitations. The prepared replacement does so. The local code meets the stated exits, while final GitHub durability remains pending an approved push.

## Prepared targeted text updates

If the attachments are refreshed later, use these short replacements in addition to uploading the prepared status/handoff replacement:

- **Master Prompt §24:** “The repository audit (Phase 0) and information foundation (Phase 1) are complete. Phase 2 implementation is on `phase-1.2-btc-ohlcv-collector`; its local reviewed HEAD and GitHub storage state are recorded in `PROJECT_STATUS_AND_PHASE_2_HANDOFF.md`. Do not start Phase 3 until that handoff's GitHub storage gate is verified. Use repository code and tests as current truth.” Remove the old Phase 0 task list.
- **Product Blueprint §7 Phase 0 status:** replace `IN PROGRESS / NOT COMPLETE` with `VERIFIED COMPLETE — see archived Phase 0 audit handoff/findings`.
- **Product Blueprint Phase 2 status:** add `Implementation meets the stated exit criteria locally; final Phase 2 commits and handoff are pending an approved feature-branch push. See PROJECT_STATUS_AND_PHASE_2_HANDOFF.md.` Do not mark GitHub durability complete yet.
- **Resource Manifest R01:** change “Provide the complete codebase” to “VERIFIED AVAILABLE — connected GitHub repository `nghia876/crypto-trading-system`; current Phase 2 branch and exact remote/local heads are listed in the project status handoff.”
- **Resource Manifest §8:** change TradingAgents codebase and project docs from `REQUIRED NEXT` to `AVAILABLE`; change public market collectors from `BUILD DURING PHASE 1` to `BUILT / VERIFY AGAINST CURRENT REPOSITORY`; leave historical data, paid APIs, and live credentials as not required unless later evidence changes that need.

## Prepared replacement

Use the full text in `docs/project-settings/PROJECT_STATUS_AND_PHASE_2_HANDOFF.md` to replace `PHASE_0_AUDIT_HANDOFF.md`. It embeds the verified Phase 2 handoff, its local/remote storage status, evidence and limits, and a prompt for a separate Phase 3 master/checkpoint chat. Keep `docs/project-handoff/PHASE_2_HANDOFF.md` as the detailed engineering record.

The app does not expose a supported Project-attachment editor in this task. The user will need to apply the keep/replace/remove recommendations in Project settings; no source attachment was altered here.
