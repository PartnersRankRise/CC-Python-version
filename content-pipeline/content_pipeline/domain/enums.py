# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:32 AM (UTC-6)

"""Pipeline enums and constants — domain-level enumeration types."""

from enum import Enum


class ClientState(Enum):
    """Client onboarding state."""
    NEW = "new"
    PARTIAL = "partial"
    FULLY_ONBOARDED = "fully_onboarded"


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"


class RunStatus(Enum):
    """Run completion status."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    PUBLISHED = "published"


class AuthorityMode(Enum):
    """Content authority validation mode."""
    NORMAL = "normal"
    EXPERT_FALLBACK = "expert_fallback"


class TopicPath(Enum):
    """Topic source/derivation."""
    USER_PROVIDED = "user_provided"
    IDEATION = "ideation"


class QADecision(Enum):
    """QA approval decision."""
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"


class QAIssueType(Enum):
    """QA issue classification for routing."""
    PIPELINE_FAILURE = "pipeline_failure"
    CLIENT_DECISION = "client_decision"
    MINOR_OBSERVATION = "minor_observation"


class ValidationStatus(Enum):
    """Source validation result status."""
    APPROVED = "APPROVED"
    APPROVED_WITH_FALLBACK = "APPROVED_WITH_FALLBACK"
    REJECTED_DOSSIER_NOT_FOUND = "REJECTED_DOSSIER_NOT_FOUND"
    REJECTED_NO_SOURCES = "REJECTED_NO_SOURCES"
    REJECTED_CONFIG_NOT_FOUND = "REJECTED_CONFIG_NOT_FOUND"
    REJECTED_MIN_SOURCES_ZERO = "REJECTED_MIN_SOURCES_ZERO"


class ProviderType(Enum):
    """LLM provider types."""
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class FallbackAuthorityType(Enum):
    """Authority fallback types when sources cannot be verified."""
    PRACTITIONER_EXPERTISE = "PRACTITIONER_EXPERTISE"
    ATTORNEY_EXPERTISE = "ATTORNEY_EXPERTISE"
    FIELD_EXPERTISE = "FIELD_EXPERTISE"
    ADVISOR_EXPERTISE = "ADVISOR_EXPERTISE"
    DEVELOPER_EXPERTISE = "DEVELOPER_EXPERTISE"
    INDUSTRY_STANDARDS = "INDUSTRY_STANDARDS"
    CLIENT_OBSERVATION = "CLIENT_OBSERVATION"
    OPEN_SOURCE_COMMUNITY = "OPEN_SOURCE_COMMUNITY"
    MANUFACTURER_DATA = "MANUFACTURER_DATA"
    CASE_PRECEDENT = "CASE_PRECEDENT"
    REGULATORY_FRAMEWORK = "REGULATORY_FRAMEWORK"
    STATUTORY_FRAMEWORK = "STATUTORY_FRAMEWORK"
