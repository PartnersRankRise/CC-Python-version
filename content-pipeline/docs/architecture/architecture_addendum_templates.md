# Architecture Addendum: Client Template Analysis

**Supplements:** `architecture_migration_plan_v2.md`  
**Source:** `Client_Template/` folder — five blank files that Stage 0 populates  
**Purpose:** Reconcile the template schema with the Stage 0 CONTEXT.md spec and the Rankrise reference run outputs; confirm the definitive data model for client onboarding

---

## What the Templates Confirm

### The Client Folder Contains a Fourth File Not in the Stage 0 Spec

The `Client_Template/` contains:
- `CONTEXT.md` — client engagement context (session-orientation file)
- `Reference/Style_Reference_Card.md`
- `Reference/Audience_Profile.md`
- `Reference/Brand_Notes.md`
- `Run_Log.md` — blank log (just `# Run Log` header)

The Stage 0 CONTEXT.md spec lists three output files — the three Reference files. `CONTEXT.md` is not mentioned as a Stage 0 output, but it exists in the template and must be present before Pre-Stage 1 can run (Pre-Stage 1 loads it first to orient the session).

**Implication:** `CONTEXT.md` is created at client folder initialization — either at Stage 0 or as part of the "copy Client_Template" step that precedes Stage 0. It is subsequently updated (not generated fresh) as the engagement progresses. The application must treat it as a mutable engagement record, not a static reference file.

### The `CONTEXT.md` Template Defines a Second Data Model Alongside the `clients` Table

The template contains fields that do not map to the `clients` table designed in v2:

| Template Field | v2 `clients` Table | Gap |
|---|---|---|
| Client name | ✓ `name` | — |
| Industry | ✓ `industry` | — |
| Website | ✓ `website_url` | — |
| Service area | ✓ `service_area` | — |
| Onboarding status | ✓ (derived from `client_reference_files.onboarding_state`) | — |
| Active since | ✗ | Missing: `engaged_at` date |
| Last run | ✗ | Derivable from `runs` table; should be a view, not stored separately |
| Posts published | ✗ | Derivable from `published_articles` count; same |
| Next planned topic | ✗ | Missing: planning field — either stored or left to the human |
| Open items | ✗ | Covered by `unresolved_items` table |
| Notes | ✗ | Missing: freetext engagement notes field |
| Run history summary | ✗ | Missing: human-authored narrative summary |

The `CONTEXT.md` is a **session-orientation document** — it summarizes the engagement state so a human (or an LLM starting a new session) can get oriented without reading every reference file. In the application, this maps to a `client_context` table or a set of additional columns on `clients`.

### The Template Schema Reveals Exactly What Stage 0 Produces

Comparing the three template files to the Stage 0 CONTEXT.md spec confirms the field structure. The spec describes what to populate; the templates define where the populated content lands.

#### `Style_Reference_Card.md` Template → What Stage 0 Must Produce

```
## WRITING STYLE GUIDELINES
  Tone & Voice Direction      → primary_tone, authority_level, attitude
  Sentence Structure          → sentence_length, voice_preference, complexity_level
  Language Preferences        → include_terms[], avoid_terms[], technical_term_policy
  Punctuation & Formatting    → oxford_comma, em_dash_policy, contractions, emphasis

## VISUAL BRAND THEME
  Observed Site Palette       → primary_color (hex), secondary_color, accent_color, neutrals[]
  Typography Direction        → display_font, body_font, fallback_fonts
  Theme Usage Guidance        → color_application, imagery_style, layout_patterns, a11y
  Visual Tone                 → aesthetic_description

## STRUCTURAL GUIDELINES
  Header Hierarchy            → h1_usage, h2_usage, h3_usage, avoid_levels
  List Formatting             → bullet_policy, numbered_policy
  Content Blocks              → max_paragraph_length, callout_usage, quote_format

## SEO & KEYWORD GUIDANCE
  primary_keywords[]
  semantic_variations[]
  local_keywords[]
  keyword_placement_priority
```

**Key observation:** The Style Reference Card contains both writing style data *and* visual brand data (colors, fonts). In the pipeline, these serve different consumers:
- Writing style sections → consumed by Stages 2, 3, 4, 5, 6
- Visual brand sections → consumed only by Stage 7 (HTML generation)

