# Inter-Stage Handoff Template

Use this template whenever a stage prepares the next stage.

Write the handoff file inside the current run folder using the naming pattern:

`NN_Stage_[NEXT]_Handoff.md`

Examples:
- `00_Stage_1_Handoff_Brief.md`
- `01_Stage_2_Handoff.md`
- `06_Stage_7_Handoff.md`
- `07_Stage_11_Handoff.md`

If QA fails, write a revision file instead of the next-stage handoff:

`06_QA_Revision_Required.md`

---

## Required Structure

```markdown
# Stage [NEXT_STAGE_NUMBER] Handoff Brief

Status: READY
Created by: Stage [CURRENT_STAGE_NUMBER] - [CURRENT_STAGE_NAME]
Created: [YYYY-MM-DD HH:MM]
Run: [RUN_FOLDER]
Client: [CLIENT]

## Next Stage

- Stage: [NEXT_STAGE_NUMBER] - [NEXT_STAGE_NAME]
- Run path: Clients/[CLIENT]/Runs/[RUN_FOLDER]/
- Expected output: [NEXT_STAGE_OUTPUT_FILE]

## Load Instructions

**Mandatory first load:** The next stage MUST read its stage contract before any other file:
- `_stages/stage[N]_[NEXT_STAGE_NAME]/CONTEXT.md` (load in full; this is the authoritative execution contract)

Load in full:
- [FILE_PATH_1]
- [FILE_PATH_2]

Load sections only:
- [FILE_PATH]: [SECTION_1], [SECTION_2]

Do not load:
- [EXCLUDED_FILE_OR_CATEGORY]

Prerequisite check:
- If [REQUIRED_FILE] is missing, stop and report that Stage [NUMBER] must run first.

## Carry Forward Context

- Topic: [TOPIC]
- Primary keyword: [KEYWORD]
- Angle/notes: [ANGLE_OR_NONE]
- Priority sources: [SOURCES_OR_NONE]
- Internal links: [LINKS_OR_NONE]
- Unresolved items: [LIST_OR_NONE]
- Issues flagged by current stage: [LIST_OR_NONE]

## Authority Mode (Source Validation - NEW)

**If source validation activated FALLBACK MODE:**

```
Authority_Mode: EXPERT_FALLBACK

Fallback_Status: [Status reason from source_validation_report.json]

Allowed_Claims:
- [Claim type 1]
- [Claim type 2]

Disallowed_Claims:
- [Claim type that requires sources]

Claim_Repositioning_Rules:
- Replace: "Research shows..." → "Our experts observe..."
- Replace: "Studies indicate..." → "In our experience..."
- [Additional replacements from config]

Authority_Phrase: [From source validation report]

Important: When Authority_Mode is EXPERT_FALLBACK, the next stage writer MUST reposition all claims per these rules. External citations are not allowed.
```

**If source validation approved all sources normally:**

```
Authority_Mode: VERIFIED_EXTERNAL

[No remediation needed; proceed normally]
```

## Quality Gates For Next Stage

- [GATE_1]
- [GATE_2]
- [GATE_3]

## Automation

- Auto-run next stage: [true/false]
- Reason if false: [REASON_OR_NONE]
```

---

## Required Notes

- Every handoff MUST list the next stage's `_stages/stage[N]_[name]/CONTEXT.md` as the first item under Load Instructions (or under a dedicated "Mandatory first load" line). The next stage cannot execute from the handoff alone — it must follow its stage contract.
- Be explicit about section-scoped loads. If a file should only be partially loaded, name the exact section titles.
- Carry forward only the details the next stage actually needs.
- Keep the handoff brief concise and operational.
- If the current stage discovered a blocker, set `Auto-run next stage: false` and explain why.
- The handoff brief is a run artifact and must stay with the run folder for debugging and re-runs.

## QA Failure Variant

If Stage 6 fails, write `06_QA_Revision_Required.md` with this structure:

```markdown
# QA Revision Required

Status: BLOCKED
Created by: Stage 6 - QA
Created: [YYYY-MM-DD HH:MM]
Run: [RUN_FOLDER]
Client: [CLIENT]

## Approval Status

- Approval Status: REVISION REQUIRED
- Suggested fix stage: [3 / 4 / 5 / 6]
- Human review required: YES

## Blocking Issues

1. [Issue description] - Stage responsible: [STAGE]
2. [Issue description] - Stage responsible: [STAGE]

## Recovery Path

- Re-run starting at: Stage [N]
- After revision: re-run Stage 6 before any later stage
- Stage 7 auto-run: false

## Notes

- Minor observations: [LIST_OR_NONE]
- Auto-fix attempted: [yes/no plus one sentence]
```
