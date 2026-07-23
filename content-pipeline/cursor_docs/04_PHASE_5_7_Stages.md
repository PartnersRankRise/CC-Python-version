# Phase 5–7 — Pipeline Stages
**Weeks 8–16 | Gate per stage listed below**

Build stages in strict dependency order. Never start a stage until the previous stage's gate check passes. The reference run files are your ground truth for every stage output.

---

# PHASE 5 — Research and Source Validation (Weeks 8–10)

## Step 5.1 — ResearchStage (Stage 1)

```
Create content_pipeline/services/research_service.py.

This stage has two sub-steps. Read BUILD_GUIDE.md — "Stage 1 — Research" section.
Read docs/architecture_addendum_gpt_researcher.md — Section 4.2 for the full implementation.

Sub-step A: gpt-researcher gathers raw research context
Sub-step B: Pipeline LLM structures it into the 8-section Research Dossier

CRITICAL: gpt-researcher is used as a library, not a server.
Set websocket=None. Set curate_sources=False at Stage 1 (curation is Stage 1.5).

gpt-researcher picks up its LLM provider from env vars (SMART_LLM, FAST_LLM, STRATEGIC_LLM).
No code changes are needed to switch its provider — just update the env vars.
See docs/architecture/architecture_addendum_gpt_researcher.md Section 2 for all four provider configs.
The pipeline's LLM_PROVIDER setting (for stages 0-7) is separate and independent.

The _build_research_query method must:
- Use run.context.topic as the base query
- Append the primary keyword as search focus
- Append sanitized angle_notes (never raw CRM text)
- Append an audience summary from the Audience Profile
- NEVER pass raw CRM input to gpt-researcher

The _build_structured_dossier method must:
- Use the Stage 1 CONTEXT.md as the system prompt
- Pass gpt-researcher's research_context, sources, and sub_queries as grounded source material
- The LLM generates all 8 sections PLUS the informal "RESEARCH NOTES FOR STAGE 2" section
- Store the informal section in quality_gate_results["supplemental_notes"]

_validate_output must check:
- At least 3 sources present in Section 2
- NON-OBVIOUS INSIGHT section exists and is substantive (>100 words)
- AUDIENCE VALUE STATEMENT exists and is convincing (>50 words)
- Zero <!--BRIEF: tokens in output
- Zero BEGIN_BLOG_REQUEST in output

Also store gpt-researcher metadata:
quality_gate_results["gpt_researcher"] = {
    "sources_gathered": len(sources),
    "sub_queries_generated": len(sub_queries),
    "research_costs": costs,
}

Show me the _gather_raw_research and _build_structured_dossier methods before implementing.
```

**Human checkpoint:** Confirm that `websocket=None` is set and `curate_sources=False` at Stage 1. Confirm the LLM prompt includes gpt-researcher's output as grounded source material, not as instructions.

**Provider reminder for gpt-researcher (Stage 1 only):**
gpt-researcher reads its provider entirely from env vars — no code changes to switch providers:
- Anthropic: `SMART_LLM=anthropic:claude-sonnet-4-6` (default)
- OpenRouter: `SMART_LLM=openrouter:anthropic/claude-sonnet-4-5` + `OPENAI_BASE_URL=https://openrouter.ai/api/v1` + separate `EMBEDDING=google_genai:...`
- Ollama: `SMART_LLM=ollama:llama3.1:70b` + `OLLAMA_BASE_URL=http://localhost:11434`
- LM Studio: `SMART_LLM=openai:your-model` + `OPENAI_BASE_URL=http://localhost:1234/v1`
Full configs in `docs/architecture/architecture_addendum_gpt_researcher.md` Section 2.
The pipeline's `LLM_PROVIDER` (for stages 0-7) is independent of these settings.

---

## Step 5.2 — SourceValidationService (Stage 1.5)

