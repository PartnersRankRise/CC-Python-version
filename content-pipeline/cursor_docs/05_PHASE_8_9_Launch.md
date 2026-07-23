# Phase 8 & 9 — Worker Queue, Frontend, and Cutover
**Weeks 17–18 | Gate: 3 complete articles through the full pipeline**

---

# PHASE 8 — Worker Queue and Frontend (Week 17)

## Step 8.1 — ARQ Worker Setup

```
Finalize the ARQ worker setup for background stage execution.

In content_pipeline/workers/stage_worker.py:

async def run_pipeline_stage(ctx, run_id: str, stage_num: int, job_id: str):
    """
    Main worker function called by ARQ.
    Loads the correct stage service, executes it, updates job state.
    """
    orchestrator = PipelineOrchestrator(...)
    try:
        await orchestrator.execute_stage(
            run_id=UUID(run_id),
            stage_num=stage_num,
            job_id=job_id,
        )
    except StageBlockedError as e:
        await update_job_state(job_id, "failed", error=str(e), error_code="STAGE_7_BLOCKED_BY_REVISION")
    except MissingPrerequisiteError as e:
        await update_job_state(job_id, "failed", error=str(e), error_code="MISSING_PREREQUISITE")

class WorkerSettings:
    functions = [run_pipeline_stage]
    redis_settings = RedisSettings.from_dsn(os.environ["REDIS_URL"])
    max_jobs = 10
    job_timeout = 600  # 10 minutes max per stage

Job state tracking — add to Redis (not a DB table to avoid DB polling overhead):
- job:{job_id}:status → "queued|running|complete|failed"
- job:{job_id}:result → JSON string of result data
- job:{job_id}:stream → list of SSE delta chunks for streaming endpoint

GET /jobs/{job_id} reads from Redis:
{
  "status": "complete",
  "stage_number": 1,
  "result": {
    "stage_name": "research",
    "quality_gate_results": {...},
    "completed_at": "..."
  }
}

Create content_pipeline/orchestration/pipeline_orchestrator.py:

Class PipelineOrchestrator with:
- execute_stage(run_id, stage_num, job_id) -> StageOutput
  Routes to the correct stage service; streams tokens to Redis job stream
- check_prerequisite(run, stage_num) -> None
  Validates the required predecessor stage is COMPLETE
- handle_qa_decision(run_id, decision) -> dict
  For APPROVED: returns {"next_stage": 7}
  For REVISION_REQUIRED: computes revision_stage from qa_result; updates run.current_stage

STAGE_SEQUENCE = [0, 10, 1, 15, 2, 3, 4, 5, 6, 7]
# 10 = Pre-Stage 1, 15 = Stage 1.5

Confirm ARQ worker starts with: arq content_pipeline.workers.stage_worker.WorkerSettings
```

---

## Step 8.2 — Complete Frontend Build

```
Build the full Next.js frontend. At a minimum, these pages must work end-to-end:

1. /dashboard — client list with run counts and last run status
2. /clients/new — create client form
3. /clients/[clientId] — client overview with stage progress for most recent run
4. /clients/[clientId]/onboard — onboarding form with progress polling
5. /clients/[clientId]/runs/new — Path A / Path B toggle; topic confirmation
6. /clients/[clientId]/runs/[runId] — run overview with stage pipeline tracker
7. /clients/[clientId]/runs/[runId]/[stage] — stage output view

For the stage output view, implement a shared layout with:
- Left panel: stage output (markdown rendered, or HTML preview for Stage 7)
- Right panel: stage-specific details
  - Stage 4: editorial_note panel with 5 sub-sections highlighted
  - Stage 5: SEO annotation panel (word count status chip, qa_flags checklist)
  - Stage 6: QA signoff (section A-I scores, issue list with type badges)

Stage-specific right panels:

Stage 4 Editorial Note Panel:
  Show 5 sections as labeled cards: Structural changes, Rhythm, Experience additions, E-E-A-T, QA concern
  Highlight QA concern in amber — this is the one the human editor should review

Stage 5 SEO Annotation Panel:
  Word count: status chip (green=within_target, red=over_target, yellow=under_target)
  Meta title: text + char count + PASS/REVISED badge
  Meta description: text + char count + PASS/REVISED badge
  Internal links: table with anchor, destination, confirmed status
  QA Flags: checklist (these carry into Stage 6 review)

Stage 6 QA Signoff Panel:
  Section A-I: each row shows PASS/FLAG/FAIL badge
  Issues list: three visual styles
    pipeline_failure → red badge, shows "Route to Stage N"
    client_decision → amber badge, shows "Client confirmation needed"
    minor_observation → gray badge, "FYI"
  AI Detection Risk: score gauge (5/15 = green; >10 = red)
  Decision button: "Approve" or "Request Revision"

Stage 7 Preview:
  iframe of the HTML output with viewport switcher (375, 768, 1280)
  "Download HTML" button
  "Download Markdown" button

Unresolved Items Drawer:
  Accessible from all stage views via a persistent icon button
  Shows all UnresolvedItems for the run with source stage, description, blocking status
  "Mark Resolved" button per item
  Items with blocks_run=True shown in red

Build these pages now. Use Tailwind for all application UI.
Do NOT use Tailwind for blog HTML output — that uses blog_integration_base.css.
```

