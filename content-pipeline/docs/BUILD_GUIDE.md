# Content Pipeline — Build Guide

**What this is:** Implementation specification for converting a prompt-driven blog production workflow into a Python/Next.js/Supabase application. Hand this to the team to begin building.

**What this is not:** A redesign. The workflow logic is preserved exactly. This is a refactor for maintainability, scalability, and reliability.

**Read alongside:** `REFERENCE.md` — data models, schema, API contracts, and code sketches.

---

## The System in One Paragraph

A multi-client blog production pipeline. Each article moves through 8 sequential stages: Onboarding (once per client), Run Init, Research, Source Validation, Brief, Writing, Humanization, SEO, QA, and Blog Formatting. Each stage has defined inputs, defined outputs, and quality gates that must pass before the next stage can run. The application replaces a folder-of-markdown-files system with a proper backend, database, and UI — but every rule, constraint, and quality gate from the original system is preserved exactly.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python + FastAPI | Async-native; matches gpt-researcher's async model |
| Worker queue | ARQ (not Celery) | Natively async; LLM stage calls are long-running async tasks |
| LLM | Anthropic (default), OpenRouter, Ollama, LM Studio | Switchable via `LLM_PROVIDER` env var; factory pattern isolates stage services from provider choice |
| Research engine | gpt-researcher library | Replaces hand-rolled scraping and source curation |
| Database | Supabase (Postgres) | Auth, RLS, and realtime built in |
| Frontend | Next.js | Server components for read-heavy views; client components for streaming |
| CSS | Inlined from `blog_integration_base.css` with brand token injection | Stage 7 output requirement |

---

## Module Structure

```
content_pipeline/
├── domain/              # Pure domain models — no I/O, no DB
│   ├── enums.py         # All enums: StageStatus, RunStatus, AuthorityMode, etc.
│   ├── client.py        # Client, ClientReferenceFiles, UnresolvedItem
│   ├── run.py           # Run, RunContext
│   └── stage.py         # StageOutput, QAResult, SEOAnnotation, ValidationReport
├── parsing/             # Document parsing — every stage output is semi-structured markdown
│   ├── brief_parser.py          # Strips BRIEF tokens; preserves tables
│   ├── dossier_parser.py        # 8 formal sections + supplemental_notes
│   ├── handoff_parser.py        # Structured handoff field extraction
│   ├── seo_annotation_parser.py # Splits article body from annotation sheet
│   ├── editorial_note_parser.py # Splits article body from editorial note
│   └── qa_signoff_parser.py     # Parses scored signoff into QAResult
├── services/            # One class per pipeline stage
│   ├── base_stage.py            # StageContract ABC
│   ├── onboarding_service.py    # Stage 0
│   ├── run_init_service.py      # Pre-Stage 1
│   ├── research_service.py      # Stage 1 — wraps gpt-researcher
│   ├── source_validation_service.py  # Stage 1.5 — wraps gpt-researcher SourceCurator
│   ├── brief_service.py         # Stage 2
│   ├── writing_service.py       # Stage 3
│   ├── humanization_service.py  # Stage 4
│   ├── seo_service.py           # Stage 5
│   ├── qa_service.py            # Stage 6
│   └── formatting_service.py    # Stage 7
├── orchestration/
│   ├── pipeline_orchestrator.py      # Drives sequential execution
│   ├── context_assembler.py          # Builds live CONTEXT.md equivalent from DB
│   ├── unresolved_item_tracker.py    # Tracks open items across handoffs
│   └── claim_repositioner.py         # Applies fallback repositioning rules
├── llm/
│   ├── base_provider.py         # Abstract LLM interface + ProviderType enum
│   ├── anthropic_provider.py    # Anthropic implementation
│   ├── openrouter_provider.py   # OpenRouter via langchain-openrouter
│   ├── ollama_provider.py       # Self-hosted Ollama via langchain-ollama
│   ├── lmstudio_provider.py     # Self-hosted LM Studio via openai client
│   ├── provider_factory.py      # LLMProviderFactory — only place provider selection lives
│   └── prompt_builder.py        # Loads stage contracts; builds prompts
├── repositories/        # All DB access
│   ├── client_repository.py
│   ├── run_repository.py
│   ├── stage_output_repository.py
│   ├── reference_file_repository.py
│   └── authority_model_repository.py
├── config/
│   ├── authority_model_loader.py   # Loads industry config + client overrides
│   └── provider_config.py          # PROVIDER_QUALITY_TOLERANCES per provider
└── api/                 # FastAPI routers
    ├── clients.py
    ├── runs.py
    └── stages.py
```

