# Source Validation & Remediation Framework

Universal, industry-agnostic system for validating external sources and remedying failed validation through intelligent retry loops and expert authority fallback.

## Overview

This framework validates all external sources listed in Stage 1 Research Dossiers before proceeding to Stage 2. If sources cannot be verified, an automated retry loop attempts to find valid replacements using different search strategies. If all attempts fail, the system activates FALLBACK MODE, which repositions all claims under expert/practitioner authority instead of external sources.

## Core Principles

1. **Automation First**: Minimal human intervention required
2. **Industry-Aware**: Different industries have different source reliability standards
3. **Transparent Fallback**: When external sources fail, content is honestly repositioned, not hidden
4. **Flexible Configuration**: Each industry defines its own validation rules and fallback behavior
5. **Client Customization**: Individual clients can override industry defaults

---

## Validation Architecture

### Stage 1: Initial URL Validation

All source URLs in the Research Dossier are checked immediately after generation:

1. **HTTP HEAD Request**: Each URL receives an HTTP HEAD request with 5-second timeout
2. **Status Code Check**: Returns 200-299 = VALID; otherwise = INVALID
3. **Categorization**: Valid sources marked as APPROVED; invalid sources queued for retry

**Output**: List of verified sources + list of failed sources needing retry

### Stage 2: Retry Loop (If Needed)

For each failed source, attempt to find a valid replacement using different search strategies:

1. **Attempt 1-6**: Each attempt uses a different search strategy (defined in industry config)
2. **Per Attempt**:
   - Call LLM: "Find [STRATEGY] sources about [TOPIC]. Return URLs only."
   - Validate each returned URL
   - If any passes, mark source as rescued and move to next failed source
3. **Exit Retry Loop When**:
   - Found enough valid sources (≥ min_valid_sources_required), OR
   - Exhausted all 6 attempts

**Output**: Final list of valid sources + list of sources still unrescued

### Stage 3: Fallback Decision

After retry loop completes:

1. **Count Valid Sources**: How many sources are now valid?
2. **Compare to Threshold**: min_valid_sources_required (defined in industry config)
3. **Decision**:
   - If valid sources ≥ threshold → **APPROVED** (pass to Stage 2 normally)
   - If valid sources < threshold → **APPROVED_WITH_FALLBACK** (activate remediation)

**Output**: Status + sources + fallback instructions (if needed)

---

## Configuration System

### Industry Configuration

Each industry defines validation behavior in `_config/authority-models/[INDUSTRY].json`:

```json
{
  "industry": "INDUSTRY_KEY",
  "validation": {
    "max_retry_attempts": 6,
    "min_valid_sources_required": NUMBER,
    "retry_strategies": [
      "strategy_1",
      "strategy_2",
      "strategy_3",
      "strategy_4",
      "strategy_5",
      "strategy_6"
    ]
  },
  "fallback_authority": {
    "primary": "AUTHORITY_TYPE",
    "secondary": ["AUTHORITY_TYPE"],
    "allowed_claims": ["claim_type_1", "claim_type_2"],
    "disallowed_claims": ["claim_type_3"]
  },
  "claim_repositioning": {
    "replacements": [
      {"old": "Research shows...", "new": "Our experts observe..."},
      {"old": "Studies indicate...", "new": "In our experience..."}
    ],
    "authority_phrase": "Based on [X] years of professional experience"
  }
}
```

### Client Override Configuration

Individual clients can override industry defaults by creating `Clients/[CLIENT]/authority-config.json`:

```json
{
  "override_industry": "health_wellness_spa",
  "custom_retry_strategies": ["strategy_A", "strategy_B"],
  "custom_authority_phrase": "At Escape Spa, based on 500+ client sessions"
}
```

### Configuration Loading Order

1. Check: `Clients/[CLIENT]/authority-config.json` (client override)
2. Fallback: `_config/authority-models/[INDUSTRY].json` (industry default)
3. Load: Merge client overrides with industry base

---

## Fallback Mode

