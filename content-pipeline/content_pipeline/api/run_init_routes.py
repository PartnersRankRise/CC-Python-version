# Created: Thursday Jul 23, 2026, 3:22 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:22 PM (UTC-6)

"""Run initialization API endpoints — Pre-Stage 1 routes."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from content_pipeline.exceptions import (
    MissingReferenceFilesError,
    OverlapDetectedError,
    RunCreationFailedError,
)
from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.repositories.run_repository import RunRepository
from content_pipeline.services.run_init_service import RunInitService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["runs"])

# ========== Pydantic Models ==========


class UserProvidedTopicRequest(BaseModel):
    """Request to create run with user-provided topic (Path A)."""

    topic: str = Field(..., min_length=1, max_length=255)
    primary_keyword: str = Field(..., min_length=1, max_length=100)
    angle_notes: Optional[str] = Field(None, max_length=500)


class IdeationRequest(BaseModel):
    """Request to generate topic recommendations (Path B)."""

    count: int = Field(default=5, ge=1, le=10)


class TopicRecommendationResponseModel(BaseModel):
    """Single topic recommendation."""

    topic: str
    primary_keyword: str
    why_now: str
    audience_intent: str
    eeat_angle: str


class ConfirmTopicRequest(BaseModel):
    """Request to confirm topic and create run (Path A or B)."""

    topic: str = Field(..., min_length=1, max_length=255)
    primary_keyword: str = Field(..., min_length=1, max_length=100)
    recommendation_n: Optional[int] = Field(None, ge=0, le=10)
    client_confirmed_open_questions: Optional[dict] = None


class OverlapConflictResponse(BaseModel):
    """Conflict response when overlap detected."""

    existing_slug: str
    conflict_type: str
    existing_keyword: Optional[str] = None
    existing_title: Optional[str] = None
    suggestion: str


class RunResponse(BaseModel):
    """Run response."""

    id: UUID
    client_id: UUID
    folder_slug: str
    status: str
    created_at: datetime


# ========== Dependency Injection ==========


def get_run_init_service() -> RunInitService:
    """Get RunInitService instance."""
    client_repo = ClientRepository()
    run_repo = RunRepository()
    return RunInitService(client_repo, run_repo)


# ========== Endpoints ==========


@router.post("/{client_id}/runs", status_code=201, response_model=RunResponse)
async def create_run_user_topic(
    client_id: UUID,
    request: UserProvidedTopicRequest,
    service: RunInitService = Depends(get_run_init_service),
) -> RunResponse:
    """POST /clients/{client_id}/runs — Create run with user-provided topic (Path A).

    Args:
        client_id: Client UUID
        request: UserProvidedTopicRequest with topic and keyword
        service: RunInitService instance

    Returns:
        201 RunResponse if successful
        409 OverlapConflictResponse if overlap detected
        400 if reference files missing
    """
    logger.info(f"Creating run for client {client_id} with user topic: {request.topic}")

    try:
        # Check for overlap first
        overlap = await service.check_overlap(
            client_id, request.topic, request.primary_keyword
        )

        if overlap:
            logger.warning(f"Overlap detected: {overlap.conflict_type}")
            return HTTPException(
                status_code=409,
                detail={
                    "error": "Overlap detected",
                    "existing_slug": overlap.existing_slug,
                    "conflict_type": overlap.conflict_type,
                    "suggestion": overlap.suggestion,
                },
            )

        # Create run
        run = await service.create_run_from_user_topic(
            client_id=client_id,
            topic=request.topic,
            keyword=request.primary_keyword,
            angle_notes=request.angle_notes,
        )

        return RunResponse(
            id=run.id,
            client_id=run.client_id,
            folder_slug=run.folder_slug,
            status=run.status,
            created_at=run.created_at,
        )

    except MissingReferenceFilesError as e:
        logger.error(f"Reference files missing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except OverlapDetectedError as e:
        logger.error(f"Overlap detected: {e}")
        raise HTTPException(status_code=409, detail=str(e))

    except RunCreationFailedError as e:
        logger.error(f"Run creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{client_id}/runs/{run_id}/topic-recommendations",
    status_code=200,
    response_model=list[TopicRecommendationResponseModel],
)
async def generate_recommendations(
    client_id: UUID,
    run_id: UUID,
    request: IdeationRequest,
    service: RunInitService = Depends(get_run_init_service),
) -> list[TopicRecommendationResponseModel]:
    """POST /clients/{client_id}/runs/{run_id}/topic-recommendations — Generate topic recommendations (Path B).

    Args:
        client_id: Client UUID
        run_id: Run UUID (for context, may be placeholder)
        request: IdeationRequest with count
        service: RunInitService instance

    Returns:
        200 list of TopicRecommendationResponseModel
        400 if reference files missing
        500 if LLM call fails
    """
    logger.info(f"Generating {request.count} recommendations for client {client_id}")

    try:
        recommendations = await service.generate_topic_recommendations(
            client_id=client_id, count=request.count
        )

        return [
            TopicRecommendationResponseModel(
                topic=rec.topic,
                primary_keyword=rec.primary_keyword,
                why_now=rec.why_now,
                audience_intent=rec.audience_intent,
                eeat_angle=rec.eeat_angle,
            )
            for rec in recommendations
        ]

    except MissingReferenceFilesError as e:
        logger.error(f"Reference files missing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.post(
    "/{client_id}/runs/{run_id}/confirm-topic",
    status_code=201,
    response_model=RunResponse,
)
async def confirm_topic(
    client_id: UUID,
    run_id: UUID,
    request: ConfirmTopicRequest,
    service: RunInitService = Depends(get_run_init_service),
) -> RunResponse:
    """POST /clients/{client_id}/runs/{run_id}/confirm-topic — Confirm topic and create run.

    Handles both Path A (from user input) and Path B (from recommendation).
    Runs overlap check; if clear, creates run folder and handoff.

    Args:
        client_id: Client UUID
        run_id: Run UUID (may be placeholder for Path B)
        request: ConfirmTopicRequest with topic, keyword, optional recommendation_n
        service: RunInitService instance

    Returns:
        201 RunResponse if successful
        409 OverlapConflictResponse if overlap detected
        400 if reference files missing
    """
    logger.info(f"Confirming topic for client {client_id}: {request.topic}")

    try:
        # Check for overlap
        overlap = await service.check_overlap(
            client_id, request.topic, request.primary_keyword
        )

        if overlap:
            logger.warning(f"Overlap detected: {overlap.conflict_type}")
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Overlap detected",
                    "existing_slug": overlap.existing_slug,
                    "conflict_type": overlap.conflict_type,
                    "suggestion": overlap.suggestion,
                },
            )

        # If open questions provided, process them (TODO: save user responses)

        # Create run
        run = await service.create_run_from_user_topic(
            client_id=client_id,
            topic=request.topic,
            keyword=request.primary_keyword,
        )

        return RunResponse(
            id=run.id,
            client_id=run.client_id,
            folder_slug=run.folder_slug,
            status=run.status,
            created_at=run.created_at,
        )

    except MissingReferenceFilesError as e:
        logger.error(f"Reference files missing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except OverlapDetectedError as e:
        logger.error(f"Overlap detected: {e}")
        raise HTTPException(status_code=409, detail=str(e))

    except RunCreationFailedError as e:
        logger.error(f"Run creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
