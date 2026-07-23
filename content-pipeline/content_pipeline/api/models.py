# Created: Thursday Jul 23, 2026, 2:44 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:44 PM (UTC-6)

"""Pydantic request/response models for FastAPI endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ========== CLIENT ENDPOINTS ==========

class CreateClientRequest(BaseModel):
    """Request to create a new client."""
    name: str = Field(..., min_length=1, max_length=255)
    website_url: Optional[str] = Field(None, max_length=2048)
    industry: Optional[str] = Field(None, max_length=100)
    service_area: Optional[str] = Field(None, max_length=255)


class ClientResponse(BaseModel):
    """Response with client record."""
    id: UUID
    name: str
    website_url: Optional[str]
    industry: Optional[str]
    service_area: Optional[str]
    onboarding_state: str  # "new", "partial", "fully_onboarded"
    created_at: datetime


# ========== ONBOARDING ENDPOINTS ==========

class ContentSample(BaseModel):
    """A single content sample: either text or URL."""
    type: str = Field(..., pattern="^(text|url)$")
    content: Optional[str] = Field(None, max_length=50000)  # For type="text"
    url: Optional[str] = Field(None, max_length=2048)  # For type="url"

    def __init__(self, **data):
        """Validate that either content or url is provided based on type."""
        super().__init__(**data)
        if self.type == "text" and not self.content:
            raise ValueError("content is required when type='text'")
        if self.type == "url" and not self.url:
            raise ValueError("url is required when type='url'")


class OnboardingRequest(BaseModel):
    """Request to start onboarding for a client."""
    content_samples: list[ContentSample] = Field(..., min_items=1, max_items=10)
    additional_context: dict = Field(default_factory=dict)
    regenerate: bool = False


class OnboardingJobResponse(BaseModel):
    """Response when onboarding job is enqueued."""
    job_id: UUID
    status: str  # "queued"
    client_state_before: str  # "new", "partial", "fully_onboarded"
    message: str


class ConflictResponse(BaseModel):
    """Response when client is already fully onboarded."""
    error: str
    client_state: str
    suggestion: str


# ========== STATUS/POLLING ENDPOINTS ==========

class OnboardingStatusResponse(BaseModel):
    """Response with validation status of reference files."""
    client_id: UUID
    client_state: str  # "new", "partial", "fully_onboarded"
    validation_status: dict  # {
        #   "style_reference_card": {"exists": bool, "sections": [...], "all_present": bool},
        #   "audience_profile": {"exists": bool, "sections": [...], "all_present": bool},
        #   "brand_notes": {"exists": bool, "sections": [...], "has_checkboxes": bool},
        #   "brand_colors": {"extracted": bool, "count": int, "all_11_valid": bool, "errors": []}
        # }
    last_updated: datetime


class JobStatusResponse(BaseModel):
    """Response with async job status."""
    job_id: UUID
    status: str  # "queued", "running", "complete", "failed"
    progress: Optional[str] = None  # "Step X/7" or similar
    result: Optional[dict] = None  # Only when status="complete"
    error: Optional[str] = None  # Only when status="failed"
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
