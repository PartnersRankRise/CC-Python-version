-- Created: Thursday Jul 23, 2026, 4:22 PM (UTC-6)
-- Last edited: Thursday Jul 23, 2026, 4:43 PM (UTC-6)

-- Supabase Seed Data: Authority Models, CSS Template, Provider Settings
-- This file populates reference data shared across all test environments
-- Run this once in your Supabase project SQL editor

-- ============================================================
-- AUTHORITY MODELS (5 industries)
-- ============================================================

-- Delete existing data if it exists (idempotent insert)
DELETE FROM authority_models WHERE industry_key IN ('home_services', 'health_wellness_spa', 'software_development', 'financial_advisory', 'legal_services');
DELETE FROM css_templates WHERE name = 'blog_integration_base';
DELETE FROM provider_settings WHERE pipeline_provider = 'anthropic';

INSERT INTO authority_models (
  industry_key, name, description, max_retry_attempts, min_valid_sources,
  retry_strategies, strategy_queries, relevance_keywords, fallback_primary,
  fallback_secondary, allowed_claims, disallowed_claims, repositioning_rules,
  authority_phrase, authority_examples, notes
) VALUES

-- Home Services (short-circuit: min_valid_sources = 0)
(
  'home_services',
  'Home Services',
  'Plumbing, HVAC, electrical, roofing, and general contracting expertise based on field experience and certifications',
  6,
  0,  -- Short-circuit: skip validation entirely
  ARRAY['direct_search', 'certification_lookup'],
  '{"direct_search": "{{claim}} plumbing expert", "certification_lookup": "NAPLPS certified {{service}}"}'::jsonb,
  ARRAY['plumbing', 'hvac', 'electrical', 'roofing', 'contractor', 'licensed', 'certified'],
  'FIELD_EXPERTISE',
  ARRAY['contractor_testimonials', 'project_photos'],
  ARRAY['{{service}} contractor', '{{certification}} licensed', 'years in business'],
  ARRAY['diagnosis not allowed', 'medical claims', 'structural engineering'],
  '{"allow_photos": true, "require_license": false}'::jsonb,
  'Based on {{years}} years of {{service}} experience and {{certification}} certification',
  ARRAY['Master Plumber with 20 years experience', 'EPA-certified HVAC technician', 'Licensed electrician in Colorado'],
  'Field expertise and certifications take priority over external sources'
),

-- Health & Wellness Spa (min_valid_sources = 1)
(
  'health_wellness_spa',
  'Health & Wellness Spa',
  'Massage therapy, wellness practices, and holistic health expertise based on practitioner credentials',
  6,
  1,  -- Minimum 1 source
  ARRAY['direct_search', 'license_lookup', 'case_study'],
  '{"direct_search": "{{claim}} massage therapist", "license_lookup": "{{state}} licensed massage therapist", "case_study": "massage therapy {{claim}} case study"}'::jsonb,
  ARRAY['massage', 'wellness', 'therapy', 'holistic', 'spa', 'relaxation'],
  'PRACTITIONER_EXPERTISE',
  ARRAY['client_testimonials', 'certification_links'],
  ARRAY['{{service}} specialist', 'licensed massage', 'certified wellness'],
  ARRAY['medical diagnosis', 'treatment claims', 'disease cure'],
  '{"allow_testimonials": true, "require_license": true}'::jsonb,
  'As a {{certification}} {{service}} specialist, my {{years}} years of experience shows...',
  ARRAY['Licensed Massage Therapist (LMT) in Colorado', 'Certified Reiki practitioner', 'Holistic wellness coach'],
  'Practitioner credentials and client experience valued highly'
),

-- Software Development (min_valid_sources = 1)
(
  'software_development',
  'Software Development',
  'Technical expertise based on published work, open source contributions, and industry credentials',
  6,
  1,
  ARRAY['github_search', 'portfolio_check', 'tech_blog'],
  '{"github_search": "github.com {{author}} {{technology}}", "portfolio_check": "{{portfolio}} {{technology}} project", "tech_blog": "{{blog}} {{technology}} tutorial"}'::jsonb,
  ARRAY['developer', 'javascript', 'python', 'react', 'api', 'database', 'cloud'],
  'DEVELOPER_EXPERTISE',
  ARRAY['github_repos', 'stack_overflow'],
  ARRAY['experience with {{technology}}', 'built {{project}}', 'certified in {{skill}}'],
  ARRAY['security vulnerabilities without disclosure', 'proprietary code'],
  '{"source_priority": "github_first", "open_source_valued": true}'::jsonb,
  'My experience building {{project}} in {{technology}} demonstrates...',
  ARRAY['Full-stack developer with 8 years experience', 'Open source contributor (200+ repos)', 'AWS Certified Solutions Architect'],
  'Published work and technical portfolio are primary authority signals'
),

