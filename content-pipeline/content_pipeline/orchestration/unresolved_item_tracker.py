# Created: Thursday Jul 23, 2026, 2:24 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:24 PM (UTC-6)

"""Unresolved item tracking across run stages."""

import logging
from typing import Any, Optional
from uuid import UUID

from content_pipeline.domain.client import UnresolvedItem

logger = logging.getLogger(__name__)


class UnresolvedItemTracker:
    """Track items that need resolution or human attention during a run.
    
    Items can be:
    - Blocking: halt execution until resolved
    - Non-blocking: carry forward for monitoring
    
    Each item has a source stage and optional resolution stage.
    """

    def __init__(self, repo: Any) -> None:
        """Initialize tracker with repository for persistence.
        
        Args:
            repo: Repository layer for database access
        """
        self._repo = repo

    async def add_item(
        self,
        run_id: UUID,
        description: str,
        blocks_run: bool,
        source_stage: int,
    ) -> UnresolvedItem:
        """Add a tracking item to a run.
        
        Args:
            run_id: Run UUID
            description: Item description
            blocks_run: If True, halts execution; if False, carries forward
            source_stage: Which stage created this item
            
        Returns:
            Created UnresolvedItem domain object
        """
        item = UnresolvedItem(
            description=description,
            blocks_run=blocks_run,
            source_stage=source_stage,
            resolved=False,
            resolved_at_stage=None,
        )
        
        logger.info(
            f"Added unresolved item to run {run_id}: "
            f"'{description}' (blocks={blocks_run}, source_stage={source_stage})"
        )
        
        # TODO: Persist to unresolved_items table when repo method exists
        # await self._repo.save_unresolved_item(run_id, item)
        
        return item

    async def resolve_item(
        self,
        run_id: UUID,
        description: str,
        resolved_at_stage: int,
    ) -> None:
        """Mark an item as resolved.
        
        Args:
            run_id: Run UUID
            description: Item description (for matching)
            resolved_at_stage: Which stage resolved this item
        """
        logger.info(
            f"Resolved item in run {run_id}: "
            f"'{description}' (resolved_at_stage={resolved_at_stage})"
        )
        
        # TODO: Update unresolved_items table
        # await self._repo.update_unresolved_item(run_id, description, resolved_at_stage)

    async def blocking_items(self, run_id: UUID) -> list[UnresolvedItem]:
        """Get items that block execution.
        
        Args:
            run_id: Run UUID
            
        Returns:
            List of UnresolvedItem objects where blocks_run=True and resolved=False
        """
        # TODO: Query unresolved_items WHERE run_id=? AND blocks_run=true AND resolved=false
        # items = await self._repo.get_blocking_items(run_id)
        logger.debug(f"Querying blocking items for run {run_id}")
        return []

    async def open_items(self, run_id: UUID) -> list[UnresolvedItem]:
        """Get all unresolved items in a run.
        
        Args:
            run_id: Run UUID
            
        Returns:
            List of UnresolvedItem objects where resolved=False
        """
        # TODO: Query unresolved_items WHERE run_id=? AND resolved=false
        # items = await self._repo.get_open_items(run_id)
        logger.debug(f"Querying open items for run {run_id}")
        return []

    async def for_handoff(self, run_id: UUID) -> str:
        """Format open items as handoff section for next stage.
        
        Args:
            run_id: Run UUID
            
        Returns:
            Markdown section with open items, or empty string if none
        """
        items = await self.open_items(run_id)
        
        if not items:
            return ""
        
        # Build handoff section
        lines = [
            "## Unresolved Items from Previous Stages",
            "",
        ]
        
        for i, item in enumerate(items, 1):
            blocking = "🔴 BLOCKS RUN" if item.blocks_run else "⚪ Monitored"
            lines.append(f"{i}. **{blocking}** (Stage {item.source_stage})")
            lines.append(f"   {item.description}")
            lines.append("")
        
        return "\n".join(lines)
