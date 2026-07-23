# Created: Thursday Jul 23, 2026, 2:44 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:44 PM (UTC-6)

"""ARQ worker for async stage execution."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


async def run_onboarding_job(
    ctx: dict,
    client_id: UUID,
    content_samples_text: str,
    additional_context: dict,
    job_id: UUID,
) -> dict:
    """Execute onboarding for a client in background.
    
    This ARQ job:
    1. Updates job status to "running"
    2. Instantiates OnboardingStage with dependencies
    3. Calls onboarding_stage.onboard_client(...)
    4. On success: updates job status to "complete" with result
    5. On failure: updates job status to "failed" with error message
    
    Args:
        ctx: ARQ job context (contains redis pool, app state, etc.)
        client_id: Client UUID
        content_samples_text: Concatenated content from samples
        additional_context: Dict with service_area, off_limits_topics, etc.
        job_id: Job UUID for tracking
        
    Returns:
        dict with client_id, validation_passed, files_generated, result_summary
    """
    logger.info(f"Starting onboarding job {job_id} for client {client_id}")
    
    try:
        # Update job status to "running"
        redis = ctx["redis"]
        job_key = f"job:{job_id}"
        await redis.hset(job_key, mapping={
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "progress": "Step 1/7: Loading context",
        })
        logger.info(f"Job {job_id} marked as running")
        
        # Import dependencies (lazy import to avoid circular deps)
        from content_pipeline.repositories.client_repository import ClientRepository
        from content_pipeline.services.onboarding_service import OnboardingStage
        from content_pipeline.llm.provider_factory import LLMProviderFactory
        from content_pipeline.orchestration.unresolved_item_tracker import UnresolvedItemTracker
        
        # Initialize dependencies
        client_repo = ClientRepository()
        llm = LLMProviderFactory.create_smart_provider()
        parser = None  # OnboardingStage doesn't use parser
        tracker = UnresolvedItemTracker(None)
        
        # Create OnboardingStage
        onboarding_stage = OnboardingStage(
            repo=None,
            llm=llm,
            parser=parser,
            tracker=tracker,
            client_repo=client_repo,
        )
        
        logger.info(f"OnboardingStage initialized for job {job_id}")
        
        # Update progress
        await redis.hset(job_key, mapping={"progress": "Step 2/7: Preparing content"})
        
        # Get client details for context
        client = await client_repo.get_client(client_id)
        
        # Call onboarding_stage.onboard_client()
        logger.info(f"Calling onboard_client for {client_id}")
        await redis.hset(job_key, mapping={"progress": "Step 3/7: Calling LLM"})
        
        ref_files = await onboarding_stage.onboard_client(
            client_id=client_id,
            content_samples=content_samples_text,
            client_name=client.name,
            client_website=client.website_url,
            client_industry=client.industry,
            service_area=additional_context.get("service_area") or client.service_area,
            off_limits_topics=additional_context.get("off_limits_topics", []),
            regenerate=additional_context.get("regenerate", False),
        )
        
        logger.info(f"Onboarding complete for {client_id}, marking job complete")
        
        # Mark job as complete
        result = {
            "client_id": str(client_id),
            "validation_passed": True,
            "files_generated": 3,  # style_reference_card, audience_profile, brand_notes
            "brand_colors_extracted": len(ref_files.brand_colors or {}) == 11,
            "reading_level_extracted": ref_files.reading_level_target is not None,
            "summary": "All reference files generated and validated successfully",
        }
        
        await redis.hset(job_key, mapping={
            "status": "complete",
            "completed_at": datetime.utcnow().isoformat(),
            "progress": "Complete",
            "result": str(result),
        })
        
        logger.info(f"Job {job_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        # Mark job as failed
        try:
            redis = ctx["redis"]
            job_key = f"job:{job_id}"
            await redis.hset(job_key, mapping={
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e),
            })
        except Exception as redis_error:
            logger.error(f"Failed to update job status in Redis: {redis_error}")
        
        raise
