# Quick Reference Card

Keep this open alongside Cursor. Copy-paste as needed.

---

## Session Start Prompt (use at the beginning of every new Cursor session)

```
Read .cursorrules. We are on Phase [N], Step [N.N].
Last completed: [describe last thing done].
Next task: [describe next thing to do].
Before writing code, confirm which file in BUILD_GUIDE.md or REFERENCE.md covers this.
```

---

## The 11 Non-Negotiables (check these every day)

1. No Python scripts from the old system (`stage1_source_validator`, `word_count.py`, `merge_manual_html`)
2. Parsers built before stage services
3. `<!--BRIEF:` tokens stripped in Stage 3 `_load_context`; never appear in Stage 3+ output
4. `## Editorial Note` split in Stage 4 `_parse_output`; stored in `editorial_note`, not `article_content`
5. `## SEO Annotation Sheet` split in Stage 5 `_parse_output`; stored in `seo_annotation`, never `article_content`
6. Word count stored as `{count, target_min, target_max, status}` dict — not a string
7. `PRIMARY_RGB` and `ACCENT_RGB` are `"r, g, b"` — no `#` prefix
8. QA Section F issues → `CLIENT_DECISION` (no revision routing)
9. home_services `min_valid_sources = 0` → immediate `APPROVED`, no validation loop
10. Stage 7 pre-flight: blocked if QA returned `revision_required`
11. Article slug from H1 text, not from topic string or folder slug

---

## Gate Checks by Phase

| Phase | Gate |
|---|---|
| 1 — Foundation | GET /health returns 200; domain models instantiate; StageContract can't be instantiated directly |
| 2 — Parsing | All 6 parsers pass tests against reference run files |
| 3 — Onboarding | Client onboards; brand_colors JSONB has 11 keys; `primary_rgb` has no `#` |
| 4 — Run Init | Path A and Path B create runs; UnresolvedItems created; overlap check works |
| 5 — Research | 8 sections in dossier; home_services short-circuits to APPROVED |
| 6 — Brief/Writing/Humanization | No BRIEF tokens in Stage 3+; editorial note separate; content types table present in Stage 3 output |
| 7 — SEO/QA/Formatting | 38/39 QA pass (or better); HTML has zero internal tokens; slug from H1 |
| 8 — Workers/Frontend | ARQ worker starts; all stage views render; QA decision flow works |
| 9 — Cutover | 3 full runs pass all structure checks; zero grep hits for old script names |

---

## Reference Run Ground Truth

Use these confirmed values to validate output:

| What | Value |
|---|---|
| Client | Rankrise_Marketing |
| Industry | home_services (min_valid_sources = 0) |
| Topic | Content Marketing for Home Service Businesses |
| Primary keyword | content marketing for home service businesses |
| Word count | 2776 words, target 2200-2800, WITHIN TARGET |
| QA checklist | 38/39 PASS |
| AI Risk Score | 5/15 |
| Section F | FLAG — CLIENT_DECISION |
| Article slug | content-marketing-home-service-businesses |
| CSS primary color | #1B3D6F |
| CSS primary_rgb | 27, 61, 111 (no # prefix) |
| CSS accent color | #E8762B |
| CSS accent_rgb | 232, 118, 43 (no # prefix) |
| HTML line count | 784 lines |
| Fonts | DM Sans (body) + DM Serif Display (headers) |

---

## Token Leakage Check (run this any time)

```python
# Paste this into Cursor and ask it to run against any stage output
FORBIDDEN_TOKENS = [
    "<!--BRIEF:",
    "BEGIN_BLOG_REQUEST",
    "END_BLOG_REQUEST",
    "## Editorial Note",
    "## SEO Annotation Sheet",
]

def check_token_leakage(content: str, stage_name: str) -> list[str]:
    violations = []
    for token in FORBIDDEN_TOKENS:
        if token in content:
            violations.append(f"LEAK in {stage_name}: found '{token}'")
    return violations
```

---

## Brand Colors Validation (run at Stage 0 and Stage 7)

```python
REQUIRED_BRAND_COLOR_KEYS = {
    "primary", "primary_2", "primary_soft", "primary_glow", "primary_rgb",
    "accent", "accent_2", "accent_soft", "accent_rgb", "ink", "line_strong"
}
RGB_TRIPLET_KEYS = {"primary_rgb", "accent_rgb"}  # must NOT have # prefix

def validate_brand_colors(colors: dict) -> list[str]:
    errors = []
    missing = REQUIRED_BRAND_COLOR_KEYS - set(colors.keys())
    if missing:
        errors.append(f"Missing brand color keys: {missing}")
    for key in RGB_TRIPLET_KEYS:
        if key in colors and colors[key].startswith("#"):
            errors.append(f"{key} must not start with '#', got: {colors[key]}")
    return errors
```

---

## Stage Load Contract Cheatsheet

What each stage loads (and what it must NOT load):

| Stage | Loads | Must NOT load |
|---|---|---|
| 0 | Content samples only | Reference files, run files |
| Pre-1 | All 3 reference files, Run Log tail | Stage files |
| 1 | Style Card + Audience Profile + Brand Notes (partial) + Handoff | anti-ai, rubric |
| 2 | Style Card + Audience Profile + Dossier + Handoff + Brand Notes (partial) | anti-ai, rubric |
| 3 | Style Card + Content Brief (STRIPPED) + Handoff + anti-ai Section 3 | Audience Profile, Dossier, Brand Notes |
| 4 | Style Card + First Draft + Handoff + anti-ai Section 3 | Content Brief, Dossier |
| 5 | Humanized Draft + Handoff + Content Brief (partial) + Style Card (partial) | Audience Profile, Brand Notes |
| 6 | SEO Draft + Handoff + anti-ai (FULL) + Style Card (partial) + Brand Notes (partial) + Brief (partial) | Dossier, earlier drafts |
| 7 | Style Card (full) + Brand Notes (full) + QA Approved Draft + Handoff | Earlier drafts, Dossier, Brief |

---

## Revision Routing

When QA returns REVISION_REQUIRED, route to:

| Failure contains | Route to |
|---|---|
| factual_claim, ymyl, cta_missing, eeat | Stage 3 |
| ai_sounding, voice_inconsistency | Stage 4 |
| keyword_placement, meta_title, header_hierarchy | Stage 5 |

CLIENT_DECISION issues → no routing, no revision. Human action only.

---

## Authority Model Min Sources

| Industry | `min_valid_sources` | Behavior |
|---|---|---|
| home_services | 0 | Immediately APPROVED — no validation |
| health_wellness_spa | 1 | Standard validation flow |
| software_development | 1 | Standard validation flow |
| financial_advisory | 2 | Standard validation flow |
| legal_services | 3 | Most restrictive |

---

## File Map (old system → application)

| Old file | Lives in application as |
|---|---|
| `Client_Template/CONTEXT.md` | `client_contexts` table + `ClientContextAssembler` |
| `Reference/Style_Reference_Card.md` | `client_reference_files.style_reference_card` |
| `Reference/Audience_Profile.md` | `client_reference_files.audience_profile` |
| `Reference/Brand_Notes.md` | `client_reference_files.brand_notes` |
| `01_Research_Dossier.md` | `stage_outputs.article_content` (stage_number=1) |
| `## Editorial Note` (in draft) | `stage_outputs.editorial_note` (stage_number=4) |
| `## SEO Annotation Sheet` (in draft) | `seo_annotations` table |
| `06_QA_Signoff.md` | `qa_results` + `qa_issues` tables |
| `06_QA_Approved_Draft.md` | `stage_outputs.article_content` (stage_number=6) |
| `07_Blog_Final.html` | `published_articles.html_content` |
| `templates/blog_integration_base.css` | `css_templates` table (seeded) |
| `_config/authority-models/*.json` | `authority_models` table (seeded) |
| `tools/word_count.py` | `len(content.split())` inline |
| `tools/stage1_source_validator.py` | `SourceValidationService` |
| `tools/merge_manual_html.py` | `POST /runs/{id}/stages/7/manual-upload` |

---

## LLM Provider Quick Switch

### Set pipeline provider (stages 0–7)
```bash
LLM_PROVIDER=anthropic       # default
LLM_PROVIDER=openrouter
LLM_PROVIDER=ollama
LLM_PROVIDER=lm_studio
```

### Set gpt-researcher provider (Stage 1 research engine only)
Format: `provider:model-name`
```bash
# Anthropic (default)
FAST_LLM=anthropic:claude-haiku-4-5-20251001
SMART_LLM=anthropic:claude-sonnet-4-6

# OpenRouter
OPENAI_BASE_URL=https://openrouter.ai/api/v1
FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
EMBEDDING=google_genai:models/text-embedding-004   # ← required; OpenRouter has no embedding

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
FAST_LLM=ollama:llama3.1:8b
SMART_LLM=ollama:llama3.1:70b
EMBEDDING=ollama:nomic-embed-text

# LM Studio (local)
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
FAST_LLM=openai:<exact-model-name-from-lm-studio-ui>
```

### Required packages per provider
```bash
pip install langchain-openrouter   # OpenRouter only
pip install langchain-ollama       # Ollama only
# LM Studio: no extra package (uses openai client)
```

### Provider capability summary
| Provider | Quality | Cost | Privacy |
|---|---|---|---|
| Anthropic | ⭐⭐⭐⭐⭐ | $$$ | Cloud |
| OpenRouter | ⭐⭐⭐⭐⭐ | $-$$$ | Cloud |
| Ollama 70B | ⭐⭐⭐ | Free | 🔒 Local |
| LM Studio 8B | ⭐⭐ | Free | 🔒 Local |

### Factory — only place to add providers
```python
# content_pipeline/llm/provider_factory.py
# Add new elif branch to _create() method
# Never add provider selection logic to stage services
```
