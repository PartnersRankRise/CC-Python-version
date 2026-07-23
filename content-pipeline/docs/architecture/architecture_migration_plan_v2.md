# Content Pipeline: Architecture & Migration Plan (v2)

**From:** Prompt-driven IDE workflow (folder-based)  
**To:** Python OOP backend · Next.js frontend · Supabase database  
**Audience:** Senior developers beginning implementation  
**Reference run:** `Rankrise_Marketing / Content_Marketing_Home_Services_2026-06`  
**Version note:** v2 incorporates analysis of all 16 real stage outputs from a complete production run, replacing v1's structural inferences with confirmed behavior.

---

## Table of Contents

1. [Workflow Analysis — Evidence-Based](#1-workflow-analysis--evidence-based)
2. [What the Real Outputs Reveal](#2-what-the-real-outputs-reveal)
3. [Backend Architecture (Python OOP)](#3-backend-architecture-python-oop)
4. [Frontend Structure (Next.js)](#4-frontend-structure-nextjs)
5. [Database Schema (Supabase)](#5-database-schema-supabase)
6. [API Layer](#6-api-layer)
7. [Migration Path](#7-migration-path)
8. [Critical Code Sketches](#8-critical-code-sketches)

---

## 1. Workflow Analysis — Evidence-Based

### 1.1 The Real Pipeline Sequence

Based on the reference run's `Run_Log.md`, all seven stages completed on the same calendar day (2026-06-22), each producing both a primary output file and a next-stage handoff file. The pipeline ran sequentially with human confirmation between stages (all handoffs show `Auto-run next stage: false`, consistent with "Sequential human-supervised run").

```
[2026-06-22] Pre-Stage 1  → run folder created, 00_Stage_1_Handoff_Brief.md
[2026-06-22] Stage 1      → 01_Research_Dossier.md + 01_Stage_2_Handoff.md
[2026-06-22] Stage 2      → 02_Content_Brief.md + 02_Stage_3_Handoff.md
[2026-06-22] Stage 3      → 03_First_Draft.md + 03_Stage_4_Handoff.md
[2026-06-22] Stage 4      → 04_Humanized_Draft.md + 04_Stage_5_Handoff.md
[2026-06-22] Stage 5      → 05_SEO_Draft.md + 05_Stage_6_Handoff.md
[2026-06-22] Stage 6      → 06_QA_Signoff.md + 06_QA_Approved_Draft.md + 06_Stage_7_Handoff.md
[not logged] Stage 7      → 07_Blog_Final.html
```

**Important:** Stage 1.5 (Source Validation) does not appear in this run's log, meaning it either was not yet deployed or ran silently without a log entry. The application must account for both behaviors.

### 1.2 Stage-by-Stage: Confirmed Inputs and Outputs

#### Stage 0 (Onboarding) — not in reference run; inferred from reference file usage downstream
Three reference files are consumed by later stages: `Style_Reference_Card.md`, `Audience_Profile.md`, `Brand_Notes.md`. All three exist for Rankrise_Marketing, confirming a completed Stage 0.

#### Pre-Stage 1 — `00_Stage_1_Handoff_Brief.md`
The handoff brief contains the following carry-forward fields that must be modeled as structured data, not free text:
- `Client`, `Run`, `Topic source` (USER PROVIDED | IDEATION-N), `Dry run` (bool)
- `Topic`, `Primary keyword`, `Angle/notes`, `Priority sources`, `Internal links`
- `Published overlap` (NONE DETECTED | CONFIRMED DISTINCT ANGLE | OVERLAP ACKNOWLEDGED)
- `Unresolved Brand Notes items` — a list of open questions, each with a note on whether they block the run
- `Auto-run next stage` (bool) + `Reason if false`

The `Unresolved Brand Notes items` field is critical: it is a list that propagates through handoffs, not a binary flag. In the reference run, four items carried forward (Google Partner status, author byline, case study permissions, national vs. Colorado scope) — none blocking, but all tracked.

#### Stage 1 Research — `01_Research_Dossier.md`
Confirmed structure (8 sections, all populated):
1. `TOPIC AND SEMANTIC FIELD` — normalized topic, audience problem, business relevance, 8 semantic queries
2. `SOURCE BANK` — 5 sources, each with: URL, institution, publication date, ≥3 specific data points
3. `NON-OBVIOUS INSIGHT` — 2-paragraph argument + explanation of why it's underexplored
4. `YMYL ASSESSMENT` — category classification + specific claims requiring credentialed backing
5. `CONTENT GAP ANALYSIS` — 5 numbered gaps in current SERP, each referencing a specific competitor weakness
6. `RECOMMENDED E-E-A-T FRAMING` — single primary pillar with client-specific rationale
7. `SEARCH INTENT CLASSIFICATION` — primary intent + SERP feature inventory
8. `AUDIENCE VALUE STATEMENT` — 2-3 sentence differentiator argument
9. `RESEARCH NOTES FOR STAGE 2` — informal section at the end (not in CONTEXT.md spec but present in output); contains structural suggestions and statistics priority. **This section must be parsed separately and not confused with the 8 formal sections.**

#### Stage 1 → Stage 2 Handoff — `01_Stage_2_Handoff.md`
The `Angle/notes` field in the handoff is already sanitized from the raw Pre-Stage 1 version. Compare:

Pre-Stage 1 raw angle: `"Position content marketing as the sustainable, ROI-positive alternative to wasted ad spend. Target the core persona frustration..."`

Stage 1 sanitized handoff: `"Position content marketing as a sustainable, compounding alternative to paid ads — specifically for home service business owners... Include a realistic 'start here' framework. Reference internal link to Rankrise's AI Overviews post where natural."`

The sanitization removes the promotional framing ("ROI-positive alternative") and retains only the strategic direction and structural notes. The application must perform this transformation programmatically.

#### Stage 2 Brief — `02_Content_Brief.md`
The brief contains `<!--BRIEF: ... -->` comments throughout the outline section. These are substantive writing instructions embedded between heading declarations. The confirmed pattern is:

```
**H2: Heading Text**
<!--BRIEF: instruction prose for Stage 3 writer -->

**H3: Sub-heading Text**
<!--BRIEF: instruction prose -->
```

The brief also contains a table that IS meant to appear in the final article (the content types table) embedded alongside a `<!--BRIEF: Table goes inside this H3 ... -->` instruction. The application parser must distinguish between:
- Content marked `<!--BRIEF: ... -->` → strip before passing to Stage 3
- Tables, lists, and other structured content outside BRIEF tags → carry forward verbatim

The Stage 2 brief confirmed sections: Keyword Strategy (with table), Audience Definition, WHO/HOW/WHY Checkpoint, Post Structure Outline, E-E-A-T Integration Instructions (with mapping table), Style Directive, Structural Specifications, Internal Linking Opportunities, CTA Direction, Author Credential Signal.

#### Stage 3 → Stage 4 Handoff — `03_Stage_4_Handoff.md`
The handoff contains a `Sections to prioritize in humanization pass` field — a freetext list identifying specific weaknesses in the first draft. This is real quality signal from Stage 3 about its own output, and it must be stored. In the reference run:

```
- Opening H2 and "What the Numbers Say" H3 — lean on data; need more voice personality
- Month 1/2/3 framework — slightly listicle-heavy; vary sentence lengths
- FAQ section — all answers follow same structure; break the pattern on at least two answers
```

This field tells Stage 4 where to focus. The application must surface it in the UI for human reviewers before Stage 4 runs.

#### Stage 4 → Stage 5 Handoff — `04_Stage_5_Handoff.md`
Notably sparse compared to earlier handoffs: no `[AGENCY INPUT NEEDED]` flags, no readability concerns, and one URL verification note. The Editorial Note appended to `04_Humanized_Draft.md` confirms what changed and flags the CTA paragraph for human scrutiny.

The Editorial Note structure (confirmed):
- `Structural changes` — what AI patterns were broken
- `Rhythm` — confirmation of burstiness requirements met (single-sentence paragraphs, length variance)
- `Experience additions` — where specificity was added or agency input flagged
- `E-E-A-T` — assertion/position check
- `QA concern` — the single paragraph a human editor should scrutinize most

This note is appended to the humanized draft file but does NOT appear in any downstream file. The application must strip it before Stage 5 receives the draft, and the database must store it separately.

#### Stage 5 SEO — `05_SEO_Draft.md`
The SEO Annotation Sheet is appended after `---` at the end of the article. Confirmed structure:
- `Summary of Changes` — bulleted list of specific edits made
- `Keyword Density Report` — primary keyword / occurrences / total words / density % / PASS
- `Meta Title` — text / character count / PASS or REVISED
- `Meta Description` — text / character count / PASS or REVISED
- `Schema Recommendation` — type + one-sentence rationale
- `Internal Link Placements` — numbered list, each: anchor / destination / section
- `Readability Note` — grade level / PASS or FLAG
- `Word Count Note` — exact script output: `2776 words | target: 2200-2800 | WITHIN TARGET`
- `AI-Search Alignment` — PASS or findings
- `Flags for QA Agent` — bulleted list of client-confirmation items

The SEO Annotation Sheet is structured data masquerading as prose. It must be parsed into discrete fields for the database — not stored as a blob. The `Flags for QA Agent` items carry forward verbatim into `05_Stage_6_Handoff.md` and then appear again in `06_QA_Signoff.md`.

#### Stage 6 QA — `06_QA_Signoff.md`
The signoff is a structured document with confirmed format:
```
Client / Run / Date / Primary Keyword
Approval Status: APPROVED or REVISION REQUIRED
Checklist Score: X of Y items PASSED (with qualification note)
AI Detection Risk Score: N/15
Human Review Flag: NONE or [reason]
Section Results: A through I, each PASS / FLAG / FAIL
Issues Requiring Resolution: each with issue + stage responsible
Minor Observations for Future Improvement: (APPROVED runs only)
```

In the reference run: 38/39 PASSED, AI Risk 5/15, one non-blocking FLAG in Section F (third internal link unconfirmed — noted as a "client/publisher decision, not a pipeline failure"). The `06_QA_Approved_Draft.md` is clean of all SEO Annotation Sheets and Editorial Notes — confirmed by grep showing zero leakage.

#### Stage 7 — `07_Blog_Final.html`
Confirmed HTML structure:
- Self-contained single file (784 lines)
- Inlined `<style>` block with full CSS token system (`:root` with 40+ custom properties)
- External Google Fonts import (DM Sans, DM Serif Display) — note: CONTEXT.md says "No external CSS or JS" but the reference run uses Google Fonts; the application must follow actual client behavior, not the spec
- `<article class="blog-wrap" id="main-content">` wrapper
- Each H2 section wrapped in `<section class="prose">`
- CTA rendered as `<div class="cta-card">` as final element
- No schema markup injected (per spec)
- No Editorial Notes, no SEO Annotation Sheet, no BRIEF tokens — confirmed clean

### 1.3 Cross-Stage Content Evolution: What Actually Changes

Comparing `03_First_Draft.md` to `06_QA_Approved_Draft.md` reveals the concrete changes across Stages 3–6:

**Stage 3 → Stage 4 (Humanization):** The opening paragraph's second sentence changed from `"That is not a marketing problem. That is a math problem."` to `"That is not a marketing problem. That is a structural problem — and it's one most home service businesses don't realize they're locked into until they've spent years and tens of thousands of dollars with nothing permanent to show for it."` — a single sentence was expanded into a full assertion with specificity. This is the humanization pattern: taking a punchy but thin claim and grounding it with operational reality. The FAQ answers were also varied in length to break structural symmetry.

**Stage 4 → Stage 5 (SEO):** The primary keyword was moved earlier in the intro (from ~word 120 to within the first 100 words). The internal link `[local SEO strategy](/services/local-seo/)` was confirmed placed in Month 2. The AI Overviews link was confirmed in FAQ answer 5. Character counts on meta title (57) and description (153) were verified.

**Stage 5 → Stage 6 (QA):** The QA Approved Draft is substantively identical to the SEO Draft's article body. The only structural change is removal of the `## SEO Annotation Sheet` section. Content was not altered at Stage 6 — the QA pass confirmed rather than revised.

**This has a direct implication for the data model:** storing diffs between stage outputs is more valuable than storing full copies of every draft. The database design should support diffing.

---

## 2. What the Real Outputs Reveal

These are things that were not apparent from the CONTEXT.md files alone and that the application must handle correctly.

### 2.1 The `<!--BRIEF: ... -->` Token Is Multi-Line

CONTEXT.md describes BRIEF tokens as wrapping "writer-facing instructions." In the actual brief, many BRIEF blocks span 3–8 lines and contain specific data to carry forward (statistics, source names, structural suggestions). The parser must handle multi-line BRIEF blocks, not just single-line ones.

### 2.2 The Content Types Table Is NOT a BRIEF Block

The content types table in the Content Brief appears immediately after a BRIEF instruction and before another BRIEF instruction. It is not wrapped in BRIEF tags. It is meant to be reproduced verbatim in Stage 3 output — and it is. The parser must not strip non-BRIEF content that appears between BRIEF blocks.

### 2.3 The Research Dossier Has an Informal Trailing Section

The `RESEARCH NOTES FOR STAGE 2` section at the end of `01_Research_Dossier.md` is not in the Stage 1 CONTEXT.md spec, but it exists in the real output and contains structural suggestions that influenced the Content Brief. The application must either:
- Treat it as valid and pass it to Stage 2 as advisory context
- Parse it separately from the 8 formal sections and store it in a `supplemental_notes` field

Ignoring it risks dropping real signal.

### 2.4 Unresolved Items Propagate Through Every Handoff

The four unresolved Brand Notes items from Pre-Stage 1 appear in every subsequent handoff (`01_Stage_2_Handoff.md` → `02_Stage_3_Handoff.md` → `03_Stage_4_Handoff.md` → ... → `06_Stage_7_Handoff.md`). They arrive in the QA Signoff as "Minor Observations." The application needs a first-class data structure for these, not just a text field that gets copy-pasted through handoffs.

### 2.5 QA Flags Are Traced Back to Specific Stages

In `06_QA_Signoff.md`, the third internal link FLAG is noted as `Stage responsible: client/publisher decision, not a pipeline failure.` This means the QA signoff distinguishes between:
- Pipeline failures (require re-running a stage)
- Client/publisher decisions (require human action outside the pipeline)

The application's QA decision model must represent both categories.

### 2.6 The HTML Output Deviates From the CONTEXT.md Spec in One Way

The CONTEXT.md for Stage 7 says "No external CSS or JS." The reference run's HTML imports Google Fonts from `fonts.googleapis.com`. This is a real client override that either overrides the spec or was not addressed by the spec. The application must store brand-level overrides that can modify stage behavior — the CSS token system in the HTML (`:root` custom properties) maps directly to values that would come from the Style Reference Card.

### 2.7 The SEO Annotation Sheet Contains Parseable Structured Data

The `Word Count Note` field in the annotation sheet contains the exact output of `word_count.py`: `2776 words | target: 2200-2800 | WITHIN TARGET`. This is a script result embedded in a markdown file. The application replaces this with a direct function call; the result is stored as structured data (`word_count: 2776`, `target_min: 2200`, `target_max: 2800`, `status: "within_target"`), not as a string.

---

## 3. Backend Architecture (Python OOP)

### 3.1 Module Organization

```
content_pipeline/
├── domain/
│   ├── client.py                 # Client, ClientReferenceFiles
│   ├── run.py                    # Run, RunContext, UnresolvedItem
│   ├── stage.py                  # StageOutput, QualityGateResult
│   ├── handoff.py                # HandoffDocument, CarryForwardContext
│   └── enums.py                  # StageStatus, RunStatus, AuthorityMode, etc.
├── parsing/                      # NEW — document parsing layer
│   ├── brief_parser.py           # Strips BRIEF tokens, preserves tables/lists
│   ├── dossier_parser.py         # Extracts 8 formal sections + supplemental notes
│   ├── handoff_parser.py         # Parses handoff structured fields
│   ├── seo_annotation_parser.py  # Extracts annotation sheet into structured fields
│   ├── qa_signoff_parser.py      # Parses signoff into scored sections
│   └── editorial_note_parser.py  # Extracts/strips editorial notes from humanized drafts
├── services/
│   ├── base_stage.py             # StageContract ABC
│   ├── onboarding_service.py
│   ├── run_init_service.py
│   ├── research_service.py
│   ├── source_validation_service.py
│   ├── brief_service.py
│   ├── writing_service.py
│   ├── humanization_service.py
│   ├── seo_service.py
│   ├── qa_service.py
│   └── formatting_service.py
├── orchestration/
│   ├── pipeline_orchestrator.py
│   ├── stage_router.py
│   └── unresolved_item_tracker.py  # NEW — tracks items across handoffs
├── llm/
│   ├── base_provider.py         # Abstract LLM interface + ProviderType enum
│   ├── anthropic_provider.py    # Anthropic (default)
│   ├── openrouter_provider.py   # OpenRouter via langchain-openrouter
│   ├── ollama_provider.py       # Self-hosted Ollama via langchain-ollama
│   ├── lmstudio_provider.py     # Self-hosted LM Studio via openai client
│   ├── provider_factory.py      # LLMProviderFactory — reads LLM_PROVIDER env var
│   └── prompt_builder.py        # Loads stage contracts; builds prompts
├── repositories/
│   ├── client_repository.py
│   ├── run_repository.py
│   ├── stage_output_repository.py
│   └── reference_file_repository.py
├── config/
│   ├── authority_model_loader.py
│   ├── anti_ai_rules.py
│   └── industry_configs/
├── api/
│   ├── clients.py
│   ├── runs.py
│   ├── stages.py
│   └── webhooks.py
└── workers/
    ├── stage_worker.py
    └── batch_worker.py
```

The `parsing/` module is the most critical addition relative to v1. Every stage output is a semi-structured markdown document with conventions that must be parsed reliably before the content can be stored or passed downstream.

### 3.2 Domain Models

```python
# domain/enums.py
from enum import Enum

class ClientState(Enum):
    NEW = "new"
    PARTIAL = "partial"
    FULLY_ONBOARDED = "fully_onboarded"

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"

class RunStatus(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    PUBLISHED = "published"

class AuthorityMode(Enum):
    NORMAL = "normal"
    EXPERT_FALLBACK = "expert_fallback"

class TopicPath(Enum):
    USER_PROVIDED = "user_provided"
    IDEATION = "ideation"

class QADecision(Enum):
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"

class QAIssueType(Enum):
    PIPELINE_FAILURE = "pipeline_failure"      # requires re-running a stage
    CLIENT_DECISION = "client_decision"         # requires human action outside pipeline
    MINOR_OBSERVATION = "minor_observation"     # non-blocking note for future improvement
```

```python
# domain/run.py
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from datetime import datetime
from .enums import RunStatus, TopicPath, AuthorityMode

@dataclass
class UnresolvedItem:
    """
    An open question that carries forward through every handoff.
    Confirmed in reference run: 4 items from Pre-Stage 1 appeared in
    every subsequent handoff and surfaced as Minor Observations in QA.
    """
    description: str
    blocks_run: bool        # True = hard stop; False = carry forward and monitor
    source_stage: int       # stage that raised it (0 = onboarding)
    resolved: bool = False
    resolved_at_stage: Optional[int] = None

@dataclass
class RunContext:
    """
    Immutable carry-forward context between stages.
    Structured from real handoff fields in the reference run.
    """
    client_id: UUID
    topic: str
    primary_keyword: str
    topic_path: TopicPath
    angle_notes_sanitized: Optional[str] = None    # never raw CRM text
    priority_sources: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = field(default_factory=list)
    authority_mode: AuthorityMode = AuthorityMode.NORMAL
    fallback_status: Optional[str] = None
    allowed_claims: list[str] = field(default_factory=list)
    disallowed_claims: list[str] = field(default_factory=list)
    # Populated by Stage 5, carried to Stage 6 and Stage 7
    article_slug: Optional[str] = None
    schema_recommendation: Optional[str] = None
    word_count_result: Optional[dict] = None       # {count, target_min, target_max, status}

@dataclass
class Run:
    id: UUID
    client_id: UUID
    folder_slug: str
    status: RunStatus
    context: RunContext
    current_stage: int
    created_at: datetime
    updated_at: datetime
    human_review_flag: Optional[str] = None
    dry_run: bool = False
```

```python
# domain/stage.py
from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from .enums import StageStatus, QADecision, QAIssueType

@dataclass
class QAIssue:
    section: str           # "A", "B", ... "I"
    issue_description: str
    issue_type: QAIssueType
    stage_responsible: Optional[int]   # None for client_decision or minor_observation

@dataclass
class QAResult:
    decision: QADecision
    checklist_score: tuple[int, int]   # (passed, total)
    ai_risk_score: int                 # /15
    section_results: dict[str, str]    # {"A": "PASS", "B": "FLAG", ...}
    issues: list[QAIssue]
    human_review_flag: Optional[str]
    revision_stage: Optional[int]      # earliest stage to re-run, if revision needed

@dataclass
class SEOAnnotation:
    """Parsed from the SEO Annotation Sheet in 05_SEO_Draft.md."""
    changes_summary: list[str]
    keyword_density: dict              # {keyword, occurrences, total_words, density_pct, status}
    meta_title: dict                   # {text, char_count, status}
    meta_description: dict             # {text, char_count, status}
    schema_recommendation: str
    internal_links: list[dict]         # [{anchor, destination, section}]
    readability_note: dict             # {target_level, status, flags}
    word_count: dict                   # {count, target_min, target_max, status}
    ai_search_alignment: str
    qa_flags: list[str]

@dataclass
class StageOutput:
    id: UUID
    run_id: UUID
    stage_number: int
    stage_name: str
    attempt: int
    status: StageStatus
    # Primary content — the article text at this stage
    article_content: Optional[str]
    # Appended sections (stored separately, never passed downstream)
    editorial_note: Optional[str]       # Stage 4 only
    seo_annotation: Optional[SEOAnnotation]  # Stage 5 only
    qa_result: Optional[QAResult]       # Stage 6 only
    # Next-stage handoff document
    handoff_content: Optional[str]
    # Quality gate results for this stage
    quality_gate_results: dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

### 3.3 The Parsing Layer

This is the module that v1 lacked. Every stage output is a markdown document with embedded structure. Parsing is required before storage and before passing content downstream.

```python
# parsing/brief_parser.py
import re
from dataclasses import dataclass

@dataclass
class ParsedBrief:
    keyword_strategy: dict
    audience_definition: str
    who_how_why: dict
    post_structure: list["HeadingNode"]  # tree of H1/H2/H3 with brief instructions stripped
    eeat_instructions: list[dict]
    style_directive: dict
    structural_specs: dict
    internal_linking: list[dict]
    cta_direction: dict
    author_credential: str
    content_table: Optional[str]    # the content types table, preserved verbatim

class BriefParser:
    """
    Parses 02_Content_Brief.md into structured fields.

    Key challenge: <!--BRIEF: ... --> blocks must be stripped from
    content that will become article copy, but the content types table
    that appears adjacent to BRIEF blocks must be preserved.

    Confirmed from reference run: the table in H3 "The Content Types
    That Work Best for Home Services" appears BETWEEN BRIEF comment blocks
    and must be carried forward to Stage 3 verbatim.
    """

    BRIEF_PATTERN = re.compile(r'<!--BRIEF:.*?-->', re.DOTALL)

    def parse(self, brief_markdown: str) -> ParsedBrief:
        # Split into named sections by ## headings
        sections = self._split_sections(brief_markdown)
        
        # Parse the post structure outline specially:
        # extract heading text, strip BRIEF instructions,
        # preserve non-BRIEF content (tables, lists)
        structure = self._parse_outline(sections.get("POST STRUCTURE OUTLINE", ""))
        
        # Extract the content types table before stripping
        content_table = self._extract_table(
            sections.get("POST STRUCTURE OUTLINE", "")
        )
        
        return ParsedBrief(
            keyword_strategy=self._parse_keyword_strategy(sections),
            audience_definition=sections.get("AUDIENCE DEFINITION", ""),
            who_how_why=self._parse_who_how_why(sections),
            post_structure=structure,
            eeat_instructions=self._parse_eeat(sections),
            style_directive=self._parse_style(sections),
            structural_specs=self._parse_specs(sections),
            internal_linking=self._parse_links(sections),
            cta_direction=self._parse_cta(sections),
            author_credential=sections.get("AUTHOR CREDENTIAL SIGNAL", ""),
            content_table=content_table,
        )

    def strip_brief_tokens(self, markdown: str) -> str:
        """
        Remove all <!--BRIEF: ... --> blocks.
        Used to produce the clean version passed to Stage 3.
        Does NOT remove tables, lists, or other structured content
        that appears adjacent to BRIEF blocks.
        """
        return self.BRIEF_PATTERN.sub("", markdown).strip()

    def _extract_table(self, section: str) -> Optional[str]:
        """Extract markdown table(s) from the outline section."""
        table_pattern = re.compile(r'(\|.+\|[\s\S]*?)(?=\n\n|\Z)', re.MULTILINE)
        tables = table_pattern.findall(section)
        return tables[0] if tables else None
```

```python
# parsing/seo_annotation_parser.py
import re
from domain.stage import SEOAnnotation

class SEOAnnotationParser:
    """
    Parses the ## SEO Annotation Sheet section from 05_SEO_Draft.md.
    
    The annotation sheet is structured data embedded in markdown prose.
    Confirmed format from reference run:
    - Word Count Note uses pipe-delimited format: "2776 words | target: 2200-2800 | WITHIN TARGET"
    - Keyword Density Report: "primary keyword / occurrences / total words / density %"
    - Internal Link Placements: numbered list, each "Anchor: X | Destination: Y | Section: Z"
    """

    ANNOTATION_SEPARATOR = "\n## SEO Annotation Sheet\n"
    WORD_COUNT_PATTERN = re.compile(
        r'(\d+) words \| target: (\d+)-(\d+) \| (WITHIN TARGET|OVER TARGET|UNDER TARGET)'
    )
    DENSITY_PATTERN = re.compile(
        r'"([^"]+)" — (\d+) occurrences / ([\d,]+) words = ([\d.]+)% density — (PASS|FLAG|FAIL)'
    )

    def split_article_and_annotation(self, seo_draft: str) -> tuple[str, str]:
        """
        Returns (article_body, annotation_sheet).
        The article body is what passes to Stage 6.
        The annotation sheet is parsed into SEOAnnotation and stored separately.
        """
        if self.ANNOTATION_SEPARATOR in seo_draft:
            parts = seo_draft.split(self.ANNOTATION_SEPARATOR, 1)
            return parts[0].rstrip(), parts[1]
        return seo_draft, ""

    def parse_annotation(self, annotation_text: str) -> SEOAnnotation:
        word_count = self._parse_word_count(annotation_text)
        keyword_density = self._parse_keyword_density(annotation_text)
        internal_links = self._parse_internal_links(annotation_text)
        qa_flags = self._parse_qa_flags(annotation_text)
        
        return SEOAnnotation(
            changes_summary=self._parse_changes_summary(annotation_text),
            keyword_density=keyword_density,
            meta_title=self._parse_meta_field("Meta Title", annotation_text),
            meta_description=self._parse_meta_field("Meta Description", annotation_text),
            schema_recommendation=self._parse_field("Schema Recommendation", annotation_text),
            internal_links=internal_links,
            readability_note=self._parse_readability(annotation_text),
            word_count=word_count,
            ai_search_alignment=self._parse_field("AI-Search Alignment", annotation_text),
            qa_flags=qa_flags,
        )

    def _parse_word_count(self, text: str) -> dict:
        match = self.WORD_COUNT_PATTERN.search(text)
        if match:
            return {
                "count": int(match.group(1)),
                "target_min": int(match.group(2)),
                "target_max": int(match.group(3)),
                "status": match.group(4).lower().replace(" ", "_"),
            }
        return {}
```

```python
# parsing/editorial_note_parser.py
import re

class EditorialNoteParser:
    """
    Extracts the ## Editorial Note from 04_Humanized_Draft.md and
    returns (article_body, editorial_note) as separate strings.
    
    The editorial note must NEVER appear in 05_SEO_Draft.md or any
    downstream file. Confirmed clean in reference run.
    """

    EDITORIAL_SEPARATOR = "\n## Editorial Note\n"

    def split(self, humanized_draft: str) -> tuple[str, Optional[str]]:
        if self.EDITORIAL_SEPARATOR in humanized_draft:
            parts = humanized_draft.split(self.EDITORIAL_SEPARATOR, 1)
            return parts[0].rstrip(), parts[1].strip()
        return humanized_draft, None
```

### 3.4 The Unresolved Item Tracker

This is a first-class service, not just a text field. Confirmed by the reference run where 4 items from Pre-Stage 1 propagated through all 7 stages.

```python
# orchestration/unresolved_item_tracker.py
from domain.run import UnresolvedItem
from repositories.run_repository import RunRepository

class UnresolvedItemTracker:
    """
    Manages the lifecycle of unresolved items across handoffs.
    Items are raised, carried forward, and resolved — or surface
    in the QA signoff as Minor Observations.
    """

    def __init__(self, run_repo: RunRepository):
        self._run_repo = run_repo

    def add_item(self, run_id, description: str, blocks_run: bool, source_stage: int):
        run = self._run_repo.get(run_id)
        item = UnresolvedItem(
            description=description,
            blocks_run=blocks_run,
            source_stage=source_stage,
        )
        run.context.unresolved_items.append(item)
        self._run_repo.save(run)

    def resolve_item(self, run_id, description: str, resolved_at_stage: int):
        run = self._run_repo.get(run_id)
        for item in run.context.unresolved_items:
            if item.description == description:
                item.resolved = True
                item.resolved_at_stage = resolved_at_stage
        self._run_repo.save(run)

    def blocking_items(self, run_id) -> list[UnresolvedItem]:
        run = self._run_repo.get(run_id)
        return [i for i in run.context.unresolved_items if i.blocks_run and not i.resolved]

    def open_items(self, run_id) -> list[UnresolvedItem]:
        run = self._run_repo.get(run_id)
        return [i for i in run.context.unresolved_items if not i.resolved]

    def for_handoff(self, run_id) -> str:
        """Render open items as the handoff section text."""
        items = self.open_items(run_id)
        if not items:
            return "None"
        return "\n".join(
            f"- {i.description} {'[BLOCKS RUN]' if i.blocks_run else '(non-blocking)'}"
            for i in items
        )
```

### 3.5 The Stage Contract and Key Implementations

```python
# services/base_stage.py
from abc import ABC, abstractmethod
from domain.run import Run
from domain.stage import StageOutput
from domain.enums import StageStatus

class StageContract(ABC):
    """
    Every stage implements this interface.
    The run() method is the public entry point and enforces the contract.
    """

    def __init__(self, repo, llm, parser, tracker):
        self._repo = repo
        self._llm = llm
        self._parser = parser
        self._tracker = tracker

    @property
    @abstractmethod
    def stage_number(self) -> int: ...

    @property
    @abstractmethod
    def stage_name(self) -> str: ...

    @abstractmethod
    def _check_prerequisites(self, run: Run) -> None:
        """Raise MissingPrerequisiteError if required predecessor outputs don't exist."""
        ...

    @abstractmethod
    def _load_context(self, run: Run) -> dict:
        """Load only the files in the stage's Load Before Starting contract."""
        ...

    @abstractmethod
    def _build_prompt(self, run: Run, context: dict) -> tuple[str, str]:
        """Returns (system_prompt, user_prompt)."""
        ...

    @abstractmethod
    def _parse_output(self, raw: str, run: Run) -> StageOutput:
        """
        Parse LLM output into a StageOutput domain object.
        This is where parsers from the parsing/ module are called.
        Separates article content from appended sections (editorial notes, annotations).
        """
        ...

    @abstractmethod
    def _validate_output(self, output: StageOutput, run: Run) -> list[str]:
        """Returns quality gate failures (empty = all pass)."""
        ...

    @abstractmethod
    def _build_handoff(self, run: Run, output: StageOutput, context: dict) -> str:
        """Produce the handoff document for the next stage."""
        ...

    def run(self, run: Run) -> StageOutput:
        self._check_prerequisites(run)
        context = self._load_context(run)
        system_prompt, user_prompt = self._build_prompt(run, context)
        raw = self._llm.complete(user_prompt, system=system_prompt)
        output = self._parse_output(raw, run)
        failures = self._validate_output(output, run)

        if failures:
            output.status = StageStatus.FAILED
            output.quality_gate_results["failures"] = failures
            return output

        output.handoff_content = self._build_handoff(run, output, context)
        output.status = StageStatus.COMPLETE
        self._repo.save(output)
        return output
```

```python
# services/humanization_service.py
from parsing.editorial_note_parser import EditorialNoteParser
from domain.stage import StageOutput
from domain.enums import StageStatus

class HumanizationStage(StageContract):
    """
    Stage 4. Confirmed behaviors from reference run:
    - Expands thin assertions with operational specificity
    - Varies FAQ answer lengths to break structural symmetry
    - Appends ## Editorial Note (stripped before Stage 5)
    - Uses geographic specificity (e.g., "Denver metro area") as experience signal
    """

    STAGE_NUMBER = 4
    STAGE_NAME = "humanization"

    def __init__(self, repo, llm, tracker):
        super().__init__(repo, llm, EditorialNoteParser(), tracker)

    def _parse_output(self, raw: str, run: Run) -> StageOutput:
        article_body, editorial_note = self._parser.split(raw)
        return StageOutput(
            run_id=run.id,
            stage_number=self.STAGE_NUMBER,
            stage_name=self.STAGE_NAME,
            attempt=self._repo.next_attempt(run.id, self.STAGE_NUMBER),
            status=StageStatus.RUNNING,
            article_content=article_body,
            editorial_note=editorial_note,    # stored in DB; never passed to Stage 5
            seo_annotation=None,
            qa_result=None,
            handoff_content=None,
            quality_gate_results={},
        )

    def _validate_output(self, output: StageOutput, run: Run) -> list[str]:
        failures = []
        article = output.article_content or ""

        if "—" in article:
            failures.append(f"Em dash found: {article.count('—')} occurrences")

        # Confirm editorial note was produced
        if not output.editorial_note:
            failures.append("Editorial Note section missing from humanized draft")

        # Confirm the editorial note mentions QA concern
        if output.editorial_note and "QA concern" not in output.editorial_note:
            failures.append("Editorial Note missing QA concern field")

        # Check for BRIEF token leakage
        if "<!--BRIEF:" in article:
            failures.append("BRIEF comment token found in humanized draft")

        return failures

    def _build_handoff(self, run: Run, output: StageOutput, context: dict) -> str:
        # Identify weak sections from the first draft handoff notes
        # (carried forward as "sections to prioritize" in Stage 3 handoff)
        weak_sections = context.get("stage3_handoff_weak_sections", [])

        return f"""# Stage 5 Handoff

Status: READY
Created by: Stage 4 - Humanization
Created: {datetime.utcnow().date()}
Client: {run.client_id}
Run: {run.folder_slug}

## Next Stage

- Stage: 5 - SEO
- Expected output: 05_SEO_Draft.md

## Load Instructions

Load in full:
- 04_Humanized_Draft.md
- 04_Stage_5_Handoff.md

Load sections only:
- 02_Content_Brief.md: Keyword Strategy, Internal Linking, Structural Specifications only
- Style_Reference_Card.md: Register and Reading Level sections only

Do not load:
- Audience_Profile.md, Brand_Notes.md, 01_Research_Dossier.md
- 03_First_Draft.md, _config/ files

## Carry Forward Context

- Topic: {run.context.topic}
- Primary keyword: {run.context.primary_keyword}
- No [AGENCY INPUT NEEDED] flags remain: {not self._has_agency_flags(output.article_content)}
- Unresolved items: {self._tracker.for_handoff(run.id)}

## Automation

- Auto-run next stage: {str(not bool(self._tracker.blocking_items(run.id))).lower()}
- Reason if false: {self._blocking_reason(run)}
"""
```

### 3.6 The QA Stage — Full Branching Model

```python
# services/qa_service.py
from domain.enums import QADecision, QAIssueType
from domain.stage import QAResult, QAIssue, StageOutput
from parsing.qa_signoff_parser import QASignoffParser

class QAStage(StageContract):
    STAGE_NUMBER = 6
    STAGE_NAME = "qa"
    AI_RISK_THRESHOLD = 10

    # From Root_Context.md revision routing table
    REVISION_ROUTING = {
        "factual_claim": 3, "ymyl": 3, "cta_missing": 3, "eeat": 3,
        "ai_sounding": 4, "voice_inconsistency": 4,
        "keyword_placement": 5, "meta_title": 5, "header_hierarchy": 5,
    }

    def run(self, run: Run) -> StageOutput:
        """
        Override base run() because QA produces multiple output files
        depending on the decision (APPROVED vs REVISION REQUIRED).
        """
        self._check_prerequisites(run)
        context = self._load_context(run)
        system, user = self._build_prompt(run, context)
        raw_signoff = self._llm.complete(user, system=system)
        
        qa_result = self._parse_qa_result(raw_signoff)
        approved_draft = self._produce_approved_draft(
            context["seo_draft"], qa_result
        ) if qa_result.decision == QADecision.APPROVED else None

        output = StageOutput(
            run_id=run.id,
            stage_number=self.STAGE_NUMBER,
            stage_name=self.STAGE_NAME,
            attempt=self._repo.next_attempt(run.id, self.STAGE_NUMBER),
            status=StageStatus.COMPLETE,
            article_content=approved_draft,    # clean; no annotation sheets
            editorial_note=None,
            seo_annotation=None,
            qa_result=qa_result,
            handoff_content=self._build_handoff(run, qa_result) if approved_draft else None,
            quality_gate_results={
                "decision": qa_result.decision.value,
                "checklist_score": qa_result.checklist_score,
                "ai_risk_score": qa_result.ai_risk_score,
                "section_results": qa_result.section_results,
                "revision_stage": qa_result.revision_stage,
                "human_review_flag": qa_result.human_review_flag,
            },
        )

        self._repo.save(output)
        return output

    def _produce_approved_draft(self, seo_draft: str, qa_result: QAResult) -> str:
        """
        Strip the SEO Annotation Sheet from the SEO draft.
        Confirmed: the QA Approved Draft is the SEO draft body only.
        No other content changes are made at Stage 6.
        """
        from parsing.seo_annotation_parser import SEOAnnotationParser
        parser = SEOAnnotationParser()
        article_body, _ = parser.split_article_and_annotation(seo_draft)
        return article_body

    def _parse_qa_result(self, raw: str) -> QAResult:
        """
        Parse the LLM-produced QA signoff into a structured QAResult.
        
        Confirmed format from reference run:
        - Section F had a FLAG with "Stage responsible: client/publisher decision"
        - This is QAIssueType.CLIENT_DECISION, not a pipeline failure
        - The distinction must be preserved in the domain model
        """
        # QASignoffParser handles the structured signoff format
        parsed = QASignoffParser().parse(raw)
        
        issues = []
        for raw_issue in parsed.get("issues", []):
            issue_type = self._classify_issue(raw_issue["stage_responsible"])
            issues.append(QAIssue(
                section=raw_issue["section"],
                issue_description=raw_issue["description"],
                issue_type=issue_type,
                stage_responsible=raw_issue.get("stage_num"),
            ))

        blocking = [i for i in issues if i.issue_type == QAIssueType.PIPELINE_FAILURE]
        revision_stage = self._compute_revision_stage(blocking) if blocking else None

        return QAResult(
            decision=QADecision(parsed["approval_status"].lower()),
            checklist_score=parsed["checklist_score"],
            ai_risk_score=parsed["ai_risk_score"],
            section_results=parsed["section_results"],
            issues=issues,
            human_review_flag=parsed.get("human_review_flag"),
            revision_stage=revision_stage,
        )

    def _classify_issue(self, stage_responsible_text: str) -> QAIssueType:
        """
        From reference run: "client/publisher decision, not a pipeline failure"
        maps to CLIENT_DECISION. Stage numbers map to PIPELINE_FAILURE.
        "Minor Observations" map to MINOR_OBSERVATION.
        """
        if stage_responsible_text is None:
            return QAIssueType.MINOR_OBSERVATION
        text = stage_responsible_text.lower()
        if "client" in text or "publisher" in text:
            return QAIssueType.CLIENT_DECISION
        if any(str(n) in text for n in range(1, 8)):
            return QAIssueType.PIPELINE_FAILURE
        return QAIssueType.MINOR_OBSERVATION

    def _compute_revision_stage(self, blocking_issues: list[QAIssue]) -> Optional[int]:
        earliest = 7
        for issue in blocking_issues:
            for keyword, stage in self.REVISION_ROUTING.items():
                if keyword in issue.issue_description.lower():
                    earliest = min(earliest, stage)
        return earliest if earliest < 7 else None
```

---

## 4. Frontend Structure (Next.js)

### 4.1 Page Organization

```
app/
├── (auth)/login/
├── dashboard/page.tsx                    # All clients + recent runs
├── clients/
│   ├── new/page.tsx                      # Stage 0 onboarding form
│   └── [clientId]/
│       ├── page.tsx                      # Client overview (server component)
│       ├── reference/page.tsx            # Style Card / Audience / Brand Notes tabs
│       └── runs/
│           ├── new/page.tsx              # Pre-Stage 1: Path A or Path B
│           └── [runId]/
│               ├── page.tsx              # Run overview + stage progress (server)
│               ├── research/page.tsx     # Stage 1 output
│               ├── brief/page.tsx        # Stage 2 — brief with BRIEF tokens hidden
│               ├── draft/page.tsx        # Stage 3 output
│               ├── humanized/page.tsx    # Stage 4 — article + editorial note panel
│               ├── seo/page.tsx          # Stage 5 — article + annotation sheet panel
│               ├── qa/page.tsx           # Stage 6 — checklist, decision, signoff
│               └── publish/page.tsx      # Stage 7 — HTML preview + download
```

### 4.2 Key Component Decisions Derived From Real Outputs

**`BriefViewer` (Stage 2):** The brief contains `<!--BRIEF: ... -->` tokens that must never be shown to the article reviewer. The component renders the article outline with BRIEF instructions collapsed into disclosure toggles ("View writing instruction for this section"). This gives editors a choice to see them but keeps the published-content view clean.

**`DraftDiffViewer` (Stages 3–5):** Since the real content changes between stages are small (confirmed by comparing Stage 3 and Stage 6 approved draft), show a diff view by default — not just the current draft. This is far more useful to reviewers than reading the full article again.

**`EditorialNotePanel` (Stage 4):** The editorial note is a separate panel alongside the article view, not embedded in it. It maps directly to the five fields confirmed in the reference run: Structural changes, Rhythm, Experience additions, E-E-A-T, QA concern. The "QA concern" field is highlighted in amber as a human action item.

**`SEOAnnotationPanel` (Stage 5):** The annotation sheet is rendered as a structured sidebar, not as appended prose. The word count result (`2776 words | target: 2200-2800 | WITHIN TARGET`) is displayed as a status chip. The `Flags for QA Agent` items are rendered as a checklist that carries into Stage 6.

**`QASignoffView` (Stage 6):** Two-column layout: left column is the section-by-section checklist (A through I), right column is the issue list. Issues are categorized with different visual treatments: PIPELINE_FAILURE (red, requires action), CLIENT_DECISION (amber, requires client confirmation), MINOR_OBSERVATION (gray, FYI). The AI Detection Risk Score is displayed as a gauge (5/15 = green).

**`HTMLPreview` (Stage 7):** iframe rendering of `07_Blog_Final.html`. Viewport switcher at 375px (mobile), 768px (tablet), 1280px (desktop). Download button for the HTML file. Secondary download for the markdown companion file.

### 4.3 Unresolved Items UI

Confirmed from the reference run that unresolved items persist across all stages. In the UI:

- A persistent `UnresolvedItemsDrawer` is accessible from any stage view
- Items are listed with source stage, description, blocking status, and resolution state
- Client-decision items that surface in QA are linked back to their origin
- Items are not auto-resolved; an editor must explicitly mark them resolved

### 4.4 Server vs. Client Components

**Server components** (data fetching only, no interactivity):
- `app/clients/[clientId]/page.tsx` — client + run list
- `app/clients/[clientId]/runs/[runId]/page.tsx` — run state + all stage summaries
- `app/clients/[clientId]/reference/page.tsx` — reference file content

**Client components** (streaming, interaction, polling):
- All stage execution views (stream LLM output via SSE)
- `BriefViewer` (BRIEF token toggle interaction)
- `DraftDiffViewer` (diff calculation in browser)
- `QASignoffView` (interactive checklist with resolution marking)
- `UnresolvedItemsDrawer` (persistent across navigation)

---

## 5. Database Schema (Supabase)

### 5.1 Core Tables

```sql
-- Clients
CREATE TABLE clients (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  website_url   TEXT,
  industry      TEXT,
  service_area  TEXT,
  off_limits    TEXT[],
  -- CSS token overrides that modify Stage 7 behavior
  -- (reference run uses Google Fonts despite "no external CSS" spec)
  style_overrides JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Client reference files
CREATE TABLE client_reference_files (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id             UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  style_reference_card  TEXT,
  audience_profile      TEXT,
  brand_notes           TEXT,
  onboarding_state      TEXT NOT NULL DEFAULT 'new'
    CHECK (onboarding_state IN ('new', 'partial', 'fully_onboarded')),
  -- Parsed brand colors for Stage 7 CSS token replacement
  brand_colors          JSONB DEFAULT '{}',
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Runs
CREATE TABLE runs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  folder_slug       TEXT NOT NULL,
  topic             TEXT NOT NULL,
  primary_keyword   TEXT NOT NULL,
  topic_path        TEXT NOT NULL CHECK (topic_path IN ('user_provided', 'ideation')),
  status            TEXT NOT NULL DEFAULT 'initiated'
    CHECK (status IN ('initiated','in_progress','approved','revision_required','published')),
  current_stage     INTEGER NOT NULL DEFAULT 0,
  dry_run           BOOLEAN DEFAULT FALSE,
  -- Sanitized context (never raw CRM)
  angle_notes       TEXT,
  priority_sources  TEXT[],
  internal_links    TEXT[],
  -- Authority mode from source validation
  authority_mode    TEXT NOT NULL DEFAULT 'normal'
    CHECK (authority_mode IN ('normal', 'expert_fallback')),
  fallback_status   TEXT,
  allowed_claims    TEXT[],
  disallowed_claims TEXT[],
  -- Populated by Stage 5, used by Stage 7
  article_slug      TEXT,
  schema_type       TEXT,
  word_count_result JSONB,     -- {count, target_min, target_max, status}
  human_review_flag TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id, folder_slug)
);

-- Unresolved items (first-class, not embedded in handoff text)
CREATE TABLE unresolved_items (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id             UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  description        TEXT NOT NULL,
  blocks_run         BOOLEAN NOT NULL DEFAULT FALSE,
  source_stage       INTEGER NOT NULL,
  resolved           BOOLEAN NOT NULL DEFAULT FALSE,
  resolved_at_stage  INTEGER,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Stage outputs
CREATE TABLE stage_outputs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id            UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  stage_number      INTEGER NOT NULL,   -- 0,10,1,15,2,3,4,5,6,7,11
  stage_name        TEXT NOT NULL,
  attempt           INTEGER NOT NULL DEFAULT 1,
  status            TEXT NOT NULL
    CHECK (status IN ('pending','running','complete','failed','awaiting_human')),
  -- Primary article content at this stage (clean; no appended sections)
  article_content   TEXT,
  -- Appended sections stored separately, never passed downstream
  editorial_note    TEXT,               -- Stage 4 only
  seo_annotation    JSONB,              -- Stage 5 only (parsed from annotation sheet)
  qa_result         JSONB,              -- Stage 6 only (parsed signoff)
  -- Next-stage handoff document
  handoff_content   TEXT,
  -- Quality gate results
  quality_gate_results JSONB DEFAULT '{}',
  error_message     TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  completed_at      TIMESTAMPTZ,
  UNIQUE(run_id, stage_number, attempt)
);

-- Structured SEO annotation (denormalized from stage_outputs.seo_annotation for querying)
CREATE TABLE seo_annotations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage_output_id   UUID NOT NULL REFERENCES stage_outputs(id) ON DELETE CASCADE,
  run_id            UUID NOT NULL REFERENCES runs(id),
  meta_title        TEXT,
  meta_title_chars  INTEGER,
  meta_description  TEXT,
  meta_desc_chars   INTEGER,
  word_count        INTEGER,
  target_min        INTEGER,
  target_max        INTEGER,
  word_count_status TEXT,     -- within_target, over_target, under_target
  keyword_density   NUMERIC,  -- percentage
  schema_type       TEXT,
  qa_flags          TEXT[],   -- carry forward to QA
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- QA results (denormalized for querying)
CREATE TABLE qa_results (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage_output_id   UUID NOT NULL REFERENCES stage_outputs(id) ON DELETE CASCADE,
  run_id            UUID NOT NULL REFERENCES runs(id),
  decision          TEXT NOT NULL CHECK (decision IN ('approved', 'revision_required')),
  checklist_passed  INTEGER,
  checklist_total   INTEGER,
  ai_risk_score     INTEGER,
  section_a         TEXT, section_b TEXT, section_c TEXT, section_d TEXT,
  section_e         TEXT, section_f TEXT, section_g TEXT, section_h TEXT, section_i TEXT,
  revision_stage    INTEGER,
  human_review_flag TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- QA issues (one row per issue in the signoff)
CREATE TABLE qa_issues (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  qa_result_id     UUID NOT NULL REFERENCES qa_results(id) ON DELETE CASCADE,
  run_id           UUID NOT NULL REFERENCES runs(id),
  section          TEXT NOT NULL,
  description      TEXT NOT NULL,
  issue_type       TEXT NOT NULL
    CHECK (issue_type IN ('pipeline_failure','client_decision','minor_observation')),
  stage_responsible INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Published articles
CREATE TABLE published_articles (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id            UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  client_id         UUID NOT NULL REFERENCES clients(id),
  article_slug      TEXT NOT NULL,
  title_tag         TEXT,
  meta_description  TEXT,
  primary_keyword   TEXT,
  html_content      TEXT,
  markdown_content  TEXT,
  published_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id, article_slug)
);

-- Topic recommendations (Path B ideation)
CREATE TABLE topic_recommendations (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id           UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  recommendation_n INTEGER NOT NULL,
  topic            TEXT NOT NULL,
  primary_keyword  TEXT NOT NULL,
  why_now          TEXT,
  audience_intent  TEXT,
  eeat_angle       TEXT,
  selected         BOOLEAN DEFAULT FALSE,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Run log (append-only; mirrors Run_Log.md format)
CREATE TABLE run_log (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id     UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  stage_name TEXT,
  entry      TEXT NOT NULL,
  logged_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Client-level run log (summary index; mirrors client-level Run_Log.md)
CREATE TABLE client_run_log (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id  UUID NOT NULL REFERENCES clients(id),
  run_id     UUID REFERENCES runs(id),
  entry      TEXT NOT NULL,
  logged_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 Key Indexes

```sql
CREATE INDEX idx_runs_client ON runs(client_id);
CREATE INDEX idx_runs_keyword ON runs(primary_keyword);
CREATE INDEX idx_stage_outputs_run ON stage_outputs(run_id, stage_number);
CREATE INDEX idx_unresolved_run ON unresolved_items(run_id, resolved);
CREATE INDEX idx_published_client ON published_articles(client_id);
CREATE INDEX idx_published_keyword ON published_articles(primary_keyword);
CREATE INDEX idx_qa_issues_run ON qa_issues(run_id, issue_type);
CREATE INDEX idx_run_log_run ON run_log(run_id, logged_at DESC);
```

### 5.3 Diff Storage Strategy

Since real stage outputs differ minimally (Stage 3 to Stage 6 showed word-level changes across a few paragraphs), store diffs rather than full copies:

```sql
-- Stage content diffs
CREATE TABLE stage_content_diffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id          UUID NOT NULL REFERENCES runs(id),
  from_stage      INTEGER NOT NULL,
  to_stage        INTEGER NOT NULL,
  diff_format     TEXT DEFAULT 'unified',
  diff_content    TEXT NOT NULL,    -- unified diff format
  additions       INTEGER,
  deletions       INTEGER,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

Full article content is stored at Stage 3 (first draft) and Stage 6 (approved draft). Diffs bridge the stages between them.

---

## 6. API Layer

### 6.1 Endpoint Structure

```
# Client management
POST   /clients                                    # Create client
GET    /clients                                    # List clients (with run counts)
GET    /clients/{client_id}                        # Client + reference file state
POST   /clients/{client_id}/onboard               # Stage 0: generate reference files
GET    /clients/{client_id}/reference             # Get all three reference files
PUT    /clients/{client_id}/reference/{file_type} # Update one reference file

# Run initialization
POST   /clients/{client_id}/runs                  # Pre-Stage 1: init new run
GET    /clients/{client_id}/runs                  # List runs
POST   /clients/{client_id}/runs/{run_id}/topic-recommendations  # Path B ideation
POST   /clients/{client_id}/runs/{run_id}/confirm-topic          # Lock topic/keyword

# Stage execution
POST   /runs/{run_id}/stages/{stage_num}/execute  # Execute a stage (async)
GET    /runs/{run_id}/stages/{stage_num}/output   # Get stage output
GET    /runs/{run_id}/stages/{stage_num}/stream   # SSE streaming for long stages

# Stage-specific queries
GET    /runs/{run_id}/stages/5/annotation         # SEO annotation sheet (structured)
GET    /runs/{run_id}/stages/6/signoff            # QA signoff (structured)
GET    /runs/{run_id}/stages/6/approved-draft     # Clean approved draft (no appended sections)

# QA decisions and revisions
POST   /runs/{run_id}/qa/decision                 # Submit APPROVED or REVISION REQUIRED
POST   /runs/{run_id}/issues/{issue_id}/resolve   # Mark unresolved item as resolved
GET    /runs/{run_id}/issues                      # All unresolved items for a run

# Publishing
GET    /runs/{run_id}/html-preview                # Stage 7 HTML preview
POST   /runs/{run_id}/publish                     # Finalize (write to published_articles)
GET    /clients/{client_id}/published             # Published articles (for overlap check)

# Async job tracking
GET    /jobs/{job_id}                             # Poll job status
```

### 6.2 Request/Response Shapes

#### `GET /runs/{run_id}/stages/5/annotation`

```json
{
  "stage_output_id": "uuid",
  "completed_at": "2026-06-22T14:33:00Z",
  "changes_summary": [
    "Added primary keyword into first 100 words",
    "Confirmed local SEO strategy anchor text in Month 2",
    "Confirmed AI Overviews link in FAQ answer 5"
  ],
  "meta_title": {
    "text": "Content Marketing for Home Service Businesses | Rank Rise",
    "char_count": 57,
    "status": "pass"
  },
  "meta_description": {
    "text": "Discover how content marketing helps home service businesses generate organic leads, rank in Google's local map pack, and reduce paid ad dependency.",
    "char_count": 153,
    "status": "pass"
  },
  "word_count": {
    "count": 2776,
    "target_min": 2200,
    "target_max": 2800,
    "status": "within_target"
  },
  "keyword_density": {
    "keyword": "content marketing for home service businesses",
    "occurrences": 5,
    "total_words": 2776,
    "density_pct": 0.18,
    "status": "pass"
  },
  "schema_recommendation": "FAQ schema (5 Q&A pairs) + Article schema",
  "internal_links": [
    {
      "anchor": "Google AI Overviews for home services queries",
      "destination": "/blog/google-ai-overviews-home-services-3-moves-for-2026",
      "section": "FAQ answer 5",
      "confirmed": true
    },
    {
      "anchor": "local SEO strategy",
      "destination": "/services/local-seo/",
      "section": "Month 2 framework",
      "confirmed": false,
      "note": "URL slug requires client confirmation"
    }
  ],
  "readability": {
    "target_grade": "8th-10th",
    "actual_grade": "8th-9th",
    "status": "pass"
  },
  "ai_search_alignment": "pass",
  "qa_flags": [
    "Confirm /services/local-seo/ URL is live on rankrisemarketing.com",
    "Confirm third internal link destination",
    "Confirm brand capitalization: Rank Rise vs Rankrise in CTA",
    "Confirm preferred byline"
  ]
}
```

#### `GET /runs/{run_id}/stages/6/signoff`

```json
{
  "qa_result_id": "uuid",
  "client_id": "uuid",
  "run_folder": "Content_Marketing_Home_Services_2026-06",
  "primary_keyword": "content marketing for home service businesses",
  "decision": "approved",
  "checklist_passed": 38,
  "checklist_total": 39,
  "ai_risk_score": 5,
  "ai_risk_max": 15,
  "human_review_flag": null,
  "section_results": {
    "A": "pass", "B": "pass", "C": "pass", "D": "pass",
    "E": "pass", "F": "flag", "G": "pass", "H": "pass", "I": "pass"
  },
  "issues": [
    {
      "section": "F",
      "description": "Third internal link destination not confirmed. Brief specified 2–3 internal links; two are present and confirmed.",
      "issue_type": "client_decision",
      "stage_responsible": null,
      "blocking": false
    }
  ],
  "minor_observations": [
    "Byline reads 'Content Team, Rankrise Marketing' — confirm preferred byline style",
    "Brand capitalization in CTA uses 'Rank Rise' (two words) — verify site usage",
    "/services/local-seo/ URL slug should be verified before final HTML output",
    "FAQ schema requires developer attention during WordPress upload"
  ],
  "next_stage": 7,
  "revision_stage": null
}
```

#### `POST /runs/{run_id}/qa/decision`

```json
// Request
{
  "decision": "approved"  // or "revision_required"
}

// Response — approved
{
  "decision": "approved",
  "next_stage": 7,
  "human_review_flag": null,
  "client_decision_items": [
    "Third internal link destination requires client confirmation before publishing"
  ]
}

// Response — revision required
{
  "decision": "revision_required",
  "revision_stage": 4,
  "revision_reason": "Voice inconsistency in FAQ section",
  "blocking_issues": ["..."],
  "next_stage": 4
}
```

### 6.3 Consistent Error Shape

```json
{
  "error": "MISSING_PREREQUISITE",
  "message": "Stage 1 must complete before Stage 2 can run.",
  "detail": {
    "required_stage": 1,
    "required_output": "01_Research_Dossier"
  }
}
```

Error codes: `MISSING_PREREQUISITE`, `CLIENT_NOT_ONBOARDED`, `OVERLAP_DETECTED`, `SOURCE_VALIDATION_REJECTED`, `QUALITY_GATE_FAILURE`, `BRIEF_TOKEN_LEAKED`, `INTERNAL_TOKEN_IN_DRAFT`, `QA_REVISION_REQUIRED`, `STAGE_7_BLOCKED_BY_REVISION`.

---

## 7. Migration Path

### 7.1 Guiding Principle

The reference run is the benchmark. For each phase, the acceptance criterion is: given the same client reference files and topic input, the application produces stage outputs that are structurally and substantively equivalent to the reference run outputs.

### 7.2 Phase Sequence

#### Phase 1 — Foundation (Weeks 1–2)
- Supabase schema (all tables, including `provider_settings`)
- Domain models with `UnresolvedItem` as first-class type
- `ClientRepository`, `RunRepository`, `StageOutputRepository`
- All four LLM providers: `AnthropicProvider`, `OpenRouterProvider`, `OllamaProvider`, `LMStudioProvider`
- `LLMProviderFactory` — reads `LLM_PROVIDER` env var; stage services use this, never individual providers
- `PROVIDER_QUALITY_TOLERANCES` in `config/provider_config.py`
- `StageContract` base class
- FastAPI skeleton
- Next.js shell
- **Acceptance:** Create Rankrise_Marketing client via API; confirm it persists. Confirm `LLMProviderFactory` returns correct provider type for all four `LLM_PROVIDER` values. Confirm no stage service imports a provider class directly.

#### Phase 2 — Parsing Layer (Weeks 3–4)
*Build before any stage service — parsers are required by every stage.*

- `BriefParser` with BRIEF token stripping and table preservation
- `DossierParser` including `supplemental_notes` field
- `HandoffParser` for structured handoff field extraction
- `SEOAnnotationParser` with word count parsing
- `EditorialNoteParser`
- `QASignoffParser`
- **Acceptance:** Parse all 16 reference run files correctly; confirm content types table is preserved by `BriefParser`; confirm word count `2776 | 2200-2800 | WITHIN TARGET` is parsed to `{count: 2776, target_min: 2200, target_max: 2800, status: "within_target"}`

#### Phase 3 — Onboarding (Weeks 5–6)
- `OnboardingStage` with client state detection
- `UnresolvedItemTracker` service
- `POST /clients/{client_id}/onboard` endpoint
- Onboarding form UI
- **Acceptance:** Run Stage 0 for a test client; compare Style Reference Card, Audience Profile, Brand Notes structure to Rankrise_Marketing reference files

#### Phase 4 — Run Initialization (Week 7)
- Overlap check against `published_articles`
- Topic recommendation generation (Path B)
- `POST /clients/{client_id}/runs` and topic recommendation endpoints
- Run init UI (Path A / Path B)
- **Acceptance:** Initiate a run via both paths; confirm overlap detection; verify `UnresolvedItem`