Stage 7's CSS token system needs hex values extracted from the Style Reference Card. These are currently free-form text inside the reference file. The application must parse them into structured fields at onboarding time, not at Stage 7 execution time.

#### `Audience_Profile.md` Template → What Stage 0 Must Produce

```
## Primary Audience
  Who they are                → age_range, professional_background, geographic_context
  What they care about        → pain_points[], goals[], decision_priorities[]
  Where they search           → search_keywords[], platforms[], content_types[]

## Secondary Audience
  role, relationship_to_primary, information_needs

## Engagement Patterns
  buying_cycle_timeline
  search_triggers[]
  trust_factors[]

## Content Preferences
  tone_preference
  technical_depth              → beginner / intermediate / expert
  preferred_formats[]
```

**Key observation:** The `technical_depth` field from the Audience Profile maps directly to the "reading level" check in Stage 5 SEO audit (Section 7: Readability Audit). The reference run targets "8th–10th grade." This value originates in the Audience Profile at onboarding and must be accessible to Stage 5 without loading the full Audience Profile (Stage 5 loads only the register/reading level section of the Style Reference Card). This suggests reading level should be stored on the `client_reference_files` record as a parsed field, not buried in the Audience Profile markdown body.

#### `Brand_Notes.md` Template → What Stage 0 Must Produce

```
## Company Overview
  business_type, years_in_business, service_area, company_size

## Brand Mission & Values
  mission_statement, core_values[], unique_positioning

## Voice & Tone
  brand_voice, personality_traits[], tone_guidelines{formal, customer_facing, educational}

## Key Messages
  primary_message, secondary_message, credibility_message

## Competitor Context
  main_competitors[], differentiation[], advantages_over_competitors[]

## Target Industry/Certification
  certifications[], compliance_considerations[], professional_standards[]
```

**Key observation:** The `certifications[]` and `compliance_considerations[]` from Brand Notes map directly to the "AUTHORITY AND TRUST SIGNALS" section in the Stage 0 CONTEXT.md spec (the section stages 1 and 2 partially load). The template calls them certifications and compliance; the spec calls them "authority and trust signals." They are the same data. The parsed fields should use the spec's naming since that's what downstream stages reference.

The template also lacks the "AUTHORITY AND TRUST SIGNALS," "PUBLISHING SPECIFICATIONS," and "OPEN QUESTIONS FOR CLIENT" sections that the Stage 0 CONTEXT.md spec mandates. These are additions that Stage 0 creates beyond the template structure — the template is the minimum, not the maximum.

### The `Run_Log.md` Template Is Just a Header

```markdown
# Run Log
```

This confirms the run log is append-only and starts empty. The application's `run_log` table (with `# Run Log` as its initial state) accurately mirrors this. No additional fields are needed at initialization.

---

## Schema Additions Required

Based on the templates, three additions are needed to the v2 schema:

### Addition 1: Client Context Table

Stores the mutable `CONTEXT.md` engagement record:

```sql
CREATE TABLE client_contexts (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id            UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  engaged_at           DATE,
  next_planned_topic   TEXT,
  engagement_notes     TEXT,        -- freetext; maps to CONTEXT.md "Notes" section
  run_history_summary  TEXT,        -- human-authored narrative; updated at milestones
  updated_at           TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id)
);
```

The "Last run" and "Posts published" fields from the template are derivable and should not be stored — they are computed from the `runs` and `published_articles` tables respectively. The `GET /clients/{client_id}` endpoint assembles them at query time.

### Addition 2: Parsed Brand Fields on `client_reference_files`

Structured fields extracted from reference file markdown at onboarding time, so downstream stages can access them without parsing markdown:

```sql
ALTER TABLE client_reference_files ADD COLUMN (
  -- From Style Reference Card (visual section) — used by Stage 7
  brand_colors          JSONB DEFAULT '{}',
  -- {primary, primary_2, primary_soft, primary_glow, primary_rgb,
  --  accent, accent_2, accent_soft, accent_rgb, ink, line_strong,
  --  cream, paper, muted, soft, line, warn, warn_soft, warn_line}
  
  display_font          TEXT,    -- e.g., "DM Serif Display"
  body_font             TEXT,    -- e.g., "DM Sans"
  google_fonts_url      TEXT,    -- populated if client uses Google Fonts (style override)
  
  -- From Audience Profile — used by Stage 5 readability check
  reading_level_target  TEXT,    -- e.g., "8th-10th grade"
  technical_depth       TEXT,    -- "beginner" | "intermediate" | "expert"
  
  -- From Brand Notes (authority section) — used by Stages 1 and 2
  certifications        TEXT[],
  years_in_business     INTEGER,
  ymyl_category         TEXT     -- health / finance / legal / safety / none
);
```