-- Financial Advisory (min_valid_sources = 2)
(
  'financial_advisory',
  'Financial Advisory',
  'Financial advice based on professional licenses, certifications, and documented credentials',
  6,
  2,  -- Minimum 2 sources required
  ARRAY['sec_search', 'cfp_lookup', 'finra_check'],
  '{"sec_search": "SEC registered {{advisor}}", "cfp_lookup": "CFP {{advisor}}", "finra_check": "FINRA registered {{advisor}}"}'::jsonb,
  ARRAY['financial advisor', 'investment', 'retirement', 'cfp', 'financial planning', 'portfolio'],
  'ADVISOR_EXPERTISE',
  ARRAY['sec_registration', 'client_testimonials'],
  ARRAY['CFP certified', 'SEC registered investment advisor', 'FINRA licensed'],
  ARRAY['guaranteed returns', 'legal tax advice', 'specific investment recommendations without disclaimer'],
  '{"regulatory_required": true, "sec_filing_required": true}'::jsonb,
  'As a {{license}} financial advisor, according to {{authority}}, this approach...',
  ARRAY['CFP (Certified Financial Planner)', 'SEC Registered Investment Advisor', 'FINRA Series 65 License holder'],
  'Regulatory compliance and professional licenses are mandatory'
),

-- Legal Services (min_valid_sources = 3)
(
  'legal_services',
  'Legal Services',
  'Legal expertise based on bar admission, published legal work, and professional standing',
  6,
  3,  -- Minimum 3 sources required
  ARRAY['bar_check', 'legal_database', 'court_records'],
  '{"bar_check": "{{state}} bar admitted {{attorney}}", "legal_database": "{{attorney}} legal cases", "court_records": "{{court}} {{attorney}} case"}'::jsonb,
  ARRAY['attorney', 'lawyer', 'legal', 'law', 'statute', 'contract', 'litigation'],
  'ATTORNEY_EXPERTISE',
  ARRAY['bar_admission', 'published_opinions'],
  ARRAY['bar admitted attorney', 'law degree from {{law_school}}', 'practiced {{area}} law for {{years}} years'],
  ARRAY['specific legal advice for {{state}} without disclaimer', 'guaranteed case outcomes'],
  '{"regulatory_required": true, "bar_admission_required": true, "disclaimer_required": true}'::jsonb,
  'As a {{state}} bar admitted attorney practicing {{area}} law, the relevant {{statute}} states...',
  ARRAY['Colorado Bar Association member (License #12345)', 'Published in Colorado Lawyer journal', 'US District Court admitted'],
  'Bar admission and regulatory compliance are non-negotiable'
);

-- ============================================================
-- CSS TEMPLATE
-- ============================================================

