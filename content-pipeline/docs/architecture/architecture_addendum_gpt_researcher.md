# Architecture Addendum: gpt-researcher Integration

**Supplements:** `architecture_migration_plan_v2.md` and `architecture_addendum_templates.md`  
**Library:** `assafelovic/gpt-researcher` (commit `5d84d2f`)  
**Scope:** Replace the hand-rolled Stage 1 research implementation and the custom Stage 1.5 source validation service with gpt-researcher as the engine for both. All downstream stages (2–7) are unaffected.

---

## 1. What gpt-researcher Is and What It Does

gpt-researcher is a production Python library implementing a **planner-executor-publisher** research pattern. Given a query, it:

1. **Plans** — decomposes the query into sub-questions using a `STRATEGIC_LLM`
2. **Executes** — runs each sub-question in parallel across 20+ sources using a `WorkerPool` of scrapers and configurable retrievers (Tavily, DuckDuckGo, Bing, Google, Arxiv, and others)
3. **Curates** — optionally ranks and filters all gathered sources by credibility, relevance, currency, and quantitative value using a `SMART_LLM` (`SourceCurator`, temperature 0.2, max tokens 8000)
4. **Synthesizes** — generates a cited research report via `ReportGenerator`

Its core classes:

| Class | Role |
|---|---|
| `GPTResearcher` | Top-level agent; manages state, config, cost tracking |
| `ResearchConductor` | Orchestrates the multi-stage research workflow |
| `BrowserManager` | Parallel URL scraping via `WorkerPool` (default 15 workers) |
| `ContextManager` | Compresses scraped content using embedding similarity |
| `SourceCurator` | LLM-based source ranking and credibility filtering |
| `ReportGenerator` | Synthesizes gathered context into a final document |
| `Config` | Loads env vars; controls retriever, LLM tiers, concurrency |

It ships with a FastAPI backend and a Next.js frontend, which overlap with the architecture already designed. Those UI components will not be used — we'll drive gpt-researcher as a library only, through the existing `ResearchStage` service class.

---

## 2. Where It Fits in the Pipeline

gpt-researcher replaces the implementation of two components in the existing design, without changing their contracts:

```
Before:
  Stage 1  → ResearchStage (hand-rolled LLM research)
  Stage 1.5→ SourceValidationService (custom retry + fallback logic)

After:
  Stage 1  → ResearchStage wraps GPTResearcher
  Stage 1.5→ SourceValidationService wraps GPTResearcher's SourceCurator
```

Everything else — the `StageContract` base class, handoff document structure, database schema, Stage 2 trust boundary, all downstream stages — is unchanged. The integration boundary is entirely inside `services/research_service.py` and `services/source_validation_service.py`.

---

## 3. Capability Mapping

Before writing integration code, it's important to be precise about which gpt-researcher capabilities solve which pipeline requirements, and where the pipeline's own logic must still run.

### 3.1 Stage 1 — Research

The pipeline's Stage 1 requires a Research Dossier with 8 specific sections:

| Required Section | gpt-researcher Provides | Gap / Pipeline Must Supply |
|---|---|---|
| Topic & Semantic Field (8 queries) | Sub-query decomposition via `ResearchConductor.plan_research()` — directly generates these | Semantic field framing and audience-problem label must be extracted from gpt-researcher's outline |
| Source Bank (≥3 sources with URL, institution, date, data points) | Gathered URLs + scraped content with source tracking | Structured extraction of institution, date, and specific data points still requires an LLM pass |
| Non-Obvious Insight | Not generated — gpt-researcher aggregates; it does not identify underexplored angles | Pipeline LLM must generate this section from the gathered context |
| YMYL Assessment | Not generated | Pipeline LLM must generate this |
| Content Gap Analysis (SERP gaps) | Not generated | Pipeline LLM must generate this |
| E-E-A-T Framing | Not generated | Pipeline LLM must generate this |
| Search Intent Classification | Not generated | Pipeline LLM must generate this |
| Audience Value Statement | Not generated | Pipeline LLM must generate this |