### Addition 3: Template Validation at Onboarding

Stage 0 must verify that its output covers all required sections from both the template and the spec. The section list from the template is the minimum; the Stage 0 CONTEXT.md spec mandates additional sections:

```python
# services/onboarding_service.py

STYLE_REFERENCE_REQUIRED_SECTIONS = [
    "WRITING STYLE GUIDELINES",
    "VISUAL BRAND THEME",
    "STRUCTURAL GUIDELINES",
    "SEO & KEYWORD GUIDANCE",
]

AUDIENCE_PROFILE_REQUIRED_SECTIONS = [
    "Primary Audience",
    "Secondary Audience",       # may be "N/A" but must be present
    "Engagement Patterns",
    "Content Preferences",
]

BRAND_NOTES_REQUIRED_SECTIONS = [
    "Company Overview",
    "Brand Mission & Values",
    "Voice & Tone",
    "Key Messages",
    "Competitor Context",
    "Target Industry/Certification",
    # Stage 0 spec adds these beyond the template:
    "PUBLISHING SPECIFICATIONS",
    "SERVICE AREA AND GEOGRAPHIC SCOPE",
    "SERVICE LINES AND SCOPE",
    "AUTHORITY AND TRUST SIGNALS",
    "PAST CONTENT PERFORMANCE NOTES",
    "OPEN QUESTIONS FOR CLIENT",
]

class OnboardingStage(StageContract):
    
    def _validate_output(self, output: StageOutput, run: Run) -> list[str]:
        failures = []
        parsed = output.quality_gate_results.get("parsed_files", {})
        
        for section in self.STYLE_REFERENCE_REQUIRED_SECTIONS:
            if section not in parsed.get("style_reference_card", ""):
                failures.append(f"Style Reference Card missing section: {section}")
        
        for section in self.AUDIENCE_PROFILE_REQUIRED_SECTIONS:
            if section not in parsed.get("audience_profile", ""):
                failures.append(f"Audience Profile missing section: {section}")
        
        for section in self.BRAND_NOTES_REQUIRED_SECTIONS:
            if section not in parsed.get("brand_notes", ""):
                failures.append(f"Brand Notes missing section: {section}")
        
        # Style Reference Card must contain brand colors
        style_card = parsed.get("style_reference_card", "")
        if not self._has_hex_colors(style_card):
            failures.append(
                "Style Reference Card missing brand color hex values — "
                "required for Stage 7 CSS token replacement"
            )
        
        # Brand Notes must have an Open Questions section with client-specific items
        brand_notes = parsed.get("brand_notes", "")
        if "OPEN QUESTIONS FOR CLIENT" not in brand_notes:
            failures.append("Brand Notes missing Open Questions section")
        elif "[CONFIRM WITH CLIENT]" not in brand_notes and "[ ]" not in brand_notes:
            failures.append(
                "Open Questions section appears empty — "
                "Stage 0 must generate client-specific questions"
            )
        
        return failures
    
    def _has_hex_colors(self, style_card: str) -> bool:
        import re
        return bool(re.search(r'#[0-9A-Fa-f]{6}', style_card))
    
    def _extract_brand_colors(self, style_card: str) -> dict:
        """
        Parse hex color values from the Style Reference Card's
        'Observed Site Palette' section. These populate brand_colors
        JSONB at onboarding time so Stage 7 doesn't need to re-parse.
        
        Confirmed token names from reference run 07_Blog_Final.html:
        --primary, --primary-2, --primary-soft, --primary-glow,
        --primary-rgb, --accent, --accent-2, --accent-soft, --accent-rgb,
        --ink, --line-strong
        """
        import re
        colors = {}
        hex_pattern = re.compile(
            r'\*\*(?:Primary|Secondary|Accent)[^*]*\*\*[^`]*`(#[0-9A-Fa-f]{6})`'
        )
        rgba_pattern = re.compile(r'rgba\([^)]+\)')
        
        # Map template labels to CSS token names
        label_to_token = {
            "primary color": "primary",
            "secondary color": "primary_2",
            "accent color": "accent",
        }
        
        for match in hex_pattern.finditer(style_card):
            label = match.group(0).lower()
            for label_key, token in label_to_token.items():
                if label_key in label:
                    colors[token] = match.group(1)
        
        return colors