---

## The Parsing Layer — Build This First

Before any stage service, build the parsers. Every stage output is a semi-structured markdown document. Without parsers, stage outputs can't be stored correctly or passed downstream safely.

**Why this matters:** The Content Brief contains `<!--BRIEF: ... -->` multi-line instruction tokens that must be stripped before Stage 3 receives it. A content types table appears *between* those tokens and must be preserved. The SEO draft appends an annotation sheet after `---` that must never appear in the QA-approved draft. The humanized draft appends an editorial note the same way. These are not edge cases — they're the normal output format of every production run.

### `BriefParser` — the most complex

```python
# parsing/brief_parser.py
import re
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ParsedBrief:
    keyword_strategy: dict
    audience_definition: str
    who_how_why: dict
    post_structure: list          # heading tree with brief instructions stripped
    content_table: Optional[str]  # preserved verbatim for Stage 3
    eeat_instructions: list[dict]
    style_directive: dict
    structural_specs: dict
    internal_linking: list[dict]
    cta_direction: dict
    author_credential: str

class BriefParser:
    # Multi-line BRIEF blocks — re.DOTALL is required
    BRIEF_PATTERN = re.compile(r'<!--BRIEF:.*?-->', re.DOTALL)
    # Markdown tables
    TABLE_PATTERN = re.compile(
        r'(\|[^\n]+\|\n\|[-| :]+\|\n(?:\|[^\n]+\|\n)*)', re.MULTILINE
    )

    def strip_brief_tokens(self, markdown: str) -> str:
        """
        Remove <!--BRIEF: ... --> blocks. Preserve everything else including
        tables that appear between BRIEF blocks.
        Confirmed: the content types table in the reference run brief sits
        between two BRIEF blocks and must survive stripping.
        """
        stripped = self.BRIEF_PATTERN.sub("", markdown)
        return re.sub(r'\n{3,}', '\n\n', stripped).strip()

    def extract_content_table(self, outline_section: str) -> Optional[str]:
        tables = self.TABLE_PATTERN.findall(outline_section)
        return tables[0].strip() if tables else None
```

### `SEOAnnotationParser` — splits article from annotation sheet

```python
# parsing/seo_annotation_parser.py
import re

class SEOAnnotationParser:
    SEPARATOR = "\n## SEO Annotation Sheet\n"
    WORD_COUNT_PATTERN = re.compile(
        r'(\d+) words \| target: (\d+)-(\d+) \| (WITHIN TARGET|OVER TARGET|UNDER TARGET)'
    )

    def split(self, seo_draft: str) -> tuple[str, str]:
        """Returns (article_body, annotation_sheet). Confirmed format from reference run."""
        if self.SEPARATOR in seo_draft:
            parts = seo_draft.split(self.SEPARATOR, 1)
            return parts[0].rstrip(), parts[1]
        return seo_draft, ""

    def parse_word_count(self, annotation: str) -> dict:
        """
        Parses: "2776 words | target: 2200-2800 | WITHIN TARGET"
        Returns: {count: 2776, target_min: 2200, target_max: 2800, status: "within_target"}
        The old system produced this string from word_count.py.
        The application produces it directly and stores as structured JSONB.
        """
        m = self.WORD_COUNT_PATTERN.search(annotation)
        if m:
            return {
                "count": int(m.group(1)),
                "target_min": int(m.group(2)),
                "target_max": int(m.group(3)),
                "status": m.group(4).lower().replace(" ", "_"),
            }
        return {}
```

### `EditorialNoteParser` — strips Stage 4's appended note

