-- Created: 2026-07-23 11:07 AM
-- Last edited: 2026-07-23 11:07 AM
-- Supabase migration: Initial schema for Content Pipeline

-- ============================================================
-- TABLE MANIFEST
-- ============================================================
-- clients, client_contexts, client_reference_files, client_run_log
-- runs, unresolved_items, topic_recommendations, run_log
-- stage_outputs, seo_annotations, qa_results, qa_issues, stage_content_diffs
-- source_validation_reports, source_validation_sources, source_validation_repositioning
-- authority_models, published_articles, css_templates, provider_settings

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
-- ASYNC JOBS (ARQ worker queue state + audit trail)
-- ============================================================

CREATE TABLE jobs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id            UUID NOT NULL UNIQUE,           -- Job ID from ARQ
  status            TEXT NOT NULL DEFAULT 'queued'  -- "queued", "running", "complete", "failed"
    CHECK (status IN ('queued', 'running', 'complete', 'failed')),
  job_type          TEXT NOT NULL DEFAULT 'onboarding'  -- "onboarding", "stage_execution", etc.
  progress          TEXT,                           -- "Step X/7", "Running validation", etc.
  result            JSONB,                          -- Result data when complete
  error_message     TEXT,                           -- Error when failed
  context_data      JSONB DEFAULT '{}',             -- Arbitrary job context (client_id, run_id, etc.)
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  started_at        TIMESTAMPTZ,
  completed_at      TIMESTAMPTZ,
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);

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