```

---

## Template vs. Spec: The Full Gap Map

The templates and the Stage 0 CONTEXT.md spec describe the same three reference files differently. This table is the authoritative reconciliation for the application:

| Data Point | Template Section | Stage 0 Spec Section | Used By Stage(s) | Application Field |
|---|---|---|---|---|
| Primary tone | Style Card: Tone & Voice | Style Card: REGISTER AND TONE | 2, 3, 4, 6 | `style_reference_card` (markdown) |
| Reading level | Style Card: (implicit in complexity) | Style Card: VOCABULARY AND LANGUAGE LEVEL | 5, 6 | `reading_level_target` (parsed) |
| Em dash policy | Style Card: Punctuation | Style Card: STRUCTURAL PATTERNS | 3, 4, 6 | `style_reference_card` (markdown) |
| Brand hex colors | Style Card: Observed Site Palette | Not in spec (implicit in style) | 7 | `brand_colors` JSONB (parsed) |
| Fonts | Style Card: Typography | Not in spec | 7 | `display_font`, `body_font`, `google_fonts_url` (parsed) |
| Pain points | Audience: What they care about | Audience Profile: INTENT AND PAIN POINTS | 1, 2 | `audience_profile` (markdown) |
| Search keywords | Audience: Where they search | Audience Profile: (implicit in audience) | 1, 2 | `audience_profile` (markdown) |
| Technical depth | Audience: Content Preferences | Audience Profile: EXPERTISE AND KNOWLEDGE LEVEL | 2, 5 | `technical_depth` (parsed) |
| Certifications | Brand: Target Industry/Certification | Brand Notes: AUTHORITY AND TRUST SIGNALS | 1 (partial), 2 (partial) | `certifications[]` (parsed) |
| Years in business | Brand: Company Overview | Brand Notes: AUTHORITY AND TRUST SIGNALS | 1 (partial), 2 (partial) | `years_in_business` (parsed) |
| Competitors | Brand: Competitor Context | Not in Stage 0 spec | 2 (implicitly) | `brand_notes` (markdown) |
| Open questions | Not in template | Brand Notes: OPEN QUESTIONS FOR CLIENT | Human review | `brand_notes` (markdown) |
| Off-limits topics | Not in template | Style Card: OFF-LIMITS | 2 (partial), 6 (partial) | `off_limits` on `clients` table |
| Publishing specs | Not in template | Brand Notes: PUBLISHING SPECIFICATIONS | 7 | `brand_notes` (markdown) |
| Service lines | Not in template | Brand Notes: SERVICE LINES AND SCOPE | 1 (partial), 2 (partial) | `brand_notes` (markdown) |
| Past performance | Not in template | Brand Notes: PAST CONTENT PERFORMANCE NOTES | Pre-1 (gap analysis) | `brand_notes` (markdown) |
| Engagement notes | CONTEXT.md: Notes | Not in reference files | Pre-1 (session orientation) | `client_contexts.engagement_notes` |
| Next planned topic | CONTEXT.md: Current State | Not in reference files | Human planning | `client_contexts.next_planned_topic` |
| Active since | CONTEXT.md: Engagement Overview | Not in reference files | Dashboard display | `clients.engaged_at` |
| Run history summary | CONTEXT.md: Run History Summary | Not in reference files | Pre-1 (session orientation) | `client_contexts.run_history_summary` |

**Storage rule derived from this table:**
- If a field is consumed by LLM stages as prose context → store as markdown in the reference file columns
- If a field is consumed programmatically (Stage 5 readability check, Stage 7 CSS tokens, overlap detection) → also store as a parsed field in a dedicated column
- If a field is for human/dashboard use only → store in `client_contexts` or `clients`, not in reference file columns

---

## Revised `CONTEXT.md` Behavior in the Application

In the folder-based system, `CONTEXT.md` is a markdown file that an LLM reads at the start of a Pre-Stage 1 session. In the application, its data lives in two places:

**Computed fields** (from database, not stored in `CONTEXT.md`):
- Onboarding status → `client_reference_files.onboarding_state`
- Last run → `MAX(runs.updated_at) WHERE client_id = ?`
- Posts published → `COUNT(*) FROM published_articles WHERE client_id = ?`
- Open items → `COUNT(*) FROM unresolved_items WHERE run_id IN (...) AND resolved = false`

**Stored fields** (in `client_contexts`):
- Active since, engagement notes, next planned topic, run history summary

The Pre-Stage 1 prompt builder assembles a synthetic "CONTEXT.md" from these sources at runtime, rather than reading a file. This is the correct pattern because it means the context is always current (computed from live data) rather than potentially stale (last edited by a human or LLM).

```python
# orchestration/context_assembler.py
class ClientContextAssembler:
    """
    Produces the session-orientation context that Pre-Stage 1 used to get
    from reading CONTEXT.md. Assembles from live database state.
    """
    
    def assemble(self, client_id: UUID) -> str:
        client = self._client_repo.get(client_id)
        context = self._context_repo.get(client_id)
        ref = self._ref_repo.get(client_id)
        
        last_run = self._run_repo.latest(client_id)
        published_count = self._article_repo.count(client_id)
        open_items = self._item_repo.open_count_across_runs(client_id)
        
        return f"""# {client.name}

## Engagement Overview

- Client: {client.name}
- Industry: {client.industry}
- Website: {client.website_url}
- Service area: {client.service_area}
- Onboarding status: {ref.state.value.replace('_', ' ').title()}
- Active since: {context.engaged_at or 'Not recorded'}

## Current State

- Last run: {last_run.folder_slug if last_run else 'None'}
- Posts published: {published_count}
- Next planned topic: {context.next_planned_topic or 'TBD'}
- Open items: {f'{open_items} items outstanding' if open_items else 'None'}

## Notes

{context.engagement_notes or 'No notes recorded.'}

## Run History Summary

{context.run_history_summary or 'No summary yet.'}
"""
```

---

## Updated Onboarding Stage Sequence

With the template structure confirmed, the Stage 0 execution sequence becomes:

```
1. Detect client state (NEW / PARTIAL / FULLY_ONBOARDED)