```python
# parsing/editorial_note_parser.py

class EditorialNoteParser:
    SEPARATOR = "\n## Editorial Note\n"

    def split(self, humanized_draft: str) -> tuple[str, Optional[str]]:
        """
        Returns (article_body, editorial_note).
        The editorial note is stored in stage_outputs.editorial_note.
        It is NEVER passed to Stage 5 or any downstream stage.
        Confirmed clean in reference run (zero leakage to SEO draft or HTML).
        """
        if self.SEPARATOR in humanized_draft:
            parts = humanized_draft.split(self.SEPARATOR, 1)
            return parts[0].rstrip(), parts[1].strip()
        return humanized_draft, None
```

**Acceptance test for parsers:** Run all parsers against the reference run files. Confirm:
- `BriefParser.strip_brief_tokens()` on `02_Content_Brief.md` → content types table is still present
- `SEOAnnotationParser.split()` on `05_SEO_Draft.md` → word count parses to `{count: 2776, target_min: 2200, target_max: 2800, status: "within_target"}`
- `EditorialNoteParser.split()` on `04_Humanized_Draft.md` → editorial note has 5 sections: Structural changes, Rhythm, Experience additions, E-E-A-T, QA concern

---

## The Stage Contract — Base Class Every Stage Extends

```python
# services/base_stage.py
from abc import ABC, abstractmethod

class StageContract(ABC):
    """
    Every pipeline stage implements this interface.
    The execution order is fixed: check prerequisites → load context →
    build prompt → call LLM → parse output → validate → build handoff.
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
    def _check_prerequisites(self, run) -> None:
        """Raise MissingPrerequisiteError if required predecessor output missing."""
        ...

    @abstractmethod
    def _load_context(self, run) -> dict:
        """Load ONLY the files in this stage's Load Before Starting contract."""
        ...

    @abstractmethod
    def _build_prompt(self, run, context) -> tuple[str, str]:
        """Returns (system_prompt, user_prompt)."""
        ...

    @abstractmethod
    def _parse_output(self, raw, run) -> "StageOutput":
        """Parse LLM output. Separate article content from appended sections."""
        ...

    @abstractmethod
    def _validate_output(self, output, run) -> list[str]:
        """Return list of quality gate failures. Empty = all pass."""
        ...

    @abstractmethod
    def _build_handoff(self, run, output, context) -> str:
        """Produce the handoff document for the next stage."""
        ...

    async def run(self, run) -> "StageOutput":
        self._check_prerequisites(run)
        context = self._load_context(run)
        system, user = self._build_prompt(run, context)
        raw = await self._llm.complete(user, system=system)
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

---

## Stage-by-Stage Build Notes

Critical implementation details derived from the reference run outputs and the original CONTEXT files. These are the things that aren't obvious from the specs alone.

### Stage 0 — Onboarding

**State detection before writing anything:**
```python
def detect_client_state(ref_files) -> ClientState:
    present = sum([
        ref_files.style_reference_card is not None,
        ref_files.audience_profile is not None,
        ref_files.brand_notes is not None,
    ])
    if present == 0: return ClientState.NEW
    if present == 3: return ClientState.FULLY_ONBOARDED
    return ClientState.PARTIAL
```

**FULLY_ONBOARDED → stop.** Never overwrite existing reference files without explicit user confirmation. Raise `ClientAlreadyOnboardedError`; the API returns 409 with a message asking whether to regenerate.

**Parse brand colors from Style Reference Card at onboarding time**, not at Stage 7. Stage 7 just reads `client_reference_files.brand_colors` JSONB. Exactly 11 tokens must be present:
`primary`, `primary_2`, `primary_soft`, `primary_glow`, `primary_rgb`, `accent`, `accent_2`, `accent_soft`, `accent_rgb`, `ink`, `line_strong`.

The `primary_rgb` and `accent_rgb` values are `"r, g, b"` strings without a `#` prefix — they're used inside `rgba()` in the CSS. Store them exactly this way.

**Validation gate:** Style Reference Card must contain hex color values (`#RRGGBB`). If it doesn't, onboarding fails — Stage 7 cannot run without brand colors.

