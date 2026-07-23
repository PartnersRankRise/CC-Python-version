# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Stage output repository — CRUD operations for stage outputs and related data."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.stage import StageOutput, QAResult, SEOAnnotation, QAIssue
from content_pipeline.domain.enums import StageStatus
from content_pipeline.repositories.base_repository import BaseRepository
from content_pipeline.repositories.exceptions import StageOutputNotFoundError


class StageOutputRepository(BaseRepository):
    """Repository for stage output data access."""

    async def create_stage_output(
        self,
        run_id: UUID,
        stage_number: int,
        stage_name: str,
    ) -> StageOutput:
        """Create a new stage output record.

        Args:
            run_id: Run UUID
            stage_number: Stage number (0-7 or 11)
            stage_name: Human-readable stage name

        Returns:
            Created StageOutput domain object

        Raises:
            RunNotFoundError: Run not found (from domain)
        """
        raise NotImplementedError

    async def get_stage_output(self, output_id: UUID) -> StageOutput:
        """Retrieve a stage output by ID.

        Args:
            output_id: StageOutput UUID

        Returns:
            StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError

    async def get_latest_stage_output(self, run_id: UUID, stage_number: int) -> Optional[StageOutput]:
        """Retrieve the latest output for a given run and stage.

        Args:
            run_id: Run UUID
            stage_number: Stage number

        Returns:
            Latest StageOutput domain object or None if not found

        Raises:
            RunNotFoundError: Run not found (from domain)
        """
        raise NotImplementedError

    async def update_stage_output_status(
        self, output_id: UUID, status: StageStatus, error_message: Optional[str] = None
    ) -> StageOutput:
        """Update stage output status (RUNNING, COMPLETE, FAILED).

        Args:
            output_id: StageOutput UUID
            status: New StageStatus
            error_message: Error message if FAILED

        Returns:
            Updated StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError

    async def save_stage_output_content(
        self,
        output_id: UUID,
        article_content: Optional[str] = None,
        editorial_note: Optional[str] = None,
        handoff_content: Optional[str] = None,
    ) -> StageOutput:
        """Save article content to a stage output.

        Args:
            output_id: StageOutput UUID
            article_content: Reader-facing article content
            editorial_note: Stage 4 editorial note (never passed downstream)
            handoff_content: Handoff brief for next stage

        Returns:
            Updated StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError

    async def save_seo_annotation(
        self, output_id: UUID, annotation: SEOAnnotation
    ) -> StageOutput:
        """Save SEO annotation to a Stage 5 output.

        Args:
            output_id: StageOutput UUID
            annotation: SEOAnnotation domain object

        Returns:
            Updated StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError

    async def save_qa_result(self, output_id: UUID, qa_result: QAResult) -> StageOutput:
        """Save QA result to a Stage 6 output.

        Args:
            output_id: StageOutput UUID
            qa_result: QAResult domain object

        Returns:
            Updated StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError

    async def list_stage_outputs_for_run(self, run_id: UUID) -> list[StageOutput]:
        """List all stage outputs for a run in order.

        Args:
            run_id: Run UUID

        Returns:
            List of StageOutput domain objects ordered by stage_number and attempt

        Raises:
            RunNotFoundError: Run not found (from domain)
        """
        raise NotImplementedError

    async def get_output_by_stage_and_attempt(
        self, run_id: UUID, stage_number: int, attempt: int
    ) -> StageOutput:
        """Retrieve a specific stage output by run, stage, and attempt number.

        Args:
            run_id: Run UUID
            stage_number: Stage number
            attempt: Attempt number

        Returns:
            StageOutput domain object

        Raises:
            StageOutputNotFoundError: Stage output not found
        """
        raise NotImplementedError
