# Phase 3 & 4 — Onboarding and Run Init
**Weeks 5–7 | Gate: Full onboarding flow + Path A and Path B run initialization**

These two phases build the client management foundation. Everything downstream depends on correctly onboarded clients and properly initialized runs.

---

# PHASE 3 — Onboarding

## Step 3.1 — Implement Repository Methods

```
Implement the client repository methods we stubbed in Phase 1.
We need these for onboarding to work.

In content_pipeline/repositories/client_repository.py, implement:

- create_client(client: Client) -> Client
  INSERT into clients table; return with generated UUID

- get_client(client_id: UUID) -> Client
  SELECT from clients; raise ClientNotFoundError if not found

- get_reference_files(client_id: UUID) -> ClientReferenceFiles
  SELECT from client_reference_files; return ClientReferenceFiles domain object
  If no row exists yet, return a ClientReferenceFiles with all None fields (ClientState.NEW)

- save_reference_files(client_id: UUID, files: ClientReferenceFiles) -> ClientReferenceFiles
  UPSERT into client_reference_files
  Also update onboarding_state based on which files are present:
    all three not None → "fully_onboarded"
    some not None → "partial"
    all None → "new"

- save_client_context(client_id: UUID, context: ClientContext) -> None
  UPSERT into client_contexts

- get_client_context(client_id: UUID) -> Optional[ClientContext]
  SELECT from client_contexts; return None if not found

Write integration tests in tests/test_repositories.py that:
1. Create a client, save it, retrieve it, confirm fields match
2. Save reference files with only style_reference_card populated
3. Retrieve and confirm state is "partial"
4. Save all three files, confirm state is "fully_onboarded"

These tests require a real Supabase connection. Use a test-specific client name
prefixed with "TEST_" so we can clean them up.

Run the tests and show me the output.
```

---

## Step 3.2 — Brand Color Extraction

```
Create content_pipeline/config/brand_color_extractor.py.

This extracts the 11 required CSS token values from a Style Reference Card markdown string.
It runs at Stage 0 (onboarding) and stores results in client_reference_files.brand_colors.

The 11 required keys and their value formats:
- primary, primary_2, primary_soft, accent, accent_2, accent_soft, ink → hex strings "#RRGGBB"
- primary_glow, line_strong → rgba strings "rgba(r, g, b, a)"
- primary_rgb, accent_rgb → triplet strings "r, g, b" (NO # prefix — used inside rgba())

Create class BrandColorExtractor with method:
- extract(style_reference_card: str) -> dict[str, str]
  Returns dict with all 11 keys populated
  Raises MissingBrandColorError if any key cannot be extracted

- validate(brand_colors: dict) -> list[str]
  Returns list of validation errors (empty = valid)
  Checks: all 11 keys present, hex values are valid hex, rgb triplets have no # prefix

Create tests/test_brand_colors.py:

def test_rgb_triplets_have_no_hash_prefix():
    """
    PRIMARY_RGB and ACCENT_RGB must NOT have # prefix.
    They are used inside rgba() in the CSS. A # prefix breaks the function.
    """
    # Use the Rankrise reference values we know are correct
    colors = {
        "primary_rgb": "27, 61, 111",
        "accent_rgb": "232, 118, 43",
    }
    extractor = BrandColorExtractor()
    errors = extractor.validate(colors)
    
    for key in ["primary_rgb", "accent_rgb"]:
        assert not colors[key].startswith("#"), \
            f"{key} must not start with #, got: {colors[key]}"

def test_all_11_keys_required():
    extractor = BrandColorExtractor()
    incomplete = {"primary": "#1B3D6F"}  # missing 10 keys
    errors = extractor.validate(incomplete)
    assert len(errors) == 10, f"Expected 10 errors, got {len(errors)}"

Run tests. Show me output.
```

---

## Step 3.3 — OnboardingStage Service

