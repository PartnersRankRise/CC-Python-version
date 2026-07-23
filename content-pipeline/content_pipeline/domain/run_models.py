# Created: Thursday Jul 23, 2026, 3:22 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:22 PM (UTC-6)

"""Run domain models — topic recommendations, overlap detection, published articles."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TopicRecommendation:
    """Topic recommendation from ideation (Path B)."""
    topic: str
    primary_keyword: str
    why_now: str
    audience_intent: str
    eeat_angle: str


@dataclass
class OverlapConflict:
    """Conflict detected during overlap check."""
    existing_slug: str
    conflict_type: str  # "keyword_overlap" | "title_similarity"
    existing_keyword: Optional[str] = None
    existing_title: Optional[str] = None
    suggestion: str = "Choose a different angle or keyword."


@dataclass
class PublishedArticle:
    """Published article for overlap check queries."""
    slug: str
    title: str
    primary_keyword: str