**Brand Notes has more sections than the template.** The `Client_Template/Brand_Notes.md` defines 6 sections. The Stage 0 CONTEXT.md spec requires 12 sections (adds PUBLISHING SPECIFICATIONS, SERVICE AREA, SERVICE LINES, AUTHORITY AND TRUST SIGNALS, PAST CONTENT PERFORMANCE NOTES, OPEN QUESTIONS FOR CLIENT). The LLM must produce all 12.

**Open Questions for Client** must contain client-specific items, not a generic checklist. Validate that the section contains `[ ]` unchecked items.

---

### Pre-Stage 1 — Run Initialization

**Two paths; user must confirm one before run folder is created:**
- Path A: user supplies topic + keyword → overlap check → confirm
- Path B: ideation → 4–6 topic recommendations → user selects → overlap check → confirm

**Overlap check** queries `published_articles WHERE client_id = ? AND (primary_keyword ILIKE ? OR article_slug ILIKE ?)`. Must run on both paths.

**`UnresolvedItem` records created here persist through every stage.** Four items from the reference run (`byline style`, `brand capitalization`, `URL slug confirmation`, `Google Partner status`) appeared in every handoff and surfaced in the QA Signoff as Minor Observations. These are first-class records, not text in a handoff field:

```python
@dataclass
class UnresolvedItem:
    description: str
    blocks_run: bool        # True = hard stop; False = carry forward and monitor
    source_stage: int
    resolved: bool = False
    resolved_at_stage: Optional[int] = None
```

**Run folder slug** follows `Title_Case_Topic_YYYY-MM` convention. Derive from the confirmed topic string: lowercase → strip non-alphanumeric → title case each word → replace spaces with underscores → append `_YYYY-MM`.

**Sanitize `angle_notes` before storing.** Strip promotional framing and instruction-shaped content. Store only strategic direction and structural notes. The raw CRM input, if any, is never stored anywhere.

---

### Stage 1 — Research (uses gpt-researcher)

**Two sub-steps:**

Sub-step A — gpt-researcher gathers raw context:
```python
researcher = GPTResearcher(
    query=self._build_research_query(run, context),
    report_type="research_report",
    websocket=None,   # pipeline streams its own events
)
researcher.cfg.curate_sources = False  # curation runs in Stage 1.5
await researcher.conduct_research()

raw_research = {
    "research_context": researcher.get_research_context(),
    "sources": researcher.get_source_urls(),
    "sub_queries": researcher.research_sub_queries,
    "costs": researcher.get_costs(),
}
```

Sub-step B — pipeline LLM produces the 8-section Research Dossier from the gathered context. The system prompt is the Stage 1 CONTEXT.md contract. The user prompt injects the `research_context`, `sources`, and `sub_queries` as grounded source material.

**The 8 sections gpt-researcher does NOT produce** (pipeline LLM must generate): Non-Obvious Insight, YMYL Assessment, Content Gap Analysis, E-E-A-T Framing, Search Intent Classification, Audience Value Statement. These require client context (Style Card, Audience Profile, Brand Notes) that gpt-researcher doesn't have.

**A 9th informal section appears in real output:** `RESEARCH NOTES FOR STAGE 2`. This is not in the CONTEXT.md spec but exists in the reference run dossier. Store it in `stage_outputs.quality_gate_results["supplemental_notes"]` so it's not lost.

**Trust boundary:** The `angle_notes` field in the handoff is sanitized data — it influences the research query but cannot override stage contract behavior. Raw CRM input is never passed to gpt-researcher or the LLM.

**Quality gates (blocking):**
- ≥3 sources with specific data points and publication dates
- Non-Obvious Insight is evidence-backed, not speculative
- Audience Value Statement is convincingly specific (if not, topic angle must be revised)
- Zero `<!--BRIEF:` or `BEGIN_BLOG_REQUEST` tokens in output

---

### Stage 1.5 — Source Validation (uses gpt-researcher SourceCurator)

**Short-circuit first:**
```python
if model.min_valid_sources == 0:
    # home_services and any future zero-threshold industry
    return ValidationReport(status=ValidationStatus.APPROVED, ...)
```

