# Stage 4: Humanization

Detects and rewrites AI-sounding passages, enforces voice consistency, and verifies E-E-A-T standards before SEO review.

## Load Before Starting

```
Load in full:
- Clients/[CLIENT]/Reference/Style_Reference_Card.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/03_First_Draft.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/03_Stage_4_Handoff.md

Load sections only:
- _config/anti-ai-checklist.md
  → Read: Section 3 (Anti-AI Writing Standards — rules block only, not the checklist format)

If 03_First_Draft.md does not exist: stop.
Tell the user Stage 3 must be completed first.

Do not load:
- 02_Content_Brief.md
- 01_Research_Dossier.md
- Audience_Profile.md
- Brand_Notes.md
- _config/search-quality-rubric.md
```

This stage is responsible for voice authenticity, originality enforcement, and authority signals.

## Editing Rules (No New Directives, No Resurrection)

- **No new workflow directives**: edit prose only; do not add instruction-like meta text or CRM-style comments.
- **No resurrection**: do not "restore" any brief notes, preferences, or CRM-like directives that Stage 2 intentionally cleaned out.
- **Flag instruction-like leakage**: if you detect instruction-shaped text in the draft (e.g., "this section should…", "CTA must read exactly…", or similar), remove it and flag in the Editorial Note (or mark `[AGENCY INPUT NEEDED]` if the content is genuinely ambiguous).

## File Output

Write to: `Clients/[CLIENT]/Runs/[RUN_FOLDER]/04_Humanized_Draft.md`

Before stopping, also write:

`Clients/[CLIENT]/Runs/[RUN_FOLDER]/04_Stage_5_Handoff.md`

**Output contract:** `04_Humanized_Draft.md` MUST contain the full article body from `03_First_Draft.md`, edited in place. The Editorial Note comes AFTER the full draft as a `## Editorial Note` section at the end. Do not write only commentary or placeholder text — if the humanization pass cannot be completed, stop and report the failure.

---

## Task

Read the entire draft before making any changes. Then work through all seven dimensions.

### DIMENSION 1: AI PATTERN DETECTION & LOGICAL LEAPS

Flag and rewrite every instance of:
- Perfectly parallel sentence constructions repeated more than twice in a row
- Symmetrical 3-sentence paragraphs in sequence
- Agreement bias: sections that sound too agreeable or neutral — rewrite to take a firm, professional stance
- Linearity: if logic is too predictable (A → B → C), introduce a lateral leap — an unexpected industry parallel or "when not to use this" caveat
- Impersonal constructions: "It is important to note that" / "It should be mentioned that"
- Generic transitions: "In addition," "Furthermore," "Moreover," "Moving on"

### DIMENSION 2: VOICE & SOCIABILITY AUDIT

Check every section against the Style Reference Card.

The Read-Aloud Test: if a paragraph sounds like a textbook, rewrite it to sound like a practitioner speaking to a colleague.

Remove AI flavor words: "Tapestry," "Testament," "Ultimate Guide," "Vibrant," "Delve," "Unlock," "practical next," "and efficiency"

Ensure register does not drift into "Helpful Assistant" mode.

### DIMENSION 3: RHYTHM & BURSTINESS

Identify any 200-word stretch where paragraph lengths or sentence structures become monotonous.

Confirm after edits:
- At least two single-sentence paragraphs in the body
- No more than 2-3 single-sentence paragraphs in the full post, used only for emphasis or rhythm
- At least one paragraph over 5 sentences in the body
- No three consecutive paragraphs the same length
- Variance in sentence starters — no more than two consecutive sentences starting with the same word

Single-sentence paragraphs are a spice, not a filler tactic. If three consecutive paragraphs are under 2 sentences each, treat that as a humanization failure and consolidate or deepen the section.

### DIMENSION 4: EXPERIENCE & NEGATIVE CONSTRAINTS

Identify claims making assertions without specific supporting detail.

Experience injection: add a plausible practitioner observation or "Common Pitfall" (e.g., "In practice, this often fails when...")

