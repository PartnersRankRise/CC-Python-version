# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:44 PM (UTC-6)

"""Client API endpoints — creation, onboarding, and status tracking."""

import logging
from typing import Any, Optional
from uuid import UUID, uuid4

import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from content_pipeline.api.models import (
    CreateClientRequest,
    ClientResponse,
    OnboardingRequest,
    OnboardingJobResponse,
    ConflictResponse,
    OnboardingStatusResponse,
    JobStatusResponse,
)
from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.exceptions import ClientAlreadyOnboardedError
from content_pipeline.domain.enums import ClientState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])

# TODO: Inject these via dependency injection in production
# For now, they're module-level singletons
_client_repo: Optional[ClientRepository] = None
_arq_queue: Optional[Any] = None
_jobs_cache: dict[str, dict] = {}  # In-memory job state (will use Redis + DB)


def get_client_repo() -> ClientRepository:
    """Get or create client repository instance."""
    global _client_repo
    if _client_repo is None:
        _client_repo = ClientRepository()
    return _client_repo


# ========== POST /clients — Create Client ==========

@router.post("", status_code=201, response_model=ClientResponse)
async def create_client(
    request: CreateClientRequest,
    repo: ClientRepository = Depends(get_client_repo),
) -> ClientResponse:
    """Create a new client.
    
    Args:
        request: CreateClientRequest with client details
        repo: ClientRepository instance
        
    Returns:
        ClientResponse with new client record (201)
    """
    logger.info(f"Creating client: {request.name}")
    
    # Create client in repository
    client = await repo.create_client(
        name=request.name,
        website_url=request.website_url,
        industry=request.industry,
        service_area=request.service_area,
    )
    
    logger.info(f"Client created: {client.id}")
    
    return ClientResponse(
        id=client.id,
        name=client.name,
        website_url=client.website_url,
        industry=client.industry,
        service_area=client.service_area,
        onboarding_state="new",
        created_at=client.created_at if hasattr(client, 'created_at') else None,
    )


# ========== POST /clients/{client_id}/onboard — Start Onboarding ==========

@router.post("/{client_id}/onboard", status_code=202)
async def start_onboarding(
    client_id: UUID,
    request: OnboardingRequest,
    repo: ClientRepository = Depends(get_client_repo),
) -> JSONResponse:
    """Start onboarding for a client (enqueue async job).
    
    Args:
        client_id: Client UUID
        request: OnboardingRequest with content samples
        repo: ClientRepository instance
        
    Returns:
        202 OnboardingJobResponse if job enqueued
        409 ConflictResponse if already fully onboarded (regenerate=False)
    """
    logger.info(f"Starting onboarding for client {client_id}, regenerate={request.regenerate}")
    
    # Check client state
    ref_files = await repo.get_reference_files(client_id)
    present_count = sum([
        ref_files.style_reference_card is not None,
        ref_files.audience_profile is not None,
        ref_files.brand_notes is not None,
    ])
    
    if present_count == 0:
        state = ClientState.NEW.value
    elif present_count == 3:
        state = ClientState.FULLY_ONBOARDED.value
    else:
        state = ClientState.PARTIAL.value
    
    logger.info(f"Client state: {state} ({present_count}/3 files)")
    
    # Check if already onboarded
    if state == ClientState.FULLY_ONBOARDED.value and not request.regenerate:
        logger.warning(f"Client {client_id} already onboarded, regenerate=False")
        return JSONResponse(
            status_code=409,
            content={
                "error": f"Client {client_id} is already fully onboarded",
                "client_state": state,
                "suggestion": "Pass regenerate=True to regenerate reference files",
            },
        )
    
    # Generate job ID
    job_id = uuid4()
    
    # Extract content from samples (fetch URLs if needed)
    content_text = await _extract_content_samples(request.content_samples)
    
    logger.info(f"Extracted {len(content_text)} characters from content samples")
    
    # Merge additional context
    context = {
        "client_id": str(client_id),
        "service_area": request.additional_context.get("service_area"),
        "off_limits_topics": request.additional_context.get("off_limits_topics", []),
    }
    
    # Enqueue job (TODO: implement ARQ integration)
    logger.info(f"Enqueueing onboarding job {job_id} for client {client_id}")
    _jobs_cache[str(job_id)] = {
        "job_id": str(job_id),
        "status": "queued",
        "client_id": str(client_id),
        "client_state_before": state,
        "created_at": None,
    }
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": str(job_id),
            "status": "queued",
            "client_state_before": state,
            "message": f"Onboarding job queued: {job_id}",
        },
    )


# ========== GET /clients/{client_id}/onboarding/status — Poll Validation Status ==========