2. If NEW:
   a. Create `clients` record
   b. Create `client_contexts` record (blank)
   c. Create `client_reference_files` record (state = 'new')
   d. Initialize `run_log` header record

3. Generate missing reference files via LLM:
   - Style_Reference_Card (maps to template + spec additional sections)
   - Audience_Profile (maps to template sections)
   - Brand_Notes (maps to template + spec additional sections including
     AUTHORITY AND TRUST SIGNALS and OPEN QUESTIONS FOR CLIENT)

4. Parse generated files for structured fields:
   - Extract hex colors → brand_colors JSONB
   - Extract fonts → display_font, body_font, google_fonts_url
   - Extract reading level → reading_level_target, technical_depth
   - Extract certifications → certifications[]
   - Extract years_in_business → years_in_business
   - Derive ymyl_category from industry + brand context

5. Validate all required sections present (template minimum + spec additions)

6. Validate hex colors present in Style Reference Card
   (required for Stage 7; absence is a blocking gate)

7. Update client_reference_files.onboarding_state:
   - All three files complete → 'fully_onboarded'
   - Some files complete → 'partial'

8. Write run log entry:
   [DATE] | Stage 0 | Onboarding | Client: [NAME] | Status: COMPLETE

9. Surface Open Questions to user (do not block; flag for review)
```

**What Stage 0 does NOT do:**
- Populate `client_contexts.engagement_notes` or `run_history_summary` — these are human-maintained
- Populate `client_contexts.next_planned_topic` — set by Pre-Stage 1
- Update `client_contexts.engaged_at` — set once at client creation, never by Stage 0

---

## Updated API Additions

Two endpoints need to be added to the v2 API spec:

```
# Client context (the CONTEXT.md equivalent)
GET    /clients/{client_id}/context           # Assembled client context (computed)
PATCH  /clients/{client_id}/context           # Update engagement_notes, next_planned_topic,
                                              # run_history_summary (human-authored fields only)

# Onboarding validation
GET    /clients/{client_id}/onboarding/status # Detailed: which sections are present/missing
                                              # per file; which structured fields were parsed
