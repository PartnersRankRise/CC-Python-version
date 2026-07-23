# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 12:00 PM (UTC-6)

"""Stage API endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/stages", tags=["stages"])


@router.post("")
async def create_stage() -> dict:
    """Create a new stage (stub implementation)."""
    return {"id": "placeholder", "status": "not_implemented"}


@router.get("")
async def list_stages() -> list:
    """List all stages (stub implementation)."""
    return []


@router.get("/{stage_id}")
async def get_stage(stage_id: str) -> dict:
    """Get a specific stage (stub implementation)."""
    raise HTTPException(status_code=501, detail="Not implemented")
