# Phase 1 — Foundation
**Weeks 1–2 | Gate: Create a client via API, confirm it persists, retrieve it**

Paste each prompt into Cursor chat in order. Complete the gate check before moving to Phase 2.

---

## Step 1.1 — Supabase Project and Schema

```
Create the Supabase database schema for the content pipeline.

Read docs/REFERENCE.md — the complete SQL schema is in the "Database Schema" section.

Create the migration file at supabase/migrations/001_initial_schema.sql containing:
- All CREATE TABLE statements in dependency order (clients first, then dependent tables)
- All CREATE INDEX statements
- A comment block at the top listing every table name

Then create supabase/seeds/001_authority_models.sql that seeds the authority_models table
with all five industry configs. The industry config data is in:
- docs/architecture_addendum_final.md — Section 3 "Authority Models"

The seed file should INSERT one row per industry:
home_services, health_wellness_spa, software_development, financial_advisory, legal_services

Also create supabase/seeds/002_css_template.sql that seeds the css_templates table
with name="blog_integration_base" and token_names as the array of 11 token names.
The css_content column should be populated from the file reference_run/07_Blog_Final.html
— extract only the <style> block content (we will replace this with the actual
blog_integration_base.css content when the file is in the project).

Show me the migration file before running it. Do not run migrations yet.
```

**Human checkpoint:** Read the migration file. Confirm every table from REFERENCE.md is present. Check that `min_valid_sources` for home_services is 0. Approve before proceeding.

---

## Step 1.2 — Python Backend Scaffold

```
Set up the Python backend project structure.

Create the following files with correct content:

pyproject.toml with dependencies:
- fastapi>=0.111
- uvicorn[standard]>=0.29
- supabase>=2.4
- anthropic>=0.28
- gpt-researcher>=0.10
- arq>=0.25
- pydantic>=2.7
- python-dotenv>=1.0

.env.example with all required environment variables:
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_KEY
- ANTHROPIC_API_KEY
- TAVILY_API_KEY
- RETRIEVER=tavily
- SMART_LLM=claude-sonnet-4-6
- FAST_LLM=claude-haiku-4-5-20251001
- STRATEGIC_LLM=claude-sonnet-4-6
- MAX_SCRAPER_WORKERS=15
- MAX_SEARCH_RESULTS_PER_QUERY=5
- CURATE_SOURCES=false

Create the directory structure from BUILD_GUIDE.md — Module Structure section.
Create __init__.py in each Python package directory.
Create a content_pipeline/main.py with a minimal FastAPI app and a GET /health endpoint
that returns {"status": "ok", "version": "0.1.0"}.

Do not write any business logic yet. Just the scaffold.
```

---

## Step 1.3 — Domain Models

```
Create all domain models in content_pipeline/domain/.

Read REFERENCE.md — the "Domain Enums" and "Domain Models" sections contain the exact code.

Create these files:
- content_pipeline/domain/enums.py — all enums exactly as specified
- content_pipeline/domain/client.py — UnresolvedItem, ClientReferenceFiles, Client
- content_pipeline/domain/run.py — RunContext, Run
- content_pipeline/domain/stage.py — QAIssue, QAResult, SEOAnnotation, StageOutput, ValidationReport, ClaimRepositioningRule, AuthorityModel

Rules:
- Use Python dataclasses (not Pydantic) for all domain models
- All fields must be typed
- No I/O, no database calls, no imports from outside the domain package
- ValidationReport should have fields matching the source_validation_reports table in REFERENCE.md

After creating the files, write a simple test in tests/test_domain.py that:
1. Creates a RunContext with a known topic and keyword
2. Creates an UnresolvedItem with blocks_run=False
3. Adds the item to run.context.unresolved_items
4. Asserts the item is retrievable and has the correct fields

Run the test and show me the output.
```

---

## Step 1.4 — Repository Layer