---

## Step 8.3 — QA Decision Flow

```
Implement the QA decision flow end-to-end.

When the user clicks "Approve" in the Stage 6 UI:
  POST /runs/{run_id}/qa/decision with {"decision": "approved"}
  Backend calls orchestrator.handle_qa_decision()
  Run status updates to "approved"
  Stage 7 handoff is written
  Frontend redirects to Stage 7 view

When the user clicks "Request Revision":
  POST /runs/{run_id}/qa/decision with {"decision": "revision_required"}
  Backend computes revision_stage from qa_result
  Run current_stage resets to revision_stage
  Frontend shows: "QA returned this run to Stage N — [reason]"
  The relevant stage view becomes active again

When Stage 6 has a Human Review Flag (word count over target):
  Show a banner: "This article passed QA but word count ({N} words) exceeds the
  {min}-{max} target. Review length before publishing."
  Allow approval anyway — word count over target is not blocking.

Also implement: POST /runs/{run_id}/issues/{issue_id}/resolve
  Mark an UnresolvedItem as resolved; update the drawer
```

---

# PHASE 9 — Validation and Cutover (Week 18)

## Step 9.1 — End-to-End Validation Run

```
Run three complete articles through the pipeline from Stage 0 through Stage 7.

For each run, compare outputs to the reference run using this checklist:

STRUCTURE CHECKS (automated — write a validation script):

def validate_run_outputs(run_id):
    checks = []
    
    # Stage 1: Dossier has 8 sections
    dossier = get_stage_output(run_id, 1).article_content
    for section in ["TOPIC AND SEMANTIC FIELD", "SOURCE BANK", "NON-OBVIOUS INSIGHT",
                    "YMYL ASSESSMENT", "CONTENT GAP ANALYSIS", "RECOMMENDED E-E-A-T",
                    "SEARCH INTENT", "AUDIENCE VALUE STATEMENT"]:
        checks.append(("dossier_section:" + section, section in dossier))
    
    # Stage 3: Zero em dashes, zero BRIEF tokens
    draft = get_stage_output(run_id, 3).article_content
    checks.append(("no_em_dashes", "—" not in draft and "\u2014" not in draft))
    checks.append(("no_brief_tokens", "<!--BRIEF:" not in draft))
    
    # Stage 4: Editorial note is separate
    stage4 = get_stage_output(run_id, 4)
    checks.append(("editorial_note_separate", stage4.editorial_note is not None))
    checks.append(("editorial_note_not_in_content", "## Editorial Note" not in stage4.article_content))
    
    # Stage 5: Word count is structured JSONB
    stage5 = get_stage_output(run_id, 5)
    wc = stage5.seo_annotation.get("word_count", {})
    checks.append(("word_count_is_dict", isinstance(wc, dict)))
    checks.append(("word_count_has_count", "count" in wc))
    checks.append(("annotation_not_in_content", "## SEO Annotation Sheet" not in stage5.article_content))
    
    # Stage 6: QA approved draft is clean
    stage6 = get_stage_output(run_id, 6)
    approved = stage6.article_content
    for forbidden in ["<!--BRIEF:", "BEGIN_BLOG_REQUEST", "## Editorial Note", "## SEO Annotation Sheet"]:
        checks.append((f"no_{forbidden[:10]}", forbidden not in approved))
    
    # Stage 7: HTML is clean
    stage7 = get_stage_output(run_id, 7)
    html = stage7.article_content
    for forbidden in ["<!--BRIEF:", "BEGIN_BLOG_REQUEST", "## Editorial Note", "## SEO Annotation Sheet"]:
        checks.append((f"html_no_{forbidden[:10]}", forbidden not in html))
    
    # CSS tokens resolved (no {{...}} remaining)
    checks.append(("css_tokens_resolved", "{{" not in html))
    
    # RGB values have no # prefix
    import re
    rgb_values = re.findall(r'--primary-rgb:\s*([^;]+)', html)
    if rgb_values:
        checks.append(("primary_rgb_no_hash", not rgb_values[0].strip().startswith("#")))
    
    return checks

Run this validation against all three test articles.
All checks must pass for all three articles.
Show me the full output.
```

---

## Step 9.2 — Side-by-Side Comparison with Reference Run

```
Compare our Stage 1 dossier output against reference_run/01_Research_Dossier.md.

I want to see:
1. Do both have exactly 8 formal sections? List the section headings from each.
2. Does our dossier have a supplemental notes section (RESEARCH NOTES equivalent)?
3. Are both dossiers similar in depth for the same topic? (rough word count comparison)

Compare our Stage 6 QA output against reference_run/06_QA_Signoff.md:
1. Same approval status (APPROVED)?
2. Checklist score — how does ours compare to 38/39?
3. AI Detection Risk Score — how does ours compare to 5/15?
4. If we have more failures, which sections failed and why?

Compare our Stage 7 HTML output against reference_run/07_Blog_Final.html:
1. Does our output have the same top-level structure?
   (blog-wrap, card-wrap, header, prose sections, cta-card)
2. Are internal links preserved with correct anchor text and href?
3. Are all 11 CSS tokens correctly resolved?

Document any differences. For each difference, decide: intentional improvement, acceptable
deviation, or a bug that needs fixing.
```

---

## Step 9.3 — Cutover Checklist

```
Before retiring the old folder-based system for any client, confirm all items on this list:

TECHNICAL
- [ ] All 9 build phases complete and gate checks passed
- [ ] Full test suite passes (show me final count)
- [ ] Three end-to-end validation runs all 100% on structure checks
- [ ] Stage 7 HTML passes manual browser check at 375px, 768px, 1280px
- [ ] No reference to old Python scripts anywhere in codebase (grep for stage1_source_validator, word_count.py, merge_manual_html)
- [ ] All 11 CSS tokens resolving correctly for at least two different clients
- [ ] ARQ worker restarts gracefully on failure without losing job state

DATA
- [ ] All five authority_models rows seeded correctly
- [ ] CSS template seeded in css_templates table
- [ ] Reference run client (Rankrise_Marketing) onboarded in the application
- [ ] Reference run published article exists in published_articles table

OPERATIONAL
- [ ] .env.example documents all required environment variables
- [ ] Supabase RLS policies in place (users see only their own clients)
- [ ] Error boundaries in Next.js frontend (stage failures don't crash the UI)
- [ ] Human review flag displays correctly when word count exceeds target

Run this grep to confirm no old script references:
grep -r "stage1_source_validator\|word_count\.py\|merge_manual_html" content_pipeline/ frontend/

It should return zero results.
```

---

## Recurring Check-In Prompt

Use this at the start of any new Cursor session during the build to reorient the AI:

```
We are building the content pipeline application. Read .cursorrules to refresh context.

Current phase: [PHASE NUMBER AND NAME]
Last completed step: [STEP NUMBER]
Last gate check result: [PASS/FAIL and any notes]

Current task: [DESCRIBE WHAT YOU ARE ABOUT TO DO]

Before writing any code:
1. Confirm which file(s) you will create or modify
2. Confirm which section of BUILD_GUIDE.md or REFERENCE.md covers this task
3. Confirm whether any reference run file in reference_run/ should be used to validate the output

Then proceed.
```

---

## If Something Goes Wrong

### The LLM is producing output that doesn't match the spec
Check `.cursorrules` — confirm the AI has read it in this session. Paste the relevant section of `BUILD_GUIDE.md` directly into the chat. The spec is the authority; the AI's intuition is not.

### A parser test is failing
Open the actual reference run file and read it manually. The parsers must match the real file format — if the test is failing, either the parser logic is wrong or the test expectation is wrong. Read the file; decide which.

### Stage output has token leakage
Token leakage means `<!--BRIEF:`, `## Editorial Note`, or `## SEO Annotation Sheet` appeared in a downstream stage output. Check:
1. Was `BriefParser.strip_brief_tokens()` called in Stage 3's `_load_context`?
2. Was `EditorialNoteParser.split()` called in Stage 4's `_parse_output`?
3. Was `SEOAnnotationParser.split()` called in Stage 5's `_parse_output`?
The split/strip must happen at the receiving stage, not at the sending stage.

### Stage 7 CSS tokens not resolving
Check `brand_colors` JSONB in `client_reference_files`. All 11 keys must be present. Check that `PRIMARY_RGB` does not start with `#`. If brand colors are missing, Stage 0 onboarding needs to re-extract them.

### QA is routing to wrong revision stage
Check `qa_service.py classify_issue()`. The Section F issue in the reference run contains the text "client/publisher decision" — that maps to `CLIENT_DECISION`. If it's being mapped to `PIPELINE_FAILURE`, the text matching is too loose.