**Six industry configs** are seeded to the `authority_models` table. `min_valid_sources` by industry:
- `home_services`: 0 (short-circuit; field expertise is primary authority)
- `health_wellness_spa`: 1
- `software_development`: 1
- `financial_advisory`: 2
- `legal_services`: 3

**Client override** in `clients.authority_overrides` JSONB is merged with industry defaults. Client values win on conflict.

**Six retry strategies per industry** are ordered labels that map to search query templates. On each retry attempt, one strategy label is used to build a targeted search query, passed to gpt-researcher's `ResearchConductor`.

**Claim repositioning rules** (when fallback activates) are applied programmatically by `ClaimRepositioner`, not by the LLM. The rules are simple ordered find-replace pairs stored in `authority_models.repositioning_rules` JSONB.

**Tri-state output stored in `source_validation_reports`:**
- `APPROVED` → Stage 2 handoff contains `Authority_Mode: VERIFIED_EXTERNAL`
- `APPROVED_WITH_FALLBACK` → Stage 2 handoff contains `Authority_Mode: EXPERT_FALLBACK` + repositioning rules
- Any `REJECTED_*` → pipeline stops; report error to user

---

### Stage 2 — Content Brief

**Trust boundary:** Stage 2 does not re-import, revive, or echo raw CRM phrasing. It works only from the normalized Research Dossier and Stage 1 handoff.

**`<!--BRIEF:` tokens are the critical contract between Stage 2 and Stage 3.** Every writer-facing instruction in the outline that is not meant to appear in the article body must be wrapped as `<!--BRIEF: instruction here -->`. These are multi-line in real output (3–8 lines typical).

**`BriefParser.strip_brief_tokens()`** is called before the brief is passed to Stage 3. The content types table (confirmed in reference run) is not inside a BRIEF block — it sits between BRIEF blocks and must survive stripping. Test this explicitly.

**WHO/HOW/WHY checkpoint** must have specific, non-generic answers before the brief proceeds. "We're experts" fails. "Rankrise manages content for home service clients across Colorado with 27K+ organic users" passes.

**If `Authority_Mode: EXPERT_FALLBACK`** in the Stage 1 handoff: Stage 2 applies `ClaimRepositioner` to any claim in the dossier that matches a repositioning rule before incorporating it into the brief. Stage 3 then writes from the brief without needing to know fallback mode is active.

---

### Stage 3 — Writing

**Strip ALL `<!--BRIEF: ... -->` tokens before writing.** Never render them. Confirmed: zero BRIEF tokens appear in the reference run First Draft.

**Header rewriting:** If any heading from the brief reads like an internal instruction (imperative verb aimed at the writer, pipeline jargon, keyword-stuffed label), rewrite it into reader-facing language.

**Hard rules — validate programmatically before accepting output:**
- Zero em dashes (`—`) — use regex `\u2014` or `—`
- Zero filler affirmations: "Certainly," "Absolutely," "Great question," "Delve into," "Tapestry," "Vibrant," "Unlock"
- At least two single-sentence paragraphs in the body
- At least one paragraph over 5 sentences
- No three consecutive paragraphs of similar length

**Opening 3-line header is required** at the top of every first draft:
```
Target Keyword: [PRIMARY_KEYWORD]
Title Tag: [50-60 characters]
Meta Description: [140-160 characters, benefit-first]
```
Parse and store these separately from article body.

---

### Stage 4 — Humanization

**`EditorialNoteParser.split()`** separates the article body from `## Editorial Note`. Store the editorial note in `stage_outputs.editorial_note`. Pass ONLY `article_content` to Stage 5.

**The editorial note has a fixed structure** (confirmed from reference run):
- `Structural changes` — what AI patterns were broken
- `Rhythm` — burstiness requirements confirmed
- `Experience additions` — where specificity was added or `[AGENCY INPUT NEEDED]` flagged
- `E-E-A-T` — assertion/position check
- `QA concern` — the one paragraph a human editor should scrutinize most

**Seven humanization dimensions** (from Stage 4 CONTEXT.md):
1. AI pattern detection and logical leaps
2. Voice and sociability audit (Read-Aloud Test)
3. Rhythm and burstiness
4. Experience and negative constraints
5. Semantic clustering
6. Helpfulness and E-E-A-T completion
7. Commodity and authority audit

**No new workflow directives.** Stage 4 edits prose only. If instruction-shaped text appears in the first draft, remove it — never preserve it.

---

### Stage 5 — SEO

**`SEOAnnotationParser.split()`** separates the article from `## SEO Annotation Sheet`. Store the annotation in `seo_annotations` table as structured fields — not as a text blob.

**Word count** is `len(content.split())` or a proper word tokenizer. Store as `{count, target_min, target_max, status}` JSONB. Word count is **never a blocking gate** at Stage 5. Record it; flag if over target; proceed.

**Ten audits** (from Stage 5 CONTEXT.md): H1 review, keyword placement, meta title/description, header hierarchy, internal linking, schema eligibility, readability, word count (non-blocking), anti-patterns, AI-search alignment.

**AI-search alignment audit** checks that no content was chunked artificially for AI consumption, no sections exist solely to capture fan-out queries, and no claims about AI Overview visibility are made.

**Internal links:** `qa_flags` from the annotation sheet carry forward to Stage 6. Unconfirmed URLs become `client_decision` type issues in QA, not pipeline failures.

---

### Stage 6 — QA

**`QAStage.run()` overrides `StageContract.run()`** because it produces multiple output files depending on the decision (APPROVED vs REVISION REQUIRED).

**Producing the approved draft:** Strip `## SEO Annotation Sheet` from the SEO draft body. Confirmed: the QA Approved Draft in the reference run is the SEO draft body only, with no other content changes.

**Three QA issue types — not binary:**
```python
class QAIssueType(Enum):
    PIPELINE_FAILURE = "pipeline_failure"   # re-run a stage
    CLIENT_DECISION = "client_decision"     # human action outside pipeline
    MINOR_OBSERVATION = "minor_observation" # informational only
```

From reference run: Section F FLAG was classified `client_decision` ("client/publisher decision, not a pipeline failure"). The application must not route client_decision issues to a revision stage.

**Revision routing table** (from Root_Context.md):

| Failure keyword | Route to stage |
|---|---|
| factual_claim, ymyl, cta_missing, eeat | Stage 3 |
| ai_sounding, voice_inconsistency | Stage 4 |
| keyword_placement, meta_title, header_hierarchy | Stage 5 |

Route to the *earliest* responsible stage. Never restart from Stage 1.

**AI Detection Risk Score** — 5 dimensions, each scored 1–3, revision required if total > 10/15:
1. Symmetrical paragraph lengths
2. Generic interchangeable section openings
3. Absence of proper nouns, named cases, local details
4. Overly comprehensive coverage with no point of view
5. No voice personality moments

**Nine checklist sections** (A through I). All must be PASS for APPROVED except:
- Non-blocking exception: word count over target (APPROVED + `Human_Review_Flag.md` equivalent field populated)

**Zero tolerance — these cause automatic FAIL regardless of other sections:**
- Any `<!--BRIEF:` token in the SEO draft
- Any `BEGIN_BLOG_REQUEST` delimiter in the SEO draft
- Any `[AGENCY INPUT NEEDED]` flags unresolved in the body

---

### Stage 7 — Blog Formatting

**Pre-flight gate — check before loading anything else:**
```python
def _check_prerequisites(self, run):
    qa = self._repo.get_stage_output(run.id, stage_number=6)
    if qa.qa_result.get("decision") == "revision_required":
        raise StageBlockedError(
            "Stage 7 blocked: QA revision is pending. "
            "Re-run Stage 6 before formatting."
        )
```

