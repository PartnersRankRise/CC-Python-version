# Phase 3, Step 3.5 — Stage Contracts & Prompt Builder
# Created: Thursday Jul 23, 2026, 2:50 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:50 PM (UTC-6)

## Overview

Stage contracts and pipeline configs have been integrated into the project. The `PromptBuilder` class now loads and manages all stage CONTEXT.md files and configuration files, making them available as system prompts for the LLM.

## Files Integrated

### Stage Contracts (9 files)
Located in: `docs/stage_contracts/`

```
stage0_onboarding_CONTEXT.md           (5,368 chars)   - Stage 0: Client onboarding
stage1_1_onboarded_CONTEXT.md          (10,664 chars)  - Stage 1.1: Run initialization (post-onboarding)
stage1_2_Research_CONTEXT.md           (10,648 chars)  - Stage 1.2: Research & dossier generation
stage2_brief_CONTEXT.md                (9,914 chars)   - Stage 2: Content brief creation
stage3_writing_CONTEXT.md              (7,686 chars)   - Stage 3: First draft writing
stage4_humanization_CONTEXT.md         (8,027 chars)   - Stage 4: Humanization & voice alignment
stage5_seo_CONTEXT.md                  (7,681 chars)   - Stage 5: SEO optimization
stage6_qa_CONTEXT.md                   (9,708 chars)   - Stage 6: Quality assurance & approval
stage7_blog-formatting_CONTEXT.md      (10,959 chars)  - Stage 7: Blog HTML formatting
```

### Pipeline Config Files (4 files)
Located in: `docs/pipeline_config/`

```
anti-ai-checklist.md                   (6,739 chars)   - AI detection rules & compliance standards
search-quality-rubric.md               (7,891 chars)   - Research quality evaluation criteria
source-validation-framework.md         (11,932 chars)  - Authority & source validation system
handoff_template.md                    (3,995 chars)   - Stage handoff document template
```

## PromptBuilder Implementation

### File: `content_pipeline/llm/prompt_builder.py`

#### Key Features

1. **Automatic Path Resolution**
   - Stage contracts: `docs/stage_contracts/` (relative to project root)
   - Pipeline configs: `docs/pipeline_config/` (relative to project root)
   - Validates directories exist on initialization

2. **Stage Contract Loading**
   ```python
   contract = await prompt_builder.load_stage_contract("stage_1_2_research")
   ```
   - Maps logical stage names to filenames
   - Supports all 9 stages via predefined `STAGE_CONTRACTS` dictionary
   - Returns full markdown content as string

3. **Config File Loading**
   ```python
   config = await prompt_builder.load_config_file("anti_ai_checklist")
   ```
   - Supports 4 global configs via `GLOBAL_CONFIGS` dictionary
   - Automatically caches configs after first load
   - Reduces I/O for repeated access

4. **System Prompt Building**
   ```python
   system_prompt = await prompt_builder.build_system_prompt(
       "stage_1_2_research",
       include_configs=["anti_ai_checklist", "search_quality_rubric"]
   )
   ```
   - Combines stage contract + selected configs
   - Stage contract always comes first (primary system instructions)
   - Configs follow as supplementary rules
   - If no configs specified, includes all 4 by default

#### State Dictionaries

```python
STAGE_CONTRACTS = {
    "stage_0_onboarding": "stage0_onboarding_CONTEXT.md",
    "stage_1_1_run_init": "stage1_1_onboarded_CONTEXT.md",
    "stage_1_2_research": "stage1_2_Research_CONTEXT.md",
    "stage_2_brief": "stage2_brief_CONTEXT.md",
    "stage_3_writing": "stage3_writing_CONTEXT.md",
    "stage_4_humanization": "stage4_humanization_CONTEXT.md",
    "stage_5_seo": "stage5_seo_CONTEXT.md",
    "stage_6_qa": "stage6_qa_CONTEXT.md",
    "stage_7_blog_formatting": "stage7_blog-formatting_CONTEXT.md",
}

GLOBAL_CONFIGS = {
    "anti_ai_checklist": "anti-ai-checklist.md",
    "search_quality_rubric": "search-quality-rubric.md",
    "source_validation_framework": "source-validation-framework.md",
    "handoff_template": "handoff_template.md",
}
```

## Test Coverage

### File: `content_pipeline/tests/test_prompt_builder.py`

**22 tests, all passing:**

#### Basic Functionality (4 tests)
- Default path initialization
- Custom path initialization
- Missing directory error handling (stage contracts)
- Missing directory error handling (pipeline configs)

#### Stage Contract Loading (6 tests)
- Load all 9 stage contracts
- Load specific stages (onboarding, research, SEO)
- Error handling for invalid stage keys
- Error handling for missing stage files