```

#### `GET /clients/{client_id}/context` response

```json
{
  "client_id": "uuid",
  "name": "Rankrise Marketing",
  "industry": "Digital Marketing / Home Services SEO",
  "website_url": "https://rankrisemarketing.com",
  "service_area": "Colorado Front Range",
  "onboarding_state": "fully_onboarded",
  "engaged_at": "2026-01-15",
  "last_run": {
    "folder_slug": "Content_Marketing_Home_Services_2026-06",
    "status": "approved",
    "updated_at": "2026-06-22"
  },
  "posts_published": 3,
  "next_planned_topic": "TBD",
  "open_items_count": 0,
  "engagement_notes": "Human-authored notes here.",
  "run_history_summary": "Three posts published covering AI Overviews and content marketing.",
  "parsed_brand_fields": {
    "brand_colors": {
      "primary": "#1B3D6F",
      "accent": "#E8762B"
    },
    "display_font": "DM Serif Display",
    "body_font": "DM Sans",
    "google_fonts_url": "family=DM+Sans:...",
    "reading_level_target": "8th-10th grade",
    "technical_depth": "intermediate",
    "certifications": [],
    "years_in_business": null,
    "ymyl_category": "financial"
  }
}
```

#### `GET /clients/{client_id}/onboarding/status` response

```json
{
  "onboarding_state": "fully_onboarded",
  "files": {
    "style_reference_card": {
      "present": true,
      "sections_present": [
        "WRITING STYLE GUIDELINES",
        "VISUAL BRAND THEME",
        "STRUCTURAL GUIDELINES",
        "SEO & KEYWORD GUIDANCE"
      ],
      "sections_missing": [],
      "hex_colors_found": true,
      "brand_colors_parsed": true
    },
    "audience_profile": {
      "present": true,
      "sections_present": [
        "Primary Audience",
        "Secondary Audience",
        "Engagement Patterns",
        "Content Preferences"
      ],
      "sections_missing": [],
      "reading_level_parsed": "8th-10th grade"
    },
    "brand_notes": {
      "present": true,
      "sections_present": [
        "Company Overview",
        "Brand Mission & Values",
        "Voice & Tone",
        "Key Messages",
        "Competitor Context",
        "Target Industry/Certification",
        "PUBLISHING SPECIFICATIONS",
        "SERVICE AREA AND GEOGRAPHIC SCOPE",
        "SERVICE LINES AND SCOPE",
        "AUTHORITY AND TRUST SIGNALS",
        "PAST CONTENT PERFORMANCE NOTES",
        "OPEN QUESTIONS FOR CLIENT"
      ],
      "sections_missing": [],
      "open_questions_count": 6
    }
  },
  "blocking_gaps": [],
  "warnings": [
    "Open Questions not yet resolved: byline style, brand capitalization, case study permissions"
  ]
}
```

---

## Summary of All Schema Changes From This Addendum

```sql
-- Addition 1: engagement date on clients table
ALTER TABLE clients ADD COLUMN engaged_at DATE;

-- Addition 2: client context (mutable engagement record)
CREATE TABLE client_contexts (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id            UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  engaged_at           DATE,
  next_planned_topic   TEXT,
  engagement_notes     TEXT,
  run_history_summary  TEXT,
  updated_at           TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id)
);

-- Addition 3: parsed structured fields on client_reference_files
ALTER TABLE client_reference_files ADD COLUMN brand_colors JSONB DEFAULT '{}';
ALTER TABLE client_reference_files ADD COLUMN display_font TEXT;
ALTER TABLE client_reference_files ADD COLUMN body_font TEXT;
ALTER TABLE client_reference_files ADD COLUMN google_fonts_url TEXT;
ALTER TABLE client_reference_files ADD COLUMN reading_level_target TEXT;
ALTER TABLE client_reference_files ADD COLUMN technical_depth TEXT;
ALTER TABLE client_reference_files ADD COLUMN certifications TEXT[];
ALTER TABLE client_reference_files ADD COLUMN years_in_business INTEGER;
ALTER TABLE client_reference_files ADD COLUMN ymyl_category TEXT;
```

All other tables from v2 remain unchanged. The `ClientContextAssembler` class replaces the folder-based `CONTEXT.md` read at Pre-Stage 1 session start.

---

*Addendum version 1.0 — July 2026. Read alongside `architecture_migration_plan_v2.md`. The v2 document remains the primary reference; this addendum adds the onboarding data model and resolves the template vs. spec discrepancies.*
