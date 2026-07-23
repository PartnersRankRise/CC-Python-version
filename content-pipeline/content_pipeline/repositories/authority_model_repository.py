# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Authority model repository — read and merge authority validation configurations."""

from typing import Optional
from uuid import UUID

from content_pipeline.domain.stage import AuthorityModel
from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import AuthorityModelNotFoundError, ClientNotFoundError


class AuthorityModelRepository(BaseRepository):
    """Repository for authority model (validation config) data access."""

    async def get_authority_model(self, industry_key: str) -> AuthorityModel:
        """Retrieve base authority model for an industry.

        Args:
            industry_key: Industry classification (e.g., "home_services", "health_wellness_spa")

        Returns:
            AuthorityModel domain object

        Raises:
            AuthorityModelNotFoundError: Authority model not found for industry
        """
        raise NotImplementedError

    async def get_authority_model_with_client_overrides(
        self, industry_key: str, client_id: UUID
    ) -> AuthorityModel:
        """Retrieve authority model with client-specific overrides merged.

        Merges base authority model with client's authority_overrides from clients table.

        Args:
            industry_key: Industry classification
            client_id: Client UUID

        Returns:
            AuthorityModel with client overrides applied

        Raises:
            AuthorityModelNotFoundError: Authority model not found for industry
            ClientNotFoundError: Client not found
        """
        raise NotImplementedError

    async def list_authority_models(self) -> list[AuthorityModel]:
        """List all available authority models.

        Returns:
            List of AuthorityModel domain objects
        """
        raise NotImplementedError

    async def get_min_valid_sources_for_industry(self, industry_key: str) -> int:
        """Get minimum valid sources required for an industry.

        Used to determine if source validation should short-circuit to APPROVED
        (when min_valid_sources == 0 for home_services).

        Args:
            industry_key: Industry classification

        Returns:
            Minimum number of valid sources required

        Raises:
            AuthorityModelNotFoundError: Authority model not found for industry
        """
        raise NotImplementedError
