# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Run repository — CRUD operations for runs and related data."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import UnresolvedItem, RunContext
from content_pipeline.domain.enums import RunStatus, TopicPath
from content_pipeline.domain.run import Run
from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import RunNotFoundError, UnresolvedItemNotFoundError


class RunRepository(BaseRepository):
    """Repository for run data access."""

    async def create_run(
        self,
        client_id: UUID,
        folder_slug: str,
        context: RunContext,
        dry_run: bool = False,
    ) -> Run:
        """Create a new article run.

        Args:
            client_id: Client UUID
            folder_slug: Run folder slug (e.g., "Topic_Name_YYYY-MM")
            context: RunContext domain object
            dry_run: Whether this is a dry run

        Returns:
            Created Run domain object
        """
        raise NotImplementedError

    async def get_run(self, run_id: UUID) -> Run:
        """Retrieve a run by ID.

        Args:
            run_id: Run UUID

        Returns:
            Run domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def get_run_by_slug(self, client_id: UUID, folder_slug: str) -> Run:
        """Retrieve a run by client and folder slug.

        Args:
            client_id: Client UUID
            folder_slug: Run folder slug

        Returns:
            Run domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def update_run(self, run: Run) -> Run:
        """Update an existing run.

        Args:
            run: Run domain object with updates

        Returns:
            Updated Run domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def update_run_status(self, run_id: UUID, status: RunStatus) -> Run:
        """Update a run's status and updated_at timestamp.

        Args:
            run_id: Run UUID
            status: New RunStatus

        Returns:
            Updated Run domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def advance_run_stage(self, run_id: UUID) -> Run:
        """Advance a run to the next stage.

        Args:
            run_id: Run UUID

        Returns:
            Updated Run domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def list_runs_by_client(self, client_id: UUID) -> list[Run]:
        """List all runs for a client.

        Args:
            client_id: Client UUID

        Returns:
            List of Run domain objects
        """
        raise NotImplementedError

    async def add_unresolved_item(self, run_id: UUID, item: UnresolvedItem) -> UnresolvedItem:
        """Add an unresolved item to a run.

        Args:
            run_id: Run UUID
            item: UnresolvedItem domain object

        Returns:
            Created UnresolvedItem domain object

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def get_unresolved_items(self, run_id: UUID) -> list[UnresolvedItem]:
        """Retrieve all unresolved items for a run.

        Args:
            run_id: Run UUID

        Returns:
            List of UnresolvedItem domain objects

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def mark_unresolved_item_resolved(
        self, item_id: UUID, resolved_at_stage: int
    ) -> UnresolvedItem:
        """Mark an unresolved item as resolved.

        Args:
            item_id: UnresolvedItem UUID
            resolved_at_stage: Stage at which resolution occurred

        Returns:
            Updated UnresolvedItem domain object

        Raises:
            UnresolvedItemNotFoundError: Item not found
        """
        raise NotImplementedError

    async def log_run_entry(self, run_id: UUID, entry: str) -> None:
        """Log an entry to the run log.

        Args:
            run_id: Run UUID
            entry: Log entry text
        """
        raise NotImplementedError

    async def get_run_log_tail(self, run_id: UUID, limit: int = 20) -> list[dict]:
        """Retrieve recent entries from the run log.

        Args:
            run_id: Run UUID
            limit: Number of recent entries to retrieve

        Returns:
            List of log entry dicts with timestamp and text

        Raises:
            RunNotFoundError: Run not found
        """
        raise NotImplementedError

    async def save_topic_recommendation(
        self, client_id: UUID, topic: str, recommendation_text: str
    ) -> dict:
        """Save a topic recommendation from ideation.

        Args:
            client_id: Client UUID
            topic: Recommended topic
            recommendation_text: Recommendation details

        Returns:
            Saved recommendation dict

        Raises:
            ClientNotFoundError: Client not found (from domain)
        """
        raise NotImplementedError
