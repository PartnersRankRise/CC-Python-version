# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Client repository — CRUD operations for clients and reference files."""

from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import Client, ClientReferenceFiles
from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import ClientNotFoundError, ReferenceFileNotFoundError


class ClientRepository(BaseRepository):
    """Repository for client data access."""

    async def get_client(self, client_id: UUID) -> Client:
        """Retrieve a client by ID.

        Args:
            client_id: Client UUID

        Returns:
            Client domain object

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def create_client(
        self,
        name: str,
        website_url: Optional[str] = None,
        industry: Optional[str] = None,
        service_area: Optional[str] = None,
    ) -> Client:
        """Create a new client.

        Args:
            name: Client name
            website_url: Client website URL
            industry: Industry classification
            service_area: Service area

        Returns:
            Created Client domain object
        """
        raise NotImplementedError

    async def update_client(self, client: Client) -> Client:
        """Update an existing client.

        Args:
            client: Client domain object with updates

        Returns:
            Updated Client domain object

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def list_clients(self) -> list[Client]:
        """List all active clients.

        Returns:
            List of Client domain objects
        """
        raise NotImplementedError

    async def get_client_reference_files(self, client_id: UUID) -> ClientReferenceFiles:
        """Retrieve parsed reference files for a client.

        Args:
            client_id: Client UUID

        Returns:
            ClientReferenceFiles domain object

        Raises:
            ClientNotFoundError: Client not found
            ReferenceFileNotFoundError: Reference files not found
        """
        raise NotImplementedError

    async def save_client_reference_files(
        self, client_id: UUID, reference_files: ClientReferenceFiles
    ) -> ClientReferenceFiles:
        """Save or update client reference files.

        Args:
            client_id: Client UUID
            reference_files: ClientReferenceFiles domain object

        Returns:
            Saved ClientReferenceFiles domain object

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def get_client_context(self, client_id: UUID) -> dict:
        """Retrieve mutable client engagement context.

        Args:
            client_id: Client UUID

        Returns:
            Client context dict with engagement notes, run history, etc.

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def update_client_context(self, client_id: UUID, context: dict) -> dict:
        """Update client engagement context.

        Args:
            client_id: Client UUID
            context: Updated context dict

        Returns:
            Updated context dict

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError
