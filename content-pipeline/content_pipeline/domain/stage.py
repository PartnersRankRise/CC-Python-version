# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:35 PM (UTC-6)

"""Stage domain models — pipeline execution outputs and QA results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.enums import (
    FallbackAuthorityType,
    QADecision,
    QAIssueType,
    StageStatus,
    ValidationStatus,
)


@dataclass
class ParsedBrief:
    """Stage 2 content brief parsed into structured sections."""
    keyword_strategy: dict
    audience_definition: str
    who_how_why: dict
    post_structure: list
    content_table: Optional[str] = None
    eeat_instructions: list[dict] = field(default_factory=list)
    style_directive: dict = field(default_factory=dict)
    structural_specs: dict = field(default_factory=dict)
    internal_linking: list[dict] = field(default_factory=list)
    cta_direction: dict = field(default_factory=dict)
    author_credential: str = ""


@dataclass
class ParsedDossier:
    """Stage 1 research dossier parsed into structured sections."""
    topic_and_semantic_field: str
    source_bank: str
    non_obvious_insight: str
    ymyl_assessment: str
    content_gap_analysis: str
    eeat_framing: str
    search_intent: str
    audience_value_statement: str
    supplemental_notes: Optional[str] = None


@dataclass
class QAIssue:
    """Quality assurance issue found during Stage 6 review."""
    section: str
    description: str
    issue_type: QAIssueType
    stage_responsible: Optional[int] = None


@dataclass
class QAResult:
    """Stage 6 QA approval decision and scoring."""
    decision: QADecision
    checklist_score: tuple[int, int]
    ai_risk_score: int
    section_results: dict[str, str]
    issues: list[QAIssue]
    human_review_flag: Optional[str] = None
    revision_stage: Optional[int] = None


@dataclass
class SEOAnnotation:
    """Stage 5 SEO optimization metadata."""
    changes_summary: list[str] = field(default_factory=list)
    keyword_density: dict = field(default_factory=dict)
    meta_title: dict = field(default_factory=dict)
    meta_description: dict = field(default_factory=dict)
    schema_recommendation: str = ""
    internal_links: list[dict] = field(default_factory=list)
    readability_note: dict = field(default_factory=dict)
    word_count: dict = field(default_factory=dict)
    ai_search_alignment: str = ""
    qa_flags: list[str] = field(default_factory=list)


@dataclass
class StageOutput:
    """Pipeline stage execution result."""
    id: UUID
    run_id: UUID
    stage_number: int
    stage_name: str
    attempt: int
    status: StageStatus
    article_content: Optional[str] = None
    editorial_note: Optional[str] = None
    seo_annotation: Optional[SEOAnnotation] = None
    qa_result: Optional[QAResult] = None
    handoff_content: Optional[str] = None
    quality_gate_results: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ValidationReport:
    """Source validation results for Stage 1.5."""
    run_id: UUID
    status: ValidationStatus
    industry_key: str
    authority_overrides_applied: bool = False
    sources_total: Optional[int] = None
    sources_verified: Optional[int] = None
    sources_unverified: Optional[int] = None
    fallback_activated: bool = False
    fallback_reason: Optional[str] = None
    fallback_primary: Optional[FallbackAuthorityType] = None
    allowed_claims: list[str] = field(default_factory=list)
    disallowed_claims: list[str] = field(default_factory=list)
    authority_phrase: Optional[str] = None


@dataclass
class ClaimRepositioningRule:
    """Authority fallback claim repositioning rule."""
    pattern: str
    replacement: str
    context: str
    sort_order: int


@dataclass
class AuthorityModel:
    """Industry-specific source validation configuration."""
    industry_key: str
    min_valid_sources: int
    retry_strategies: list[str]
    strategy_queries: dict[str, str]
    fallback_primary: FallbackAuthorityType
    fallback_secondary: list[FallbackAuthorityType]
    allowed_claims: list[str]
    disallowed_claims: list[str]
    repositioning_rules: list[ClaimRepositioningRule]
    authority_phrase: str
    authority_examples: list[str] = field(default_factory=list)
