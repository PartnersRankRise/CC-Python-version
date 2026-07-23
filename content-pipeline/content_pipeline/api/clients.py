# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 12:00 PM (UTC-6)

"""Client API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientResponse(BaseModel):
    """Stub client response model."""
    id: str
    status: str


@router.post("")
async def create_client() -> ClientResponse:
    """Create a new client (stub implementation)."""
    return ClientResponse(id="placeholder", status="not_implemented")


@router.get("")
async def list_clients() -> list:
    """List all clients (stub implementation)."""
    return []


@router.get("/{client_id}")
async def get_client(client_id: str) -> dict:
    """Get a specific client (stub implementation)."""
    raise HTTPException(status_code=501, detail="Not implemented")
