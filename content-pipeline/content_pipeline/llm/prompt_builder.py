# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:50 PM (UTC-6)

"""Prompt builder — loads stage contracts and builds LLM prompts."""

import logging
from pathlib import Path
from typing import Optional

from content_pipeline.llm.exceptions import LLMAPIError

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Loads stage contracts and pipeline configs, builds LLM system prompts."""

    # Stage contract filenames (must exist in docs/stage_contracts/)
    STAGE_CONTRACTS = {
        "stage_0_onboarding": "stage0_onboarding_CONTEXT.md",
        "stage_1_1_run_init": "stage1_1_onboarded_CONTEXT.md",
        "stage_1_2_research": "stage1_2_Research_CONTEXT.md",
        "stage_2_brief": "stage2_brief_CONTEXT.md",
        "stage_3_writing": "stage3_writing_CONTEXT.md",
        "stage_4_humanization": "stage4_humanization_CONTEXT.md",
        "stage_5_seo": "stage5_seo_CONTEXT.md",
        "stage_6_qa": "stage6_qa_CONTEXT.md",
        "stage_7_blog_formatting": "stage7_blog-formatting_CONTEXT.md",
    }

    # Config files that apply globally (loaded once, cached)
    GLOBAL_CONFIGS = {
        "anti_ai_checklist": "anti-ai-checklist.md",
        "search_quality_rubric": "search-quality-rubric.md",
        "source_validation_framework": "source-validation-framework.md",
        "handoff_template": "handoff_template.md",
    }

    def __init__(
        self,
        stage_contracts_dir: Optional[str] = None,
        pipeline_config_dir: Optional[str] = None,
    ) -> None:
        """Initialize prompt builder.

        Args:
            stage_contracts_dir: Directory containing stage contract files.
                If None, uses docs/stage_contracts/ relative to project root.
            pipeline_config_dir: Directory containing pipeline config files.
                If None, uses docs/pipeline_config/ relative to project root.
        """
        project_root = Path(__file__).parent.parent.parent

        if stage_contracts_dir is None:
            stage_contracts_dir = project_root / "docs" / "stage_contracts"
        if pipeline_config_dir is None:
            pipeline_config_dir = project_root / "docs" / "pipeline_config"

        self.stage_contracts_dir = Path(stage_contracts_dir)
        self.pipeline_config_dir = Path(pipeline_config_dir)

        # Verify directories exist
        if not self.stage_contracts_dir.exists():
            raise ValueError(f"Stage contracts directory not found: {self.stage_contracts_dir}")
        if not self.pipeline_config_dir.exists():
            raise ValueError(f"Pipeline config directory not found: {self.pipeline_config_dir}")

        # Cache for loaded configs (read once, reuse)
        self._config_cache: dict[str, str] = {}

        logger.info(f"PromptBuilder initialized")
        logger.info(f"  Stage contracts: {self.stage_contracts_dir}")
        logger.info(f"  Pipeline config: {self.pipeline_config_dir}")

    async def load_stage_contract(self, stage_key: str) -> str:
        """Load a stage contract by stage key.

        Args:
            stage_key: Stage key from STAGE_CONTRACTS dict
                (e.g., "stage_0_onboarding", "stage_5_seo")

        Returns:
            Stage contract markdown content

        Raises:
            KeyError: Stage key not recognized
            FileNotFoundError: Contract file not found
            LLMAPIError: Error reading contract file
        """
        if stage_key not in self.STAGE_CONTRACTS:
            raise KeyError(
                f"Unknown stage key: {stage_key}. "
                f"Valid keys: {list(self.STAGE_CONTRACTS.keys())}"
            )

        filename = self.STAGE_CONTRACTS[stage_key]
        contract_file = self.stage_contracts_dir / filename

        if not contract_file.exists():
            raise FileNotFoundError(
                f"Stage contract not found: {contract_file}"
            )

        try:
            with open(contract_file, "r", encoding="utf-8") as f:
                content = f.read()
                logger.debug(f"Loaded stage contract: {filename}")
                return content
        except IOError as e:
            raise LLMAPIError(f"Error reading contract file {contract_file}: {str(e)}") from e

    async def load_config_file(self, config_key: str) -> str:
        """Load a pipeline config file (cached after first load).

        Args:
            config_key: Config key from GLOBAL_CONFIGS dict
                (e.g., "anti_ai_checklist", "search_quality_rubric")

        Returns:
            Config file markdown content

        Raises:
            KeyError: Config key not recognized
            FileNotFoundError: Config file not found
            LLMAPIError: Error reading config file
        """
        if config_key not in self.GLOBAL_CONFIGS:
            raise KeyError(
                f"Unknown config key: {config_key}. "
                f"Valid keys: {list(self.GLOBAL_CONFIGS.keys())}"
            )

        # Return cached version if available
        if config_key in self._config_cache:
            return self._config_cache[config_key]

        filename = self.GLOBAL_CONFIGS[config_key]
        config_file = self.pipeline_config_dir / filename

        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_file}"
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
                self._config_cache[config_key] = content
                logger.debug(f"Loaded and cached config: {filename}")
                return content
        except IOError as e:
            raise LLMAPIError(f"Error reading config file {config_file}: {str(e)}") from e

    async def build_system_prompt(
        self,
        stage_key: str,
        include_configs: Optional[list[str]] = None,
    ) -> str:
        """Build a complete system prompt for a stage.

        The system prompt includes:
        1. The stage contract (system instructions)
        2. Optional global configs (anti-AI checklist, quality rubrics, etc.)

        Args:
            stage_key: Stage key from STAGE_CONTRACTS dict
            include_configs: Optional list of config keys to include.
                If None, includes all applicable configs.

        Returns:
            Complete system prompt markdown
        """
        logger.info(f"Building system prompt for {stage_key}")

        # Load stage contract (always first)
        stage_contract = await self.load_stage_contract(stage_key)

        # If no specific configs requested, include all by default
        if include_configs is None:
            include_configs = list(self.GLOBAL_CONFIGS.keys())

        # Load and append configs
        configs_content = []
        for config_key in include_configs:
            try:
                config_content = await self.load_config_file(config_key)
                configs_content.append(config_content)
                logger.debug(f"Included config: {config_key}")
            except KeyError:
                logger.warning(f"Config key not recognized: {config_key}")
            except FileNotFoundError:
                logger.warning(f"Config file not found: {config_key}")

        # Combine: stage contract first, then configs
        if configs_content:
            system_prompt = "\n\n" + "="*60 + "\n" + "\n\n".join(
                [stage_contract] + configs_content
            )
        else:
            system_prompt = stage_contract

        logger.info(f"System prompt built for {stage_key} ({len(system_prompt)} chars)")
        return system_prompt
