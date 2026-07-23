# Pre-Stage 1: New Run

Entry point for starting a blog production run for an already-onboarded client. Handles two paths: topic provided vs. topic ideation needed. Verifies reference files, scans for overlap, creates the run folder, and writes the persistent Stage 1 Handoff Brief.

Run this before Stage 1 for all existing clients. For new clients, run Stage 0 (Onboarding) first.

## Load Before Starting

```
Load in full:
- Clients/[CLIENT]/Reference/Style_Reference_Card.md
- Clients/[CLIENT]/Reference/Audience_Profile.md
- Clients/[CLIENT]/Reference/Brand_Notes.md

Load partially:
- Clients/[CLIENT]/Run_Log.md  (last 20 lines only — recent summary index history)
- Clients/[CLIENT]/Published/  (filenames only — for overlap check)

Do not load:
- Any Runs/ stage files
- _config/search-quality-rubric.md
- _config/anti-ai-checklist.md
```

## Position in Pipeline

```
Stage 0: Onboarding       → Reference files
[THIS STAGE]              → Run folder + 00_Stage_1_Handoff_Brief.md
Stage 1: Research         → 01_Research_Dossier.md
```

---

## Two Paths

**Path A: User has a topic and keyword ready**
Steps: 1 → 2A → 3 → 4 → 5

**Path B: User needs topic ideation**
Steps: 1 → 2B → 2C → 3 → 4 → 5

Determine path at the end of Step 1:
> Do you have a topic and keyword in mind for this post, or would you like suggestions based on what would work best for this client?

---

## Task

### STEP 1: CONFIRM CLIENT AND REFERENCE FILES

Ask the user which client this run is for if not already named.

Check that all three reference files exist:
- `Clients/[CLIENT]/Reference/Style_Reference_Card.md`
- `Clients/[CLIENT]/Reference/Audience_Profile.md`
- `Clients/[CLIENT]/Reference/Brand_Notes.md`

If any file is missing: stop. Name the missing file. Tell the user Stage 0 must run first.

If all three exist: read them in full. Check Brand_Notes.md for open `[CONFIRM WITH CLIENT]` placeholders. If any critical items remain unresolved (service area, approved claims language, CMS specs, author byline), flag them:

> Brand Notes contains unresolved items that may affect this run: [list each]. These can proceed if they do not apply to this specific topic, but confirm before Stage 3 (Writing).

Do not block the run on unresolved placeholders. Flag and continue.

Then ask the user which path to take.

---

### STEP 2A: TOPIC PROVIDED — SCAN FOR OVERLAP

*Path A only.*

Read tail of `Clients/[CLIENT]/Run_Log.md` (summary index only). Scan `Clients/[CLIENT]/Published/` filenames.

Build Published Content Inventory:
```
PUBLISHED CONTENT INVENTORY — [CLIENT]
[N] posts published

1. [Filename or topic slug] — [date if available]
2. ...

No overlap check required if this is the first run.
```

Check proposed topic and keyword against the inventory.

**Overlap found:** Name the specific post. Ask user to choose:
- Proceed (distinct angle)
- Adjust topic/keyword to differentiate
- Cancel and choose different topic

Do not proceed until user confirms one option.

**No overlap found:** Confirm clearly. Move to Step 3.

---

### STEP 2B: NO TOPIC — CONTENT GAP ANALYSIS

*Path B only.*

Build the Published Content Inventory first (same format as 2A). Present it to the user.

Then perform a Content Gap Analysis using the three reference files and the inventory. Every candidate must connect to a specific gap — no generic topic ideas.

Analyse in order:

**From Audience_Profile.md:**
- What pain points, fears, and unanswered questions does the audience carry?
- What have they already tried before finding this client?
- What decisions do they need to make that no published post addresses?

**From Style_Reference_Card.md:**
- What topical authority has this client established?
- What adjacent topics are referenced but not fully addressed?
- What content categories are out of scope? Exclude them.

**From Brand_Notes.md:**
- What content gaps were noted under "Past Content Performance Notes"?
- What services or differentiators haven't been the subject of a post yet?
- Any seasonal demand patterns relevant to the current month?

**From Published Content Inventory:**
- What topics are already covered?
- Which post performed strongest? What related angles extend from it?

---

### STEP 2C: PRESENT TOPIC RECOMMENDATIONS

Present 4–6 recommendations. No fewer than 4. No more than 6.

Format each recommendation:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPIC RECOMMENDATION [N]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Topic:           [One-sentence description]
Primary keyword: [Exact keyword phrase]
Why now:         [One sentence: current need, seasonal signal, or content gap]
Audience intent: [Informational / Commercial / Transactional + one sentence]
E-E-A-T angle:   [One sentence: why this client has authority here]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

After presenting, ask:
> Which of these would you like to pursue, or would you like me to adjust any of them? You can also provide your own topic.

If user chooses: use that topic/keyword, move to Step 3.
If user adjusts: revise only flagged recommendations, re-present.
If user provides own topic: treat as Path A, run overlap check before Step 3.
Do not generate a third set without asking user to provide their own topic as alternative.

Filter out any overlap-free check failures silently before presenting.

Do not proceed to Step 3 until user confirms a single topic and keyword.

---

### STEP 3: COLLECT REMAINING INPUTS

Optional but recommended:
- Specific angle, argument, or insight for this post
- Sources or data points to prioritise in research
- Internal pages to link from this post
- Target publish date (for run folder naming)

