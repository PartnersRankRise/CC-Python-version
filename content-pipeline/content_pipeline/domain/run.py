# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:32 AM (UTC-6)

"""Run domain models — article production run state."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import RunContext
from content_pipeline.domain.enums import RunStatus


@dataclass
class Run:
    """Single article production run."""
    id: UUID
    client_id: UUID
    folder_slug: str
    status: RunStatus
    context: RunContext
    current_stage: int
    created_at: datetime
    updated_at: datetime
    human_review_flag: Optional[str] = None
    dry_run: bool = False
