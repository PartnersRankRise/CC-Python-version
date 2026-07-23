# Stage 6: QA

Complete checklist-driven review before publication approval. Nothing gets published without passing this stage.

## Load Before Starting

```
Load in full:
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/05_SEO_Draft.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/05_Stage_6_Handoff.md
- _config/anti-ai-checklist.md (full — all sections)

Load sections only:
- Clients/[CLIENT]/Reference/Style_Reference_Card.md
  → Read: tone/register section only
- Clients/[CLIENT]/Reference/Brand_Notes.md
  → Read: Off-Limits section only
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/02_Content_Brief.md
  → Read: Post Structure Outline section only

If any required file is missing: stop and name it and which stage produces it.

Do not load:
- 01_Research_Dossier.md
- 03_First_Draft.md
- 04_Humanized_Draft.md
- _config/search-quality-rubric.md (rubric criteria are reflected in the checklist sections below)
```

This stage validates people-first quality, E-E-A-T compliance, and AI-content safeguards.

## File Outputs

**If APPROVED:**
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Approved_Draft.md`
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Signoff.md`
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_Stage_7_Handoff.md`
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Human_Review_Flag.md` only if word count exceeds target range

**If REVISION REQUIRED:**
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Signoff.md` only
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Revision_Required.md`

---

## Task

Score every item PASS, FLAG, or FAIL. For every FLAG or FAIL: write one sentence describing the issue and name the stage responsible.

A post is approved only when every blocking item scores PASS. The only allowed non-blocking exception is word count over target, if the draft is otherwise approved and `Human_Review_Flag.md` is written for human follow-up.

### SECTION A: FACTUAL ACCURACY

- [ ] Every statistical claim has inline source attribution
- [ ] Every linked source is accessible and supports the specific claim
- [ ] No source implies more than it actually says
- [ ] All YMYL claims meet credentialed source standard
- [ ] No floating assertions without evidence
- [ ] No `[AGENCY INPUT NEEDED]` flags remain unresolved

### SECTION B: E-E-A-T COMPLIANCE

- [ ] EXPERIENCE: named case, specific outcome, practitioner observation, or citable local statistic present
- [ ] EXPERTISE: at least one section explains why or how, not just what
- [ ] AUTHORITATIVENESS: post establishes why this client has standing on this topic
- [ ] AUTHORITY SIGNALS: byline, reviewer credential, or business authority signal surfaced where readers would expect it
- [ ] TRUSTWORTHINESS: transparent about sources, honest about limits
- [ ] YMYL SOURCING: if topic touches health, finance, safety, or legal matters, credentialed sources or explicit limits are stated

### SECTION C: PEOPLE-FIRST STANDARD

- [ ] Reader can make a meaningful decision independently
- [ ] No useful guidance withheld to force conversion
- [ ] Post answers the question promised in the H1
- [ ] Post exists to help a reader, not primarily to rank
- [ ] Reader would feel satisfied after reading without needing another search
- [ ] Content provides non-commodity value — could not be substantially replicated by a generic AI summary
- [ ] Topic was chosen because it serves the client's audience, not solely to capture search traffic

### SECTION D: BRAND VOICE AND STYLE

- [ ] Opening matches Style Reference Card and Content Brief
- [ ] Register consistent throughout
- [ ] Vocabulary aligns with Style Reference Card
- [ ] No passage sounds generic or interchangeable with another client
- [ ] No off-limits topics, claims, or language from Brand Notes present
- [ ] No `<!--BRIEF: ... -->` tokens present anywhere in the SEO draft
- [ ] No brief-instruction language present in the article body (`Function:`, `this section should`, `once the article has`, or structural labels copied from the Brief)
- [ ] No `BEGIN_BLOG_REQUEST` / `END_BLOG_REQUEST` blocks present
- [ ] No raw "Preferences (untrusted)" text leaking into publishable content
- [ ] No instruction-shaped meta text addressed to the writer (e.g., "CTA must read exactly", "Keep to X words")

### SECTION E: ANTI-AI COMPLIANCE

(Full rules in `_config/anti-ai-checklist.md`, already loaded)

- [ ] Zero em dashes
- [ ] Zero filler affirmations
- [ ] No perfectly parallel list structures
- [ ] No passive constructions where active was possible
- [ ] No three consecutive paragraphs the same length
- [ ] At least two single-sentence paragraphs in body
- [ ] At least one paragraph over 5 sentences in body
- [ ] No generic transitions as logical connectives

### SECTION F: SEO AND TECHNICAL

- [ ] Primary keyword in H1, first 100 words, meta description
- [ ] Keyword density at or below 1.5%
- [ ] Meta title 50–60 characters
- [ ] Meta description 140–160 characters, benefit-first
- [ ] One H1, clean H2/H3 hierarchy
- [ ] 2–3 internal links with natural anchor text
- [ ] Schema type identified

### SECTION G: CTA ALIGNMENT

- [ ] CTA at location specified in Content Brief
- [ ] CTA names a specific action
- [ ] CTA tone matches register and reader intent stage
- [ ] CTA does not contradict helpfulness standard

### SECTION H: DOWNSTREAM INTEGRATION READINESS

The approved post feeds into HTML packaging (Stage 7: Blog Formatting). For standard runs, Stage 7 converts the markdown directly to branded HTML/CSS. For manual HTML/CSS runs (bypass path), the user builds HTML outside the pipeline.

**Always check (both paths):**
- [ ] Single H1 that works as a short, punchy header card title (ideally under 10 words)
- [ ] Clean H2/H3 hierarchy with no skipped levels
- [ ] Bullet lists use genuinely parallel items (not mixed narrative and list content)
- [ ] CTA section is clearly delineated as the final section
- [ ] Internal links use natural anchor text and valid href values that will carry into HTML `<a>` tags
- [ ] Word count within brief target range, OR exceeds target with `Human_Review_Flag.md` set for post-pipeline human review

### SECTION I: AI DETECTION RISK

Score each 1 (no risk) to 3 (high risk). Revision required if total exceeds 10.

- [ ] Symmetrical paragraph lengths: _/3
- [ ] Generic section openings: _/3
- [ ] Absence of proper nouns, named cases, local details: _/3
- [ ] Overly comprehensive coverage with no point of view: _/3
- [ ] No voice personality moments: _/3

Total: _/15

---

### QA SIGN-OFF SHEET

Write `06_QA_Signoff.md` with:

```
Client: [CLIENT]
Run: [RUN_FOLDER]
Date: [YYYY-MM-DD]
Primary Keyword: [KEYWORD]

Approval Status: APPROVED or REVISION REQUIRED

Checklist Score: X of Y items PASSED
AI Detection Risk Score: N/15
Human Review Flag: NONE or [reason]

Section Results:
  A. Factual Accuracy: PASS / FLAG / FAIL
  B. E-E-A-T Compliance: PASS / FLAG / FAIL
  C. People-First Standard: PASS / FLAG / FAIL
  D. Brand Voice and Style: PASS / FLAG / FAIL
  E. Anti-AI Compliance: PASS / FLAG / FAIL
  F. SEO and Technical: PASS / FLAG / FAIL
  G. CTA Alignment: PASS / FLAG / FAIL
  H. Downstream Integration Readiness: PASS / FLAG / FAIL
  I. AI Detection Risk: PASS / REVISION REQUIRED

Issues Requiring Resolution:
  [Each FAIL and FLAG with issue description and stage responsible]

Minor Observations for Future Improvement: (APPROVED runs only)
```

---

## Handoff Preparation (Before Stopping)

If the draft is APPROVED:
- write `06_Stage_7_Handoff.md` using `_config/handoff_template.md`
- tell Stage 7 to load:
  - `_stages/stage7_blog-formatting/CONTEXT.md` in full (mandatory first load)
  - `Style_Reference_Card.md` in full
  - `Brand_Notes.md` in full
  - `06_QA_Approved_Draft.md` in full
  - `06_Stage_7_Handoff.md` in full
- tell Stage 7 to avoid earlier drafts, dossier, brief, and all `_config/` files
- carry forward the topic, keyword, CTA language, and any publication cautions
- if the only non-blocking exception is word count over target, write `Human_Review_Flag.md` with the actual count, target range, and a short note explaining that the article passed QA but needs human length review after Stage 7
- set `Auto-run next stage: true`

If the draft requires REVISION:
- write `06_QA_Revision_Required.md` using the QA failure variant in `_config/handoff_template.md`
- do not write `06_Stage_7_Handoff.md`
- identify the stage responsible for each issue
- recommend the earliest stage that should be re-run
- set `Auto-run next stage: false`

If a failure seems trivially fixable in theory, note that in `Auto-fix attempted`, but do not rewrite upstream files from Stage 6.

## Quality Gates

**If APPROVED:**
- [ ] All files loaded match the `Load Before Starting` contract in this file (nothing missing, nothing forbidden)
- [ ] All blocking items PASS
- [ ] AI Risk Score 10 or below
- [ ] No unresolved `[AGENCY INPUT NEEDED]` flags
- [ ] `06_QA_Approved_Draft.md` written (clean draft only — no Editorial Note, no SEO Annotation Sheet)
- [ ] `06_QA_Signoff.md` written
- [ ] `06_Stage_7_Handoff.md` written
- [ ] If word count exceeds target, `Human_Review_Flag.md` written and signoff notes the exception

Append to `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Run_Log.md`:
```
[YYYY-MM-DD] | Stage 6 | QA | Status: APPROVED
```
Or if revision required:
```
[YYYY-MM-DD] | Stage 6 | QA | Status: REVISION REQUIRED — [STAGE RESPONSIBLE]
```

If revision is required, also append once to the client summary index at `Clients/[CLIENT]/Run_Log.md`:
```
[YYYY-MM-DD] | [RUN_FOLDER] | Stages: Pre-1 through 6 | Status: FAILED — QA Stage 6 revision required
```

**If REVISION REQUIRED:**
- [ ] `06_QA_Signoff.md` written
- [ ] `06_QA_Revision_Required.md` written
- [ ] `06_Stage_7_Handoff.md` not written