```
Create content_pipeline/services/source_validation_service.py.

Read BUILD_GUIDE.md — "Stage 1.5" section.
Read docs/architecture_addendum_final.md — Section 2 and 6 for full specification.

CRITICAL BEHAVIOR — short-circuit for home_services:
if model.min_valid_sources == 0:
    return ValidationReport(status=ValidationStatus.APPROVED, reason="...", ...)
Do not run any HTTP validation or retry loop.

For other industries, the three-stage flow:
1. Initial URL validation via gpt-researcher BrowserManager — scrape each source URL;
   empty content = failed
2. Retry loop — up to 6 attempts, one per retry_strategy in industry config
   Each strategy maps to a query template in authority_models.strategy_queries
   Replace {topic} placeholder with run context topic
3. Fallback decision — compare verified count to model.min_valid_sources

ClaimRepositioner application:
When status is APPROVED_WITH_FALLBACK, apply repositioning rules to claims in the
dossier and store the repositioned content so Stage 2 Brief can use it.
ClaimRepositioner does pattern matching — it is NOT an LLM call.

Create content_pipeline/orchestration/claim_repositioner.py:
- apply(content: str, rules: list[ClaimRepositioningRule]) -> str
  Simple ordered find-replace; case-insensitive; preserve surrounding sentence structure

Also implement authority_model_repository.py:
- load(industry_key: str, client_overrides: dict) -> AuthorityModel
  SELECT from authority_models WHERE industry_key = ?
  Merge client_overrides: client values win on conflict
- get_strategy_queries(industry_key: str) -> dict[str, str]
  Returns {strategy_label: query_template} dict

Write tests:

def test_home_services_short_circuits():
    service = SourceValidationService(...)
    run = create_test_run(industry="home_services")
    report = await service.validate(dossier_text, run)
    assert report.status == ValidationStatus.APPROVED
    assert report.fallback_activated == False
    # Must not have tried any HTTP requests

def test_fallback_mode_generates_repositioning_rules():
    # Use health_wellness_spa (min=1) with a mock that returns 0 verified sources
    report = await service.validate(dossier_text, run_with_failed_sources)
    assert report.status == ValidationStatus.APPROVED_WITH_FALLBACK
    assert len(report.repositioning_rules) > 0
    assert report.fallback_primary == "PRACTITIONER_EXPERTISE"

Run tests. Show me output.
```

---

## Step 5.3 — Stage 1 API and Streaming

```
Implement the Stage 1 execution endpoint with SSE streaming.

In content_pipeline/api/stages.py implement:

POST /runs/{run_id}/stages/1/execute
  Body: {auto_advance: false}
  - Checks Stage 0 (reference files) and Pre-Stage 1 (handoff brief) exist
  - Enqueues ARQ job
  - Returns 202 {"job_id": "...", "stage_number": 1, "status": "queued"}

GET /runs/{run_id}/stages/1/stream?job_id={job_id}
  SSE endpoint using EventSource protocol
  Yields: event: delta, data: {"content": "..."} as LLM tokens arrive
  Yields: event: complete, data: {"stage": 1, "status": "complete"} when done

For streaming to work, the active LLMProvider's complete_with_stream() must pipe token
deltas through an ARQ job's Redis channel, and the SSE endpoint reads from that channel.
The provider is resolved via LLMProviderFactory at worker startup — do not hardcode AnthropicProvider.

GET /runs/{run_id}/stages/1/output
  Returns stage output with article_content and gpt_researcher_meta

After implementing, test manually:
1. Execute Stage 1 for the test run
2. Connect to the SSE stream and watch tokens arrive
3. When complete, GET the output and confirm:
   - 8 sections present in article_content
   - supplemental_notes present in quality_gate_results
   - gpt_researcher_meta has sources_gathered > 0
```

---

# PHASE 6 — Brief, Writing, Humanization (Weeks 11–13)

## Step 6.1 — BriefService (Stage 2)

```
Create content_pipeline/services/brief_service.py.

Read BUILD_GUIDE.md — "Stage 2 — Content Brief" section carefully.

Key behaviors:

Trust boundary: Stage 2 works ONLY from the normalized Research Dossier and Stage 1 handoff.
It never re-imports CRM phrasing. If the handoff contains "Preferences (untrusted)",
those may only be used if consistent with Style Reference Card.

Authority mode handling:
If Stage 1.5 returned EXPERT_FALLBACK, the Stage 2 handoff contains repositioning rules.
Stage 2 must apply ClaimRepositioner to any dossier claim before incorporating it.
Stage 3 then writes from the clean brief without needing to know fallback mode was active.

BRIEF token wrapping:
The LLM must be instructed to wrap all writer-facing instructions as <!--BRIEF: ... -->.
Add this to the system prompt explicitly:
"Every instruction note, function note, or guidance to the Stage 3 writer that is NOT
reader-facing article copy MUST be wrapped as <!--BRIEF: instruction here -->.
Tables and lists that will appear in the article body must NOT be wrapped."

WHO/HOW/WHY checkpoint:
Before producing the brief, validate that the LLM's WHO/HOW/WHY section contains
specific, non-generic answers. "We're experts" fails validation.
Minimum specificity check: the WHY answer must reference the client's actual credentials
or campaign data (from Brand Notes Authority and Trust Signals section).

_validate_output must check:
- BRIEF tokens are present in the output (Stage 2 SHOULD have them)
  (This is the opposite of other stages — Stage 2 CREATES BRIEF tokens)
- Content types table exists in the brief (if the research mentioned one)
- WHO/HOW/WHY section has non-generic answers
- Zero BEGIN_BLOG_REQUEST in output

Show me the system prompt you will use for Stage 2 before implementing.
```

