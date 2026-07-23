# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Stage contract base class — abstract interface for all pipeline stages."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from content_pipeline.domain.run import Run
from content_pipeline.domain.stage import StageOutput
from content_pipeline.domain.enums import StageStatus


class StageContract(ABC):
    """Abstract base class for all pipeline stages.

    Every pipeline stage implements this interface. The execution order is fixed:
    check prerequisites → load context → build prompt → call LLM → parse output →
    validate → build handoff.
    """

    def __init__(
        self,
        repo: Any,
        llm: Any,
        parser: Any,
        tracker: Any,
    ) -> None:
        """Initialize stage contract with dependencies.

        Args:
            repo: Repository layer for database access
            llm: LLM provider instance
            parser: Parser for this stage's output format
            tracker: Unresolved item tracker
        """
        self._repo = repo
        self._llm = llm
        self._parser = parser
        self._tracker = tracker

    @property
    @abstractmethod
    def stage_number(self) -> int:
        """Stage number in pipeline (0-7 or 11 for SEOcial)."""
        pass

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Human-readable stage name (e.g., 'Research', 'Writing')."""
        pass

    @abstractmethod
    def _check_prerequisites(self, run: Run) -> None:
        """Check that all required predecessor outputs exist.

        Args:
            run: Run domain object

        Raises:
            MissingPrerequisiteError: Required predecessor output is missing
        """
        pass

    @abstractmethod
    def _load_context(self, run: Run) -> dict:
        """Load ONLY the files specified in this stage's Load Before Starting section.

        Args:
            run: Run domain object

        Returns:
            Context dict with loaded files and data
        """
        pass

    @abstractmethod
    def _build_prompt(self, run: Run, context: dict) -> tuple[str, str]:
        """Build system and user prompts for LLM.

        Args:
            run: Run domain object
            context: Context dict from _load_context

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        pass

    @abstractmethod
    def _parse_output(self, raw: str, run: Run) -> StageOutput:
        """Parse raw LLM output into StageOutput.

        Separate article content from appended sections (editorial notes,
        SEO annotations, etc.) and store in appropriate fields.

        Args:
            raw: Raw LLM completion text
            run: Run domain object

        Returns:
            Parsed StageOutput domain object
        """
        pass

    @abstractmethod
    def _validate_output(self, output: StageOutput, run: Run) -> list[str]:
        """Validate parsed output against quality gates.

        Args:
            output: Parsed StageOutput from _parse_output
            run: Run domain object

        Returns:
            List of quality gate failure descriptions. Empty list = all pass.
        """
        pass

    @abstractmethod
    def _build_handoff(
        self, run: Run, output: StageOutput, context: dict
    ) -> str:
        """Build handoff document for the next stage.

        Args:
            run: Run domain object
            output: Validated StageOutput
            context: Context dict from _load_context

        Returns:
            Handoff markdown content for next stage
        """
        pass

    async def run(self, run: Run) -> StageOutput:
        """Execute this stage in the standard pipeline order.

        Order: prerequisites → load context → build prompt → LLM complete →
        parse output → validate → handoff → save → return

        Args:
            run: Run domain object

        Returns:
            StageOutput with status COMPLETE (passed validation) or FAILED

        Raises:
            MissingPrerequisiteError: Prerequisites not met
            Any other domain exception (ValidationError, InternalTokenLeakError, etc.)
        """
        # 1. Check prerequisites
        self._check_prerequisites(run)

        # 2. Load context
        context = self._load_context(run)

        # 3. Build prompts
        system, user = self._build_prompt(run, context)

        # 4. Call LLM
        raw = await self._llm.complete(user, system=system)

        # 5. Parse output
        output = self._parse_output(raw, run)

        # 6. Validate output
        failures = self._validate_output(output, run)

        # If validation failed, mark output as FAILED and return
        if failures:
            output.status = StageStatus.FAILED
            output.quality_gate_results["failures"] = failures
            return output

        # 7. Build handoff for next stage
        output.handoff_content = self._build_handoff(run, output, context)

        # 8. Mark as complete
        output.status = StageStatus.COMPLETE

        # 9. Save to database (when repository implementation is ready)
        # self._repo.save(output)

        return output