When external source validation fails (after 6 retry attempts), FALLBACK MODE activates:

### Fallback Activation Criteria

- min_valid_sources_required = 3, actual valid sources = 1 → FALLBACK ACTIVATED
- min_valid_sources_required = 1, actual valid sources = 1 → NO FALLBACK (threshold met)
- min_valid_sources_required = 0 → NO FALLBACK (zero sources required, content uses no external sources)

### Fallback Remediation

1. **Load Authority Rules**: Pull fallback_authority config for the industry
2. **Identify Safe Claims**: Only use claims in allowed_claims list
3. **Reposition Language**: Replace research-backed language with expert-backed language
4. **Generate Instructions**: Create Stage 2 handoff with claim repositioning templates
5. **Pass to Stage 2**: Stage 2 writer must follow remediation rules

### Fallback Authority Types

Different industries use different authority types:

- **PRACTITIONER_EXPERTISE**: "Our therapists observe..." (wellness, massage)
- **ATTORNEY_EXPERTISE**: "In our legal experience..." (law)
- **FIELD_EXPERTISE**: "Based on 20+ years of installations..." (trades, home services)
- **ADVISOR_EXPERTISE**: "As financial advisors..." (finance, investment)
- **DEVELOPER_EXPERTISE**: "Our developers have found..." (software)
- **INDUSTRY_STANDARDS**: "Industry best practices show..." (general)

---

## Integration with Stage 1

### When Validator Runs

After Stage 1 Research generates `[RUN_FOLDER]/01_Research_Dossier.md`:

```
Stage 1 generates dossier
      ↓
Stage 1 executor calls:
  python tools/stage1_source_validator.py --dossier [path] --client [CLIENT]
      ↓
Validator outputs:
  - source_validation_report.json
  - validation_log.txt (optional)
      ↓
Check report.status:
  - APPROVED? Continue to Stage 2
  - APPROVED_WITH_FALLBACK? Add flags to handoff
  - REJECTED? Block Stage 2, return error
```

### Validator Invocation

```bash
python tools/stage1_source_validator.py \
  --dossier "Clients/Escape_Spa/Runs/Vichy_2026-06/01_Research_Dossier.md" \
  --client "Escape_Spa_Fort_Collins" \
  --output "Clients/Escape_Spa/Runs/Vichy_2026-06/source_validation_report.json"
```

### Output Format

```json
{
  "status": "APPROVED_WITH_FALLBACK",
  "dossier_path": "...",
  "client": "Escape_Spa_Fort_Collins",
  "industry": "health_wellness_spa",
  "validation_timestamp": "2026-06-29T13:45:00Z",
  "sources": {
    "total": 5,
    "verified": 2,
    "unverified": 3,
    "details": [
      {
        "source_num": 1,
        "claimed_claim": "Vichy originates from Vichy, France",
        "url": "https://...",
        "status": "VERIFIED",
        "attempts": 0
      },
      {
        "source_num": 2,
        "claimed_claim": "67% improvement in relaxation",
        "url": "https://...",
        "status": "UNVERIFIED_AFTER_6_ATTEMPTS",
        "attempts": 6,
        "fallback_action": "Reposition as expert observation"
      }
    ]
  },
  "fallback_mode": {
    "activated": true,
    "reason": "Only 2 of 5 sources verified; min required: 3",
    "authority_rules": {
      "primary": "PRACTITIONER_EXPERTISE",
      "allowed_claims": ["client_outcomes", "mechanism_of_action", "safety_protocols"],
      "disallowed_claims": ["specific_percentages_without_source", "disease_treatment"]
    },
    "claim_repositioning": {
      "replacements": [...]
    }
  }
}
```

---

## Stage 1 → Stage 2 Handoff

If FALLBACK MODE is activated, new fields are added to the Stage 1→2 handoff file:

```markdown
## Authority_Mode

EXPERT_FALLBACK

## Fallback_Status

Source validation activated fallback mode after 6 retry attempts. 2 of 5 external sources could be verified.

## Allowed_Claims

The following claim types are safe to make under expert authority:
- client_outcomes
- mechanism_of_action  
- safety_protocols

## Disallowed_Claims

The following claim types require external sources and cannot be made:
- specific_percentages_without_source
- disease_treatment_claims
- regulatory_compliance_citations

## Claim_Repositioning_Rules

Replace external-source-backed language with expert-backed language:
- "Research shows..." → "Our therapists observe..."
- "Studies indicate..." → "In our experience..."
- "67% of clients..." → "Most clients we work with..."
```

---

## Error Handling

### Validator Error States

1. **REJECTED_DOSSIER_NOT_FOUND**: Dossier path doesn't exist
2. **REJECTED_NO_SOURCES**: Dossier has no sources section
3. **REJECTED_CONFIG_NOT_FOUND**: Can't find industry or client config
4. **APPROVED**: All sources verified on first pass
5. **APPROVED_WITH_FALLBACK**: Sources failed but fallback activated
6. **REJECTED_MIN_SOURCES_ZERO**: Min sources required is 0, no external sources allowed (special case)

### Timeout & Network Errors

- URL validation timeout (5s) → treated as INVALID
- Network errors → treated as INVALID
- Retry attempts continue on failed sources

---

## Audit & Logging

All validation runs are logged to `[RUN_FOLDER]/source_validation_report.json`:

- Full validation report with all source details
- All retry attempts and strategies tried
- Fallback mode activation reason
- Industry config used (with any client overrides noted)
- Timestamp and duration

---

## Integration Points

### With Stage 1 CONTEXT.md
- Documents that validator is invoked after dossier generation
- Specifies validator command format
- Lists expected output files

### With Stage 2 CONTEXT.md  
- Documents Authority_Mode field interpretation
- Specifies claim repositioning requirements when EXPERT_FALLBACK
- Disallows external citations when fallback is active

### With Handoff Template
- Adds Authority_Mode field
- Adds Fallback_Status field
- Adds Allowed_Claims and Disallowed_Claims lists
- Adds Claim_Repositioning_Rules section

---

## Client Configuration Examples

### Health & Wellness Spa
- Industry: health_wellness_spa
- Min sources: 1 (can proceed with just 1 verified peer-reviewed source)
- Fallback authority: PRACTITIONER_EXPERTISE
- Allowed claims under fallback: client outcomes, mechanism, safety

### Legal Services
- Industry: legal_services
- Min sources: 3 (conservative; needs multiple legal sources)
- Fallback authority: ATTORNEY_EXPERTISE  
- Allowed claims under fallback: legal process, common scenarios, risk assessment

### Home Services (Plumbing)
- Industry: home_services
- Min sources: 0 (expert-led content okay without external sources)
- Fallback authority: FIELD_EXPERTISE
- Allowed claims: installation procedures, troubleshooting, cost factors

---

## Troubleshooting

### Q: Validator is running but not finding any valid sources
**A**: Check that:
1. URLs are correctly formatted (http:// or https://)
2. URLs aren't behind paywalls or authentication
3. Try running URLs manually in browser to verify they work
4. Some sites may block automated HEAD requests; contact site owner or use alternative source

### Q: All sources pass validation but Stage 2 still gets fallback instructions
**A**: This shouldn't happen. Check:
1. Validate that report.json shows "status": "APPROVED"
2. Stage 1 handoff may have been manually edited; regenerate from validator output

### Q: How do I force fallback mode for testing?
**A**: Temporarily set `"min_valid_sources_required": 999` in industry config to force fallback on any dossier.

### Q: Can I see what LLM prompts are being used for retries?
**A**: Yes, check `source_validation_report.json` → sources → [source] → retry_attempts → [attempt] → llm_prompt

---

## Future Enhancements

- Semantic validation (verify that URL content actually discusses the claimed topic)
- Caching of validated URLs (don't re-validate same URL across multiple dossiers)
- Custom retry strategy definitions per client
- A/B testing of different fallback authority framings
- Integration with external fact-checking APIs