#### Config File Loading (6 tests)
- Load all 4 config files
- Load specific configs (anti-AI, quality rubric, source validation)
- Config file caching mechanism
- Error handling for invalid config keys

#### System Prompt Building (4 tests)
- Build prompts with default configs (all 4)
- Build prompts with selective configs
- Build prompts for all stages
- Verify stage contract is included in final prompt

#### State Dictionary Validation (2 tests)
- STAGE_CONTRACTS dictionary structure (9 entries)
- GLOBAL_CONFIGS dictionary structure (4 entries)

## Usage Example

```python
from content_pipeline.llm.prompt_builder import PromptBuilder

# Initialize
prompt_builder = PromptBuilder()

# Load a stage contract
research_contract = await prompt_builder.load_stage_contract("stage_1_2_research")

# Load a config
anti_ai_rules = await prompt_builder.load_config_file("anti_ai_checklist")

# Build complete system prompt for Stage 3 (includes all configs)
stage_3_system_prompt = await prompt_builder.build_system_prompt("stage_3_writing")

# Build prompt with selective configs
stage_5_prompt = await prompt_builder.build_system_prompt(
    "stage_5_seo",
    include_configs=["search_quality_rubric", "anti_ai_checklist"]
)
```

## Architecture Notes

### System Prompt Structure

Each stage receives a complete system prompt consisting of:

1. **Stage Contract** (Required)
   - Workflow rules specific to that stage
   - Input/output specifications
   - Quality gates and validation rules
   - Always first in the prompt (primary context)

2. **Global Configs** (Optional)
   - Rules that apply across all stages
   - Examples: AI detection standards, source validation framework
   - Included by default but can be customized per stage

### Caching Strategy

- **Stage Contracts**: No caching (relatively small, stage-specific)
- **Config Files**: Cached after first load (large, static, reused across stages)
- **System Prompts**: Not cached (composition varies by stage/config selection)

### Error Handling

- Invalid stage key: `KeyError` with list of valid keys
- Missing stage file: `FileNotFoundError` with full path
- Missing config file: `FileNotFoundError` with full path
- Directory not found: `ValueError` during initialization

## Integration Points

### For Stage Services

When implementing stage execution, services should:

1. Initialize `PromptBuilder` in `__init__`
2. Call `build_system_prompt(stage_key)` to get the complete system prompt
3. Pass system prompt to LLM as the system message (not user message)
4. User message contains: run data, handoff, and dynamic context

Example:
```python
class ResearchStage(StageContract):
    def __init__(self, llm, ...):
        self.prompt_builder = PromptBuilder()
        self.llm = llm
    
    async def execute(self, run: Run) -> StageOutput:
        # Build system prompt from stage contract + configs
        system_prompt = await self.prompt_builder.build_system_prompt("stage_1_2_research")
        
        # User message contains run data
        user_message = f"Client: {run.client_name}\nTopic: {run.topic}\n..."
        
        # Call LLM with proper separation
        response = await self.llm.call(
            system_prompt=system_prompt,
            user_message=user_message,
            model="claude-sonnet-4-6"
        )
```

## Verification

All stage contracts and config files verified to load correctly:

```
Stage 0 Onboarding:              5,368 bytes ✓
Stage 1.1 Run Init:             10,664 bytes ✓
Stage 1.2 Research:             10,648 bytes ✓
Stage 2 Brief:                   9,914 bytes ✓
Stage 3 Writing:                 7,686 bytes ✓
Stage 4 Humanization:            8,027 bytes ✓
Stage 5 SEO:                      7,681 bytes ✓
Stage 6 QA:                       9,708 bytes ✓
Stage 7 Blog Formatting:         10,959 bytes ✓
Anti-AI Checklist:               6,739 bytes ✓
Search Quality Rubric:           7,891 bytes ✓
Source Validation Framework:    11,932 bytes ✓
Handoff Template:                3,995 bytes ✓

Total: 120,608 bytes across 13 files
Test suite: 22/22 passing
```

## Next Steps

The PromptBuilder is ready to be integrated into:
1. **Stage services** — Use `build_system_prompt()` for LLM calls
2. **API endpoints** — Return system prompts for debugging
3. **UI dashboard** — Display contract contents for transparency
4. **Audit trail** — Log which contracts were used for each run

## Technical Details

- **Language**: Python 3.12+
- **Async**: All methods are async for integration with FastAPI
- **Type Hints**: Full type annotations on all public methods
- **Logging**: Detailed logging at INFO and DEBUG levels
- **Error Handling**: Explicit error types with descriptive messages
