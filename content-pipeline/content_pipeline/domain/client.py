# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:32 AM (UTC-6)

"""Client domain models — client profile and engagement context."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from content_pipeline.domain.enums import AuthorityMode, TopicPath


@dataclass
class UnresolvedItem:
    """Tracked issue blocking or pending resolution during run."""
    description: str
    blocks_run: bool
    source_stage: int
    resolved: bool = False
    resolved_at_stage: Optional[int] = None


@dataclass
class RunContext:
    """Live execution context for a single article run."""
    client_id: UUID
    topic: str
    primary_keyword: str
    topic_path: TopicPath
    angle_notes_sanitized: Optional[str] = None
    priority_sources: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = field(default_factory=list)
    authority_mode: AuthorityMode = AuthorityMode.NORMAL
    fallback_status: Optional[str] = None
    allowed_claims: list[str] = field(default_factory=list)
    disallowed_claims: list[str] = field(default_factory=list)
    article_slug: Optional[str] = None
    schema_recommendation: Optional[str] = None
    word_count_result: Optional[dict] = None


@dataclass
class ClientReferenceFiles:
    """Parsed client reference materials."""
    style_reference_card: Optional[str] = None
    audience_profile: Optional[str] = None
    brand_notes: Optional[str] = None
    brand_colors: dict = field(default_factory=dict)
    display_font: Optional[str] = None
    body_font: Optional[str] = None
    google_fonts_url: Optional[str] = None
    reading_level_target: Optional[str] = None
    technical_depth: Optional[str] = None
    certifications: list[str] = field(default_factory=list)
    years_in_business: Optional[int] = None
    ymyl_category: Optional[str] = None


@dataclass
class Client:
    """Client profile and configuration."""
    id: UUID
    name: str
    website_url: Optional[str] = None
    industry: Optional[str] = None
    service_area: Optional[str] = None
    off_limits: list[str] = field(default_factory=list)
    reference_files: ClientReferenceFiles = field(default_factory=ClientReferenceFiles)
