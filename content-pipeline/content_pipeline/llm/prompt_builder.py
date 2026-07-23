# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:42 AM (UTC-6)

"""Prompt builder — loads stage contracts and builds LLM prompts."""

import os
from pathlib import Path
from typing import Optional

from content_pipeline.llm.exceptions import LLMAPIError


class PromptBuilder:
    """Loads stage contracts and builds LLM prompts."""

    def __init__(self, contracts_dir: Optional[str] = None) -> None:
        """Initialize prompt builder.

        Args:
            contracts_dir: Directory containing stage contract files.
                If None, uses docs/stage_contracts/ relative to project root.
        """
        if contracts_dir is None:
            # Use docs/stage_contracts/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            contracts_dir = project_root / "docs" / "stage_contracts"

        self.contracts_dir = Path(contracts_dir)

    async def load_stage_contract(self, stage_name: str) -> str:
        """Load a stage contract by name.

        Args:
            stage_name: Stage name (e.g., "stage_1_research", "stage_5_seo")

        Returns:
            Stage contract markdown content

        Raises:
            FileNotFoundError: Contract file not found
            LLMAPIError: Error reading contract file
        """
        # Normalize stage name to filename
        contract_file = self.contracts_dir / f"{stage_name}.md"

        if not contract_file.exists():
            raise FileNotFoundError(
                f"Stage contract not found: {contract_file}"
            )

        try:
            with open(contract_file, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            raise LLMAPIError(f"Error reading contract file: {str(e)}") from e