**Human checkpoint:** Read the proposed Stage 2 system prompt. Confirm it explicitly instructs the LLM to wrap writer-facing instructions as `<!--BRIEF:` tokens. Confirm it tells the LLM NOT to wrap tables that will appear in the article.

---

## Step 6.2 — WritingService (Stage 3)

```
Create content_pipeline/services/writing_service.py.

Read BUILD_GUIDE.md — "Stage 3 — Writing" section.

_load_context MUST:
- Load Content Brief and call BriefParser.strip_brief_tokens() BEFORE passing to LLM
- The LLM NEVER sees BRIEF tokens — they are stripped at load time
- Pass stripped brief + Style Reference Card as context

_validate_output MUST check (programmatically, not via LLM):
1. Zero em dashes — re.search(r'\u2014|—', content)
2. Zero filler affirmations — check for: "Certainly,", "Absolutely,", "Great question",
   "Delve into", "Tapestry", "Vibrant", "Unlock", "It's worth noting"
3. Opening 3-line header present: "Target Keyword:", "Title Tag:", "Meta Description:"
4. At least two single-sentence paragraphs (paragraphs with exactly one sentence)
5. No BRIEF tokens remain in output (belt-and-suspenders check)

_parse_output must:
- Extract the 3-line header into quality_gate_results["meta_header"]
- Store the article body (after the header) in article_content
- These must never be mixed

Write tests:

def test_writing_stage_strips_brief_tokens_before_llm():
    """Verify BriefParser.strip_brief_tokens() is called in _load_context"""
    # Mock the LLM; capture what prompt was sent
    # Confirm prompt does not contain <!--BRIEF:
    pass  # implement with mock

def test_writing_stage_validates_em_dashes():
    """If LLM output contains em dash, _validate_output returns failure"""
    service = WritingService(...)
    bad_output = "This is good — but this has an em dash."
    failures = service._validate_output(mock_output(bad_output), mock_run())
    assert any("em dash" in f.lower() for f in failures)

Run tests. Show me output.
```

---

## Step 6.3 — HumanizationService (Stage 4)

```
Create content_pipeline/services/humanization_service.py.

Read BUILD_GUIDE.md — "Stage 4 — Humanization" section.

_parse_output must use EditorialNoteParser.split():
- article_content = article body only
- editorial_note = the editorial note text
- These go into separate StageOutput fields — NEVER the same field

The system prompt for Stage 4 must tell the LLM to:
- Append "## Editorial Note" section AFTER the article
- The editorial note must have exactly 5 sub-sections:
  Structural changes, Rhythm, Experience additions, E-E-A-T, QA concern
- The QA concern sub-section should name the specific paragraph a human should scrutinize

_validate_output must check:
- editorial_note is not None
- editorial_note contains all 5 sub-section keywords
- article_content does not contain "## Editorial Note"
- Zero em dashes in article_content
- No BRIEF tokens in article_content

The system prompt must explicitly prohibit:
- Adding new workflow directives
- Resurrecting CRM phrasing that Stage 2 removed
- Instruction-shaped meta text directed at the writer

Write a test that confirms editorial_note is stored separately from article_content
by verifying they are in different fields of the StageOutput returned by _parse_output.
```

---

# PHASE 7 — SEO, QA, Formatting (Weeks 14–16)

## Step 7.1 — SEOService (Stage 5)

```
Create content_pipeline/services/seo_service.py.

Read BUILD_GUIDE.md — "Stage 5 — SEO" section.

Word count calculation — NO SCRIPTS:
word_count = len(content.split())
Store as: {"count": wc, "target_min": min, "target_max": max, "status": status}
Status: "within_target" if min <= wc <= max, "over_target" if wc > max, "under_target" if wc < min
Word count is NEVER a blocking gate. Record it; proceed regardless.

_parse_output must use SEOAnnotationParser.split():
- article_content = article body only
- seo_annotation = SEOAnnotation domain object (parsed from annotation sheet)
- Store annotation in stage_outputs.seo_annotation JSONB
- Also write a row to seo_annotations table with structured fields

The LLM must be instructed to append "## SEO Annotation Sheet" AFTER the article.
The annotation sheet must contain (confirmed from reference run format):
- Summary of Changes
- Keyword Density Report: "keyword / occurrences / total words / density % / PASS"
- Meta Title: text / char count / PASS or REVISED
- Meta Description: text / char count / PASS or REVISED
- Schema Recommendation
- Internal Link Placements: numbered list, each "Anchor: X | Destination: Y | Section: Z"
- Readability Note
- Word Count Note: "{count} words | target: {min}-{max} | {STATUS}"
- AI-Search Alignment: PASS or findings
- Flags for QA Agent: bulleted list

After the LLM generates this, parse it with SEOAnnotationParser.
The "Word Count Note" line is parsed by parse_word_count() — it must produce structured JSONB.

_validate_output checks:
- article_content does not contain "## SEO Annotation Sheet"
- seo_annotation.word_count is a dict (not a string)
- seo_annotation.qa_flags is a list (will carry to Stage 6)
- Primary keyword appears in first 100 words of article_content
- Keyword density <= 1.5%
```

---

## Step 7.2 — QAService (Stage 6)

```
Create content_pipeline/services/qa_service.py.

Read BUILD_GUIDE.md — "Stage 6 — QA" section. This is the most complex stage.

QAStage.run() overrides StageContract.run() because it produces multiple outputs
depending on APPROVED vs REVISION REQUIRED.

The LLM produces the QA Signoff document. QASignoffParser.parse() converts it to QAResult.

APPROVED flow:
1. Strip "## SEO Annotation Sheet" from SEO draft using SEOAnnotationParser.split()
2. The stripped article body becomes the QA Approved Draft (article_content)
3. Create qa_results and qa_issues DB records
4. Build Stage 7 handoff
5. If word count was OVER TARGET (from seo_annotation), set human_review_flag

REVISION REQUIRED flow:
1. Compute revision_stage using the routing table:
   factual_claim/ymyl/cta/eeat → Stage 3
   ai_sounding/voice → Stage 4
   keyword/meta_title/headers → Stage 5
2. Create qa_results and qa_issues DB records
3. Do NOT build Stage 7 handoff
4. Return status that triggers API to return revision routing info

Issue type classification MUST use classify_issue():
- "client/publisher decision" in text → CLIENT_DECISION (no revision stage)
- Stage number in text → PIPELINE_FAILURE (has revision stage)
- None/minor → MINOR_OBSERVATION

The LLM must be given the full anti-ai-checklist.md as part of its system context for Stage 6.

_validate_output checks:
- article_content does NOT contain "## SEO Annotation Sheet"
- article_content does NOT contain "## Editorial Note"
- article_content does NOT contain "<!--BRIEF:"
- article_content does NOT contain "BEGIN_BLOG_REQUEST"
- If APPROVED: ai_risk_score <= 10

Write a test that simulates the reference run QA outcome:
def test_qa_matches_reference_run_outcome():
    # Load reference 05_SEO_Draft.md as input
    # Mock the LLM to return the content of reference_run/06_QA_Signoff.md
    # Run QAService
    # Assert output matches reference run: 38/39, 5/15, Section F = CLIENT_DECISION
    pass
```

---

## Step 7.3 — FormattingService (Stage 7)

```
Create content_pipeline/services/formatting_service.py.

Read BUILD_GUIDE.md — "Stage 7 — Blog Formatting" section.

Pre-flight gate — check BEFORE anything else:
def _check_prerequisites(self, run):
    qa = self._repo.get_stage_output(run.id, stage_number=6)
    if not qa: raise MissingPrerequisiteError("Stage 6 must complete before Stage 7")
    if qa.qa_result.get("decision") == "revision_required":
        raise StageBlockedError("Stage 7 blocked: QA revision pending")

CSS token injection — apply_brand_tokens():
Load CSS template from css_templates table (name="blog_integration_base")
Replace exactly 11 {{PLACEHOLDER}} tokens with brand_colors values
Validate no {{...}} tokens remain after replacement
PRIMARY_RGB and ACCENT_RGB must NOT have # prefix — validate this explicitly

HTML structure (confirmed from reference_run/07_Blog_Final.html):
- <!DOCTYPE html> with lang="en"
- <meta viewport> present
- Single inlined <style> block (no external CSS except Google Fonts if client has google_fonts_url)
- <a class="skip-link" href="#main-content">Skip to content</a>
- <article class="blog-wrap" id="main-content">
- H1 inside a .header div inside .card-wrap
- Optional .toc-card if article has >= 4 H2 sections
- One <section class="prose"> per H2
- <div class="cta-card"> as final element

Article slug from H1 (NOT from topic string):
def derive_slug(h1: str) -> str:
    slug = h1.lower()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    return re.sub(r'\s+', '-', slug.strip())

Internal token hard stop:
FORBIDDEN = ["<!--BRIEF:", "BEGIN_BLOG_REQUEST", "END_BLOG_REQUEST",
             "## Editorial Note", "## SEO Annotation Sheet"]
for token in FORBIDDEN:
    if token in html_output:
        raise InternalTokenLeakError(f"Found '{token}' in HTML output")

Three outputs:
1. stage_outputs.article_content = HTML string
2. INSERT into published_articles (html_content + markdown_content)
3. markdown companion starts with:
   Target Keyword: {keyword}
   Title Tag: {title}
   Meta Description: {description}
   [blank line]
   [full article markdown]

Write tests:

def test_stage7_blocked_when_qa_revision_required():
    # Create a run where Stage 6 returned revision_required
    # Attempt to run Stage 7
    # Confirm StageBlockedError is raised

def test_css_rgb_tokens_have_no_hash_prefix():
    colors = {... all 11 keys ...}
    colors["primary_rgb"] = "27, 61, 111"  # correct format
    css = apply_brand_tokens(template, colors)
    # Confirm PRIMARY_RGB value in CSS does not have #
    assert "#27, 61, 111" not in css
    assert "rgba(27, 61, 111" in css  # correct usage

def test_no_internal_tokens_in_html_output():
    # Run formatting stage with reference run QA approved draft
    html = formatting_service.generate_html(approved_draft, brand_colors, ...)
    for token in FORBIDDEN:
        assert token not in html, f"Found forbidden token: {token}"

def test_slug_derived_from_h1_not_topic():
    # "Content Marketing for Home Service Businesses: How to Turn..."
    h1 = "Content Marketing for Home Service Businesses: How to Turn Your Expertise Into Local Leads"
    slug = derive_slug(h1)
    assert slug == "content-marketing-for-home-service-businesses-how-to-turn-your-expertise-into-local-leads"
    # NOT derived from the folder_slug or topic string

Run all tests. Show me output.
```

---

## Phase 5–7 Gate Check

```
Final gate check for Phases 5-7.

Run the full test suite. Show me totals.

Then run a complete article through Stages 1-7 using the reference run client
(Rankrise_Marketing, topic: content marketing for home service businesses):

1. Execute Stage 1. Confirm 8 sections in dossier output.
2. Execute Stage 1.5. Confirm APPROVED (home_services min_valid=0 short-circuit).
3. Execute Stage 2. Confirm BRIEF tokens PRESENT in brief output (Stage 2 CREATES them).
4. Execute Stage 3. Confirm BRIEF tokens ABSENT in first draft (Stage 3 strips them).
5. Execute Stage 4. Confirm editorial_note stored separately; NOT in article_content.
6. Execute Stage 5. Confirm word_count is JSONB dict; annotation sheet not in article_content.
7. Execute Stage 6. Confirm 38/39 PASS; AI Risk 5/15; Section F = CLIENT_DECISION.
8. Execute Stage 7. Confirm HTML has zero internal tokens. Confirm article slug
   starts with "content-marketing". Confirm PRIMARY_RGB in CSS has no # prefix.

Report each as PASS or FAIL. If any fail, fix before Phase 8.
```

**Human:** After Stage 7 completes, open the generated HTML file and check it manually:
- View it in a browser at three viewport widths (375px, 768px, 1280px)
- Confirm internal links are present and correctly formatted
- Confirm the CTA section is the last element
- Confirm no Editorial Note, SEO Annotation Sheet, or BRIEF tokens are visible