**Conclusion:** gpt-researcher handles the data gathering and sub-query generation layers of Stage 1. The 8-section Dossier structure still requires a pipeline LLM pass that takes gpt-researcher's raw output as its source material. The research stage is therefore two sub-steps: (A) `GPTResearcher.conduct_research()` → raw context, (B) pipeline LLM → structured 8-section dossier.

### 3.2 Stage 1.5 — Source Validation

The pipeline's custom Stage 1.5 currently implements:
- URL accessibility verification with up to 6 retries
- Industry-specific authority model evaluation (`authority-models/[industry].json`)
- APPROVED / APPROVED_WITH_FALLBACK / REJECTED status
- EXPERT_FALLBACK mode with claim repositioning rules

gpt-researcher's `SourceCurator` provides:
- LLM-based ranking of sources on: quantitative value, relevance, credibility, currency, objectivity
- Fallback: if curation fails, returns original unranked sources (pipeline continues)
- Structured JSON output of ranked sources

**Mapping:**

| Pipeline Requirement | gpt-researcher Coverage | Gap |
|---|---|---|
| URL accessibility check | `BrowserManager` scrapes URLs; failures are silently dropped | Pipeline still needs to detect when a claimed source URL is inaccessible post-scrape |
| Authority model (industry config) | `SourceCurator` uses credibility criteria but not industry-specific configs | Industry JSON configs must be passed as additional prompt context to `SourceCurator`, or the pipeline runs its own authority check on the curator's output |
| APPROVED / FALLBACK / REJECTED status | `SourceCurator` ranks but doesn't produce a tri-state status | Pipeline `SourceValidationService` still computes the tri-state from curator output |
| EXPERT_FALLBACK claim repositioning | Not provided | Pipeline generates fallback rules from the authority model + curator reasoning |
| 6-retry logic | gpt-researcher does not retry failed URL scrapes | Pipeline retries remain in `SourceValidationService` at the URL level |

**Conclusion:** gpt-researcher's `SourceCurator` replaces the core credibility-ranking logic inside Stage 1.5. The tri-state status computation, industry-authority model evaluation, EXPERT_FALLBACK mode, and retry loop remain in the pipeline's `SourceValidationService`, which now uses the curator's ranked output as its primary input instead of raw URL validation.

---

## 4. Integration Architecture

### 4.1 Installation and Configuration

```bash
pip install gpt-researcher
```

Key environment variables that control gpt-researcher behavior in the pipeline context.
gpt-researcher's provider config is **independent** from the pipeline's `LLM_PROVIDER` setting — both systems can use different providers simultaneously.

```bash
# Retriever — Tavily recommended for authoritative sources
TAVILY_API_KEY=...
RETRIEVER=tavily

# Concurrency
MAX_SCRAPER_WORKERS=15
MAX_SEARCH_RESULTS_PER_QUERY=5
CURATE_SOURCES=false              # Disabled at Stage 1; SourceCurator called directly in Stage 1.5
REPORT_TYPE=research_report

# --- Option A: Anthropic (default) ---
FAST_LLM=anthropic:claude-haiku-4-5-20251001
SMART_LLM=anthropic:claude-sonnet-4-6
STRATEGIC_LLM=anthropic:claude-sonnet-4-6

# --- Option B: OpenRouter ---
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# OPENAI_API_KEY=dummy_value
# FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
# SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
# STRATEGIC_LLM=openrouter:google/gemini-2.5-pro-exp-03-25
# EMBEDDING=google_genai:models/text-embedding-004   # Required — OpenRouter has no embeddings
# GOOGLE_API_KEY=...

# --- Option C: Ollama (self-hosted) ---
# OLLAMA_BASE_URL=http://localhost:11434
# FAST_LLM=ollama:llama3.1:8b
# SMART_LLM=ollama:llama3.1:70b
# STRATEGIC_LLM=ollama:llama3.1:70b
# EMBEDDING=ollama:nomic-embed-text
# EMBEDDING_PROVIDER=ollama

# --- Option D: LM Studio (self-hosted) ---
# OPENAI_BASE_URL=http://localhost:1234/v1
# OPENAI_API_KEY=lm-studio
# FAST_LLM=openai:<exact-model-name-from-lm-studio-ui>
# SMART_LLM=openai:<exact-model-name-from-lm-studio-ui>
# STRATEGIC_LLM=openai:<exact-model-name-from-lm-studio-ui>
# Note: LM Studio uses the openai: prefix in gpt-researcher, not lm_studio:
```

