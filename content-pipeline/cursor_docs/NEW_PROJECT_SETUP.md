# New Project Setup Guide

**What this is:** Step-by-step instructions for creating a clean project folder from scratch. Follow this before opening Cursor.

**Time required:** ~20 minutes to set up the folder structure. No code yet.

---

## The Final Folder Structure

When you're done, your project folder should look exactly like this:

```
content-pipeline/
│
├── .cursorrules                        ← Cursor AI rules (auto-loads every session)
│
├── docs/
│   ├── BUILD_GUIDE.md                  ← Primary implementation spec (read this first)
│   ├── REFERENCE.md                    ← Schema, models, API contracts (look things up here)
│   │
│   ├── stage_contracts/                ← LLM system prompts for each pipeline stage
│   │   ├── stage0_onboarding_CONTEXT.md
│   │   ├── stage1_1_onboarded_CONTEXT.md
│   │   ├── stage1_2_Research_CONTEXT.md
│   │   ├── stage2_brief_CONTEXT.md
│   │   ├── stage3_writing_CONTEXT.md
│   │   ├── stage4_humanization_CONTEXT.md
│   │   ├── stage5_seo_CONTEXT.md
│   │   ├── stage6_qa_CONTEXT.md
│   │   └── stage7_blog-formatting_CONTEXT.md
│   │
│   ├── pipeline_config/                ← Pipeline rules loaded at runtime
│   │   ├── anti-ai-checklist.md
│   │   ├── search-quality-rubric.md
│   │   ├── handoff_template.md
│   │   └── source-validation-framework.md
│   │
│   └── architecture/                   ← Background reference (not needed daily)
│       ├── architecture_migration_plan_v2.md
│       ├── architecture_addendum_templates.md
│       ├── architecture_addendum_gpt_researcher.md
│       ├── architecture_addendum_final.md
│       └── architecture_addendum_llm_providers.md
│
├── cursor_docs/                        ← Phase-by-phase build instructions
│   ├── 00_KICKOFF.md                   ← Start here — paste kickoff prompt into Cursor
│   ├── 01_PHASE_1_Foundation.md
│   ├── 02_PHASE_2_Parsing.md
│   ├── 03_PHASE_3_4_Onboarding_RunInit.md
│   ├── 04_PHASE_5_7_Stages.md
│   ├── 05_PHASE_8_9_Launch.md
│   └── QUICK_REFERENCE.md              ← Keep this open while building
│
├── reference_run/                      ← Real pipeline outputs used to validate parsers/stages
│   ├── 00_Stage_1_Handoff_Brief.md
│   ├── 01_Research_Dossier.md
│   ├── 01_Stage_2_Handoff.md
│   ├── 02_Content_Brief.md
│   ├── 02_Stage_3_Handoff.md
│   ├── 03_First_Draft.md
│   ├── 03_Stage_4_Handoff.md
│   ├── 04_Humanized_Draft.md
│   ├── 04_Stage_5_Handoff.md
│   ├── 05_SEO_Draft.md
│   ├── 05_Stage_6_Handoff.md
│   ├── 06_QA_Approved_Draft.md
│   ├── 06_QA_Signoff.md
│   ├── 06_Stage_7_Handoff.md
│   ├── 07_Blog_Final.html
│   └── Run_Log.md
│
├── pipeline_assets/                    ← Static assets seeded into the database at deploy
│   ├── css/
│   │   └── blog_integration_base.css
│   ├── authority_models/
│   │   ├── _template.json
│   │   ├── home_services.json
│   │   ├── health_wellness_spa.json
│   │   ├── legal_services.json
│   │   ├── financial_advisory.json
│   │   └── software_development.json
│   └── client_template/
│       ├── CONTEXT.md
│       ├── Style_Reference_Card.md
│       ├── Audience_Profile.md
│       └── Brand_Notes.md
│
└── .env.example                        ← All environment variables with comments
```

---

## Step 1 — Create the Folder and Initialize Git

```bash
mkdir content-pipeline
cd content-pipeline
git init
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".venv/" >> .gitignore
echo "node_modules/" >> .gitignore
```

---

## Step 2 — Create All Subdirectories

```bash
mkdir -p docs/stage_contracts
mkdir -p docs/pipeline_config
mkdir -p docs/architecture
mkdir -p cursor_docs
mkdir -p reference_run
mkdir -p pipeline_assets/css
mkdir -p pipeline_assets/authority_models
mkdir -p pipeline_assets/client_template
```

---

## Step 3 — Copy Files From This Session's Outputs

These are the files generated during our architecture conversations. Copy each one to its destination.

### From `cursor_docs/` outputs → `content-pipeline/cursor_docs/`

| File | Destination |
|---|---|
| `.cursorrules` | `content-pipeline/.cursorrules` (root — not inside cursor_docs/) |
| `00_KICKOFF.md` | `content-pipeline/cursor_docs/00_KICKOFF.md` |
| `01_PHASE_1_Foundation.md` | `content-pipeline/cursor_docs/01_PHASE_1_Foundation.md` |
| `02_PHASE_2_Parsing.md` | `content-pipeline/cursor_docs/02_PHASE_2_Parsing.md` |
| `03_PHASE_3_4_Onboarding_RunInit.md` | `content-pipeline/cursor_docs/03_PHASE_3_4_Onboarding_RunInit.md` |
| `04_PHASE_5_7_Stages.md` | `content-pipeline/cursor_docs/04_PHASE_5_7_Stages.md` |
| `05_PHASE_8_9_Launch.md` | `content-pipeline/cursor_docs/05_PHASE_8_9_Launch.md` |
| `QUICK_REFERENCE.md` | `content-pipeline/cursor_docs/QUICK_REFERENCE.md` |

### From architecture outputs → `content-pipeline/docs/`

| File | Destination |
|---|---|
| `BUILD_GUIDE.md` | `content-pipeline/docs/BUILD_GUIDE.md` |
| `REFERENCE.md` | `content-pipeline/docs/REFERENCE.md` |
| `architecture_migration_plan_v2.md` | `content-pipeline/docs/architecture/architecture_migration_plan_v2.md` |
| `architecture_addendum_templates.md` | `content-pipeline/docs/architecture/architecture_addendum_templates.md` |
| `architecture_addendum_gpt_researcher.md` | `content-pipeline/docs/architecture/architecture_addendum_gpt_researcher.md` |
| `architecture_addendum_final.md` | `content-pipeline/docs/architecture/architecture_addendum_final.md` |
| `architecture_addendum_llm_providers.md` | `content-pipeline/docs/architecture/architecture_addendum_llm_providers.md` |

---

## Step 4 — Copy Files From the Original Pipeline (Stage CONTEXT Files)

These are the pipeline's stage contract files — the LLM system prompts for each stage. They live in your existing Claude Project knowledge panel. Export or copy each one.

Destination: `content-pipeline/docs/stage_contracts/`

| Original filename | Save as |
|---|---|
| `stage0_onboarding_CONTEXT.md` | `stage0_onboarding_CONTEXT.md` |
| `stage1_1_onboarded_CONTEXT.md` | `stage1_1_onboarded_CONTEXT.md` |
| `1_2_Research_CONTEXT.md` | `stage1_2_Research_CONTEXT.md` |
| `stage2_brief_CONTEXT.md` | `stage2_brief_CONTEXT.md` |
| `stage3_writing_CONTEXT.md` | `stage3_writing_CONTEXT.md` |
| `stage4_humanization_CONTEXT.md` | `stage4_humanization_CONTEXT.md` |
| `stage5_seo_CONTEXT.md` | `stage5_seo_CONTEXT.md` |
| `stage6_qa_CONTEXT.md` | `stage6_qa_CONTEXT.md` |
| `stage7_blog-formatting_CONTEXT.md` | `stage7_blog-formatting_CONTEXT.md` |

**Note on `1_2_Research_CONTEXT.md`:** Rename it to `stage1_2_Research_CONTEXT.md` for consistent naming.

---

## Step 5 — Copy Pipeline Config Files (From This Session's Uploads)

These were uploaded during our conversation. They are pipeline rules and templates.

Destination: `content-pipeline/docs/pipeline_config/`

| File | Destination |
|---|---|
| `anti-ai-checklist.md` | `docs/pipeline_config/anti-ai-checklist.md` |
| `search-quality-rubric.md` | `docs/pipeline_config/search-quality-rubric.md` |
| `handoff_template.md` | `docs/pipeline_config/handoff_template.md` |
| `source-validation-framework.md` | `docs/pipeline_config/source-validation-framework.md` |

---

## Step 6 — Copy the Reference Run (16 Files)

These are real pipeline outputs used to validate parsers and stage behavior. They are your ground truth.

Destination: `content-pipeline/reference_run/`

| File |
|---|
| `00_Stage_1_Handoff_Brief.md` |
| `01_Research_Dossier.md` |
| `01_Stage_2_Handoff.md` |
| `02_Content_Brief.md` |
| `02_Stage_3_Handoff.md` |
| `03_First_Draft.md` |
| `03_Stage_4_Handoff.md` |
| `04_Humanized_Draft.md` |
| `04_Stage_5_Handoff.md` |
| `05_SEO_Draft.md` |
| `05_Stage_6_Handoff.md` |
| `06_QA_Approved_Draft.md` |
| `06_QA_Signoff.md` |
| `06_Stage_7_Handoff.md` |
| `07_Blog_Final.html` |
| `Run_Log.md` |

---

## Step 7 — Copy Pipeline Assets (Database Seed Files)

These files are loaded into the Supabase database during initial setup, not read at runtime by Python.

### CSS template → `content-pipeline/pipeline_assets/css/`

| File |
|---|
| `blog_integration_base.css` |

### Authority model configs → `content-pipeline/pipeline_assets/authority_models/`

| File |
|---|
| `_template.json` |
| `home_services.json` |
| `health_wellness_spa.json` |
| `legal_services.json` |
| `financial_advisory.json` |
| `software_development.json` |

### Client template → `content-pipeline/pipeline_assets/client_template/`

These are the blank templates Stage 0 uses as a structural reference when generating reference files.

| File |
|---|
| `CONTEXT.md` |
| `Style_Reference_Card.md` |
| `Audience_Profile.md` |
| `Brand_Notes.md` |

---

## Step 8 — Create `.env.example`

Create `content-pipeline/.env.example` with this content:

```bash
# ============================================================
# SUPABASE
# ============================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# ============================================================
# PIPELINE LLM PROVIDER
# Options: anthropic | openrouter | ollama | lm_studio
# ============================================================
LLM_PROVIDER=anthropic
PIPELINE_SMART_MODEL=claude-sonnet-4-6
PIPELINE_FAST_MODEL=claude-haiku-4-5-20251001

# ============================================================
# ANTHROPIC (default)
# ============================================================
ANTHROPIC_API_KEY=sk-ant-...

# ============================================================
# OPENROUTER (alternative)
# ============================================================
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_LIMIT_RPS=1
# When using OpenRouter: PIPELINE_SMART_MODEL=anthropic/claude-sonnet-4-5

# ============================================================
# OLLAMA (self-hosted)
# ============================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_CTX=8192
# When using Ollama: PIPELINE_SMART_MODEL=llama3.1:70b

# ============================================================
# LM STUDIO (self-hosted)
# ============================================================
LM_STUDIO_BASE_URL=http://localhost:1234/v1
# When using LM Studio: PIPELINE_SMART_MODEL=<model-name-from-lm-studio-ui>

# ============================================================
# GPT-RESEARCHER (Stage 1 research engine — separate from pipeline LLM)
# ============================================================
RETRIEVER=tavily
TAVILY_API_KEY=tvly-...
MAX_SCRAPER_WORKERS=15
MAX_SEARCH_RESULTS_PER_QUERY=5
CURATE_SOURCES=false

# --- Option A: Anthropic (default) ---
FAST_LLM=anthropic:claude-haiku-4-5-20251001
SMART_LLM=anthropic:claude-sonnet-4-6
STRATEGIC_LLM=anthropic:claude-sonnet-4-6

# --- Option B: OpenRouter (uncomment to use) ---
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# OPENAI_API_KEY=dummy_value
# FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
# SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
# STRATEGIC_LLM=openrouter:google/gemini-2.5-pro-exp-03-25
# EMBEDDING=google_genai:models/text-embedding-004
# GOOGLE_API_KEY=...

# --- Option C: Ollama (uncomment to use) ---
# FAST_LLM=ollama:llama3.1:8b
# SMART_LLM=ollama:llama3.1:70b
# STRATEGIC_LLM=ollama:llama3.1:70b
# EMBEDDING=ollama:nomic-embed-text
# EMBEDDING_PROVIDER=ollama

# --- Option D: LM Studio (uncomment to use) ---
# OPENAI_BASE_URL=http://localhost:1234/v1
# OPENAI_API_KEY=lm-studio
# FAST_LLM=openai:<your-model-name>
# SMART_LLM=openai:<your-model-name>
# STRATEGIC_LLM=openai:<your-model-name>

# ============================================================
# REDIS (for ARQ worker queue)
# ============================================================
REDIS_URL=redis://localhost:6379
```