```
Create content_pipeline/services/onboarding_service.py.

This implements StageContract for Stage 0.

Key behaviors (from BUILD_GUIDE.md — Stage 0 section):

1. _check_prerequisites: Always passes (Stage 0 has no prerequisites)

2. _load_context: Returns the client state and content samples provided by the user

3. Client state detection must happen BEFORE writing anything:
   - NEW → generate all 3 reference files
   - PARTIAL → generate only missing files; never overwrite existing
   - FULLY_ONBOARDED → raise ClientAlreadyOnboardedError
     (unless regenerate=True was passed, which requires explicit user confirmation)

4. _build_prompt: Constructs the LLM prompt using the Stage 0 CONTEXT.md contract.
   The system prompt is: read docs/stage_contracts/stage0_onboarding_CONTEXT.md
   The user prompt contains the content samples and client info.

5. _parse_output: The LLM output contains three sections separated by ### OUTPUT headers.
   Parse each into the corresponding reference file content.
   Also extract:
   - Brand colors from Style Reference Card → brand_colors JSONB
   - Reading level from Audience Profile → reading_level_target
   - Certifications from Brand Notes → certifications[]
   - YMYL category from industry → ymyl_category

6. _validate_output: Check that:
   - All 3 reference files have content
   - Style Reference Card contains required sections (WRITING STYLE GUIDELINES,
     VISUAL BRAND THEME, STRUCTURAL GUIDELINES, SEO & KEYWORD GUIDANCE)
   - Brand Notes contains OPEN QUESTIONS FOR CLIENT section with [ ] items
   - Brand colors were successfully extracted (all 11 keys present)

7. _build_handoff: No handoff file for Stage 0 (it produces reference files, not a run handoff)
   Instead, write a run log entry to client_run_log.

Also create content_pipeline/orchestration/unresolved_item_tracker.py:
Class UnresolvedItemTracker with methods:
- add_item(run_id, description, blocks_run, source_stage) -> UnresolvedItem
- resolve_item(run_id, description, resolved_at_stage) -> None
- blocking_items(run_id) -> list[UnresolvedItem]
- open_items(run_id) -> list[UnresolvedItem]
- for_handoff(run_id) -> str  (formats open items as handoff section text)

Show me onboarding_service.py before implementing. Wait for approval.
```

**Human checkpoint:** Read the proposed `onboarding_service.py` before the AI implements it. Confirm: state detection is first, ClientAlreadyOnboardedError is raised for FULLY_ONBOARDED, brand color extraction is called in `_parse_output`. Approve before the AI proceeds.

---

## Step 3.4 — Onboarding API Endpoint and UI

```
Implement the onboarding endpoint and a basic UI form.

FastAPI — implement content_pipeline/api/clients.py:

POST /clients
  Body: CreateClientRequest {name, website_url, industry, service_area, off_limits: []}
  Creates client record; returns ClientResponse with id and onboarding_state="new"

POST /clients/{client_id}/onboard
  Body: OnboardingRequest {content_samples: [{type, content/url}], additional_context: {}, regenerate: false}
  - If client is FULLY_ONBOARDED and regenerate=False → 409 ClientAlreadyOnboarded
  - Otherwise → enqueue background job via ARQ; return 202 {"job_id": "...", "status": "queued"}

GET /clients/{client_id}/onboarding/status
  Returns section-by-section validation status per REFERENCE.md API section

GET /jobs/{job_id}
  Returns {"status": "queued|running|complete|failed", "result": {...}}

ARQ worker — create content_pipeline/workers/stage_worker.py:
  async def run_stage(ctx, run_id, stage_num, job_id) — calls orchestrator.execute_stage
  For Stage 0 (onboarding), job_id is stored differently (not tied to a run)
  Create a jobs table or use Redis for job state tracking

Next.js — create frontend/app/clients/new/page.tsx:
  A form with fields: Client Name, Industry (dropdown of 5 options), Website URL, Service Area
  On submit, POST to /clients then redirect to /clients/{id}/onboard
  
  Create frontend/app/clients/[clientId]/onboard/page.tsx:
  A form to paste content samples (textarea) and additional context
  On submit, POST to /clients/{clientId}/onboard
  Poll /jobs/{job_id} every 2 seconds; show progress; redirect to client page when done

Show me the API endpoint signatures before implementing.
```

---

## Step 3.5 — Stage Contract Files

```
Copy the pipeline's stage CONTEXT.md files into the project so prompt_builder.py can load them.

Create docs/stage_contracts/ directory and copy these files into it:
- stage0_onboarding_CONTEXT.md
- stage1_1_onboarded_CONTEXT.md (Pre-Stage 1)
- stage1_2_Research_CONTEXT.md
- stage2_brief_CONTEXT.md
- stage3_writing_CONTEXT.md
- stage4_humanization_CONTEXT.md
- stage5_seo_CONTEXT.md
- stage6_qa_CONTEXT.md
- stage7_blog-formatting_CONTEXT.md

Also copy these _config files:
- docs/pipeline_config/anti-ai-checklist.md
- docs/pipeline_config/search-quality-rubric.md
- docs/pipeline_config/handoff_template.md
- docs/pipeline_config/source-validation-framework.md

Then update content_pipeline/llm/prompt_builder.py to load from these paths.

IMPORTANT: These files contain the workflow rules that the LLM must follow.
They are the system prompt for each stage. When building a stage prompt,
the stage contract is always the system prompt — never part of the user message.
```

---

# PHASE 4 — Run Initialization

## Step 4.1 — ClientContextAssembler