The pipeline does not use gpt-researcher's `ReportGenerator` — the pipeline's own LLM pass produces the structured dossier from the research context. Set `report_type="research_report"` to get the fullest context rather than a pre-synthesized summary.

### 4.2 Revised `ResearchStage` Implementation

```python
# services/research_service.py
from gpt_researcher import GPTResearcher
from domain.run import Run
from domain.stage import StageOutput
from domain.enums import StageStatus
from services.base_stage import StageContract
from services.mixins.trust_boundary import TrustBoundaryMixin

class ResearchStage(TrustBoundaryMixin, StageContract):
    """
    Stage 1: Research.
    
    Sub-step A: Run GPTResearcher to gather raw research context.
      - Generates sub-queries from the topic/keyword
      - Scrapes 20+ sources in parallel
      - Returns source list, scraped content, and research context
    
    Sub-step B: Pipeline LLM pass to produce the 8-section Research Dossier.
      - Uses gathered context as grounded source material
      - Generates sections gpt-researcher does not produce:
        Non-Obvious Insight, YMYL Assessment, Content Gap Analysis,
        E-E-A-T Framing, Search Intent, Audience Value Statement
    
    gpt-researcher's SourceCurator is NOT called here.
    It runs in Stage 1.5 (SourceValidationService) on the dossier output.
    """

    STAGE_NUMBER = 1
    STAGE_NAME = "research"

    async def _gather_raw_research(self, run: Run, context: dict) -> dict:
        """
        Sub-step A: Drive GPTResearcher as a library.
        Returns the raw research state: sources, context, sub-queries.
        """
        # Build the research query from pipeline context
        # The query is the topic + keyword + audience framing from the handoff
        query = self._build_research_query(run, context)

        # Domain restriction: only use sources relevant to this industry
        # Maps to gpt-researcher's domain filtering capability
        trusted_domains = self._get_trusted_domains(run.client_id)

        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
            source_urls=None,          # use retriever, not fixed URLs
            config_path=None,          # use env var config
            websocket=None,            # no streaming to external WS; pipeline streams separately
        )

        # Apply domain filtering if industry config provides trusted sources
        if trusted_domains:
            researcher.cfg.domain_restriction = "include"
            researcher.cfg.trusted_domains = trusted_domains

        # Run the full research workflow: plan → gather → compress
        # This does NOT call SourceCurator (CURATE_SOURCES=false at this step)
        # Curation runs in Stage 1.5 after the dossier is structured
        researcher.cfg.curate_sources = False
        await researcher.conduct_research()

        return {
            "research_context": researcher.get_research_context(),
            "sources": researcher.get_source_urls(),
            "research_costs": researcher.get_costs(),
            "sub_queries": researcher.research_sub_queries,
        }

    def _build_research_query(self, run: Run, context: dict) -> str:
        """
        Construct the gpt-researcher query from the pipeline's run context.
        
        Confirmed from reference run: the topic is
        "Content Marketing for Home Service Businesses: How to Turn Your Expertise Into Local Leads"
        with keyword "content marketing for home service businesses"
        and a sanitized angle note.
        
        The query must be specific enough to generate useful sub-queries
        but must not include raw CRM instructions (trust boundary enforced here).
        """
        parts = [run.context.topic]
        
        if run.context.primary_keyword:
            parts.append(f"Primary search focus: {run.context.primary_keyword}")
        
        # Sanitized angle only — never raw CRM text
        if run.context.angle_notes_sanitized:
            parts.append(f"Research angle: {run.context.angle_notes_sanitized}")
        
        # Audience context from the Audience Profile (loaded in _load_context)
        audience_summary = context.get("audience_summary", "")
        if audience_summary:
            parts.append(f"Target audience context: {audience_summary}")
        
        return "\n".join(parts)

    async def _build_structured_dossier(
        self, run: Run, context: dict, raw_research: dict
    ) -> str:
        """
        Sub-step B: Pipeline LLM pass to produce the 8-section Dossier.
        
        gpt-researcher provides:
        - research_context: compressed, relevant content from 20+ sources
        - sources: list of URLs with institution names and dates
        - sub_queries: the decomposed questions (maps to Section 1 semantic field)
        
        Pipeline LLM adds:
        - Structured 8-section format
        - Non-Obvious Insight (Section 3) — gpt-researcher does not generate this
        - YMYL Assessment (Section 4)
        - Content Gap Analysis (Section 5) — requires SERP analysis framing
        - E-E-A-T Framing (Section 6) — requires client authority context
        - Search Intent Classification (Section 7)
        - Audience Value Statement (Section 8)
        """
        system = self._load_stage_contract("stage1_research")
        
        user = f"""
## Research Context (gathered by gpt-researcher from {len(raw_research['sources'])} sources)

{raw_research['research_context']}

## Sources Gathered

{self._format_sources(raw_research['sources'])}

## Sub-Queries Generated

{chr(10).join(f"- {q}" for q in raw_research['sub_queries'])}

## Client Reference Context

### Style Reference Card
{context['style_reference_card']}

### Audience Profile
{context['audience_profile']}

### Brand Notes (Authority and Trust Signals, Service Lines)
{context['brand_notes_excerpt']}

### Stage 1 Handoff Brief
{context['stage1_handoff']}

---

Using the research context above as your source material, produce the full 8-section 
Research Dossier as specified in the Stage 1 contract. The research context is your 
grounded evidence base — do not invent sources or data points beyond what is present.

The Sub-Queries Generated above directly map to Section 1 (Topic and Semantic Field).
Format the Source Bank (Section 2) from the Sources Gathered list above.
Sections 3–8 require your analysis of the gathered material combined with client context.
"""
        return await self._llm.complete(user, system=system)

    async def run(self, run: Run) -> StageOutput:
        """
        Override base run() to implement the two-sub-step pattern.
        """
        self._check_prerequisites(run)
        context = self._load_context(run)
        
        # Sub-step A: gpt-researcher gathers raw research
        raw_research = await self._gather_raw_research(run, context)
        
        # Sub-step B: pipeline LLM structures it into the 8-section dossier
        raw_dossier = await self._build_structured_dossier(run, context, raw_research)
        
        output = self._parse_output(raw_dossier, run)
        
        # Store raw research metadata alongside the structured dossier
        output.quality_gate_results["gpt_researcher"] = {
            "sources_gathered": len(raw_research["sources"]),
            "sub_queries_generated": len(raw_research["sub_queries"]),
            "research_costs": raw_research["research_costs"],
        }
        
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

### 4.3 Revised `SourceValidationService` (Stage 1.5)

```python
# services/source_validation_service.py
from gpt_researcher import GPTResearcher
from gpt_researcher.skills.curator import SourceCurator
from domain.enums import AuthorityMode
from config.authority_model_loader import AuthorityModelLoader

