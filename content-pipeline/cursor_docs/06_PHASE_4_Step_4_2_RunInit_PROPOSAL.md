# Phase 4, Step 4.2 — Run Init Service (Pre-Stage 1)
# DESIGN PROPOSAL FOR USER REVIEW
# Created: Thursday Jul 23, 2026, 3:11 PM (UTC-6)

## RunInitService Design

### Overview

`RunInitService` implements Pre-Stage 1 (Run Initialization), which handles two paths for starting a new run:
- **Path A:** User provides topic + keyword → overlap check → confirm → create run
- **Path B:** No topic → ideation (generate 4-6 recommendations) → user selects → overlap check → create run

### Key Behaviors

1. **Overlap Check:** Queries `published_articles` for existing content with same keyword/slug
2. **Topic Recommendations:** LLM generates 4-6 recommendations using Content Gap Analysis
3. **Run Folder Slug:** `Title_Case_Topic_YYYY-MM` format
4. **Unresolved Items:** Extract from Brand Notes and create UnresolvedItem records
5. **Handoff Brief:** Create 00_Stage_1_Handoff_Brief.md with carry-forward context

### Class Structure

```python
class RunInitService(StageContract):
    def __init__(
        self,
        repo: RunRepository,
        client_repo: ClientRepository,
        llm: LLMProvider,
        prompt_builder: PromptBuilder,
        context_assembler: ClientContextAssembler,
    ):
        self.repo = repo
        self.client_repo = client_repo
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.context_assembler = context_assembler
    
    # From StageContract
    async def validate_prerequisites(run: Run) -> bool
    async def execute(run: Run) -> StageOutput
    async def parse_output(raw: str) -> StageOutput
    
    # Pre-Stage 1 specific
    async def generate_topic_recommendations(
        self,
        client_id: UUID,
        count: int = 5
    ) -> list[TopicRecommendation]
        """Generate ideation recommendations using Content Gap Analysis"""
    
    async def check_overlap(
        self,
        client_id: UUID,
        topic: str,
        keyword: str
    ) -> Optional[OverlapConflict]
        """Check for existing published content with same keyword/slug"""
    
    async def create_run_from_topic(
        self,
        client_id: UUID,
        topic: str,
        keyword: str,
        recommendation_n: Optional[int] = None
    ) -> Run
        """Create run folder and handoff brief after user confirms topic"""
```

### The _build_prompt Method (FOR REVIEW)

This is the core logic that generates the LLM prompt for topic recommendations:

```python
def _build_prompt(
    self,
    client_name: str,
    audience_profile: str,
    style_card: str,
    brand_notes: str,
    published_slugs: list[str],
    count: int = 5,
) -> str:
    """Build LLM prompt for topic ideation using Content Gap Analysis.
    
    The prompt structure:
    1. System prompt: Pre-Stage 1 contract from PromptBuilder
    2. User message: Client context + reference files + published inventory + task
    
    The LLM is instructed to:
    - Analyze audience pain points from Audience Profile
    - Scan published content inventory to identify gaps
    - Generate 4-6 topic recommendations that:
      * Fill identified content gaps
      * Align with audience needs
      * Respect style guide and brand guidelines
      * Have distinct keywords (no overlap)
    - Return structured JSON with each recommendation
    
    Each recommendation includes:
    - topic: Human-readable topic
    - primary_keyword: SEO keyword
    - why_now: Why this topic is timely/relevant
    - audience_intent: What problem this solves
    - eeat_angle: How to frame for E-E-A-T (if YMYL)
    """
    
    # Published inventory for gap analysis
    inventory = "\n".join([f"- {slug}" for slug in published_slugs]) if published_slugs else "- (No articles published yet)"
    
    prompt = f"""
You are the ideation assistant for {client_name}.

## CLIENT CONTEXT

**Audience Profile:**
{audience_profile}

**Style Reference Card:**
{style_card}

**Brand Notes:**
{brand_notes}

## PUBLISHED CONTENT INVENTORY

{inventory}

## TASK

Generate {count} topic recommendations using Content Gap Analysis:

1. Identify pain points and interests from the Audience Profile
2. Scan the Published Content Inventory for gaps
3. Recommend topics that:
   - Fill identified gaps
   - Serve audience needs
   - Are distinct from existing content (no keyword overlap)
   - Align with brand voice and style guidelines
   - Have high search intent and commercial value

## RESPONSE FORMAT

Return a JSON array with this structure (no markdown, raw JSON only):

[
  {{
    "topic": "How to Fix a Leaking Furnace (Without Calling an HVAC Tech First)",
    "primary_keyword": "leaking furnace repair",
    "why_now": "Seasonal heating problems spike in fall; users search for DIY solutions before spending $300+ on service calls",
    "audience_intent": "Homeowner wants to diagnose/fix furnace leak, or understand if they need professional help",
    "eeat_angle": "Frame as experienced HVAC tech sharing troubleshooting wisdom, not replacement for professional service when needed"
  }},
  ...
]

Important:
- Each recommendation must have a unique primary_keyword
- No topic should duplicate any slug in the Published Content Inventory
- Focus on keywords with search volume but manageable competition
- Consider seasonal relevance and content freshness
- Return exactly {count} recommendations
"""
    
    return prompt
```

