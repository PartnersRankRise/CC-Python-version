# Created: Thursday Jul 23, 2026, 3:22 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:22 PM (UTC-6)

"""Run repository — CRUD operations for runs, published articles, and unresolved items."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import UnresolvedItem
from content_pipeline.domain.run import Run
from content_pipeline.domain.run_models import PublishedArticle
from content_pipeline.exceptions import RunNotFoundError, RunCreationFailedError
from content_pipeline.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RunRepository(BaseRepository):
    """Repository for run-related database operations."""

    async def create_run(
        self,
        client_id: UUID,
        folder_slug: str,
        context,  # RunContext
        status: str = "initiated",
    ) -> Run:
        """Create a new run record.

        Args:
            client_id: Client UUID
            folder_slug: Run folder slug (e.g., "Topic_Name_2026-07")
            context: RunContext object
            status: Run status (default "initiated")

        Returns:
            Run object with database-assigned id and timestamps

        Raises:
            RunCreationFailedError: If database operation fails
        """
        logger.info(f"Creating run for client {client_id} with slug {folder_slug}")

        try:
            run_id = str(__import__("uuid").uuid4())
            now = datetime.utcnow().isoformat()

            data = {
                "id": run_id,
                "client_id": str(client_id),
                "folder_slug": folder_slug,
                "status": status,
                "context": context.__dict__,  # Serialize RunContext
                "current_stage": 0,
                "created_at": now,
                "updated_at": now,
            }

            response = self.supabase.table("runs").insert(data).execute()

            if not response.data:
                raise RuntimeError("Failed to insert run record")

            logger.info(f"Run created: {run_id}")

            # Return Run domain object
            return Run(
                id=UUID(run_id),
                client_id=client_id,
                folder_slug=folder_slug,
                status=status,
                context=context,
                current_stage=0,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
            )

        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            raise RunCreationFailedError(f"Failed to create run: {str(e)}") from e

    async def get_run(self, run_id: UUID) -> Run:
        """Retrieve a run by ID.

        Args:
            run_id: Run UUID

        Returns:
            Run object

        Raises:
            RunNotFoundError: If run not found
        """
        logger.debug(f"Fetching run {run_id}")

        try:
            response = (
                self.supabase.table("runs")
                .select("*")
                .eq("id", str(run_id))
                .single()
                .execute()
            )

            if not response.data:
                raise RunNotFoundError(f"Run {run_id} not found")

            data = response.data
            return Run(
                id=UUID(data["id"]),
                client_id=UUID(data["client_id"]),
                folder_slug=data["folder_slug"],
                status=data["status"],
                context=data["context"],  # TODO: deserialize to RunContext
                current_stage=data["current_stage"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                human_review_flag=data.get("human_review_flag"),
            )

        except Exception as e:
            if isinstance(e, RunNotFoundError):
                raise
            logger.error(f"Failed to fetch run: {e}")
            raise RunNotFoundError(f"Failed to fetch run {run_id}: {str(e)}") from e

    async def get_published_articles(self, client_id: UUID) -> list[PublishedArticle]:
        """Get all published articles for a client (for overlap check).

        Args:
            client_id: Client UUID

        Returns:
            List of PublishedArticle objects

        Raises:
            Exception: If database query fails
        """
        logger.debug(f"Fetching published articles for client {client_id}")

        try:
            response = (
                self.supabase.table("published_articles")
                .select("article_slug, markdown_content")
                .eq("client_id", str(client_id))
                .execute()
            )

            articles = []
            for row in response.data or []:
                # Extract title from markdown (first h1)
                markdown = row.get("markdown_content", "")
                lines = markdown.split("\n")
                title = ""
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                articles.append(
                    PublishedArticle(
                        slug=row.get("article_slug", ""),
                        title=title,
                        primary_keyword="",  # TODO: Extract from metadata if stored
                    )
                )

            logger.debug(f"Found {len(articles)} published articles for client {client_id}")
            return articles

        except Exception as e:
            logger.error(f"Failed to fetch published articles: {e}")
            return []

    async def get_published_slugs(self, client_id: UUID) -> list[str]:
        """Get list of published article slugs for overlap check.

        Args:
            client_id: Client UUID

        Returns:
            List of article slugs

        Raises:
            Exception: If database query fails
        """
        try:
            response = (
                self.supabase.table("published_articles")
                .select("article_slug")
                .eq("client_id", str(client_id))
                .execute()
            )

            slugs = [row.get("article_slug", "") for row in response.data or []]
            return slugs

        except Exception as e:
            logger.error(f"Failed to fetch published slugs: {e}")
            return []

    async def save_unresolved_item(
        self, run_id: UUID, item: UnresolvedItem
    ) -> UnresolvedItem:
        """Save an unresolved item to database.

        Args:
            run_id: Run UUID
            item: UnresolvedItem object

        Returns:
            UnresolvedItem with database-assigned id

        Raises:
            Exception: If database operation fails
        """
        logger.info(f"Saving unresolved item to run {run_id}: {item.description}")

        try:
            item_id = str(__import__("uuid").uuid4())
            now = datetime.utcnow().isoformat()

            data = {
                "id": item_id,
                "run_id": str(run_id),
                "description": item.description,
                "blocks_run": item.blocks_run,
                "source_stage": item.source_stage,
                "resolved": item.resolved,
                "resolved_at_stage": item.resolved_at_stage,
                "created_at": now,
            }

            response = self.supabase.table("unresolved_items").insert(data).execute()

            if not response.data:
                raise RuntimeError("Failed to insert unresolved item")

            return item

        except Exception as e:
            logger.error(f"Failed to save unresolved item: {e}")
            raise RunCreationFailedError(f"Failed to save unresolved item: {str(e)}") from e

    async def get_unresolved_items(self, run_id: UUID) -> list[UnresolvedItem]:
        """Retrieve unresolved items for a run.

        Args:
            run_id: Run UUID

        Returns:
            List of UnresolvedItem objects

        Raises:
            Exception: If database query fails
        """
        logger.debug(f"Fetching unresolved items for run {run_id}")

        try:
            response = (
                self.supabase.table("unresolved_items")
                .select("*")
                .eq("run_id", str(run_id))
                .eq("resolved", False)
                .execute()
            )

            items = []
            for row in response.data or []:
                items.append(
                    UnresolvedItem(
                        description=row["description"],
                        blocks_run=row["blocks_run"],
                        source_stage=row["source_stage"],
                        resolved=row["resolved"],
                        resolved_at_stage=row.get("resolved_at_stage"),
                    )
                )

            return items

        except Exception as e:
            logger.error(f"Failed to fetch unresolved items: {e}")
            return []