```
Create the repository classes in content_pipeline/repositories/.

These classes are the ONLY place database calls happen. No service or stage class
ever imports from supabase directly.

Create:
- content_pipeline/repositories/base_repository.py — base class with supabase client init
- content_pipeline/repositories/client_repository.py — CRUD for clients, client_contexts, client_reference_files
- content_pipeline/repositories/run_repository.py — CRUD for runs, unresolved_items, run_log, topic_recommendations
- content_pipeline/repositories/stage_output_repository.py — CRUD for stage_outputs, seo_annotations, qa_results, qa_issues
- content_pipeline/repositories/authority_model_repository.py — read authority_models, merge client overrides
- content_pipeline/repositories/reference_file_repository.py — read/write reference file content

Each repository method should:
- Accept typed domain model parameters
- Return typed domain model objects (not raw dicts)
- Raise specific exceptions (ClientNotFoundError, RunNotFoundError, etc.) not generic exceptions

For now, stub out all methods with NotImplementedError and the correct signature.
We will implement them one at a time as each phase needs them.

Show me client_repository.py and run_repository.py signatures.
```

---

## Step 1.5 — LLM Provider

```
Create the LLM abstraction layer in content_pipeline/llm/.

Create:

content_pipeline/llm/base_provider.py:
  Abstract class LLMProvider with methods:
  - async complete(prompt: str, system: str = "", **kwargs) -> str
  - async complete_with_stream(prompt: str, system: str = "", **kwargs) -> AsyncIterator[str]

content_pipeline/llm/anthropic_provider.py:
  Implements LLMProvider using the Anthropic Python SDK.
  - Uses claude-sonnet-4-6 by default
  - complete() returns the full text response
  - complete_with_stream() yields text delta chunks via async generator
  - Handles anthropic.APIError with a wrapped LLMProviderError

content_pipeline/llm/prompt_builder.py:
  Class PromptBuilder with method:
  - load_stage_contract(stage_name: str) -> str
  For now this reads from a docs/stage_contracts/ directory.
  We will populate that directory with the stage CONTEXT.md files.

After creating these, write a test in tests/test_llm.py that:
1. Creates an AnthropicProvider (uses real API key from .env)
2. Calls complete() with a simple "Say hello in one sentence." prompt
3. Asserts the response is a non-empty string
4. Calls complete_with_stream() with the same prompt
5. Asserts at least 3 chunks are yielded and the concatenated result is non-empty

Run the test. Show me the output.
```

---

## Step 1.6 — Stage Contract Base Class

```
Create the StageContract base class in content_pipeline/services/base_stage.py.

Read BUILD_GUIDE.md — the "Stage Contract" section contains the exact class structure.

The base class should:
- Be abstract (ABC)
- Have abstract properties: stage_number (int), stage_name (str)
- Have abstract methods: _check_prerequisites, _load_context, _build_prompt,
  _parse_output, _validate_output, _build_handoff
- Have a concrete async run(run: Run) -> StageOutput method that calls them in order:
  check_prerequisites → load_context → build_prompt → LLM complete → parse_output →
  validate_output → if failures: return FAILED output; else: build_handoff → save → return
- Accept repo, llm, parser, tracker in __init__

Also create these custom exceptions in content_pipeline/exceptions.py:
- MissingPrerequisiteError
- StageBlockedError (used by Stage 7 pre-flight gate)
- InternalTokenLeakError (used by Stage 7 token check)
- ClientNotFoundError
- ClientAlreadyOnboardedError
- RunNotFoundError
- LLMProviderError
- MissingBrandColorError
- ValidationError

Show me base_stage.py.
```

---

## Step 1.7 — FastAPI Skeleton and Next.js Shell