INSERT INTO css_templates (name, version, css_content, token_names) VALUES
(
  'blog_integration_base',
  '1.0.0',
  $CSS_CONTENT$/*
 * Blog Integration Base CSS
 * Canonical design system for Stage 7 Blog Formatting (07_Blog_Final.html).
 * The stage8_blog_integration.py script injects brand tokens into the
 * :root block below (replacing {{PRIMARY}}, {{ACCENT}}, etc.) and then
 * inlines this stylesheet into the <style> element of the output HTML.
 *
 * Token placeholders (replaced at build time):
 *   {{PRIMARY}}        — client primary hex
 *   {{PRIMARY_2}}      — client primary-2 hex
 *   {{PRIMARY_SOFT}}   — client primary-soft hex
 *   {{PRIMARY_GLOW}}   — client primary-glow rgba
 *   {{PRIMARY_RGB}}    — client primary r, g, b triplet
 *   {{ACCENT}}         — client accent hex
 *   {{ACCENT_2}}       — client accent-2 hex
 *   {{ACCENT_SOFT}}    — client accent-soft hex
 *   {{ACCENT_RGB}}     — client accent r, g, b triplet
 *   {{INK}}            — client ink hex
 *   {{LINE_STRONG}}    — client line-strong rgba
 */

/* === TOKEN SYSTEM === */
:root {
  color-scheme: light;

  /* Brand palette — injected per client */
  --primary:       {{PRIMARY}};
  --primary-2:     {{PRIMARY_2}};
  --primary-soft:  {{PRIMARY_SOFT}};
  --primary-glow:  {{PRIMARY_GLOW}};
  --primary-rgb:   {{PRIMARY_RGB}};
  --accent:        {{ACCENT}};
  --accent-2:      {{ACCENT_2}};
  --accent-soft:   {{ACCENT_SOFT}};
  --accent-rgb:    {{ACCENT_RGB}};

  /* Neutral surface palette */
  --cream:        #FEF9F3;
  --paper:        #FFFDFC;
  --paper-2:      #F7F3EC;
  --ink:          {{INK}};
  --muted:        #686760;
  --soft:         #929087;
  --line:         rgba(44, 44, 42, 0.13);
  --line-strong:  {{LINE_STRONG}};
  --success-soft: #EDF8F1;
  --warn:         #D85A30;
  --warn-soft:    #FFF0EA;
  --warn-line:    #F4C4B3;
  --white:        #FFFFFF;

  /* Fluid type scale */
  --step--2: clamp(0.72rem, 0.70rem + 0.08vw, 0.78rem);
  --step--1: clamp(0.82rem, 0.78rem + 0.17vw, 0.94rem);
  --step-0:  clamp(0.96rem, 0.90rem + 0.26vw, 1.06rem);
  --step-1:  clamp(1.08rem, 0.99rem + 0.45vw, 1.30rem);
  --step-2:  clamp(1.32rem, 1.10rem + 0.95vw, 1.75rem);
  --step-3:  clamp(1.65rem, 1.29rem + 1.55vw, 2.45rem);
  --step-4:  clamp(2.05rem, 1.50rem + 2.35vw, 3.45rem);
  --step-5:  clamp(2.55rem, 1.72rem + 3.60vw, 4.75rem);

  /* Fluid spacing scale */
  --space-1: clamp(0.35rem, 0.31rem + 0.18vw, 0.50rem);
  --space-2: clamp(0.65rem, 0.55rem + 0.42vw, 0.95rem);
  --space-3: clamp(0.95rem, 0.78rem + 0.75vw, 1.45rem);
  --space-4: clamp(1.25rem, 1.00rem + 1.05vw, 2.00rem);
  --space-5: clamp(1.70rem, 1.28rem + 1.75vw, 3.00rem);
  --space-6: clamp(2.20rem, 1.62rem + 2.45vw, 4.25rem);
  --space-7: clamp(3.00rem, 2.15rem + 3.60vw, 6.25rem);
  --space-8: clamp(4.00rem, 2.75rem + 5.40vw, 9.00rem);

  /* Border radius */
  --radius-sm:   0.85rem;
  --radius-md:   1.15rem;
  --radius-lg:   1.65rem;
  --radius-xl:   2.15rem;
  --radius-pill: 999px;

  /* Shadows */
  --shadow-sm: 0 0.6rem 1.6rem rgba(19, 46, 96, 0.08);
  --shadow-md: 0 1.1rem 2.8rem rgba(19, 46, 96, 0.12);
  --shadow-lg: 0 2rem 5rem rgba(19, 46, 96, 0.16);

  /* Layout widths */
  --content: min(100% - 2rem, 72rem);
  --visual:  min(100% - 1rem, 78rem);
  --wide:    min(100% - 1rem, 90rem);
}
$CSS_CONTENT$,
  ARRAY['PRIMARY', 'PRIMARY_2', 'PRIMARY_SOFT', 'PRIMARY_GLOW', 'PRIMARY_RGB', 'ACCENT', 'ACCENT_2', 'ACCENT_SOFT', 'ACCENT_RGB', 'INK', 'LINE_STRONG']
);

-- ============================================================
-- PROVIDER SETTINGS
-- ============================================================

INSERT INTO provider_settings (
  pipeline_provider, pipeline_smart_model, pipeline_fast_model,
  gptr_smart_llm, gptr_fast_llm, gptr_strategic_llm, gptr_embedding
) VALUES
(
  'anthropic',
  'claude-sonnet-4-6',
  'claude-haiku-4-5-20251001',
  'anthropic:claude-sonnet-4-6',
  'anthropic:claude-haiku-4-5-20251001',
  'anthropic:claude-sonnet-4-6',
  'openai:text-embedding-3-small'
);
