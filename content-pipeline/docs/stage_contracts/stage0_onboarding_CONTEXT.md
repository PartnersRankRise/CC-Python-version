# Stage 0: Onboarding

Runs once per new client. Analyzes existing content samples and generates all three reference artifacts. Must complete before any production run begins.

This stage captures durable client authority signals and trust assets that downstream stages need for E-E-A-T compliance (see `_config/search-quality-rubric.md` Section 2 if reference is needed).

## Load Before Starting

```
Load in full:
- Client content samples (provided by user in this session)

Do not load:
- Any Reference files (they don't exist yet, or are being regenerated)
- Any _config/ files
- Any Runs/ files
```

## Required Inputs

Ask the user to provide:
- Client name
- Client website URL
- Client industry
- 1–3 existing blog posts or content samples (pasted or as file paths)
- Additional context: service area, known off-limits topics

## File Outputs

Write all three files to `Clients/[CLIENT_NAME]/Reference/`:
- `Style_Reference_Card.md`
- `Audience_Profile.md`
- `Brand_Notes.md`

---

## Preflight: Check Current State Before Writing Anything

**New client** (folder `Clients/[CLIENT_NAME]/` does not exist):
- Copy `Clients/Client_Template` to `Clients/[CLIENT_NAME]`
- Run full Stage 0 — generate all three reference files

**Partially onboarded** (folder exists, but one or more reference files missing):
- Generate only the missing files
- Do not overwrite existing files

**Fully onboarded** (all three reference files exist):
- STOP. Tell the user this client is already onboarded. Ask if they meant to start a new run instead.
- Only proceed if the user explicitly requests regenerating reference files.

---

## Task

Read every content sample in full before writing anything. Then generate all three artifacts.

---

### OUTPUT 1: Style_Reference_Card.md

#### REGISTER AND TONE
- Primary register: Conversational-Humorous / Authoritative-Practical / Balanced — choose the closest match
- Formality level (1 = casual, 5 = formal)
- Second person usage — with example from sample
- Humor permission — with example if yes
- Sarcasm or irony — with example if yes
- Authority signals used

#### VOCABULARY AND LANGUAGE LEVEL
- Estimated reading level
- Technical jargon policy
- Industry terms to always include (extracted from samples)
- Words and phrases to use (extracted from samples)
- Words and phrases to avoid
- Client-specific fingerprint phrases

#### STRUCTURAL PATTERNS
- Post opening approach
- Argument structure
- Closing approach
- Preferred list length
- Bullet usage
- H3 style
- Paragraph length pattern observed in samples

#### SEO FINGERPRINTS
- Primary keyword introduction style
- Secondary keyword placement
- Meta description style

#### AUTHENTICITY MARKERS
- Storytelling technique
- Opinion signals
- Evidence types used

#### OFF-LIMITS
- Topics this client does not address
- Claims this client cannot or should not make
- Tone violations to avoid
- Competitor mention policy

---

### OUTPUT 2: Audience_Profile.md

Sections to populate:
- DEMOGRAPHIC BASELINE
- EXPERTISE AND KNOWLEDGE LEVEL
- INTENT AND PAIN POINTS
- CONTENT PROMISES (what the audience expects this client to deliver)
- TOPICAL AUTHORITY SIGNALS (what makes this client credible to this audience)

---

### OUTPUT 3: Brand_Notes.md

Sections to populate:

**PUBLISHING SPECIFICATIONS**

**SERVICE AREA AND GEOGRAPHIC SCOPE**

**SERVICE LINES AND SCOPE**

**AUTHORITY AND TRUST SIGNALS** — capture durable evidence that downstream stages use for E-E-A-T compliance:
- Preferred authorship model: company voice, named author, or expert-reviewed
- Available credentials, certifications, or licenses
- Years in business or relevant experience
- Case studies, testimonials, or proprietary data available
- Awards, recognitions, or industry memberships
- Claims the client can credibly make from direct practice
- Claims that require external credentialed sources

**PAST CONTENT PERFORMANCE NOTES**

**OPEN QUESTIONS FOR CLIENT** — specific to this client, not a generic template. Always include:
- [ ] Named author or byline for posts?
- [ ] Expert reviewer available for YMYL topics?
- [ ] Confirmed service area boundaries?
- [ ] Approved claims language for sensitive topics?
- [ ] Active promotions to reference?
- [ ] Case studies or testimonials available?
- [ ] Credentials or certifications to surface in content?

---

## Quality Gates

- [ ] All files loaded match the `Load Before Starting` contract in this file (nothing missing, nothing forbidden)
- [ ] Client state correctly identified (new, partial, or fully onboarded)
- [ ] No existing reference files overwritten
- [ ] Every section populated; `[CONFIRM WITH CLIENT]` used only where genuinely unknown
- [ ] No specifics invented that are not supported by sample content
- [ ] Style Reference Card includes at least two direct examples from the samples
- [ ] Open Questions list is specific to this client
- [ ] Authority and Trust Signals section populated with available credentials, evidence types, and claims constraints
- [ ] All three files present under `Clients/[CLIENT_NAME]/Reference/` after completion
- [ ] Downstream note respected: Stage 0 does not create a run-scoped handoff; Pre-Stage 1 creates the first handoff after topic confirmation

Append to `Clients/[CLIENT_NAME]/Run_Log.md`:
```
[YYYY-MM-DD] | Stage 0 | Onboarding | Client: [CLIENT_NAME] | Status: COMPLETE
```