```
Create the FastAPI router structure and a basic Next.js frontend shell.

FastAPI:
Create content_pipeline/api/clients.py with stubbed endpoints:
- POST /clients — stub that returns {"id": "placeholder", "status": "not_implemented"}
- GET /clients — stub that returns []
- GET /clients/{client_id} — stub that raises HTTPException(501)

Create content_pipeline/api/runs.py and content_pipeline/api/stages.py with similar stubs.

Register all routers in content_pipeline/main.py.

Add CORS middleware configured for localhost:3000.

Next.js:
Run: npx create-next-app@14 frontend --typescript --tailwind --app --no-src-dir

After creation, replace the default app/page.tsx with a minimal dashboard page that:
- Has a heading "Content Pipeline"
- Has a "Clients" section that shows "Loading..." (will be populated later)
- Has a hardcoded status badge showing "Phase 1 — Foundation"

Start both servers and confirm:
- GET http://localhost:8000/health returns {"status": "ok", "version": "0.1.0"}
- GET http://localhost:3000 renders the dashboard page without errors
```

---

## Phase 1 Gate Check

Run this prompt after completing all steps above:

```
Phase 1 gate check. Please do the following:

1. Run the full test suite (pytest) and show me all results

2. Make a POST request to /clients with this body:
   {"name": "Test Client", "industry": "home_services", "website_url": "https://test.com"}
   
   This will return 501 — that's expected. Confirm the endpoint exists and responds.

3. Show me the directory tree of content_pipeline/ — confirm every directory and
   __init__.py from BUILD_GUIDE.md Module Structure exists.

4. Check that these five things are true:
   a. domain/ contains only dataclasses with no database imports
   b. repositories/ has stub methods with correct type signatures
   c. AnthropicProvider.complete() successfully called the Anthropic API in tests
   d. StageContract is abstract and cannot be instantiated directly
   e. The FastAPI app starts without errors

Report each check as PASS or FAIL with one sentence of explanation.
```

**Human:** If all five checks pass, move to Phase 2. If any fail, fix before proceeding.

---

## Step 1.5b — Additional LLM Providers (add after Step 1.5)

```
After creating AnthropicProvider, create the remaining three providers
and the factory that selects between them.

Read docs/architecture_addendum_llm_providers.md — Sections 3 and 4 contain
the exact implementation for all four providers and the factory.

Create:
- content_pipeline/llm/openrouter_provider.py — OpenRouterProvider
- content_pipeline/llm/ollama_provider.py — OllamaProvider
- content_pipeline/llm/lmstudio_provider.py — LMStudioProvider
- content_pipeline/llm/provider_factory.py — LLMProviderFactory

Also create:
- content_pipeline/config/provider_config.py — PROVIDER_QUALITY_TOLERANCES dict

Update pyproject.toml to add optional extras:
  [tool.poetry.extras]
  openrouter = ["langchain-openrouter"]
  ollama = ["langchain-ollama"]
  all-providers = ["langchain-openrouter", "langchain-ollama"]

Update .env.example with the full provider configuration block
from docs/architecture_addendum_llm_providers.md — Section 4.

IMPORTANT RULES:
- Stage services must use LLMProviderFactory, never import providers directly
- OpenRouterProvider uses langchain_openrouter.ChatOpenRouter
- OllamaProvider uses langchain_ollama.ChatOllama
- LMStudioProvider uses the standard openai.AsyncOpenAI client with base_url override
- All three implement complete() and complete_with_stream() matching the ABC

After creating all four, run the provider tests from
docs/architecture_addendum_llm_providers.md — Section 9.

The integration tests (marked @pytest.mark.integration) only run when the
corresponding API key or local service is available. Show me which tests
pass in your environment.
```

**Human checkpoint:** Before moving on, confirm:
1. `LLMProviderFactory.create_smart_provider()` returns `AnthropicProvider` when `LLM_PROVIDER=anthropic`
2. `LLMProviderFactory.create_smart_provider()` returns `OpenRouterProvider` when `LLM_PROVIDER=openrouter`
3. No stage service file imports any provider class directly — all go through the factory
