# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 12:00 PM (UTC-6)

"""Run API endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("")
async def create_run() -> dict:
    """Create a new run (stub implementation)."""
    return {"id": "placeholder", "status": "not_implemented"}


@router.get("")
async def list_runs() -> list:
    """List all runs (stub implementation)."""
    return []


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict:
    """Get a specific run (stub implementation)."""
    raise HTTPException(status_code=501, detail="Not implemented")
