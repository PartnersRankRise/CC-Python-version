# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Reference file repository — read and write client reference content."""

from uuid import UUID

from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import ClientNotFoundError, ReferenceFileNotFoundError


class ReferenceFileRepository(BaseRepository):
    """Repository for client reference file data access."""

    async def get_style_reference_card(self, client_id: UUID) -> str:
        """Retrieve parsed style reference card for a client.

        Args:
            client_id: Client UUID

        Returns:
            Style reference card markdown content

        Raises:
            ClientNotFoundError: Client not found
            ReferenceFileNotFoundError: Reference file not found
        """
        raise NotImplementedError

    async def save_style_reference_card(self, client_id: UUID, content: str) -> str:
        """Save or update style reference card for a client.

        Args:
            client_id: Client UUID
            content: Style reference card markdown content

        Returns:
            Saved content

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def get_audience_profile(self, client_id: UUID) -> str:
        """Retrieve parsed audience profile for a client.

        Args:
            client_id: Client UUID

        Returns:
            Audience profile markdown content

        Raises:
            ClientNotFoundError: Client not found
            ReferenceFileNotFoundError: Reference file not found
        """
        raise NotImplementedError

    async def save_audience_profile(self, client_id: UUID, content: str) -> str:
        """Save or update audience profile for a client.

        Args:
            client_id: Client UUID
            content: Audience profile markdown content

        Returns:
            Saved content

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def get_brand_notes(self, client_id: UUID) -> str:
        """Retrieve parsed brand notes for a client.

        Args:
            client_id: Client UUID

        Returns:
            Brand notes markdown content

        Raises:
            ClientNotFoundError: Client not found
            ReferenceFileNotFoundError: Reference file not found
        """
        raise NotImplementedError

    async def save_brand_notes(self, client_id: UUID, content: str) -> str:
        """Save or update brand notes for a client.

        Args:
            client_id: Client UUID
            content: Brand notes markdown content

        Returns:
            Saved content

        Raises:
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError
