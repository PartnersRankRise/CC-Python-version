# Phase 4, Step 4.2 — Run Init Service (Pre-Stage 1)
# UPDATED DESIGN - USER APPROVED MODIFICATIONS
# Created: Thursday Jul 23, 2026, 3:11 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:18 PM (UTC-6)

## Your Approved Changes

1. ✓ `_build_prompt` structure: APPROVED as designed
2. ✓ JSON response format: APPROVED (JSON array from LLM)
3. ✓ **UPDATED:** Overlap check now includes title similarity (not just keywords)
4. ✓ **UPDATED:** Brand Notes open questions: Alert user, let them answer or skip (don't auto-create UnresolvedItems)
5. ✓ **CLARIFIED:** Handoff structure for transition to Stage 1 (Research)

---

## #5 — How Pre-Stage 1 Transitions to Stage 1 (gpt-researcher)

### Stage 1 Workflow (High Level)

Stage 1 (Research) has **two sub-steps**:

**Sub-step A:** gpt-researcher gathers raw research context
```python
researcher = GPTResearcher(
    query=self._build_research_query(run, context),
    report_type="research_report",
)
await researcher.conduct_research()

raw_research = {
    "research_context": researcher.get_research_context(),
    "sources": researcher.get_source_urls(),
    "sub_queries": researcher.research_sub_queries,
    "costs": researcher.get_costs(),
}
```

**Sub-step B:** Pipeline LLM produces 8-section Research Dossier
- System prompt: Stage 1 CONTEXT.md contract (from PromptBuilder)
- User prompt: Injects `research_context`, `sources`, `sub_queries` from gpt-researcher
- LLM adds 6 strategic sections gpt-researcher can't produce:
  - Non-Obvious Insight
  - YMYL Assessment
  - Content Gap Analysis
  - E-E-A-T Framing
  - Search Intent Classification
  - Audience Value Statement

### The `_build_research_query` Input

The research query is built from Pre-Stage 1 handoff carry-forward data:

```python
def _build_research_query(run: Run, context: str) -> str:
    """
    Input from Pre-Stage 1 handoff:
    - Topic: "How to Fix a Leaking Furnace"
    - Primary keyword: "leaking furnace repair"
    - Audience intent: "Homeowner wants to diagnose/fix"
    - Angle notes (sanitized): Any strategic direction from Pre-Stage 1
    
    Output query for gpt-researcher:
    "Find authoritative sources on furnace leak diagnosis and repair for
    homeowners. Focus on cost comparison, DIY vs professional help,
    seasonal patterns. Look for HVAC industry insights and common causes."
    """
```

### The Complete Handoff from Pre-Stage 1 to Stage 1

Pre-Stage 1 creates: `00_Stage_1_Handoff_Brief.md`

```markdown
# Stage 1 Handoff Brief

Status: READY
Created by: Pre-Stage 1 - Run Initialization
Created: 2026-07-23 14:30
Run: How_To_Fix_Leaking_Furnace_2026-07
Client: Example HVAC Services

## Next Stage

- Stage: 1 - Research
- Run path: Clients/Example_HVAC_Services/Runs/How_To_Fix_Leaking_Furnace_2026-07/
- Expected output: 01_Research_Dossier.md

## Load Instructions

**Mandatory first load:** Stage 1 CONTEXT.md contract
- _config/stage_contracts/stage1_2_Research_CONTEXT.md (load in full)

Load in full:
- Clients/Example_HVAC_Services/Reference/Style_Reference_Card.md
- Clients/Example_HVAC_Services/Reference/Audience_Profile.md
- Clients/Example_HVAC_Services/Reference/Brand_Notes.md

Do not load:
- 00_Stage_1_Handoff_Brief.md (this file — for metadata only)

## Carry Forward Context

- Topic: "How to Fix a Leaking Furnace (Without Calling an HVAC Tech First)"
- Primary keyword: "leaking furnace repair"
- Angle/notes: "DIY diagnostic first, professional service as fallback; seasonal angle for fall maintenance"
- Priority sources: None (open research)
- Internal links: None (new run)
- Unresolved items: None (fully confirmed at run init)
- Issues flagged: None

## Authority Mode (Source Validation)

Authority_Mode: VERIFIED_EXTERNAL
(Source validation will run at Stage 1.5 after dossier generation)

## Quality Gates For Next Stage

- ≥3 sources with specific data points and publication dates
- Non-Obvious Insight is evidence-backed, not speculative
- Audience Value Statement is convincingly specific
- Zero internal tokens in output

## Automation

- Auto-run next stage: false
- Reason: Sequential human-supervised mode (user reviews handoff before Stage 1 starts)
```

### Data Flow: Pre-Stage 1 → Stage 1

```
PRE-STAGE 1 (Run Init)
├─ Confirmed topic: "How to Fix a Leaking Furnace..."
├─ Primary keyword: "leaking furnace repair"
├─ Audience intent: "Homeowner wants DIY solution first"
└─ CREATES: 00_Stage_1_Handoff_Brief.md

        ↓ (User reviews, confirms to proceed)

STAGE 1 (Research)
├─ READS: 00_Stage_1_Handoff_Brief.md (extracts topic, keyword, intent)
├─ READS: Reference files (Style Card, Audience Profile, Brand Notes)
├─ BUILDS research_query from topic + keyword + intent
├─ CALLS gpt-researcher.conduct_research(query)
├─ RECEIVES: research_context, sources, sub_queries, costs
├─ BUILDS LLM prompt with context + sources
├─ LLM GENERATES: 8-section Research Dossier + 6 strategic insights
└─ CREATES: 01_Research_Dossier.md + 01_Stage_2_Handoff.md

        ↓ (User reviews dossier quality)

STAGE 1.5 (Source Validation)
├─ READS: Research Dossier sources
├─ VALIDATES: Against authority model (home_services = 0 sources required)
└─ SHORT-CIRCUITS: APPROVED (no sources needed for field expertise)

        ↓

STAGE 2 (Content Brief)
├─ READS: Research Dossier
├─ CREATES: Content Brief outline with claims + structure
└─ CREATES: 02_Content_Brief.md + 02_Stage_3_Handoff.md
```

---

## Updated Design: UnresolvedItems from Brand Notes

### Previous Design (REJECTED)
- Auto-create UnresolvedItem for every open question in Brand Notes

### New Design (APPROVED)
- Alert user about open questions in Brand Notes
- User can:
  1. Answer them immediately (fill in the placeholder)
  2. Skip them (will be revisited at Stage 3 pre-flight before writing starts)
  3. Confirm they don't apply to this topic

### Implementation

```python
async def flag_brand_notes_open_questions(brand_notes: str) -> list[str]:
    """Extract [CONFIRM WITH CLIENT] placeholders from Brand Notes.
    
    Returns: List of unresolved items text
    """
    import re
    open_items = re.findall(r'\[CONFIRM WITH CLIENT\].*?(?=\n|$)', brand_notes)
    return open_items

async def create_run_from_topic(self, client_id, topic, keyword, ...):
    # ... (overlap check, folder creation) ...
    
    # Flag any open questions in Brand Notes
    open_questions = await self.flag_brand_notes_open_questions(brand_notes)
    
    if open_questions:
        # Alert user and request confirmation
        user_response = await self.prompt_user(
            f"Found {len(open_questions)} open questions in Brand Notes:\n"
            + "\n".join([f"- {q}" for q in open_questions])
            + "\n\nProceed without resolving, or would you like to update them?",
            options=["Proceed", "Update Now", "Cancel"]
        )
        
        if user_response == "Update Now":
            # User updates Brand Notes before run proceeds
            # We don't auto-create UnresolvedItems
            pass
        elif user_response == "Proceed":
            # Continue without creating UnresolvedItems
            # Stage 3 pre-flight will flag these again
            pass
        else:
            return None  # Cancel run creation
    
    # Create run (NO automatic UnresolvedItem creation from open questions)
    run = await self.repo.create_run(...)
    
    return run
```

---

## Updated Design: Overlap Check with Title Similarity

### Previous Design
- Check keyword ILIKE match only

### New Design (APPROVED)
- Check keyword ILIKE
- Check title similarity (semantic or string matching)

### Implementation

```python
async def check_overlap(self, client_id: UUID, topic: str, keyword: str) -> Optional[OverlapConflict]:
    """Check published articles for keyword and title overlap.
    
    Args:
        client_id: Client UUID
        topic: Proposed topic
        keyword: Proposed primary keyword
    
    Returns:
        None if no conflict, or OverlapConflict with details
    """
    published = await self.repo.get_published_articles(client_id)
    
    for article in published:
        # Check 1: Exact keyword match
        if keyword.lower() in article.primary_keyword.lower() \
           or article.primary_keyword.lower() in keyword.lower():
            return OverlapConflict(
                existing_slug=article.slug,
                conflict_type="keyword_overlap",
                existing_keyword=article.primary_keyword,
                suggestion="This keyword is already covered. Choose a differentangle or keyword."
            )
        
        # Check 2: Title/topic similarity
        if self._topics_are_similar(topic, article.title):
            return OverlapConflict(
                existing_slug=article.slug,
                conflict_type="title_similarity",
                existing_title=article.title,
                suggestion="Very similar topic already published. Differentiate the angle or scope."
            )
    
    return None

def _topics_are_similar(self, topic1: str, topic2: str) -> bool:
    """Check if two topics are semantically similar.
    
    Simple approach: Compare first 3 words + check for keyword overlap
    """
    words1 = set(topic1.lower().split()[:3])
    words2 = set(topic2.lower().split()[:3])
    
    # If 2+ words overlap in first 3 words, topics are similar
    overlap = len(words1 & words2)
    return overlap >= 2
```

---

## Summary of Changes

| Requirement | Original | Updated | Status |
|---|---|---|---|
| Overlap check | Keywords only | Keywords + title similarity | ✓ UPDATED |
| Brand Notes open questions | Auto-create UnresolvedItems | User alert + choice to answer/skip | ✓ UPDATED |
| Handoff structure | (Not specified) | Full handoff per template + carry-forward context | ✓ CLARIFIED |
| Transition to Stage 1 | (Not specified) | Query from handoff → gpt-researcher → LLM dossier | ✓ CLARIFIED |
| `_build_prompt` | (Proposed) | APPROVED as designed | ✓ APPROVED |
| JSON response | (Proposed) | APPROVED as designed | ✓ APPROVED |

---

## Ready to Implement

Now that you've approved these changes, I'm ready to implement:

1. **RunInitService** class with:
   - `generate_topic_recommendations()` (Path B ideation)
   - `check_overlap()` (with title similarity)
   - `create_run_from_topic()` (with user alert for open questions)
   - `_build_prompt()` for ideation

2. **RunRepository** methods:
   - `create_run()`, `get_run()`
   - `save_unresolved_item()`, `get_unresolved_items()`
   - `get_published_articles()`, `get_published_slugs()`

3. **API Endpoints**:
   - `POST /clients/{id}/runs` (Path A: user topic)
   - `POST /clients/{id}/runs/{run_id}/topic-recommendations` (Path B ideation)
   - `POST /clients/{id}/runs/{run_id}/confirm-topic` (overlap check + create run)

4. **Tests**: 25+ integration tests

Ready to proceed?