### Response Format

The LLM returns a JSON array of topic recommendations:

```json
[
  {
    "topic": "How to Fix a Leaking Furnace",
    "primary_keyword": "leaking furnace repair",
    "why_now": "Seasonal heating problems spike in fall",
    "audience_intent": "Homeowner wants to diagnose or fix furnace leak",
    "eeat_angle": "Frame as experienced HVAC tech sharing troubleshooting wisdom"
  },
  ...
]
```

Each is parsed into a `TopicRecommendation` domain model.

### Overlap Check Logic

```python
async def check_overlap(
    self,
    client_id: UUID,
    topic: str,
    keyword: str
) -> Optional[OverlapConflict]:
    """Query published_articles for potential conflicts.
    
    Checks:
    1. Exact keyword match (ILIKE)
    2. Slug similarity (partial match)
    
    Returns:
    - None if no overlap
    - OverlapConflict with existing article details if found
    """
    published = await self.repo.get_published_slugs(client_id)
    
    # Check keyword
    for slug in published:
        if keyword.lower() in slug.lower() or slug.lower() in keyword.lower():
            return OverlapConflict(
                existing_slug=slug,
                conflict_type="keyword_overlap",
                suggestion="Choose a different angle or keyword"
            )
    
    return None
```

### Run Folder Slug Generation

```python
def _generate_folder_slug(topic: str) -> str:
    """
    "Content Marketing for Home Service Businesses"
    → "Content_Marketing_Home_Services_2026-07"
    """
    import re
    from datetime import datetime
    
    # Lowercase, strip non-alphanumeric
    slug = re.sub(r'[^a-z0-9\s]', '', topic.lower())
    
    # Title case each word
    words = slug.split()
    slug = "_".join(word.capitalize() for word in words)
    
    # Append YYYY-MM
    today = datetime.now()
    month_year = today.strftime("%Y-%m")
    
    return f"{slug}_{month_year}"
```

### Handoff Brief Structure

Creates `00_Stage_1_Handoff_Brief.md` with:
- Confirmed topic + keyword
- Client context (from ClientContextAssembler)
- Reference files summary (sections present)
- Open questions from Brand Notes (as UnresolvedItems)
- Auto-run: false (sequential, human-supervised)
- Next stage: Stage 1 - Research

---

## Question for User

Before implementing, please review this design:

1. **_build_prompt structure:** Does the prompt correctly use Content Gap Analysis approach?
2. **Response parsing:** Is the JSON structure clear enough for reliable parsing?
3. **Overlap check:** Should we also check title similarity, or just keywords?
4. **Unresolved items:** Should all Brand Notes open questions become UnresolvedItems?
5. **Handoff format:** Align with handoff_template.md?

Once approved, I'll implement:
- RunInitService class (execute, validate_prerequisites, generate_recommendations, check_overlap)
- RunRepository methods (create_run, get_run, save_unresolved_item, etc.)
- API endpoints (POST /runs, POST /runs/{id}/topic-recommendations, POST /runs/{id}/confirm-topic)
- Comprehensive test suite