class SourceValidationService:
    """
    Stage 1.5: Source Validation.
    
    Uses gpt-researcher's SourceCurator as the core credibility-ranking engine.
    Pipeline logic layered on top:
    - Industry authority model applied as additional curator context
    - Tri-state status (APPROVED / APPROVED_WITH_FALLBACK / REJECTED) computed
      from curator's ranked output
    - EXPERT_FALLBACK mode and claim repositioning rules generated when needed
    - URL accessibility retry loop (gpt-researcher drops failed URLs silently;
      pipeline tracks and retries them explicitly)
    
    Input: 01_Research_Dossier.md (from Stage 1 stage_output.article_content)
    Output: source_validation_report stored in stage_outputs + runs tables
    """

    MAX_RETRIES = 6
    MIN_VERIFIED_SOURCES = 3

    def __init__(self, authority_loader: AuthorityModelLoader):
        self._authority_loader = authority_loader

    async def validate(
        self, dossier: str, run: Run
    ) -> ValidationReport:
        # Extract the Source Bank from Section 2 of the dossier
        sources = self._extract_source_bank(dossier)
        
        # Load industry authority model for this client
        authority_model = self._authority_loader.load(
            client_id=run.client_id,
            industry=run.context.industry,
        )
        
        # Attempt URL accessibility verification with retry
        verified_sources, failed_sources = await self._verify_with_retry(
            sources, max_retries=self.MAX_RETRIES
        )
        
        # Run SourceCurator on verified sources with industry context injected
        curated = await self._run_curator(
            verified_sources=verified_sources,
            query=run.context.topic,
            authority_model=authority_model,
        )
        
        # Compute tri-state status
        return self._compute_status(
            curated=curated,
            failed_sources=failed_sources,
            authority_model=authority_model,
            run=run,
        )

    async def _run_curator(
        self, verified_sources: list, query: str, authority_model: dict
    ) -> list:
        """
        Drive SourceCurator directly as a component, not through GPTResearcher.
        Inject the industry authority model as additional evaluation criteria.
        """
        # Build a minimal GPTResearcher instance to satisfy SourceCurator's
        # dependency on the parent researcher object
        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
        )
        # No hardcoded model — gpt-researcher reads SMART_LLM from env vars automatically
        researcher.cfg.curate_sources = True
        
        # Inject industry authority guidance into the curator prompt
        # gpt-researcher's PromptFamily is extensible; we override the
        # curate_sources prompt to include industry-specific criteria
        researcher.prompt_family = IndustryAwarePromptFamily(
            base_family=researcher.prompt_family,
            authority_model=authority_model,
        )
        
        # Set research_data to our verified sources
        researcher.research_data = [
            {"url": s["url"], "raw_content": s["content"]}
            for s in verified_sources
        ]
        
        curator = SourceCurator(researcher)
        return await curator.curate_sources(
            query=query,
            source_data=researcher.research_data,
            max_results=10,
        )

    def _compute_status(
        self, curated: list, failed_sources: list,
        authority_model: dict, run: Run
    ) -> ValidationReport:
        """
        Map curator output to pipeline tri-state status.
        
        APPROVED:
          - All required sources verified
          - Curator returned ≥ MIN_VERIFIED_SOURCES results
          - At least one source meets authority model's credibility threshold
        
        APPROVED_WITH_FALLBACK:
          - Some sources failed verification but curated set is non-empty
          - Curator results do not meet authority model's tier-1 criteria
          - Pipeline enters EXPERT_FALLBACK: claims repositioned under
            practitioner expertise rather than external citations
        
        REJECTED:
          - Curated set is empty after retries
          - OR all sources below authority model's minimum threshold
        """
        if not curated:
            return ValidationReport(status=ValidationStatus.REJECTED)
        
        high_authority = [
            s for s in curated
            if self._meets_authority_threshold(s, authority_model, tier=1)
        ]
        
        if len(high_authority) >= self.MIN_VERIFIED_SOURCES:
            return ValidationReport(
                status=ValidationStatus.APPROVED,
                curated_sources=curated,
            )
        
        # Fallback: generate claim repositioning rules from the authority model
        fallback_rules = self._generate_fallback_rules(authority_model, curated)
        
        return ValidationReport(
            status=ValidationStatus.APPROVED_WITH_FALLBACK,
            curated_sources=curated,
            authority_mode=AuthorityMode.EXPERT_FALLBACK,
            fallback_reason=f"Only {len(high_authority)} tier-1 sources verified",
            allowed_claims=fallback_rules["allowed"],
            disallowed_claims=fallback_rules["disallowed"],
        )
