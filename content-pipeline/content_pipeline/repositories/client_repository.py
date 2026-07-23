# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:53 PM (UTC-6)

"""Client repository — CRUD operations for clients and reference files."""

from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import Client, ClientReferenceFiles
from content_pipeline.domain.enums import ClientState
from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import ClientNotFoundError, ReferenceFileNotFoundError


class ClientRepository(BaseRepository):
    """Repository for client data access."""

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
            Created Client domain object with generated UUID
        """
        data = {
            "name": name,
            "website_url": website_url,
            "industry": industry,
            "service_area": service_area,
        }
        response = self.supabase.table("clients").insert(data).execute()
        if not response.data:
            raise RuntimeError("Failed to create client")
        row = response.data[0]
        return Client(
            id=UUID(row["id"]),
            name=row["name"],
            website_url=row["website_url"],
            industry=row["industry"],
            service_area=row["service_area"],
            off_limits=row.get("off_limits", []),
        )

    async def get_client(self, client_id: UUID) -> Client:
        """Retrieve a client by ID.

        Args:
            client_id: Client UUID

        Returns:
            Client domain object

        Raises:
            ClientNotFoundError: Client not found
        """
        response = (
            self.supabase.table("clients")
            .select("*")
            .eq("id", str(client_id))
            .execute()
        )
        if not response.data:
            raise ClientNotFoundError(f"Client {client_id} not found")
        row = response.data[0]
        return Client(
            id=UUID(row["id"]),
            name=row["name"],
            website_url=row["website_url"],
            industry=row["industry"],
            service_area=row["service_area"],
            off_limits=row.get("off_limits", []),
        )

    async def update_client(self, client: Client) -> Client:
        """Update an existing client.

        Args:
            client: Client domain object with updates

        Returns:
            Updated Client domain object

        Raises:
            ClientNotFoundError: Client not found
        """
        data = {
            "name": client.name,
            "website_url": client.website_url,
            "industry": client.industry,
            "service_area": client.service_area,
            "off_limits": client.off_limits,
        }
        response = (
            self.supabase.table("clients")
            .update(data)
            .eq("id", str(client.id))
            .execute()
        )
        if not response.data:
            raise ClientNotFoundError(f"Client {client.id} not found")
        return client

    async def list_clients(self) -> list[Client]:
        """List all active clients.

        Returns:
            List of Client domain objects
        """
        response = self.supabase.table("clients").select("*").execute()
        return [
            Client(
                id=UUID(row["id"]),
                name=row["name"],
                website_url=row["website_url"],
                industry=row["industry"],
                service_area=row["service_area"],
                off_limits=row.get("off_limits", []),
            )
            for row in response.data
        ]

    async def get_reference_files(self, client_id: UUID) -> ClientReferenceFiles:
        """Retrieve parsed reference files for a client.

        Returns ClientReferenceFiles with all None fields if no record exists (NEW state).

        Args:
            client_id: Client UUID

        Returns:
            ClientReferenceFiles domain object
        """
        response = (
            self.supabase.table("client_reference_files")
            .select("*")
            .eq("client_id", str(client_id))
            .execute()
        )
        if not response.data:
            return ClientReferenceFiles()
        row = response.data[0]
        return ClientReferenceFiles(
            style_reference_card=row.get("style_reference_card"),
            audience_profile=row.get("audience_profile"),
            brand_notes=row.get("brand_notes"),
            brand_colors=row.get("brand_colors", {}),
            display_font=row.get("display_font"),
            body_font=row.get("body_font"),
            google_fonts_url=row.get("google_fonts_url"),
            reading_level_target=row.get("reading_level_target"),
            technical_depth=row.get("technical_depth"),
            certifications=row.get("certifications", []),
            years_in_business=row.get("years_in_business"),
            ymyl_category=row.get("ymyl_category"),
        )

    async def save_reference_files(
        self, client_id: UUID, files: ClientReferenceFiles
    ) -> ClientReferenceFiles:
        """Save or update client reference files.

        Also updates onboarding_state based on which files are present:
        - all three not None → "fully_onboarded"
        - some not None → "partial"
        - all None → "new"

        Args:
            client_id: Client UUID
            files: ClientReferenceFiles domain object

        Returns:
            Saved ClientReferenceFiles domain object
        """
        data = {
            "client_id": str(client_id),
            "style_reference_card": files.style_reference_card,
            "audience_profile": files.audience_profile,
            "brand_notes": files.brand_notes,
            "brand_colors": files.brand_colors,
            "display_font": files.display_font,
            "body_font": files.body_font,
            "google_fonts_url": files.google_fonts_url,
            "reading_level_target": files.reading_level_target,
            "technical_depth": files.technical_depth,
            "certifications": files.certifications,
            "years_in_business": files.years_in_business,
            "ymyl_category": files.ymyl_category,
        }

        present_count = sum([
            files.style_reference_card is not None,
            files.audience_profile is not None,
            files.brand_notes is not None,
        ])
        if present_count == 0:
            onboarding_state = ClientState.NEW.value
        elif present_count == 3:
            onboarding_state = ClientState.FULLY_ONBOARDED.value
        else:
            onboarding_state = ClientState.PARTIAL.value

        data["onboarding_state"] = onboarding_state

        response = (
            self.supabase.table("client_reference_files")
            .upsert(data, on_conflict="client_id")
            .execute()
        )
        if not response.data:
            raise RuntimeError("Failed to save reference files")

        return files

    async def save_client_context(self, client_id: UUID, context: dict) -> None:
        """Save or update client engagement context.

        Args:
            client_id: Client UUID
            context: Context dict
        """
        data = {
            "client_id": str(client_id),
            "context_data": context,
        }
        self.supabase.table("client_contexts").upsert(data, on_conflict="client_id").execute()

    async def get_client_context(self, client_id: UUID) -> Optional[dict]:
        """Retrieve mutable client engagement context.

        Args:
            client_id: Client UUID

        Returns:
            Client context dict or None if not found
        """
        response = (
            self.supabase.table("client_contexts")
            .select("context_data")
            .eq("client_id", str(client_id))
            .execute()
        )
        if not response.data:
            return None
        return response.data[0].get("context_data")

    async def get_reference_files_complete(self, client_id: UUID) -> bool:
        """Check if all 3 reference files exist for a client.

        Args:
            client_id: Client UUID

        Returns:
            True if all 3 files exist, False otherwise
        """
        ref_files = await self.get_reference_files(client_id)
        return (
            ref_files.style_reference_card is not None
            and ref_files.audience_profile is not None
            and ref_files.brand_notes is not None
        )
