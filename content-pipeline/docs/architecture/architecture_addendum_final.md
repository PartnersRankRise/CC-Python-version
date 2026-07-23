# Architecture Addendum: Source Validation, Authority Models, and CSS Template

**Supplements:** `architecture_migration_plan_v2.md`, `architecture_addendum_templates.md`, `architecture_addendum_gpt_researcher.md`  
**Sources analyzed:** `source-validation-framework.md`, all six `authority-models/*.json` files, `blog_integration_base.css`  
**Critical correction:** All references to Python scripts in earlier documents are superseded here. No Python scripts are carried forward from the old system.

---

## 1. Script Removal — Complete List of Corrections

The old system used three Python scripts that are part of the compromised system and must not be replicated:

| Script | Old role | Application replacement |
|---|---|---|
| `tools/stage1_source_validator.py` | Ran HTTP HEAD validation + retry loop | gpt-researcher `BrowserManager` + `SourceCurator` (see gpt-researcher addendum) |
| `tools/word_count.py` | Counted article words; formatted output string | `len(content.split())` utility in `FormattingService`; result stored as `{count, target_min, target_max, status}` JSONB |
| `tools/merge_manual_html.py` | Merged manual HTML/CSS for bypass path | `POST /runs/{run_id}/stages/7/manual-upload` API endpoint |

Every `quality_gate_results` field, stage output, or handoff document that previously referenced a script output now references the application service or database field that produces the equivalent result.

---

## 2. Source Validation — Confirmed Architecture

The `source-validation-framework.md` confirms and extends what was inferred in v2. Key things it settles:

### 2.1 The Three-Stage Validation Flow

The framework defines three sequential stages that map directly to gpt-researcher's capabilities:

```
Stage 1: URL validation (HTTP HEAD, 5s timeout)
         → gpt-researcher BrowserManager handles this natively.
           Failed URLs are dropped silently. The application tracks
           which dossier sources came back empty vs. scraped.

Stage 2: Retry loop (up to 6 attempts, each with a different strategy)
         → gpt-researcher ResearchConductor runs sub-queries per strategy.
           The six retry_strategies in each industry JSON become
           six targeted search queries if initial sources fail.

Stage 3: Fallback decision (count valid vs. min_valid_sources_required)
         → SourceValidationService computes the tri-state from
           gpt-researcher's curated output + the industry threshold.
```

### 2.2 The Tri-State Output — Confirmed Field Names

The framework's JSON output format confirms the exact field names the application must produce and store:

```json
{
  "status": "APPROVED | APPROVED_WITH_FALLBACK | REJECTED",
  "client": "CLIENT_NAME",
  "industry": "INDUSTRY_KEY",
  "validation_timestamp": "ISO-8601",
  "sources": {
    "total": 5,
    "verified": 2,
    "unverified": 3,
    "details": [
      {
        "source_num": 1,
        "claimed_claim": "text of the claim",
        "url": "https://...",
        "status": "VERIFIED | UNVERIFIED_AFTER_6_ATTEMPTS",
        "attempts": 0,
        "fallback_action": "Reposition as expert observation"
      }
    ]
  },
  "fallback_mode": {
    "activated": true,
    "reason": "Only 2 of 5 sources verified; min required: 3",
    "authority_rules": {
      "primary": "PRACTITIONER_EXPERTISE",
      "allowed_claims": ["client_outcomes", "mechanism_of_action"],
      "disallowed_claims": ["specific_percentages_without_source"]
    },
    "claim_repositioning": {
      "replacements": [...]
    }
  }
}
```

This becomes the schema for the `source_validation_reports` table. The `details` array maps to `source_validation_sources`, a child table.

### 2.3 Six Error States — Confirmed

The framework defines exactly six possible error/status codes:

```python
class ValidationStatus(Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_FALLBACK = "APPROVED_WITH_FALLBACK"
    REJECTED_DOSSIER_NOT_FOUND = "REJECTED_DOSSIER_NOT_FOUND"
    REJECTED_NO_SOURCES = "REJECTED_NO_SOURCES"
    REJECTED_CONFIG_NOT_FOUND = "REJECTED_CONFIG_NOT_FOUND"
    REJECTED_MIN_SOURCES_ZERO = "REJECTED_MIN_SOURCES_ZERO"
```