```
Create content_pipeline/orchestration/context_assembler.py.

This class replaces the old CONTEXT.md file by assembling engagement context
from live database state. Read docs/architecture_addendum_templates.md —
Section "Revised CONTEXT.md Behavior in the Application" for the full specification.

The assembled context includes:
- Client name, industry, website, service area, onboarding state (from clients table)
- Active since, engagement notes, next planned topic (from client_contexts table)
- Last run folder slug (from MAX(runs.updated_at) WHERE client_id)
- Posts published count (from COUNT(*) WHERE published_articles.client_id)
- Open items count (from unresolved_items)

Class ClientContextAssembler with method:
- assemble(client_id: UUID) -> str
  Returns formatted markdown string that mimics CONTEXT.md structure

The computed fields (last run, posts published, open items) are NEVER stored —
they are always computed fresh at assembly time.

Write a test that:
1. Creates a test client in the DB
2. Calls assemble(client_id)
3. Confirms the output contains the client name
4. Confirms it contains "Posts published: 0" (no articles yet)
5. Confirms it contains "Open items: None" (no unresolved items yet)
```

---

## Step 4.2 — Run Init Service (Pre-Stage 1)

```
Create content_pipeline/services/run_init_service.py.

This implements Pre-Stage 1. Read BUILD_GUIDE.md — "Pre-Stage 1" section.

Two paths that must both be supported:
- PATH_A: User provides topic + keyword → overlap check → confirm → create run
- PATH_B: No topic → generate 4-6 recommendations → user selects → overlap check → create run

Key behaviors:
1. Overlap check queries published_articles for matching keyword or slug
   If overlap found: return overlap details; do not create run until user confirms
   
2. Topic recommendations (Path B): LLM generates 4-6 recommendations using the
   Content Gap Analysis approach (audience pain points + published content inventory)
   Each recommendation has: topic, primary_keyword, why_now, audience_intent, eeat_angle

3. Run folder slug: Title_Case_Topic_YYYY-MM convention
   "Content Marketing for Home Service Businesses" + 2026-06
   → "Content_Marketing_Home_Services_2026-06"

4. UnresolvedItem creation: Brand Notes open questions become UnresolvedItem records
   attached to the new run. blocks_run=False for all standard open questions.

5. Handoff file (00_Stage_1_Handoff_Brief.md content stored as stage_output):
   Contains all carry-forward context per handoff_template.md format
   Auto-run: false (sequential human-supervised mode)

Also implement run_repository.py methods:
- create_run(run: Run) -> Run
- get_run(run_id: UUID) -> Run
- save_unresolved_item(item: UnresolvedItem) -> UnresolvedItem
- get_unresolved_items(run_id: UUID) -> list[UnresolvedItem]
- get_published_slugs(client_id: UUID) -> list[str]  (for overlap check)

Implement the API endpoints:
POST /clients/{client_id}/runs
  Body: RunInitRequest {topic_path: "user_provided"|"ideation", topic?, keyword?}
  Returns: RunResponse with id, folder_slug, status="initiated"

POST /clients/{client_id}/runs/{run_id}/topic-recommendations
  Body: {count: 5}
  Returns: TopicRecommendationsResponse per REFERENCE.md API section

POST /clients/{client_id}/runs/{run_id}/confirm-topic
  Body: {topic, primary_keyword, recommendation_n?}
  Runs overlap check; if clear, creates run folder; returns run

Show me the run_init_service.py _build_prompt method before implementing.
```

---

## Phase 3 & 4 Gate Check

```
Phase 3 & 4 gate check. Run the full test suite and show me results.

Then run these manual checks:

1. Onboarding a new client:
   POST /clients with name="Test Onboard Client", industry="home_services"
   POST /clients/{id}/onboard with a text sample about a plumbing business
   Poll /jobs/{job_id} until complete
   GET /clients/{id}/reference and confirm three files are present
   GET /clients/{id}/onboarding/status and confirm onboarding_state="fully_onboarded"

2. Attempting to onboard a FULLY_ONBOARDED client without regenerate=true:
   POST /clients/{id}/onboard again (same client)
   Confirm the API returns 409 with error code CLIENT_ALREADY_ONBOARDED

3. Run initialization — Path A:
   POST /clients/{id}/runs with topic_path="user_provided",
   topic="Content Marketing for Home Services", keyword="content marketing home services"
   Confirm run is created with status="initiated"
   Confirm at least one UnresolvedItem exists for the run
   (The Brand Notes open questions should have created items)

4. Run initialization — Path B:
   POST /clients/{id}/runs with topic_path="ideation"
   POST /clients/{id}/runs/{run_id}/topic-recommendations with count=5
   Confirm 5 recommendations returned
   POST /clients/{id}/runs/{run_id}/confirm-topic with the first recommendation
   Confirm run status updates

Report each as PASS or FAIL with one sentence.
All four must pass before Phase 5.
```

**Human:** Test the onboarding output quality manually. Open the generated Style Reference Card in the database and check that it has all four required sections. Check that brand_colors JSONB has all 11 keys and that primary_rgb does NOT start with "#".
