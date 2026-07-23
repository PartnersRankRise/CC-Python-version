# Project Kickoff Prompt

**How to use this file:** You have already set up the project folder by following `NEW_PROJECT_SETUP.md` and verifying the file counts. Now paste the prompt below into Cursor's chat. Do this before writing a single line of code.

---

## Paste This into Cursor Chat

```
I am building a blog production pipeline application. Before we write any code, I need you to read and understand the project documentation.

Please read these files in this order:
1. .cursorrules — the persistent rules for this project
2. docs/BUILD_GUIDE.md — what to build and in what order
3. docs/REFERENCE.md — schema, models, API contracts

Then confirm you understand the following by answering each question:

1. What are the three Python scripts from the old system that must NEVER be replicated or referenced?

2. Why does the parsing layer get built before any stage service?

3. What is the difference between stage_outputs.article_content and stage_outputs.editorial_note? Which stages produce each, and what happens if they get mixed?

4. What does min_valid_sources_required = 0 mean in home_services.json, and what should the SourceValidationService do when it sees this?

5. What format must PRIMARY_RGB be stored in, and why does it matter?

6. What are the three QAIssueType values, and which one should NOT trigger a revision stage re-run?

7. We have a reference run in reference_run/. Name three specific things from those files that we should use to validate our parser output.

8. What are the four supported LLM providers, and which environment variable controls which one is used for pipeline stages?

After you answer these questions correctly, we will begin Phase 1.
```

---

## What to Do With the Answers

The AI should answer all eight correctly before you proceed. If any answer is wrong or vague, do not move forward — correct it using the relevant section of `docs/BUILD_GUIDE.md` or `docs/REFERENCE.md` and re-ask.

**Correct answers to check against:**

1. `stage1_source_validator.py`, `word_count.py`, `merge_manual_html.py`

2. Because every stage service depends on parsers to correctly separate article content from appended sections (editorial notes, annotation sheets). A stage service built without parsers will mix these together and break every downstream stage.

3. `article_content` is the reader-facing article body only. `editorial_note` is the Stage 4 appended section, stored in a separate column and never passed to Stage 5. If mixed, the editorial note leaks into the SEO draft, the QA approved draft, and ultimately the published HTML — a token leakage violation.

4. It means immediately return `APPROVED` without running any validation or retry loop. Home services content is field-expertise-led and does not require external source verification.

5. `"r, g, b"` — a comma-separated triplet with no `#` prefix. It is used inside `rgba(var(--primary-rgb), 0.04)` CSS calls in `blog_integration_base.css`. A `#` prefix breaks the rgba() function and corrupts the HTML output.

6. `pipeline_failure`, `client_decision`, `minor_observation`. `client_decision` should NOT trigger a revision stage — it requires human action outside the pipeline.

7. Any three of: `BriefParser` should preserve the content types table after stripping BRIEF tokens (confirmed in `reference_run/02_Content_Brief.md`); `SEOAnnotationParser` should produce `{count: 2776, target_min: 2200, target_max: 2800, status: "within_target"}` from `reference_run/05_SEO_Draft.md`; `QASignoffParser` should produce 38/39 PASS, AI Risk 5/15, Section F as FLAG with `client_decision` type from `reference_run/06_QA_Signoff.md`; `EditorialNoteParser` should split `reference_run/04_Humanized_Draft.md` into article body + editorial note with 5 sub-sections.

8. Anthropic, OpenRouter, Ollama, and LM Studio. The `LLM_PROVIDER` environment variable controls which one is active for pipeline stages 0–7. This is independent of gpt-researcher's provider, which is controlled by the `SMART_LLM`, `FAST_LLM`, and `STRATEGIC_LLM` env vars.

---

## Before You Start — Verified Folder Structure

Your project folder should already look like this (confirmed by the setup verification step):

```
content-pipeline/
├── .cursorrules                         ← loads automatically in every Cursor session
├── .env.example                         ← copy to .env and fill in your keys
│
├── docs/
│   ├── BUILD_GUIDE.md                   ← primary implementation spec
│   ├── REFERENCE.md                     ← schema, models, API contracts
│   ├── stage_contracts/                 ← 9 LLM system prompts (one per stage)
│   ├── pipeline_config/                 ← 4 runtime rule files
│   └── architecture/                    ← 5 background reference docs
│
├── cursor_docs/                         ← you are here
│   ├── 00_KICKOFF.md                    ← this file
│   ├── 01_PHASE_1_Foundation.md
│   ├── 02_PHASE_2_Parsing.md
│   ├── 03_PHASE_3_4_Onboarding_RunInit.md
│   ├── 04_PHASE_5_7_Stages.md
│   ├── 05_PHASE_8_9_Launch.md
│   ├── QUICK_REFERENCE.md               ← keep this open while building
│   └── NEW_PROJECT_SETUP.md             ← setup reference (already done)
│
├── reference_run/                       ← 16 ground-truth files for parser validation
│
└── pipeline_assets/
    ├── css/                             ← blog_integration_base.css (seeded to DB)
    ├── authority_models/                ← 6 industry JSON configs (seeded to DB)
    └── client_template/                 ← 4 blank onboarding template files
```

If anything is missing, refer to `cursor_docs/NEW_PROJECT_SETUP.md` for the complete setup checklist.

---

## After the Kickoff — What's Next

Once the AI has answered all eight questions correctly:

1. Open `cursor_docs/01_PHASE_1_Foundation.md`
2. Work through the steps in order — each step is a prompt to paste into Cursor chat
3. Do not move to the next phase until the gate check at the end of each phase passes
4. Keep `cursor_docs/QUICK_REFERENCE.md` open in a separate tab while building

Human checkpoints are marked in **bold** throughout the phase files. At those points, read the output yourself before telling the AI to continue.