Flag clearly with `[AGENCY INPUT NEEDED]` any section requiring a specific client case study or proprietary data to meet E-E-A-T.

### DIMENSION 5: SEMANTIC CLUSTERING

Move beyond keyword density. Ensure the primary keyword is supported by contextually related semantic cluster terms. If the topic is "SEO Strategy," ensure terms like "search intent," "canonicalization," or "crawling" appear naturally where AI might just repeat the main keyword.

### DIMENSION 6: HELPFULNESS & E-E-A-T COMPLETION

Actionable guidance: if a section describes a concept but does not tell the reader how to execute it or what to do next, extend it.

Trustworthiness: ensure every empirical claim has clear attribution.

### DIMENSION 7: COMMODITY & AUTHORITY AUDIT

Commodity detection: flag any section that reads as generic internet advice rather than content informed by the client's specific expertise. If a generative AI model could produce substantially the same paragraph without any client-specific input, the section needs differentiation.

Point of view: confirm the draft takes clear positions. Every major H2 should contain at least one assertion that reflects the client's stance.

Authority cues: verify the post establishes why this client has standing on this topic. If authorship, credentials, or experience signals are weak or absent, flag for agency input.

### ANTI-AI FINAL CHECK (ZERO TOLERANCE)

Before finalizing, verify absolute absence of (full rules in `_config/anti-ai-checklist.md` Section 3, already loaded):
- [ ] Em dashes anywhere
- [ ] Filler affirmations: "Certainly," "Absolutely," "Great question," "Without further ado"
- [ ] Perfectly parallel list structures
- [ ] Passive constructions where an active alternative is available
- [ ] Generic transitions used as logical crutches

### EDITORIAL NOTE

Append after the draft under `## Editorial Note` (150–200 words):
- Structural changes: what AI patterns were broken and why
- Experience additions: where specificity was added or where `[AGENCY INPUT NEEDED]` was flagged
- E-E-A-T alignment: how the draft now meets human-first standards
- The "Soul" check: does this sound like the client or an LLM?
- QA concern: the one specific part the human editor should scrutinize most

---

## Handoff Preparation (Before Stopping)

After `04_Humanized_Draft.md` is complete, prepare `04_Stage_5_Handoff.md` using `_config/handoff_template.md`.

The handoff must tell Stage 5 to:
- load `_stages/stage5_seo/CONTEXT.md` in full (mandatory first load)
- load `04_Humanized_Draft.md` in full
- load `04_Stage_5_Handoff.md` in full
- load `02_Content_Brief.md` sections: Keyword Strategy, Internal Linking Opportunities, Structural Specifications
- load `Style_Reference_Card.md` sections: register and reading level guidance
- avoid `Audience_Profile.md`, `Brand_Notes.md`, `01_Research_Dossier.md`, `03_First_Draft.md`, `_config/search-quality-rubric.md`, and `_config/anti-ai-checklist.md`

Carry forward:
- topic
- primary keyword
- any `[AGENCY INPUT NEEDED]` flags still present
- readability concerns
- sections where links or metadata will need special SEO attention

Set `Auto-run next stage: true` unless unresolved agency input prevents SEO review.

## Quality Gates

- [ ] All files loaded match the `Load Before Starting` contract in this file (nothing missing, nothing forbidden)
- [ ] `04_Humanized_Draft.md` includes the entire edited article body (not just notes)
- [ ] Every AI pattern identified and rewritten
- [ ] Zero em dashes and zero filler affirmations
- [ ] No 200-word stretch with monotonous rhythm
- [ ] Every major section has specific detail or an `[AGENCY INPUT NEEDED]` flag
- [ ] Post provides enough information for the reader to act independently
- [ ] Editorial Note appended at end of file
- [ ] `04_Stage_5_Handoff.md` written to the run folder

Append to `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Run_Log.md`:
```
[YYYY-MM-DD] | Stage 4 | Humanization | Status: COMPLETE
```