If Path B, carry the E-E-A-T angle from the chosen recommendation forward automatically.

Present confirmation summary:
```
RUN INPUTS CONFIRMED
Client:           [CLIENT]
Primary keyword:  [KEYWORD]
Topic:            [TOPIC STRING]
Angle/notes:      [IF PROVIDED, otherwise: None specified]
Priority sources: [IF PROVIDED, otherwise: None specified]
Internal links:   [IF PROVIDED, otherwise: None specified]
```

Ask user to confirm or correct before Step 4.

---

### STEP 4: CREATE THE RUN FOLDER

Naming rule: `Clients/[CLIENT]/Runs/[TOPIC_SLUG]_[YYYY-MM]`

- Slug from confirmed topic string → Title_Case with underscores
- If no topic string: use primary keyword instead
- YYYY-MM from user's preferred publish month, otherwise current month

Full naming rules: `tools/planning_loader.md`

Examples:
- Topic "Choosing a Home Service Provider - May 2026" → `Choosing_Home_Service_Provider_May_2026_2026-05`
- Keyword "mobile windshield replacement loveland", 2025-06 → `Mobile_Windshield_Replacement_Loveland_2025-06`

Show proposed folder name. Confirm before creating. Once confirmed, create the folder only — no files. Stage 1 writes the first file.

---

### STEP 5: STAGE 1 HANDOFF BRIEF

Write this file to the run folder:

`Clients/[CLIENT]/Runs/[RUN_FOLDER]/00_Stage_1_Handoff_Brief.md`

```
# Stage 1 Handoff Brief

Status: READY
Created by: Pre-Stage 1 - New Run
Created: [YYYY-MM-DD HH:MM]
Client: [CLIENT]
Run: [RUN_FOLDER]
Topic source: [USER PROVIDED / IDEATION - Recommendation N]
Dry run: [true/false]

## Next Stage

- Stage: 1 - Research
- Run path: Clients/[CLIENT]/Runs/[RUN_FOLDER]/
- Expected output: 01_Research_Dossier.md

## Load Instructions

**Mandatory first load:**
- `_stages/stage1_research/CONTEXT.md` (load in full; authoritative Stage 1 contract)

Load in full:
- Clients/[CLIENT]/Reference/Style_Reference_Card.md
- Clients/[CLIENT]/Reference/Audience_Profile.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/00_Stage_1_Handoff_Brief.md

Load sections only:
- Clients/[CLIENT]/Reference/Brand_Notes.md: Service Lines and Scope, Authority and Trust Signals

Do not load:
- _config/anti-ai-checklist.md
- _config/search-quality-rubric.md
- Any other Runs/ files

Prerequisite check:
- If any reference file is missing, stop and report Stage 0 must run first.

## Carry Forward Context

- Topic: [TOPIC STRING]
- Primary keyword: [KEYWORD]
- Angle/notes: [IF PROVIDED, otherwise: None]
- Priority sources: [IF PROVIDED, otherwise: None]
- Internal links: [IF PROVIDED, otherwise: None]
- Published overlap: [NONE DETECTED / CONFIRMED DISTINCT ANGLE / OVERLAP ACKNOWLEDGED: (post name)]
- Unresolved Brand Notes items: [LIST IF ANY, otherwise: None]

## Quality Gates For Next Stage

- Minimum 3 authoritative sources with specific data points and publication dates
- Non-Obvious Insight is defensible with evidence, not speculation
- Search intent classified and SERP features noted
- Audience Value Statement articulates non-commodity value

## Automation

- Auto-run next stage: [true/false]
- Reason if false: [REASON OR NONE]
```

After writing the handoff file, display a short confirmation summary to the user, then append to `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Run_Log.md`:
```
[YYYY-MM-DD] | Pre-Stage 1 | New Run | Keyword: [KEYWORD] | Source: [USER PROVIDED / IDEATION-N] | Status: INITIATED
```

Then stop. Do not trigger Stage 1 from this stage.

---

## Quality Gates

- [ ] All files loaded match the `Load Before Starting` contract in this file (nothing missing, nothing forbidden)
- [ ] All three reference files exist and were read in full
- [ ] User asked which path to take
- [ ] Published Content Inventory built regardless of path
- [ ] Overlap check completed (Path A) or recommendations confirmed (Path B)
- [ ] User explicitly confirmed a single topic and keyword before Step 3
- [ ] Run folder created at correct path with correct naming
- [ ] `00_Stage_1_Handoff_Brief.md` written to the run folder
- [ ] Topic source recorded
- [ ] Unresolved Brand Notes placeholders flagged
- [ ] Run log entry written with Source field populated

---

## Error Handling

**Client folder does not exist:** Stop. Tell the user the client has not been onboarded. Direct them to Stage 0.

**Run-scoped `Run_Log.md` does not exist:** Create `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Run_Log.md` with `# Run Log` header before writing the first entry.

**Published folder empty or missing:** Note no published content exists. Skip overlap check. Create the Published folder if absent.

**Reference files sparse:** Generate recommendations using available data. Flag inferred items: `[Based on inferred audience intent — confirm with client before proceeding]`.

**User selects recommendation then provides different keyword:** Use user's keyword. Update topic string to match. Run overlap check before Step 3.

**User rejects all recommendations:** Ask one clarifying question about what is missing. Generate a revised set. If rejected again, ask user to provide their own topic.