```

### 4.4 Industry-Aware Prompt Injection

gpt-researcher's `PromptFamily` controls the curator's evaluation criteria. We subclass it to inject the pipeline's industry authority model:

```python
# llm/industry_aware_prompt_family.py
class IndustryAwarePromptFamily:
    """
    Wraps gpt-researcher's PromptFamily to inject industry-specific
    source authority criteria into the SourceCurator prompt.
    
    The authority model (e.g., home_services.json) defines:
    - Tier-1 sources: government agencies, industry standards bodies,
      licensed professional associations
    - Tier-2 sources: major trade publications, recognized research firms
    - Forbidden sources: aggregators, unsourced opinion blogs,
      competitor sites
    
    These criteria are appended to the base curator prompt so the
    SMART_LLM evaluates sources against industry-specific standards,
    not just generic credibility.
    """
    
    def __init__(self, base_family, authority_model: dict):
        self._base = base_family
        self._authority_model = authority_model

    def curate_sources(self, *args, **kwargs) -> str:
        base_prompt = self._base.curate_sources(*args, **kwargs)
        
        industry_criteria = self._build_industry_criteria()
        
        return f"""{base_prompt}

## Industry-Specific Authority Criteria

Industry: {self._authority_model.get('industry', 'General')}

Tier-1 Sources (highest credibility for this industry):
{chr(10).join(f"- {s}" for s in self._authority_model.get('tier1_sources', []))}

Tier-2 Sources (acceptable with attribution):
{chr(10).join(f"- {s}" for s in self._authority_model.get('tier2_sources', []))}

Sources to treat with low credibility in this industry:
{chr(10).join(f"- {s}" for s in self._authority_model.get('low_credibility_patterns', []))}

Apply these criteria in addition to the general credibility guidelines above.
"""
```

---

## 5. Data Flow Changes

The introduction of gpt-researcher changes the internal data flow of Stage 1 but not its contract with Stage 2.

### Before (hand-rolled)
```
Stage 1 input → Single LLM call → 8-section dossier output
```

### After (gpt-researcher)
```
Stage 1 input
  → GPTResearcher.conduct_research()
    → ResearchConductor.plan_research()      [sub-query generation]
    → BrowserManager parallel scrape         [20+ sources, 15 workers]
    → ContextManager.compress()              [embedding similarity filter]
  → raw_research dict {context, sources, sub_queries, costs}
  → Pipeline LLM call with raw_research as grounded source material
  → 8-section dossier output (same contract as before)