---

## Step 9 — Verify the Folder Structure

Run this in your terminal to confirm everything is in place:

```bash
cd content-pipeline

echo "=== ROOT ==="
ls -la | grep -E "\.cursorrules|\.env\.example"

echo ""
echo "=== docs/ ==="
ls docs/
ls docs/stage_contracts/ | wc -l    # should be 9
ls docs/pipeline_config/ | wc -l   # should be 4
ls docs/architecture/ | wc -l      # should be 5

echo ""
echo "=== cursor_docs/ ==="
ls cursor_docs/ | wc -l            # should be 7 (6 .md files + QUICK_REFERENCE)

echo ""
echo "=== reference_run/ ==="
ls reference_run/ | wc -l          # should be 16

echo ""
echo "=== pipeline_assets/ ==="
ls pipeline_assets/css/            # should be 1 file
ls pipeline_assets/authority_models/ | wc -l  # should be 6
ls pipeline_assets/client_template/ | wc -l   # should be 4
```

Expected output:
```
docs/stage_contracts/    → 9 files
docs/pipeline_config/    → 4 files
docs/architecture/       → 5 files
cursor_docs/             → 7 files
reference_run/           → 16 files
pipeline_assets/css/     → blog_integration_base.css
authority_models/        → 6 files
client_template/         → 4 files
```

---

## Step 10 — Open in Cursor and Run the Kickoff

1. Open Cursor
2. File → Open Folder → select `content-pipeline/`
3. Confirm `.cursorrules` is visible in the file tree (it may be hidden — show hidden files)
4. Open `cursor_docs/00_KICKOFF.md`
5. Follow the instructions in that file — paste the kickoff prompt into Cursor chat
6. Answer the seven validation questions correctly before writing any code

---

## What You Do NOT Need to Copy

These are explicitly excluded:

| What | Why |
|---|---|
| The old folder-based pipeline runs (`Clients/`, `Runs/`) | Replaced by the database |
| `folder-organization-guide.md` | Was documentation for the old system; not relevant to the new build |
| `Root_Claude.md`, `Root_Context.md` | Were the old system's routing files; their logic is now in the application code |
| `_archive_v1_DO_NOT_USE.md` | Superseded version of the architecture; discard it |
| `architecture_migration_plan_v2.md` at the root | Moved to `docs/architecture/`; the root copy is redundant |
| Any `*.py` files from the old system | The old system is compromised; nothing from it carries forward |
| Old `tools/`, `scripts/` directories | Replaced by application code |

---

## File Count Summary

| Location | Count | Purpose |
|---|---|---|
| `.cursorrules` | 1 | AI behavior rules for every Cursor session |
| `docs/BUILD_GUIDE.md` + `REFERENCE.md` | 2 | Primary implementation docs |
| `docs/stage_contracts/` | 9 | LLM system prompts (stage CONTEXT files) |
| `docs/pipeline_config/` | 4 | Runtime pipeline rules |
| `docs/architecture/` | 5 | Background reference |
| `cursor_docs/` | 7 | Phase build prompts + quick reference |
| `reference_run/` | 16 | Ground truth for parser/stage validation |
| `pipeline_assets/css/` | 1 | CSS template for Stage 7 |
| `pipeline_assets/authority_models/` | 6 | Source validation industry configs |
| `pipeline_assets/client_template/` | 4 | Blank onboarding templates |
| `.env.example` | 1 | Environment variable reference |
| **Total** | **56 files** | |

That's everything. Once these 56 files are in place and the folder structure is verified, open Cursor and follow `cursor_docs/00_KICKOFF.md`.
