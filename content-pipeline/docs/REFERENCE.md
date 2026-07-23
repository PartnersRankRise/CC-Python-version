# Content Pipeline — Reference

**What this is:** Data models, database schema, API contracts, and domain rules. Look things up here during implementation. Read alongside `BUILD_GUIDE.md`.

---

## Domain Enums

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
    PIPELINE_FAILURE = "pipeline_failure"    # route to revision stage
    CLIENT_DECISION = "client_decision"      # human action outside pipeline
    MINOR_OBSERVATION = "minor_observation"  # informational; no action required

class ValidationStatus(Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_FALLBACK = "APPROVED_WITH_FALLBACK"
    REJECTED_DOSSIER_NOT_FOUND = "REJECTED_DOSSIER_NOT_FOUND"
    REJECTED_NO_SOURCES = "REJECTED_NO_SOURCES"
    REJECTED_CONFIG_NOT_FOUND = "REJECTED_CONFIG_NOT_FOUND"
    REJECTED_MIN_SOURCES_ZERO = "REJECTED_MIN_SOURCES_ZERO"

class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"

class FallbackAuthorityType(Enum):
    PRACTITIONER_EXPERTISE = "PRACTITIONER_EXPERTISE"  # health_wellness_spa
    ATTORNEY_EXPERTISE = "ATTORNEY_EXPERTISE"          # legal_services
    FIELD_EXPERTISE = "FIELD_EXPERTISE"                # home_services
    ADVISOR_EXPERTISE = "ADVISOR_EXPERTISE"            # financial_advisory
    DEVELOPER_EXPERTISE = "DEVELOPER_EXPERTISE"        # software_development
    INDUSTRY_STANDARDS = "INDUSTRY_STANDARDS"          # secondary, multiple industries
    CLIENT_OBSERVATION = "CLIENT_OBSERVATION"
    OPEN_SOURCE_COMMUNITY = "OPEN_SOURCE_COMMUNITY"
    MANUFACTURER_DATA = "MANUFACTURER_DATA"
    CASE_PRECEDENT = "CASE_PRECEDENT"
    REGULATORY_FRAMEWORK = "REGULATORY_FRAMEWORK"
    STATUTORY_FRAMEWORK = "STATUTORY_FRAMEWORK"
```

---

## Domain Models

```python
# domain/client.py
@dataclass
class UnresolvedItem:
    description: str
    blocks_run: bool
    source_stage: int
    resolved: bool = False
    resolved_at_stage: Optional[int] = None

@dataclass
class RunContext:
    client_id: UUID
    topic: str
    primary_keyword: str
    topic_path: TopicPath
    angle_notes_sanitized: Optional[str] = None   # never raw CRM text
    priority_sources: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = field(default_factory=list)
    authority_mode: AuthorityMode = AuthorityMode.NORMAL
    fallback_status: Optional[str] = None
    allowed_claims: list[str] = field(default_factory=list)
    disallowed_claims: list[str] = field(default_factory=list)
    article_slug: Optional[str] = None            # derived from H1 at Stage 7
    schema_recommendation: Optional[str] = None   # from Stage 5 annotation
    word_count_result: Optional[dict] = None      # {count, target_min, target_max, status}

@dataclass
class Run:
    id: UUID
    client_id: UUID
    folder_slug: str      # e.g., "Content_Marketing_Home_Services_2026-06"
    status: RunStatus
    context: RunContext
    current_stage: int
    created_at: datetime
    updated_at: datetime
    human_review_flag: Optional[str] = None
    dry_run: bool = False

# domain/stage.py
@dataclass
class QAIssue:
    section: str                          # "A" through "I"
    description: str
    issue_type: QAIssueType
    stage_responsible: Optional[int]      # None for client_decision, minor_observation

@dataclass
class QAResult:
    decision: QADecision
    checklist_score: tuple[int, int]      # (passed, total)
    ai_risk_score: int                    # /15; revision if > 10
    section_results: dict[str, str]       # {"A": "PASS", "F": "FLAG", ...}
    issues: list[QAIssue]
    human_review_flag: Optional[str]
    revision_stage: Optional[int]

@dataclass
class SEOAnnotation:
    changes_summary: list[str]
    keyword_density: dict                 # {keyword, occurrences, total_words, density_pct, status}
    meta_title: dict                      # {text, char_count, status}
    meta_description: dict                # {text, char_count, status}
    schema_recommendation: str
    internal_links: list[dict]            # [{anchor, destination, section, confirmed}]
    readability_note: dict                # {target_level, actual_level, status}
    word_count: dict                      # {count, target_min, target_max, status}
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
    article_content: Optional[str]        # reader-facing content only; no appended sections
    editorial_note: Optional[str]         # Stage 4 only; never passed downstream
    seo_annotation: Optional[SEOAnnotation]  # Stage 5 only; never passed downstream
    qa_result: Optional[QAResult]         # Stage 6 only
    handoff_content: Optional[str]
    quality_gate_results: dict
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

---

## Database Schema

```sql
-- ============================================================
-- CLIENTS
-- ============================================================

CREATE TABLE clients (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              TEXT NOT NULL,
  website_url       TEXT,
  industry          TEXT,            -- matches authority_models.industry_key
  service_area      TEXT,
  off_limits        TEXT[],
  engaged_at        DATE,
  style_overrides   JSONB DEFAULT '{}',   -- e.g., google_fonts override
  authority_overrides JSONB DEFAULT '{}', -- client-level source validation overrides
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE client_contexts (
  -- Mutable engagement record. Replaces CONTEXT.md.
  -- "Last run" and "Posts published" are computed from runs/published_articles; not stored here.
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id            UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  next_planned_topic   TEXT,
  engagement_notes     TEXT,
  run_history_summary  TEXT,
  updated_at           TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id)
);

CREATE TABLE client_reference_files (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id             UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  style_reference_card  TEXT,
  audience_profile      TEXT,
  brand_notes           TEXT,
  onboarding_state      TEXT NOT NULL DEFAULT 'new'
    CHECK (onboarding_state IN ('new', 'partial', 'fully_onboarded')),
  -- Parsed from Style Reference Card at Stage 0 — used by Stage 7
  brand_colors          JSONB DEFAULT '{}',
  -- Exact keys required in brand_colors:
  -- primary, primary_2, primary_soft, primary_glow, primary_rgb (no # prefix),
  -- accent, accent_2, accent_soft, accent_rgb (no # prefix), ink, line_strong
  display_font          TEXT,
  body_font             TEXT,
  google_fonts_url      TEXT,
  -- Parsed from Audience Profile at Stage 0 — used by Stage 5 readability check
  reading_level_target  TEXT,        -- e.g., "8th-10th grade"
  technical_depth       TEXT,        -- "beginner" | "intermediate" | "expert"
  -- Parsed from Brand Notes at Stage 0 — used by Stages 1 and 2
  certifications        TEXT[],
  years_in_business     INTEGER,
  ymyl_category         TEXT,        -- "health" | "finance" | "legal" | "safety" | "none"
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id)
);

CREATE TABLE client_run_log (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id  UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  run_id     UUID,
  entry      TEXT NOT NULL,
  logged_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- RUNS
-- ============================================================

CREATE TABLE runs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  folder_slug       TEXT NOT NULL,        -- "Content_Marketing_Home_Services_2026-06"
  topic             TEXT NOT NULL,
  primary_keyword   TEXT NOT NULL,
  topic_path        TEXT NOT NULL CHECK (topic_path IN ('user_provided', 'ideation')),
  status            TEXT NOT NULL DEFAULT 'initiated'
    CHECK (status IN ('initiated','in_progress','approved','revision_required','published')),
  current_stage     INTEGER NOT NULL DEFAULT 0,
  dry_run           BOOLEAN DEFAULT FALSE,
  angle_notes       TEXT,               -- sanitized; never raw CRM text
  priority_sources  TEXT[],
  internal_links    TEXT[],
  authority_mode    TEXT NOT NULL DEFAULT 'normal'
    CHECK (authority_mode IN ('normal', 'expert_fallback')),
  fallback_status   TEXT,
  allowed_claims    TEXT[],
  disallowed_claims TEXT[],
  article_slug      TEXT,               -- derived from H1 at Stage 7
  schema_type       TEXT,               -- from Stage 5 annotation
  word_count_result JSONB,              -- {count, target_min, target_max, status}
  human_review_flag TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id, folder_slug)
);

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

CREATE TABLE run_log (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id     UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  stage_name TEXT,
  entry      TEXT NOT NULL,
  logged_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- STAGE OUTPUTS
-- ============================================================

CREATE TABLE stage_outputs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  stage_number          INTEGER NOT NULL,
  -- Stage number encoding:
  --   0 = Onboarding, 10 = Pre-Stage 1, 1 = Research,
  --   15 = Source Validation (1.5), 2-7 = Brief through Formatting, 11 = SEOcial
  stage_name            TEXT NOT NULL,
  attempt               INTEGER NOT NULL DEFAULT 1,
  status                TEXT NOT NULL
    CHECK (status IN ('pending','running','complete','failed','awaiting_human')),
  article_content       TEXT,           -- reader-facing content only
  editorial_note        TEXT,           -- Stage 4 only; never passed downstream
  seo_annotation        JSONB,          -- Stage 5 only; parsed from annotation sheet
  qa_result             JSONB,          -- Stage 6 only; parsed signoff
  handoff_content       TEXT,
  quality_gate_results  JSONB DEFAULT '{}',
  gpt_researcher_meta   JSONB,          -- Stage 1 only: {sources_gathered, sub_queries, costs}
  error_message         TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  completed_at          TIMESTAMPTZ,
  UNIQUE(run_id, stage_number, attempt)
);

-- Structured SEO annotation fields (denormalized from stage_outputs.seo_annotation)
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
  word_count_status TEXT,    -- "within_target" | "over_target" | "under_target"
  keyword_density   NUMERIC,
  schema_type       TEXT,
  qa_flags          TEXT[],  -- carries forward to Stage 6
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- QA results (denormalized for querying and routing)
CREATE TABLE qa_results (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage_output_id   UUID NOT NULL REFERENCES stage_outputs(id) ON DELETE CASCADE,
  run_id            UUID NOT NULL REFERENCES runs(id),
  decision          TEXT NOT NULL CHECK (decision IN ('approved', 'revision_required')),
  checklist_passed  INTEGER,
  checklist_total   INTEGER,
  ai_risk_score     INTEGER,
  section_a TEXT, section_b TEXT, section_c TEXT, section_d TEXT,
  section_e TEXT, section_f TEXT, section_g TEXT, section_h TEXT, section_i TEXT,
  revision_stage    INTEGER,
  human_review_flag TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE qa_issues (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  qa_result_id     UUID NOT NULL REFERENCES qa_results(id) ON DELETE CASCADE,
  run_id           UUID NOT NULL REFERENCES runs(id),
  section          TEXT NOT NULL,
  description      TEXT NOT NULL,
  issue_type       TEXT NOT NULL
    CHECK (issue_type IN ('pipeline_failure','client_decision','minor_observation')),
  stage_responsible INTEGER,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Content diffs between stages (avoid storing full copies of near-identical drafts)
CREATE TABLE stage_content_diffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id          UUID NOT NULL REFERENCES runs(id),
  from_stage      INTEGER NOT NULL,
  to_stage        INTEGER NOT NULL,
  diff_content    TEXT NOT NULL,    -- unified diff format
  additions       INTEGER,
  deletions       INTEGER,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
-- Full article stored at Stage 3 (first draft) and Stage 6 (approved draft).
-- Diffs bridge Stages 3→4, 4→5, 5→6.

-- ============================================================
-- SOURCE VALIDATION
-- ============================================================

CREATE TABLE source_validation_reports (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                      UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  status                      TEXT NOT NULL
    CHECK (status IN (
      'APPROVED', 'APPROVED_WITH_FALLBACK',
      'REJECTED_DOSSIER_NOT_FOUND', 'REJECTED_NO_SOURCES',
      'REJECTED_CONFIG_NOT_FOUND', 'REJECTED_MIN_SOURCES_ZERO'
    )),
  industry_key                TEXT NOT NULL,
  authority_overrides_applied BOOLEAN DEFAULT FALSE,
  sources_total               INTEGER,
  sources_verified            INTEGER,
  sources_unverified          INTEGER,
  fallback_activated          BOOLEAN NOT NULL DEFAULT FALSE,
  fallback_reason             TEXT,
  fallback_primary            TEXT,
  allowed_claims              TEXT[],
  disallowed_claims           TEXT[],
  authority_phrase            TEXT,
  validation_timestamp        TIMESTAMPTZ DEFAULT NOW(),
  created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE source_validation_sources (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id       UUID NOT NULL REFERENCES source_validation_reports(id) ON DELETE CASCADE,
  run_id          UUID NOT NULL REFERENCES runs(id),
  source_num      INTEGER NOT NULL,
  claimed_claim   TEXT,
  url             TEXT,
  status          TEXT NOT NULL
    CHECK (status IN ('VERIFIED', 'UNVERIFIED_AFTER_6_ATTEMPTS', 'SKIPPED')),
  attempts        INTEGER DEFAULT 0,
  fallback_action TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE source_validation_repositioning (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id   UUID NOT NULL REFERENCES source_validation_reports(id) ON DELETE CASCADE,
  pattern     TEXT NOT NULL,
  replacement TEXT NOT NULL,
  context     TEXT,
  sort_order  INTEGER NOT NULL
);

-- ============================================================
-- AUTHORITY MODELS
-- ============================================================

CREATE TABLE authority_models (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry_key         TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  description          TEXT,
  max_retry_attempts   INTEGER NOT NULL DEFAULT 6,
  min_valid_sources    INTEGER NOT NULL DEFAULT 1,
  retry_strategies     TEXT[] NOT NULL,
  strategy_queries     JSONB DEFAULT '{}',  -- {strategy_label: query_template}
  relevance_keywords   TEXT[],
  fallback_primary     TEXT NOT NULL,
  fallback_secondary   TEXT[],
  allowed_claims       TEXT[] NOT NULL,
  disallowed_claims    TEXT[] NOT NULL,
  repositioning_rules  JSONB NOT NULL,      -- [{old, new, context}]
  authority_phrase     TEXT NOT NULL,
  authority_examples   TEXT[],
  notes                TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Seed data summary:
-- industry_key          | min_valid_sources | fallback_primary
-- home_services         | 0 (short-circuit) | FIELD_EXPERTISE
-- health_wellness_spa   | 1                 | PRACTITIONER_EXPERTISE
-- software_development  | 1                 | DEVELOPER_EXPERTISE
-- financial_advisory    | 2                 | ADVISOR_EXPERTISE
-- legal_services        | 3                 | ATTORNEY_EXPERTISE

-- ============================================================
-- PUBLISHING
-- ============================================================

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

-- ============================================================
-- CSS TEMPLATES
-- ============================================================

CREATE TABLE css_templates (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL UNIQUE,   -- "blog_integration_base"
  version      TEXT,
  css_content  TEXT NOT NULL,          -- full file content
  token_names  TEXT[] NOT NULL,        -- validation: all 11 must be present
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Seed:
-- name: "blog_integration_base"
-- token_names: ["PRIMARY","PRIMARY_2","PRIMARY_SOFT","PRIMARY_GLOW","PRIMARY_RGB",
--               "ACCENT","ACCENT_2","ACCENT_SOFT","ACCENT_RGB","INK","LINE_STRONG"]

-- ============================================================
-- PROVIDER SETTINGS (runtime-switchable LLM config)
-- ============================================================

CREATE TABLE provider_settings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- Singleton table: one row per deployment
  pipeline_provider     TEXT NOT NULL DEFAULT 'anthropic'
    CHECK (pipeline_provider IN ('anthropic', 'openrouter', 'ollama', 'lm_studio')),
  pipeline_smart_model  TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
  pipeline_fast_model   TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
  gptr_smart_llm        TEXT NOT NULL DEFAULT 'anthropic:claude-sonnet-4-6',
  gptr_fast_llm         TEXT NOT NULL DEFAULT 'anthropic:claude-haiku-4-5-20251001',
  gptr_strategic_llm    TEXT NOT NULL DEFAULT 'anthropic:claude-sonnet-4-6',
  gptr_embedding        TEXT NOT NULL DEFAULT 'openai:text-embedding-3-small',
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);
-- LLMProviderFactory reads this table first; env vars are the fallback.
-- Allows switching providers from the UI without restarting the server.

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_runs_client ON runs(client_id);
CREATE INDEX idx_runs_keyword ON runs(primary_keyword);
CREATE INDEX idx_stage_outputs_run ON stage_outputs(run_id, stage_number);
CREATE INDEX idx_unresolved_run ON unresolved_items(run_id, resolved);
CREATE INDEX idx_published_client ON published_articles(client_id);
CREATE INDEX idx_published_keyword ON published_articles(primary_keyword);
CREATE INDEX idx_qa_issues_run ON qa_issues(run_id, issue_type);
CREATE INDEX idx_run_log_run ON run_log(run_id, logged_at DESC);
CREATE INDEX idx_client_run_log ON client_run_log(client_id, logged_at DESC);
```

---


---

## LLM Provider Configuration

### Provider Types

```python
# content_pipeline/llm/base_provider.py
class ProviderType(Enum):
    ANTHROPIC = "anthropic"     # Default; cloud; highest quality
    OPENROUTER = "openrouter"   # Cloud; multi-model access; cost-flexible
    OLLAMA = "ollama"           # Self-hosted; free; lower quality on small models
    LM_STUDIO = "lm_studio"    # Self-hosted with GUI; free; OpenAI-compatible API
```

### Provider Selection

`LLM_PROVIDER` env var → `LLMProviderFactory` → correct `LLMProvider` subclass.
Stage services never import individual provider classes. Always use the factory.

```python
# content_pipeline/llm/provider_factory.py
smart_provider  = LLMProviderFactory.create_smart_provider()  # complex stages
fast_provider   = LLMProviderFactory.create_fast_provider()   # structured stages
```

### Two Independent LLM Systems

| System | Controls | Config method |
|---|---|---|
| Pipeline LLM (Stages 0–7) | Onboarding, writing, QA, formatting | `LLM_PROVIDER` + `PIPELINE_SMART_MODEL` env vars |
| gpt-researcher (Stage 1 only) | Research gathering, source curation | `SMART_LLM`, `FAST_LLM`, `STRATEGIC_LLM` env vars in `provider:model` format |

These are **independent**. Pipeline can use Anthropic while gpt-researcher uses Ollama, or both can use OpenRouter.

### gpt-researcher Provider Format

```bash
# provider:model-name format for all three tiers
FAST_LLM=anthropic:claude-haiku-4-5-20251001        # Anthropic
FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001 # OpenRouter
FAST_LLM=ollama:llama3.1:8b                          # Ollama (local)
FAST_LLM=openai:your-model-name                      # LM Studio (local, openai: prefix)
```

### Critical OpenRouter Constraint

OpenRouter does not support embeddings. When using OpenRouter for gpt-researcher,
add a separate embedding provider:

```bash
EMBEDDING=google_genai:models/text-embedding-004  # free Google tier
GOOGLE_API_KEY=...
```

### Required Packages Per Provider

```bash
pip install langchain-openrouter   # OpenRouter only
pip install langchain-ollama       # Ollama only
# LM Studio: no extra package (uses openai client already installed)
```

### Quality Tolerance Config

Local models produce lower-quality output. Thresholds auto-adjust:

```python
# content_pipeline/config/provider_config.py
PROVIDER_QUALITY_TOLERANCES = {
    "anthropic":   {"max_validation_retries": 1, "min_insight_words": 100},
    "openrouter":  {"max_validation_retries": 2, "min_insight_words": 80},
    "ollama":      {"max_validation_retries": 3, "min_insight_words": 50},
    "lm_studio":   {"max_validation_retries": 3, "min_insight_words": 40},
}
```

---

## API Endpoints

```
# Clients
POST   /clients                                   Create client
GET    /clients                                   List clients
GET    /clients/{client_id}                       Client detail + reference file state
POST   /clients/{client_id}/onboard              Run Stage 0
GET    /clients/{client_id}/reference            Get reference files
PUT    /clients/{client_id}/reference/{type}     Update one reference file
GET    /clients/{client_id}/context              Assembled context (computed from DB)
PATCH  /clients/{client_id}/context              Update engagement_notes, next_planned_topic
GET    /clients/{client_id}/onboarding/status    Section-by-section validation status
GET    /clients/{client_id}/published            Published articles (overlap check source)

# Runs
POST   /clients/{client_id}/runs                           Init new run (Pre-Stage 1)
GET    /clients/{client_id}/runs                           List runs
GET    /clients/{client_id}/runs/{run_id}                  Run detail + stage summary
POST   /clients/{client_id}/runs/{run_id}/topic-recommendations   Path B ideation
POST   /clients/{client_id}/runs/{run_id}/confirm-topic           Lock topic + keyword

# Stage execution
POST   /runs/{run_id}/stages/{stage_num}/execute    Execute a stage (async → job_id)
GET    /runs/{run_id}/stages/{stage_num}/output     Get stage output
GET    /runs/{run_id}/stages/{stage_num}/stream     SSE streaming

# Stage-specific reads
GET    /runs/{run_id}/stages/5/annotation           SEO annotation (structured)
GET    /runs/{run_id}/stages/6/signoff              QA signoff (structured)
GET    /runs/{run_id}/stages/6/approved-draft       Clean approved draft

# QA decisions
POST   /runs/{run_id}/qa/decision                   Submit APPROVED or REVISION_REQUIRED

# Unresolved items
GET    /runs/{run_id}/issues                        All unresolved items
POST   /runs/{run_id}/issues/{issue_id}/resolve     Mark resolved

# Publishing
GET    /runs/{run_id}/html-preview                  Stage 7 HTML preview
POST   /runs/{run_id}/publish                       Finalize to published_articles

# Jobs
GET    /jobs/{job_id}                               Poll async job status
```

### Key Request/Response Shapes

#### `POST /clients/{client_id}/onboard`
```json
// Request
{
  "content_samples": [
    { "type": "text", "content": "..." },
    { "type": "url", "url": "https://..." }
  ],
  "additional_context": {
    "service_area": "Denver Metro",
    "off_limits_topics": ["competitor mentions"]
  },
  "regenerate": false
}
// Response 202
{ "job_id": "uuid", "status": "queued", "client_state_before": "new" }
```

#### `POST /clients/{client_id}/runs/{run_id}/topic-recommendations`
```json
// Request
{ "count": 5 }
// Response
{
  "recommendations": [
    {
      "n": 1,
      "topic": "Why Most HVAC Maintenance Plans Fail in Year One",
      "primary_keyword": "hvac maintenance plan what to expect",
      "why_now": "Post-summer surge in first-year contract renewals",
      "audience_intent": "commercial_investigation",
      "eeat_angle": "Client has direct service records showing failure patterns"
    }
  ],
  "published_content_inventory": [
    { "slug": "hvac-emergency-repair-costs", "published_at": "2025-11-01" }
  ],
  "overlap_check": "none_detected"
}
```

#### `POST /runs/{run_id}/stages/{stage_num}/execute`
```json
// Request
{ "auto_advance": false }
// Response 202
{ "job_id": "uuid", "stage_number": 1, "status": "queued" }
```

#### `GET /runs/{run_id}/stages/6/signoff`
```json
{
  "decision": "approved",
  "checklist_passed": 38,
  "checklist_total": 39,
  "ai_risk_score": 5,
  "section_results": {
    "A": "pass", "B": "pass", "C": "pass", "D": "pass",
    "E": "pass", "F": "flag", "G": "pass", "H": "pass", "I": "pass"
  },
  "issues": [
    {
      "section": "F",
      "description": "Third internal link destination not confirmed.",
      "issue_type": "client_decision",
      "stage_responsible": null,
      "blocking": false
    }
  ],
  "minor_observations": ["Byline style not confirmed with client"],
  "next_stage": 7,
  "revision_stage": null
}
```

#### `POST /runs/{run_id}/qa/decision`
```json
// Request
{ "decision": "approved" }
// Response — approved
{ "decision": "approved", "next_stage": 7, "human_review_flag": null }
// Response — revision required
{
  "decision": "revision_required",
  "revision_stage": 4,
  "revision_reason": "Voice inconsistency in FAQ section",
  "next_stage": 4
}
```

### Error Shape (all endpoints)
```json
{
  "error": "MISSING_PREREQUISITE",
  "message": "Stage 1 must complete before Stage 2 can run.",
  "detail": { "required_stage": 1, "required_output": "01_Research_Dossier" }
}
```

**Error codes:** `MISSING_PREREQUISITE`, `CLIENT_NOT_ONBOARDED`, `CLIENT_ALREADY_ONBOARDED`, `OVERLAP_DETECTED`, `SOURCE_VALIDATION_REJECTED`, `QUALITY_GATE_FAILURE`, `BRIEF_TOKEN_LEAKED`, `INTERNAL_TOKEN_IN_DRAFT`, `QA_REVISION_REQUIRED`, `STAGE_7_BLOCKED_BY_REVISION`, `MISSING_BRAND_COLORS`

---

## Pipeline Stage Map

| Stage | Number | Name | Key Input | Primary Output | Human Checkpoint |
|---|---|---|---|---|---|
| 0 | 0 | Onboarding | Content samples | 3 reference files | Review all three |
| Pre-1 | 10 | Run Init | Reference files + keyword | Run folder + handoff | Confirm topic/keyword |
| 1 | 1 | Research | Reference files + handoff | Research Dossier | Review before validation |
| 1.5 | 15 | Source Validation | Research Dossier | validation_report | Review if fallback |
| 2 | 2 | Brief | Dossier + validation result | Content Brief | Review structure |
| 3 | 3 | Writing | Content Brief | First Draft | Review before humanization |
| 4 | 4 | Humanization | First Draft | Humanized Draft + Editorial Note | Review voice |
| 5 | 5 | SEO | Humanized Draft | SEO Draft + Annotation Sheet | Review metadata |
| 6 | 6 | QA | SEO Draft + full checklist | QA Signoff + Approved Draft | Must PASS before Stage 7 |
| 7 | 7 | Formatting | Approved Draft | HTML + Published files | Final review |
| 11 | 11 | SEOcial | Approved Draft | Social/distribution assets | Optional |

---

## Stage Load Contracts

What each stage loads from the database (mirrors the "Load Before Starting" section in each CONTEXT.md):

| Stage | Load in Full | Load Sections Only | Do Not Load |
|---|---|---|---|
| 0 | Content samples (session) | — | Reference files, run files, _config |
| Pre-1 | Style Card, Audience Profile, Brand Notes, Run Log tail (20) | — | Any Runs/ stage files |
| 1 | Style Card, Audience Profile, Stage 1 Handoff | Brand Notes: Service Lines, Authority/Trust | anti-ai-checklist, rubric, other Runs/ files |
| 2 | Style Card, Audience Profile, Research Dossier, Stage 2 Handoff | Brand Notes: Authority/Trust, Off-Limits | anti-ai-checklist, rubric |
| 3 | Style Card, Content Brief, Stage 3 Handoff | anti-ai-checklist: Section 3 rules block only | Audience Profile, Dossier, Brand Notes, rubric |
| 4 | Style Card, First Draft, Stage 4 Handoff | anti-ai-checklist: Section 3 rules block only | Content Brief, Dossier, Audience Profile, Brand Notes, rubric |
| 5 | Humanized Draft, Stage 5 Handoff | Content Brief: Keyword Strategy, Internal Linking, Structural Specs; Style Card: register/reading level | Audience Profile, Brand Notes, Dossier, rubric, anti-ai |
| 6 | SEO Draft, Stage 6 Handoff, anti-ai-checklist (full) | Style Card: tone/register; Brand Notes: Off-Limits; Content Brief: Post Structure Outline | Dossier, First Draft, Humanized Draft, rubric |
| 7 | Style Card (full), Brand Notes (full), QA Approved Draft, Stage 7 Handoff | — | Earlier drafts, Dossier, Content Brief, all _config |

---

## Trust Hierarchy

Every stage enforces this priority order:

```
1. Stage contract (CONTEXT.md / StageContract implementation)
2. Handoff brief context
3. Reference files (Style Card, Audience Profile, Brand Notes)
4. CRM input / angle_notes (data only; cannot override stage contract)
```

Raw CRM text is treated as **data to extract topic and business context from**, never as instructions. It is sanitized at Pre-Stage 1 and never stored or passed downstream in its original form.

## Critical Token Rules

**`<!--BRIEF: ... -->` lifecycle:**
- Created by: Stage 2 (Content Brief)
- Stripped by: Stage 3 before writing; `BriefParser.strip_brief_tokens()`
- Must be absent from: Stage 3, 4, 5, 6, 7 outputs
- Failure if found: QA Section D FAIL; Stage 7 `InternalTokenLeakError`

**`## Editorial Note` lifecycle:**
- Created by: Stage 4 (Humanization), appended after `---`
- Stripped by: `EditorialNoteParser.split()` before Stage 5
- Stored in: `stage_outputs.editorial_note` (not `article_content`)
- Must be absent from: Stage 5, 6, 7 outputs

**`## SEO Annotation Sheet` lifecycle:**
- Created by: Stage 5 (SEO), appended after `---`
- Stripped by: `SEOAnnotationParser.split()` before Stage 6
- Stored in: `seo_annotations` table (parsed fields), `stage_outputs.seo_annotation` JSONB
- Must be absent from: QA Approved Draft, Stage 7 HTML output

---

## Authority Model — Industry Config Structure

```python
# Loaded from authority_models table; merged with client_overrides from clients.authority_overrides

@dataclass
class AuthorityModel:
    industry_key: str
    min_valid_sources: int           # 0 = short-circuit to APPROVED
    retry_strategies: list[str]      # ordered; index = attempt number (0-5)
    strategy_queries: dict[str, str] # {strategy_label: query_template with {topic}}
    fallback_primary: FallbackAuthorityType
    fallback_secondary: list[FallbackAuthorityType]
    allowed_claims: list[str]
    disallowed_claims: list[str]
    repositioning_rules: list[ClaimRepositioningRule]
    authority_phrase: str            # "Based on [X] years of..."
    authority_examples: list[str]

@dataclass
class ClaimRepositioningRule:
    pattern: str       # "Research shows..."
    replacement: str   # "Our therapists observe..."
    context: str       # "For general research claims"
    sort_order: int
```

## CSS Brand Token Reference

The `blog_integration_base.css` file requires exactly 11 client-specific tokens. All others are static.

| Token | Key in brand_colors | Format | Example |
|---|---|---|---|
| `{{PRIMARY}}` | `primary` | hex | `"#1B3D6F"` |
| `{{PRIMARY_2}}` | `primary_2` | hex | `"#1E4F8A"` |
| `{{PRIMARY_SOFT}}` | `primary_soft` | hex | `"#EEF3FA"` |
| `{{PRIMARY_GLOW}}` | `primary_glow` | rgba() string | `"rgba(27, 61, 111, 0.08)"` |
| `{{PRIMARY_RGB}}` | `primary_rgb` | `"r, g, b"` — **no # prefix** | `"27, 61, 111"` |
| `{{ACCENT}}` | `accent` | hex | `"#E8762B"` |
| `{{ACCENT_2}}` | `accent_2` | hex | `"#D4621E"` |
| `{{ACCENT_SOFT}}` | `accent_soft` | hex | `"#FDF1E8"` |
| `{{ACCENT_RGB}}` | `accent_rgb` | `"r, g, b"` — **no # prefix** | `"232, 118, 43"` |
| `{{INK}}` | `ink` | hex | `"#1C1C1A"` |
| `{{LINE_STRONG}}` | `line_strong` | rgba() string | `"rgba(27, 61, 111, 0.22)"` |

**`PRIMARY_RGB` and `ACCENT_RGB` must not have a `#` prefix.** They are used inside `rgba(var(--primary-rgb), 0.04)` calls in the CSS. A `#` prefix breaks the rgba() function.

## CSS Component Classes (Stage 7 HTML)

| Class | Element | When rendered |
|---|---|---|
| `.skip-link` | `<a>` | Always (accessibility) |
| `.blog-wrap` | `<article>` | Always (outer wrapper) |
| `.header` | `<div>` inside `.card-wrap` | Always (H1 hero) |
| `.header-eyebrow` | `<span>` | Optional (category badge above H1) |
| `.toc-card` | `<nav>` | When article has ≥ 4 H2 sections |
| `.prose` | `<section>` | One per H2 |
| `.cta-card` | `<div>` | Always (last element in blog-wrap) |
| `.cta-pills` / `.cta-pill` | `<div>` / `<span>` | Inside CTA when service bullets present |
| `.callout-text` | `<p>` | When markdown blockquote in prose |
| Infographic classes | Various | Future enhancement; not in standard blog output |

---

## gpt-researcher Configuration

```bash
# Required environment variables
TAVILY_API_KEY=...
RETRIEVER=tavily
SMART_LLM=claude-sonnet-4-6      # SourceCurator
FAST_LLM=claude-haiku-4-5-20251001  # sub-query generation, scraping summaries
STRATEGIC_LLM=claude-sonnet-4-6  # research planning
MAX_SCRAPER_WORKERS=15
MAX_SEARCH_RESULTS_PER_QUERY=5
CURATE_SOURCES=false              # disabled at Stage 1; SourceCurator called directly in Stage 1.5
```

**Stage 1 usage:**
```python
researcher = GPTResearcher(query=query, report_type="research_report", websocket=None)
researcher.cfg.curate_sources = False
await researcher.conduct_research()
# Use: researcher.get_research_context(), researcher.get_source_urls(),
#       researcher.research_sub_queries, researcher.get_costs()
```

**Stage 1.5 usage (SourceCurator directly):**
```python
# Build minimal GPTResearcher to satisfy SourceCurator's parent dependency
researcher = GPTResearcher(query=topic, report_type="research_report")
researcher.research_data = [{"url": s["url"], "raw_content": s["content"]} for s in verified_sources]
researcher.prompt_family = IndustryAwarePromptFamily(researcher.prompt_family, authority_model)
curator = SourceCurator(researcher)
ranked = await curator.curate_sources(query=topic, source_data=researcher.research_data, max_results=10)
```

---

## Revision Routing (Stage 6 → Earlier Stage)

When QA returns `REVISION_REQUIRED`, route to the earliest stage responsible:

| Failure keyword | Earliest stage |
|---|---|
| factual_claim, ymyl, cta_missing, eeat | Stage 3 |
| ai_sounding, voice_inconsistency | Stage 4 |
| keyword_placement, meta_title, header_hierarchy | Stage 5 |

After revision, re-run from the revised stage forward. Never restart from Stage 1.

---

## File Reference — What Replaces What

Every file from the old system is accounted for:

| Old system file | Application replacement |
|---|---|
| `CLAUDE.md` | `Root_Claude.md` content → `StageContract` routing logic |
| `CONTEXT.md` (client) | `client_contexts` table + `ClientContextAssembler` |
| `Reference/Style_Reference_Card.md` | `client_reference_files.style_reference_card` + parsed `brand_colors` JSONB |
| `Reference/Audience_Profile.md` | `client_reference_files.audience_profile` + parsed `reading_level_target` |
| `Reference/Brand_Notes.md` | `client_reference_files.brand_notes` + parsed `certifications`, `ymyl_category` |
| `Run_Log.md` (client-level) | `client_run_log` table |
| `Runs/[FOLDER]/Run_Log.md` | `run_log` table |
| `00_Stage_1_Handoff_Brief.md` | `stage_outputs.handoff_content` (stage_number=10) |
| `01_Research_Dossier.md` | `stage_outputs.article_content` (stage_number=1) |
| `01_Stage_2_Handoff.md` | `stage_outputs.handoff_content` (stage_number=1) |
| `source_validation_report.json` | `source_validation_reports` + `source_validation_sources` tables |
| `02_Content_Brief.md` | `stage_outputs.article_content` (stage_number=2) |
| `03_First_Draft.md` | `stage_outputs.article_content` (stage_number=3) |
| `04_Humanized_Draft.md` | `stage_outputs.article_content` (stage_number=4) |
| `## Editorial Note` | `stage_outputs.editorial_note` (stage_number=4) |
| `05_SEO_Draft.md` (body) | `stage_outputs.article_content` (stage_number=5) |
| `## SEO Annotation Sheet` | `seo_annotations` table + `stage_outputs.seo_annotation` JSONB |
| `06_QA_Signoff.md` | `qa_results` + `qa_issues` tables |
| `06_QA_Approved_Draft.md` | `stage_outputs.article_content` (stage_number=6) |
| `06_QA_Revision_Required.md` | `qa_results.decision = "revision_required"` + API 409 response |
| `Human_Review_Flag.md` | `runs.human_review_flag` TEXT field |
| `07_Blog_Final.html` | `published_articles.html_content` |
| `Published/[slug].html` | `published_articles.html_content` (same record) |
| `Published/[slug].md` | `published_articles.markdown_content` |
| `tools/word_count.py` | `len(content.split())` in `FormattingService` |
| `tools/stage1_source_validator.py` | `SourceValidationService` + gpt-researcher |
| `tools/merge_manual_html.py` | `POST /runs/{run_id}/stages/7/manual-upload` endpoint |
| `templates/blog_integration_base.css` | `css_templates` table (seeded at deploy) |
| `_config/authority-models/*.json` | `authority_models` table (seeded at deploy) |