@router.get("/{client_id}/onboarding/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    client_id: UUID,
    repo: ClientRepository = Depends(get_client_repo),
) -> OnboardingStatusResponse:
    """Get validation status of reference files.
    
    Args:
        client_id: Client UUID
        repo: ClientRepository instance
        
    Returns:
        OnboardingStatusResponse with validation details
    """
    logger.debug(f"Getting onboarding status for client {client_id}")
    
    # Get reference files
    ref_files = await repo.get_reference_files(client_id)
    
    # Detect state
    present_count = sum([
        ref_files.style_reference_card is not None,
        ref_files.audience_profile is not None,
        ref_files.brand_notes is not None,
    ])
    
    if present_count == 0:
        state = "new"
    elif present_count == 3:
        state = "fully_onboarded"
    else:
        state = "partial"
    
    # Build validation status
    validation_status = {
        "style_reference_card": {
            "exists": ref_files.style_reference_card is not None,
            "sections": ["WRITING STYLE GUIDELINES", "VISUAL BRAND THEME", "STRUCTURAL GUIDELINES", "SEO & KEYWORD GUIDANCE"],
            "all_present": all([
                "WRITING STYLE GUIDELINES" in (ref_files.style_reference_card or ""),
                "VISUAL BRAND THEME" in (ref_files.style_reference_card or ""),
                "STRUCTURAL GUIDELINES" in (ref_files.style_reference_card or ""),
                "SEO & KEYWORD GUIDANCE" in (ref_files.style_reference_card or ""),
            ]) if ref_files.style_reference_card else False,
        },
        "audience_profile": {
            "exists": ref_files.audience_profile is not None,
            "sections": ["DEMOGRAPHIC BASELINE", "EXPERTISE AND KNOWLEDGE LEVEL", "INTENT AND PAIN POINTS", "CONTENT PROMISES", "TOPICAL AUTHORITY SIGNALS"],
            "all_present": all([
                section in (ref_files.audience_profile or "")
                for section in ["DEMOGRAPHIC BASELINE", "EXPERTISE AND KNOWLEDGE LEVEL", "INTENT AND PAIN POINTS"]
            ]),
        },
        "brand_notes": {
            "exists": ref_files.brand_notes is not None,
            "sections": ["PUBLISHING SPECIFICATIONS", "SERVICE AREA AND GEOGRAPHIC SCOPE", "AUTHORITY AND TRUST SIGNALS", "OPEN QUESTIONS FOR CLIENT"],
            "has_checkboxes": "[ ]" in (ref_files.brand_notes or "") if "OPEN QUESTIONS FOR CLIENT" in (ref_files.brand_notes or "") else False,
        },
        "brand_colors": {
            "extracted": len(ref_files.brand_colors or {}) > 0,
            "count": len(ref_files.brand_colors or {}),
            "all_11_valid": len(ref_files.brand_colors or {}) == 11,
            "errors": [],  # TODO: Validate color formats
        },
    }
    
    return OnboardingStatusResponse(
        client_id=client_id,
        client_state=state,
        validation_status=validation_status,
        last_updated=None,  # TODO: Add timestamp from DB
    )


# ========== GET /jobs/{job_id} — Poll Async Job Status ==========

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID) -> JobStatusResponse:
    """Get status of async job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        JobStatusResponse with job state
    """
    logger.debug(f"Getting status for job {job_id}")
    
    # TODO: Query Redis (ARQ) and jobs table
    # For now, use in-memory cache
    job_data = _jobs_cache.get(str(job_id))
    
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatusResponse(
        job_id=UUID(job_data["job_id"]),
        status=job_data["status"],
        progress=job_data.get("progress"),
        result=job_data.get("result"),
        error=job_data.get("error"),
        created_at=job_data.get("created_at"),
        started_at=job_data.get("started_at"),
        completed_at=job_data.get("completed_at"),
    )


# ========== HELPER FUNCTIONS ==========

async def _extract_content_samples(samples: list) -> str:
    """Extract and concatenate content from samples (fetch URLs if needed).
    
    Args:
        samples: List of ContentSample objects
        
    Returns:
        Concatenated content text
    """
    content_parts = []
    
    for sample in samples:
        if sample.type == "text":
            content_parts.append(sample.content)
        elif sample.type == "url":
            # Fetch URL content
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(sample.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            content_parts.append(text)
                        else:
                            logger.warning(f"Failed to fetch {sample.url}: {resp.status}")
            except Exception as e:
                logger.warning(f"Error fetching {sample.url}: {e}")
    
    return "\n\n---\n\n".join(content_parts)