`REJECTED_MIN_SOURCES_ZERO` is a special case: when `min_valid_sources_required = 0` (as in `home_services.json`), the pipeline should proceed immediately without running any validation at all. This is not a failure — it means the industry is field-expertise-led and external sources are optional. The application should short-circuit to `APPROVED` when `min_valid_sources_required = 0`.

### 2.4 Client Override Configuration

The framework defines a client-level override file at `Clients/[CLIENT]/authority-config.json`. This maps to a new `client_authority_overrides` column on the `clients` table, stored as JSONB:

```sql
ALTER TABLE clients ADD COLUMN authority_overrides JSONB DEFAULT '{}';
-- Example value:
-- {
--   "override_industry": "health_wellness_spa",
--   "custom_retry_strategies": ["peer_reviewed_medical", "government_health_databases"],
--   "custom_authority_phrase": "At Escape Spa, based on 500+ client sessions"
-- }
```

**Loading order** (confirmed from framework):
1. Check `clients.authority_overrides` (client override)
2. Fall back to `authority_models` table keyed by `clients.industry`
3. Merge: client overrides replace matching industry fields; unoverridden fields keep industry defaults

---

## 3. Authority Models — Confirmed Schema and Industry Configs

All six JSON files confirm the authority model schema. The `_template.json` is the definitive schema; the five industry files are populated instances.

### 3.1 Database Schema for Authority Models

Authority models are configuration data, not user data. They belong in a seed table, not derived from user input:

```sql
CREATE TABLE authority_models (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry_key          TEXT NOT NULL UNIQUE,   -- matches clients.industry
  name                  TEXT NOT NULL,
  description           TEXT,
  -- Validation config
  max_retry_attempts    INTEGER NOT NULL DEFAULT 6,
  min_valid_sources     INTEGER NOT NULL DEFAULT 1,
  retry_strategies      TEXT[] NOT NULL,         -- ordered; index = attempt number
  relevance_keywords    TEXT[],
  -- Fallback authority
  fallback_primary      TEXT NOT NULL,           -- e.g., "PRACTITIONER_EXPERTISE"
  fallback_secondary    TEXT[],
  allowed_claims        TEXT[] NOT NULL,
  disallowed_claims     TEXT[] NOT NULL,
  -- Claim repositioning
  repositioning_rules   JSONB NOT NULL,          -- [{old, new, context}]
  authority_phrase      TEXT NOT NULL,
  authority_examples    TEXT[],
  -- Notes
  notes                 TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);
```

**Seed data** (from the five industry JSON files):

| `industry_key` | `min_valid_sources` | `fallback_primary` | Special behavior |
|---|---|---|---|
| `home_services` | **0** | `FIELD_EXPERTISE` | Short-circuit to APPROVED immediately |
| `health_wellness_spa` | 1 | `PRACTITIONER_EXPERTISE` | Standard flow |
| `software_development` | 1 | `DEVELOPER_EXPERTISE` | Standard flow |
| `financial_advisory` | 2 | `ADVISOR_EXPERTISE` | Notes suggest 3-4 for investment content |
| `legal_services` | 3 | `ATTORNEY_EXPERTISE` | Most restrictive; notes suggest 5 for high-liability |

### 3.2 The `min_valid_sources = 0` Short-Circuit

`home_services.json` sets `min_valid_sources_required: 0`. This is the most important behavioral difference between industries. The `SourceValidationService` must check this before running any validation:

```python
class SourceValidationService:

    async def validate(self, dossier: str, run: Run) -> ValidationReport:
        model = self._load_model(run)

        # Short-circuit: home services (and any future zero-threshold industry)
        # proceeds without any source validation. External sources are
        # optional for field-expertise-led industries.
        if model.min_valid_sources == 0:
            return ValidationReport(
                status=ValidationStatus.APPROVED,
                reason="Industry does not require external source verification",
                curated_sources=[],
                authority_mode=AuthorityMode.NORMAL,
            )

        sources = self._extract_source_bank(dossier)
        # ... rest of validation flow
```

### 3.3 Retry Strategies as gpt-researcher Sub-Queries

The six `retry_strategies` in each industry JSON are strategy labels, not literal search strings. In the application, they translate to targeted search queries passed to gpt-researcher's `ResearchConductor`:

```python
# Example: home_services.json retry strategies
RETRY_STRATEGY_QUERIES = {
    "trade_associations": "site:nrca.net OR site:phccweb.org OR site:acca.com {topic}",
    "manufacturer_specifications": "{topic} manufacturer specifications installation guide",
    "building_codes": "{topic} IPC IRC building code requirements",
    "industry_forums": "{topic} professional contractor forum discussion",
    "textbooks_trade": "{topic} trade certification textbook",
    "government_building_databases": "{topic} site:energy.gov OR site:hud.gov",
}

# legal_services.json retry strategies
RETRY_STRATEGY_QUERIES = {
    "primary_legal_sources": "{topic} site:law.cornell.edu OR site:justia.com",
    "case_law_databases": "{topic} case law precedent Google Scholar",
    "bar_association_publications": "{topic} site:americanbar.org OR state bar publication",
    "law_review_articles": "{topic} law review journal",
    "government_statutes": "{topic} site:congress.gov OR state statutes",
    "legal_textbooks": "{topic} legal textbook education",
}
```

These query templates are stored in `authority_models.repositioning_rules` JSONB or as a separate `retry_strategy_queries` JSONB column. The `{topic}` placeholder is replaced at runtime with the dossier's normalized topic.

### 3.4 Fallback Authority Types — Complete Enum

The five industry files confirm the full set of fallback authority types the application needs to handle:

```python
class FallbackAuthorityType(Enum):
    PRACTITIONER_EXPERTISE = "PRACTITIONER_EXPERTISE"   # health_wellness_spa
    ATTORNEY_EXPERTISE = "ATTORNEY_EXPERTISE"           # legal_services
    FIELD_EXPERTISE = "FIELD_EXPERTISE"                 # home_services
    ADVISOR_EXPERTISE = "ADVISOR_EXPERTISE"             # financial_advisory
    DEVELOPER_EXPERTISE = "DEVELOPER_EXPERTISE"         # software_development
    INDUSTRY_STANDARDS = "INDUSTRY_STANDARDS"           # secondary for multiple
    # From framework (not yet in a JSON file):
    CLIENT_OBSERVATION = "CLIENT_OBSERVATION"           # health_wellness_spa secondary
    OPEN_SOURCE_COMMUNITY = "OPEN_SOURCE_COMMUNITY"     # software_development secondary
    MANUFACTURER_DATA = "MANUFACTURER_DATA"             # home_services secondary
    CASE_PRECEDENT = "CASE_PRECEDENT"                  # legal_services secondary
    REGULATORY_FRAMEWORK = "REGULATORY_FRAMEWORK"       # financial_advisory secondary
    STATUTORY_FRAMEWORK = "STATUTORY_FRAMEWORK"         # legal_services secondary
```

### 3.5 Claim Repositioning — Stored as Structured Data

Each industry JSON's `claim_repositioning.replacements` array is an ordered list of find-replace rules. These are stored in the database and applied programmatically, not evaluated by an LLM:

```python
@dataclass
class ClaimRepositioningRule:
    pattern: str        # "Research shows..."
    replacement: str    # "Our therapists observe..."
    context: str        # "For general research claims"

class ClaimRepositioner:
    """
    Applies industry-specific claim repositioning rules to article content
    when Authority_Mode is EXPERT_FALLBACK.
    
    Rules are applied in order. Pattern matching is case-insensitive,
    partial string match. The replacement preserves surrounding sentence
    structure — only the matched phrase is replaced, not the whole sentence.
    
    Applied by Stage 2 (Brief) when the handoff contains Authority_Mode: EXPERT_FALLBACK.
    Stage 2 is responsible for ensuring the Content Brief reflects repositioned language;
    Stage 3 then writes from the Brief without needing to know fallback mode is active.
    """

    def apply(self, content: str, rules: list[ClaimRepositioningRule]) -> str:
        import re
        result = content
        for rule in rules:
            pattern = re.escape(rule.pattern.rstrip("...")).rstrip(r"\.")
            result = re.sub(
                pattern + r'[^.]*',
                rule.replacement,
                result,
                flags=re.IGNORECASE
            )
        return result
```

---

## 4. CSS Template — Confirmed Token Set and Component Inventory

### 4.1 Exactly 11 Client-Injected Tokens

The `blog_integration_base.css` header comment is authoritative. Exactly eleven `{{PLACEHOLDER}}` tokens are injected at Stage 7 build time:

```
{{PRIMARY}}       → --primary (hex)
{{PRIMARY_2}}     → --primary-2 (hex)
{{PRIMARY_SOFT}}  → --primary-soft (hex)
{{PRIMARY_GLOW}}  → --primary-glow (rgba)
{{PRIMARY_RGB}}   → --primary-rgb (r, g, b triplet — no # prefix)
{{ACCENT}}        → --accent (hex)
{{ACCENT_2}}      → --accent-2 (hex)
{{ACCENT_SOFT}}   → --accent-soft (hex)
{{ACCENT_RGB}}    → --accent-rgb (r, g, b triplet — no # prefix)
{{INK}}           → --ink (hex)
{{LINE_STRONG}}   → --line-strong (rgba)
```

Everything else in `:root` (cream, paper, muted, soft, line, warn, radius values, spacing scale, type scale, layout widths) is **static** — the same across all clients. Only these 11 values change per client.

This is an important correction to the v2 architecture: `brand_colors` JSONB on `client_reference_files` must store exactly these 11 keys, with the correct value types (hex strings for hex tokens, `"r, g, b"` strings for RGB triplets, `rgba(...)` strings for glow/line-strong).

```python
# The authoritative brand_colors schema
REQUIRED_BRAND_COLOR_KEYS = {
    "primary",       # "#1B3D6F"
    "primary_2",     # "#1E4F8A"
    "primary_soft",  # "#EEF3FA"
    "primary_glow",  # "rgba(27, 61, 111, 0.08)"
    "primary_rgb",   # "27, 61, 111"   ← no # prefix; used inside rgba()
    "accent",        # "#E8762B"
    "accent_2",      # "#D4621E"
    "accent_soft",   # "#FDF1E8"
    "accent_rgb",    # "232, 118, 43"  ← no # prefix
    "ink",           # "#1C1C1A"
    "line_strong",   # "rgba(27, 61, 111, 0.22)"
}

def apply_brand_tokens(css_template: str, brand_colors: dict) -> str:
    token_map = {
        "{{PRIMARY}}":      brand_colors["primary"],
        "{{PRIMARY_2}}":    brand_colors["primary_2"],
        "{{PRIMARY_SOFT}}": brand_colors["primary_soft"],
        "{{PRIMARY_GLOW}}": brand_colors["primary_glow"],
        "{{PRIMARY_RGB}}":  brand_colors["primary_rgb"],
        "{{ACCENT}}":       brand_colors["accent"],
        "{{ACCENT_2}}":     brand_colors["accent_2"],
        "{{ACCENT_SOFT}}":  brand_colors["accent_soft"],
        "{{ACCENT_RGB}}":   brand_colors["accent_rgb"],
        "{{INK}}":          brand_colors["ink"],
        "{{LINE_STRONG}}":  brand_colors["line_strong"],
    }
    result = css_template
    for token, value in token_map.items():
        result = result.replace(token, value)
    
    # Verify all tokens were replaced (none remaining)
    remaining = [t for t in token_map if t in result]
    if remaining:
        raise MissingBrandColorError(
            f"Brand colors not provided for: {remaining}"
        )
    return result
```

### 4.2 Complete Component Inventory

The CSS file defines more components than appeared in the reference run article. Stage 7's `FormattingService` should support all of them, but only render components present in the approved draft. Here is the complete component list from the CSS:

**Structural layout**
- `.blog-wrap` — outer article wrapper (`<article class="blog-wrap" id="main-content">`)
- `.skip-link` — accessibility skip navigation (always present)
- `.header` — full-bleed hero header with H1
- `.header-eyebrow` — optional pill label above H1 (e.g., category badge)
- `.card-wrap` — width-constrained wrapper for infographic modules
- `.prose` — standard content section; one per H2
- `.toc-card` — collapsible table of contents (optional; generated if ≥4 H2 sections)

**Infographic modules** (rendered when content warrants; optional)
- `.infographic-card` — outer container for visual modules
- `.section-label` — uppercase section badge within infographic
- `.card-box` — bordered card surface within infographic
- `.stats-grid` — grid layout for stat blocks (`.two-up`, `.three-up`, `.four-up` variants)
- `.stat-card` — individual statistic display
- `.flow-grid` — numbered step/process layout
- `.checklist-grid` — two-column checklist layout (`.single-col` variant)
- `.table-scroll` — responsive table wrapper
- `.compare-table` — styled comparison table
- `.insight-box` — pull quote / key insight callout
- `.warning-card` — caution/warning callout with icon