```

**The Stage 2 handoff document is identical.** Stage 2 loads `01_Research_Dossier.md` and `01_Stage_2_Handoff.md` — neither file changes structure. Stage 2 is completely unaware that gpt-researcher was used.

### Stage 1.5 data flow changes

```
Before:
  Dossier → URL accessibility check (retry loop) → industry authority eval → tri-state

After:
  Dossier 
    → URL accessibility check (retry loop, same as before)
    → GPTResearcher + SourceCurator [credibility ranking replaces manual authority eval]
      + IndustryAwarePromptFamily [authority model injected as curator context]
    → tri-state status (same APPROVED/FALLBACK/REJECTED contract as before)
    → fallback rules if needed (same structure as before)
```

**Stage 2 handoff is identical.** Stage 2 reads `Authority_Mode` and fallback rules from `01_Stage_2_Handoff.md` — that document's structure does not change.

---

## 6. Database Changes

Minimal. One new column on `stage_outputs` to store gpt-researcher's metadata alongside the structured dossier:

```sql
-- Store gpt-researcher run metadata with the Stage 1 output
ALTER TABLE stage_outputs ADD COLUMN gpt_researcher_meta JSONB;

-- Example stored value:
-- {
--   "sources_gathered": 23,
--   "sub_queries_generated": 7,
--   "research_costs": {"total_tokens": 42000, "estimated_cost_usd": 0.18},
--   "retriever": "tavily",
--   "curate_sources_used": false
-- }
```

The `source_validation_reports` table is unchanged — it stores the same tri-state output regardless of whether gpt-researcher's curator or a custom ranking produced it.

---

## 7. What gpt-researcher's Frontend and Backend Are Not Used For

gpt-researcher ships with a FastAPI server (`backend/server.py`) and a Next.js frontend. These are **not used** in the integration:

- The pipeline has its own FastAPI backend (`api/`) — gpt-researcher is imported as a Python library, not run as a server
- The pipeline has its own Next.js frontend — gpt-researcher's UI is not deployed
- The pipeline has its own WebSocket/SSE streaming — gpt-researcher's `websocket` parameter is set to `None`; the pipeline streams its own stage execution events

gpt-researcher's Docker setup (`Dockerfile`, `docker-compose.yml`) is similarly not used — the pipeline's own deployment handles containerization.

---

## 8. Dependency and Version Constraints

```toml
# pyproject.toml additions
[tool.poetry.dependencies]
gpt-researcher = "^0.10"       # pinned to 0.10.x series; API stable since 0.9
tavily-python = "^0.3"         # primary retriever
```

gpt-researcher uses `asyncio` throughout. The pipeline's `StageContract.run()` must be `async` — the revised `ResearchStage.run()` is already async (see Section 4.2). All other stage contracts that do not use gpt-researcher remain synchronous or can be wrapped with `asyncio.run()` at the worker level.

---

## 9. Migration Path Changes

The existing Phase 5 (Core Stages 1–5) in `architecture_migration_plan_v2.md` gains one sub-step at Stage 1:

**Revised Stage 1 build sequence:**

1. Install `gpt-researcher` and configure environment variables
2. Write `_gather_raw_research()` (Sub-step A) — drive `GPTResearcher` as a library, verify it returns expected `research_context`, `sources`, and `sub_queries`
3. Write `_build_structured_dossier()` (Sub-step B) — verify the 8-section dossier output matches the reference run's `01_Research_Dossier.md` structure
4. Verify the `RESEARCH NOTES FOR STAGE 2` informal section still appears (pipeline LLM generates it; gpt-researcher does not)
5. Store `gpt_researcher_meta` JSONB alongside the output

**Revised Stage 1.5 build sequence:**

1. Write `IndustryAwarePromptFamily` and verify the curator prompt includes industry criteria
2. Write `_run_curator()` using `SourceCurator` directly as a component
3. Write `_compute_status()` and verify tri-state output matches the existing `ValidationReport` contract
4. Verify `APPROVED_WITH_FALLBACK` path produces `allowed_claims` / `disallowed_claims` in the same format Stage 2 expects

**Acceptance criteria are unchanged** from v2: given the same client reference files and topic, the Dossier and source validation outputs must be structurally equivalent to the reference run.

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| gpt-researcher sub-query decomposition generates queries that miss the pipeline's audience angle | Medium | Medium | Enrich the `_build_research_query()` prompt with Audience Profile summary; validate sub-queries against the reference run's 8 semantic queries |
| SourceCurator ranks sources differently than the pipeline's manual authority eval | Medium | Low | Stage 1.5 still applies industry authority model as a secondary filter; curator ranking is an input, not the final decision |
| gpt-researcher API changes break the `SourceCurator` direct instantiation pattern | Low | High | Pin to `0.10.x`; monitor releases; the curator is a standalone class with a stable interface |
| Tavily API cost at 20+ sources per run adds up at scale | Medium | Medium | `MAX_SEARCH_RESULTS_PER_QUERY=5` with 7 sub-queries ≈ 35 searches per run; benchmark cost per article and set budget alerts |
| gpt-researcher's `conduct_research()` is async; worker task queue must support async | Low | High | ARQ natively async; Celery requires `asyncio` bridge (`celery[gevent]` or `asgiref`); choose ARQ for the worker layer |
| gpt-researcher's WebSocket callbacks fire during research and cannot be easily suppressed | Low | Low | Set `websocket=None`; callbacks no-op silently; pipeline streams its own events |

---

*Addendum version 1.0 — July 2026. Read alongside `architecture_migration_plan_v2.md`. This addendum scopes the integration to Stage 1 and Stage 1.5 only. All other stages, database tables, API contracts, and frontend components are unaffected.*