**CSS token injection — exactly 11 tokens, exact value formats:**
```python
REQUIRED_TOKENS = {
    "{{PRIMARY}}":      brand_colors["primary"],       # "#1B3D6F"
    "{{PRIMARY_2}}":    brand_colors["primary_2"],     # "#1E4F8A"
    "{{PRIMARY_SOFT}}": brand_colors["primary_soft"],  # "#EEF3FA"
    "{{PRIMARY_GLOW}}": brand_colors["primary_glow"],  # "rgba(27, 61, 111, 0.08)"
    "{{PRIMARY_RGB}}":  brand_colors["primary_rgb"],   # "27, 61, 111" ← no # prefix
    "{{ACCENT}}":       brand_colors["accent"],        # "#E8762B"
    "{{ACCENT_2}}":     brand_colors["accent_2"],      # "#D4621E"
    "{{ACCENT_SOFT}}":  brand_colors["accent_soft"],   # "#FDF1E8"
    "{{ACCENT_RGB}}":   brand_colors["accent_rgb"],    # "232, 118, 43" ← no # prefix
    "{{INK}}":          brand_colors["ink"],           # "#1C1C1A"
    "{{LINE_STRONG}}":  brand_colors["line_strong"],   # "rgba(27, 61, 111, 0.22)"
}
```

The `PRIMARY_RGB` and `ACCENT_RGB` values are comma-separated triplets used inside `rgba()` in the CSS. They must not have a `#` prefix.

**CSS template** is stored in `css_templates` table (seeded at deploy time). Stage 7 fetches by name `"blog_integration_base"`, applies tokens, inlines into `<style>` block.

**HTML structure — confirmed from reference run:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[TITLE_TAG]</title>
  <meta name="description" content="[META_DESCRIPTION]">
  <!-- Google Fonts if client has google_fonts_url set -->
  <style>/* inlined CSS with tokens replaced */</style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to content</a>
  <article class="blog-wrap" id="main-content">
    <div class="card-wrap">
      <header class="header"><!-- H1 here --></header>
    </div>
    <!-- Optional: toc-card if ≥4 H2 sections -->
    <section class="prose"><!-- one per H2 --></section>
    <section class="prose">...</section>
    <div class="cta-card"><!-- always last --></div>
  </article>
</body>
</html>
```

**Article slug** derived from H1 (not the topic string):
```python
def derive_slug(h1: str) -> str:
    slug = h1.lower()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug
# "Content Marketing for Home Service Businesses..."
# → "content-marketing-home-service-businesses"
```

**Internal token check — hard stop:**
```python
FORBIDDEN_IN_HTML = [
    "<!--BRIEF:", "BEGIN_BLOG_REQUEST", "END_BLOG_REQUEST",
    "## Editorial Note", "## SEO Annotation Sheet",
]
```
If any are found in the HTML output, raise `InternalTokenLeakError` and stop. Do not publish.

**Three output files:**
1. `07_Blog_Final.html` → stored in `stage_outputs.article_content` + `published_articles.html_content`
2. `Published/[slug].html` → same content; `published_articles` table row
3. `Published/[slug].md` → markdown companion with 3-line meta header:
   ```
   Target Keyword: [KEYWORD]
   Title Tag: [TITLE]
   Meta Description: [DESCRIPTION]

   [full article body in markdown]
   ```

---

## Build Phases

### Phase 1 — Foundation (Weeks 1–2)
- Supabase project + full schema (all tables from REFERENCE.md)
- Domain models (`enums.py`, `client.py`, `run.py`, `stage.py`)
- Repository classes with Supabase client
- `AnthropicProvider` with streaming support
- `OpenRouterProvider`, `OllamaProvider`, `LMStudioProvider`
- `LLMProviderFactory` — reads `LLM_PROVIDER` env var; stage services use this, never individual providers directly
- `PROVIDER_QUALITY_TOLERANCES` config in `config/provider_config.py`
- `StageContract` base class
- FastAPI skeleton with health check
- Next.js shell

**Gate:** Create a client via API; confirm it persists; retrieve it. Also confirm:
- `LLMProviderFactory.create_smart_provider()` returns `AnthropicProvider` when `LLM_PROVIDER=anthropic`
- `LLMProviderFactory.create_smart_provider()` returns `OpenRouterProvider` when `LLM_PROVIDER=openrouter`
- No stage service file imports any provider class directly

### Phase 2 — Parsing Layer (Weeks 3–4)
All six parsers. No stage services yet.

**Gate:** Run all six parsers against the reference run files. Confirm:
- Content types table survives BRIEF token stripping
- Editorial note splits cleanly from humanized draft body
- SEO Annotation Sheet splits cleanly; word count parses to structured JSONB
- QA Signoff parses to `QAResult` with correct section scores

### Phase 3 — Onboarding (Weeks 5–6)
- `OnboardingStage` with state detection, file generation, brand color extraction
- `client_contexts` table and `ClientContextAssembler`
- `UnresolvedItemTracker`
- `POST /clients/{client_id}/onboard` endpoint
- Onboarding form UI

**Gate:** Run Stage 0 against sample client content; compare output to reference `Style_Reference_Card.md` structure; confirm brand colors extracted to JSONB with correct 11 keys.

### Phase 4 — Run Initialization (Week 7)
- Overlap check against `published_articles`
- Topic recommendation generation (Path B)
- Run init endpoints and UI

**Gate:** Both Path A and Path B produce a run with correct `UnresolvedItem` records; overlap detection fires correctly.

### Phase 5 — Research and Source Validation (Weeks 8–10)
- Install `gpt-researcher`; configure environment variables
- `ResearchStage` — Sub-step A (gpt-researcher gather) + Sub-step B (pipeline LLM structure)
- `SourceValidationService` with short-circuit for `min_valid_sources = 0`
- `authority_models` table seeded with all five industry configs
- `IndustryAwarePromptFamily` for curator prompt injection
- SSE streaming endpoint

**Gate:** Run Stage 1 on reference run topic; compare 8-section dossier structure to `01_Research_Dossier.md`. Confirm `RESEARCH NOTES FOR STAGE 2` section stored in `supplemental_notes`. Test home_services client short-circuits validation to APPROVED. Test health_wellness_spa client runs full validation flow.

### Phase 6 — Brief, Writing, Humanization (Weeks 11–13)
Build Stages 2, 3, 4 in order.

**Gate per stage:**
- Stage 2: BRIEF tokens absent from handoff; content types table in brief → present in Stage 3 output
- Stage 3: Zero em dashes; zero filler affirmations; opening 3-line header parsed separately
- Stage 4: Editorial note stored in `editorial_note` column; Stage 5 receives `article_content` only

### Phase 7 — SEO, QA, Formatting (Weeks 14–16)
Build Stages 5, 6, 7.

**Gate per stage:**
- Stage 5: Annotation sheet stored as structured JSONB; `qa_flags` array extracted; word count parses to structured fields; stage completes even if word count over target
- Stage 6: Three QA issue types correctly classified; revision routing sends failures to correct earliest stage; approved draft has annotation sheet stripped; reference run scores 38/39 PASS, AI Risk 5/15
- Stage 7: All 11 CSS tokens replaced correctly; `PRIMARY_RGB` has no `#` prefix; zero internal tokens in HTML output; slug derived from H1; three output files written

### Phase 8 — Worker Queue and Auto-Advance (Week 17)
- ARQ worker setup for background stage execution
- `auto_advance` mode (runs until next human checkpoint)
- Job status polling and SSE streaming UI

### Phase 9 — Validation and Cutover (Week 18)
- Run 3–5 complete articles through the application for real clients
- Side-by-side output comparison with the original system
- Fix discrepancies; confirm intentional vs. defect
- Retire the old system per client as confidence is established

---

## Non-Negotiable Validation Checklist

Before any stage is marked done:

- [ ] `<!--BRIEF:` tokens never appear in Stage 3, 4, 5, 6, or 7 outputs
- [ ] Content types table from the brief appears verbatim in Stage 3 output
- [ ] Editorial note is stored separately; not in `article_content`; not passed to Stage 5
- [ ] SEO annotation sheet is stored separately; not in `article_content`; not in QA approved draft
- [ ] Word count stored as `{count, target_min, target_max, status}` JSONB — not as a string
- [ ] `UnresolvedItem` records from Pre-Stage 1 visible in every stage UI view
- [ ] QA issues classified as `pipeline_failure`, `client_decision`, or `minor_observation`
- [ ] Article slug derived from H1, not from topic string
- [ ] `PRIMARY_RGB` and `ACCENT_RGB` brand color values stored without `#` prefix
- [ ] Stage 7 HTML output contains zero internal tokens (grep-verified)
- [ ] No Python scripts from the old system are referenced or replicated anywhere