**CTA section**
- `.cta-card` — final CTA block (always present; last element in `blog-wrap`)
- `.cta-pills` — flex container for service/benefit chips
- `.cta-pill` — individual pill badge

**Typography utilities**
- `.callout-text` — styled blockquote/callout within prose
- `.prose li` — card-style list items (all `<ul>` and `<ol>` in prose)

### 4.3 What This Means for Stage 7

The reference run article used only `.header`, `.prose`, and `.cta-card`. But the CSS supports richer output. Stage 7's `FormattingService` builds HTML from the approved markdown, and for standard blog posts the three components are sufficient. The infographic modules (`.stats-grid`, `.flow-grid`, etc.) are available for future enhancement but require the LLM to generate structured HTML for them — they can't be derived from plain markdown alone.

The `FormattingService` should:
1. Always render `.header`, one `.prose` per H2, and `.cta-card`
2. Optionally generate `.toc-card` when the article has ≥4 H2 sections (the CSS includes the full TOC component with collapsible `<details>`)
3. Not attempt to render infographic modules from standard markdown input — those are a future feature

The `font-family` in the CSS body rule is `'DM Sans'` with system-ui fallbacks. This matches the reference run's Google Fonts import. The `google_fonts_url` field on `client_reference_files` stores the specific Google Fonts URL, and the `FormattingService` injects the `<link>` preconnect tags when that field is populated.

### 4.4 The CSS Comment References a Nonexistent Script

Line 7 of `blog_integration_base.css` reads:
```
* The stage8_blog_integration.py script injects brand tokens...
```

This is a reference to the old compromised system. It does not exist in the new system. The token injection is performed by `apply_brand_tokens()` in the application's `FormattingService`. The comment is documentation debt from the old system — it can be stripped when the CSS is stored or when it is inlined into the HTML output.

---

## 5. Revised `source_validation_reports` Table

Incorporating the confirmed JSON output format from the framework:

```sql
-- Source validation report (one per Stage 1.5 run)
CREATE TABLE source_validation_reports (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  status                TEXT NOT NULL
    CHECK (status IN (
      'APPROVED',
      'APPROVED_WITH_FALLBACK',
      'REJECTED_DOSSIER_NOT_FOUND',
      'REJECTED_NO_SOURCES',
      'REJECTED_CONFIG_NOT_FOUND',
      'REJECTED_MIN_SOURCES_ZERO'
    )),
  industry_key          TEXT NOT NULL,
  authority_overrides_applied BOOLEAN DEFAULT FALSE,
  sources_total         INTEGER,
  sources_verified      INTEGER,
  sources_unverified    INTEGER,
  fallback_activated    BOOLEAN NOT NULL DEFAULT FALSE,
  fallback_reason       TEXT,
  fallback_primary      TEXT,             -- e.g., "PRACTITIONER_EXPERTISE"
  allowed_claims        TEXT[],
  disallowed_claims     TEXT[],
  authority_phrase      TEXT,
  validation_timestamp  TIMESTAMPTZ DEFAULT NOW(),
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Individual source validation results
CREATE TABLE source_validation_sources (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id        UUID NOT NULL REFERENCES source_validation_reports(id) ON DELETE CASCADE,
  run_id           UUID NOT NULL REFERENCES runs(id),
  source_num       INTEGER NOT NULL,
  claimed_claim    TEXT,
  url              TEXT,
  status           TEXT NOT NULL
    CHECK (status IN ('VERIFIED', 'UNVERIFIED_AFTER_6_ATTEMPTS', 'SKIPPED')),
  attempts         INTEGER DEFAULT 0,
  fallback_action  TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Claim repositioning rules applied to this run (when fallback activated)
CREATE TABLE source_validation_repositioning (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id   UUID NOT NULL REFERENCES source_validation_reports(id) ON DELETE CASCADE,
  pattern     TEXT NOT NULL,
  replacement TEXT NOT NULL,
  context     TEXT,
  sort_order  INTEGER NOT NULL
);
```

---

## 6. Revised `SourceValidationService` — No Python Script

This replaces the implementation in the gpt-researcher addendum, incorporating the confirmed framework behavior:

```python
# services/source_validation_service.py
from domain.enums import AuthorityMode, ValidationStatus
from domain.run import Run

class SourceValidationService:
    """
    Stage 1.5: Source Validation.
    
    Implements the three-stage flow from source-validation-framework.md:
      1. URL validation (via gpt-researcher BrowserManager)
      2. Retry loop — up to 6 attempts, one per retry_strategy in industry config
      3. Fallback decision — APPROVED / APPROVED_WITH_FALLBACK / REJECTED
    
    No Python scripts. All behavior is implemented in this service class
    using gpt-researcher as the search/scraping engine.
    """

    def __init__(self, authority_model_repo, gpt_researcher_factory):
        self._models = authority_model_repo
        self._gptr = gpt_researcher_factory

    async def validate(self, dossier: str, run: Run) -> ValidationReport:
        model = self._models.load(
            industry=run.context.industry,
            client_overrides=run.context.authority_overrides,
        )

        # Short-circuit for field-expertise-led industries (home_services: min = 0)
        if model.min_valid_sources == 0:
            return ValidationReport(
                status=ValidationStatus.APPROVED,
                reason="Industry does not require external source verification (min_valid_sources_required = 0)",
                sources_total=0, sources_verified=0, sources_unverified=0,
                fallback_activated=False,
                authority_mode=AuthorityMode.NORMAL,
            )

        # Extract source URLs from Section 2 of the Research Dossier
        sources = self._extract_source_bank(dossier)
        if not sources:
            return ValidationReport(status=ValidationStatus.REJECTED_NO_SOURCES)

        # Stage 1: Initial validation via gpt-researcher's BrowserManager
        verified, failed = await self._initial_validation(sources, run.context.topic)

        # Stage 2: Retry loop — one attempt per strategy in industry config
        if len(verified) < model.min_valid_sources and failed:
            for i, strategy in enumerate(model.retry_strategies):
                if len(verified) >= model.min_valid_sources:
                    break
                rescued = await self._retry_with_strategy(
                    failed_sources=failed,
                    strategy=strategy,
                    topic=run.context.topic,
                    industry=model.industry_key,
                    attempt_num=i + 1,
                )
                verified.extend(rescued)
                failed = [s for s in failed if s not in rescued]

        # Stage 3: Fallback decision
        return self._compute_status(verified, failed, model)

    async def _initial_validation(self, sources, topic):
        """
        Use gpt-researcher to scrape each source URL.
        Sources where BrowserManager returns empty content are treated as failed.
        """
        researcher = self._gptr.create(query=topic)
        researcher.cfg.curate_sources = False

        verified, failed = [], []
        for source in sources:
            content = await researcher.scrape_url(source["url"])
            if content and len(content.strip()) > 50:
                verified.append({**source, "scraped_content": content, "attempts": 0})
            else:
                failed.append({**source, "attempts": 0})

        return verified, failed

    async def _retry_with_strategy(self, failed_sources, strategy, topic, industry, attempt_num):
        """
        For each failed source, attempt to find a replacement using the
        given strategy. Returns any newly verified sources.
        """
        strategy_queries = self._models.get_strategy_queries(industry)
        query_template = strategy_queries.get(strategy, f"{topic} {strategy}")
        query = query_template.replace("{topic}", topic)

        researcher = self._gptr.create(query=query)
        researcher.cfg.curate_sources = False
        await researcher.conduct_research()

        new_sources = []
        for url in researcher.get_source_urls():
            content = await researcher.scrape_url(url)
            if content and len(content.strip()) > 50:
                new_sources.append({
                    "url": url,
                    "scraped_content": content,
                    "status": "VERIFIED",
                    "attempts": attempt_num,
                })
        return new_sources

    def _compute_status(self, verified, failed, model) -> ValidationReport:
        if len(verified) >= model.min_valid_sources:
            return ValidationReport(
                status=ValidationStatus.APPROVED,
                sources_verified=len(verified),
                sources_unverified=len(failed),
                fallback_activated=False,
                authority_mode=AuthorityMode.NORMAL,
            )

        # Fallback activated
        return ValidationReport(
            status=ValidationStatus.APPROVED_WITH_FALLBACK,
            sources_verified=len(verified),
            sources_unverified=len(failed),
            fallback_activated=True,
            fallback_reason=f"Only {len(verified)} of {len(verified)+len(failed)} sources verified; min required: {model.min_valid_sources}",
            authority_mode=AuthorityMode.EXPERT_FALLBACK,
            fallback_primary=model.fallback_primary,
            allowed_claims=model.allowed_claims,
            disallowed_claims=model.disallowed_claims,
            repositioning_rules=model.repositioning_rules,
            authority_phrase=model.authority_phrase,
        )
```

