# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Provider configuration — quality gate tolerances by LLM backend."""

from content_pipeline.domain.enums import ProviderType


# Quality gate thresholds auto-adjust based on provider
# Local models (Ollama, LM Studio) produce lower-quality output
# Expect more validation retries with local providers
PROVIDER_QUALITY_TOLERANCES = {
    ProviderType.ANTHROPIC: {
        "ai_risk_score_threshold": 10,
        "checklist_pass_rate_threshold": 0.95,
        "max_validation_retries": 2,
    },
    ProviderType.OPENROUTER: {
        "ai_risk_score_threshold": 10,
        "checklist_pass_rate_threshold": 0.90,
        "max_validation_retries": 3,
    },
    ProviderType.OLLAMA: {
        "ai_risk_score_threshold": 12,
        "checklist_pass_rate_threshold": 0.85,
        "max_validation_retries": 4,
    },
    ProviderType.LM_STUDIO: {
        "ai_risk_score_threshold": 12,
        "checklist_pass_rate_threshold": 0.85,
        "max_validation_retries": 4,
    },
}
