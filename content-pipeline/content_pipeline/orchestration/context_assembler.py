# Created: Thursday Jul 23, 2026, 3:07 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:07 PM (UTC-6)

"""ClientContextAssembler — assembles engagement context from database state.

Replaces the old CONTEXT.md file by reading live data from:
- clients table (basic info, industry, website, service area, onboarding state)
- client_contexts table (engagement notes, next planned topic, run history)
- runs table (last run folder slug, computed fresh at assembly time)
- published_articles table (posts published count, computed fresh)
- unresolved_items table (open items count, computed fresh)

The context is assembled on-demand and formatted as markdown that mimics
the original CONTEXT.md structure. This becomes the session-orientation
document for Pre-Stage 1 and all downstream stages.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.domain.client import Client

logger = logging.getLogger(__name__)


class ClientContextAssembler:
    """Assembles client engagement context from live database state."""

    def __init__(self, client_repo: ClientRepository) -> None:
        """Initialize context assembler.

        Args:
            client_repo: ClientRepository instance for database queries
        """
        self.client_repo = client_repo

    async def assemble(self, client_id: UUID) -> str:
        """Assemble engagement context markdown for a client.

        Fetches live data from database and formats as markdown that mimics
        the original CONTEXT.md structure. This document serves as the
        session-orientation brief for stages.

        Args:
            client_id: Client UUID

        Returns:
            Formatted markdown string (CONTEXT.md equivalent)

        Raises:
            ClientNotFoundError: Client not found in database
        """
        logger.info(f"Assembling context for client {client_id}")

        # Fetch all required data
        client = await self.client_repo.get_client(client_id)
        context = await self.client_repo.get_client_context(client_id)

        # Compute dynamic fields (never stored, always fresh)
        last_run_folder = await self._get_last_run_folder(client_id)
        posts_published = await self._count_published_articles(client_id)
        open_items_count = await self._count_open_items(client_id)

        # Format as markdown
        markdown = self._format_context(
            client=client,
            context=context,
            last_run_folder=last_run_folder,
            posts_published=posts_published,
            open_items_count=open_items_count,
        )

        logger.info(f"Context assembled for {client.name} ({len(markdown)} chars)")
        return markdown

    async def _get_last_run_folder(self, client_id: UUID) -> Optional[str]:
        """Get the most recent run folder slug for a client.

        Args:
            client_id: Client UUID

        Returns:
            Run folder slug (e.g., "Why_Wont_My_House_Cool_Down_2026-05") or None
        """
        # TODO: Query runs table for MAX(updated_at) WHERE client_id
        # SELECT run_folder FROM runs WHERE client_id = ? ORDER BY updated_at DESC LIMIT 1
        return None

    async def _count_published_articles(self, client_id: UUID) -> int:
        """Count published articles for a client.

        Args:
            client_id: Client UUID

        Returns:
            Count of published articles
        """
        # TODO: Query published_articles table
        # SELECT COUNT(*) FROM published_articles WHERE client_id = ?
        return 0

    async def _count_open_items(self, client_id: UUID) -> int:
        """Count open (unresolved) items for a client.

        Args:
            client_id: Client UUID

        Returns:
            Count of unresolved items (resolved=false)
        """
        # TODO: Query unresolved_items table
        # SELECT COUNT(*) FROM unresolved_items WHERE client_id = ? AND resolved = false
        return 0

    def _format_context(
        self,
        client: Client,
        context: Optional[dict],
        last_run_folder: Optional[str],
        posts_published: int,
        open_items_count: int,
    ) -> str:
        """Format assembled data as markdown CONTEXT.md equivalent.

        Args:
            client: Client object from database
            context: Client context object (next_planned_topic, engagement_notes, run_history_summary)
            last_run_folder: Most recent run folder slug
            posts_published: Count of published articles
            open_items_count: Count of open unresolved items

        Returns:
            Formatted markdown string
        """
        # Determine onboarding state label
        ref_files = context.get("onboarding_state", "new") if isinstance(context, dict) else "new"
        state_map = {
            "new": "New",
            "partial": "Partially Onboarded",
            "fully_onboarded": "Ready for Content Production",
        }
        state_label = state_map.get(ref_files, "Unknown")

        # Extract context fields (or provide defaults)
        if isinstance(context, dict):
            next_planned_topic = context.get("next_planned_topic") or "—"
            engagement_notes = context.get("engagement_notes") or "None"
            run_history_summary = context.get("run_history_summary") or "No runs yet"
        else:
            next_planned_topic = "—"
            engagement_notes = "None"
            run_history_summary = "No runs yet"

        # Build markdown
        lines = [
            "# Client Context",
            "",
            "## Engagement Status",
            "",
            f"**Client:** {client.name}",
            f"**Industry:** {client.industry or '—'}",
            f"**Service Area:** {client.service_area or '—'}",
            f"**Website:** {client.website_url or '—'}",
            f"**Onboarding State:** {state_label}",
            "",
            "## Engagement History",
            "",
            f"**Posts Published:** {posts_published}",
            f"**Last Run:** {last_run_folder or 'None'}",
            f"**Open Items:** {open_items_count if open_items_count > 0 else 'None'}",
            "",
            "## Planning",
            "",
            f"**Next Planned Topic:** {next_planned_topic}",
            "",
            "## Notes",
            "",
            f"{engagement_notes}",
            "",
            "## Run History Summary",
            "",
            f"{run_history_summary}",
            "",
            f"---",
            f"*Context assembled: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        ]

        return "\n".join(lines)