---

## 7. Complete File Inventory Status

Every file referenced across all stage CONTEXT files, now resolved:

| File | Status | Resolution |
|---|---|---|
| `_config/anti-ai-checklist.md` | ✓ Provided | Fully modeled in v2 |
| `_config/search-quality-rubric.md` | ✓ Provided | Fully modeled in v2 |
| `_config/handoff_template.md` | ✓ Provided | Fully modeled in v2 |
| `_config/source-validation-framework.md` | ✓ Provided | Modeled in this addendum |
| `_config/authority-models/_template.json` | ✓ Provided | Schema confirmed; `authority_models` table |
| `_config/authority-models/home_services.json` | ✓ Provided | Seeded to `authority_models` |
| `_config/authority-models/health_wellness_spa.json` | ✓ Provided | Seeded to `authority_models` |
| `_config/authority-models/legal_services.json` | ✓ Provided | Seeded to `authority_models` |
| `_config/authority-models/financial_advisory.json` | ✓ Provided | Seeded to `authority_models` |
| `_config/authority-models/software_development.json` | ✓ Provided | Seeded to `authority_models` |
| `templates/blog_integration_base.css` | ✓ Provided | Modeled in this addendum; stored verbatim in `templates` table |
| `_config/batch-controller.md` | Not provided | Application handles via worker queue; not needed |
| `_config/stage_automation_rules.md` | Not provided | `auto_advance` flag on `StageOutput`; not needed |
| `_config/manual-stage-execution-request.md` | Not provided | Not applicable — old system manual run template |
| `_config/handoff-contracts.md` | Not provided | Covered by stage CONTEXT files; not needed separately |
| `_config/blog-publishing-guide.md` | Not provided | Post-Stage 7; not needed for application |
| `_config/html-style-lint.md` | Not provided | Replaced by application's `_verify_no_internal_tokens()` |
| `_config/source-validation-guide.md` | Not provided | Troubleshooting reference; not needed for application |
| `tools/stage1_source_validator.py` | ❌ Not carried forward | Old compromised system; replaced by `SourceValidationService` |
| `tools/word_count.py` | ❌ Not carried forward | Old compromised system; replaced by `len(content.split())` |
| `tools/merge_manual_html.py` | ❌ Not carried forward | Old compromised system; replaced by API endpoint |
| `tools/planning_loader.md` | Not provided | Run folder slug logic confirmed from reference run examples |

**All files needed to implement the pipeline are now accounted for.** No further files are outstanding.

---

## 8. One Storage Addition: CSS Template Table

The `blog_integration_base.css` file needs to be accessible at Stage 7 build time. Storing it in the database (rather than on the filesystem) keeps the application self-contained:

```sql
CREATE TABLE css_templates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL UNIQUE,    -- "blog_integration_base"
  version       TEXT,
  css_content   TEXT NOT NULL,           -- the full CSS file content
  token_names   TEXT[] NOT NULL,         -- ["PRIMARY","PRIMARY_2",...] — for validation
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Seed with the blog_integration_base.css content
INSERT INTO css_templates (name, version, css_content, token_names)
VALUES (
  'blog_integration_base',
  '1.0',
  '<full CSS file content>',
  ARRAY['PRIMARY','PRIMARY_2','PRIMARY_SOFT','PRIMARY_GLOW','PRIMARY_RGB',
        'ACCENT','ACCENT_2','ACCENT_SOFT','ACCENT_RGB','INK','LINE_STRONG']
);
```

At Stage 7, `FormattingService` fetches the template by name, applies brand tokens, and inlines the result into the `<style>` block. This also means updating the CSS design system is a database operation (update `css_content`), not a deployment.

---

*Addendum version 1.0 — July 2026. This is the final addendum in the architecture series. Read alongside `architecture_migration_plan_v2.md`, `architecture_addendum_templates.md`, and `architecture_addendum_gpt_researcher.md`. Together the four documents constitute the complete implementation specification.*
