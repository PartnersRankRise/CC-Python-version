# Created: Thursday Jul 23, 2026, 2:50 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:50 PM (UTC-6)

"""Tests for PromptBuilder — stage contracts and config loading."""

import pytest
from pathlib import Path

from content_pipeline.llm.prompt_builder import PromptBuilder


@pytest.fixture
def prompt_builder():
    """Create a PromptBuilder instance."""
    return PromptBuilder()


class TestPromptBuilderBasics:
    """Basic functionality tests for PromptBuilder."""

    @pytest.mark.asyncio
    async def test_init_default_paths(self):
        """Test initialization with default paths."""
        pb = PromptBuilder()
        assert pb.stage_contracts_dir.exists()
        assert pb.pipeline_config_dir.exists()

    @pytest.mark.asyncio
    async def test_init_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        stage_dir = tmp_path / "stages"
        config_dir = tmp_path / "config"
        stage_dir.mkdir()
        config_dir.mkdir()

        pb = PromptBuilder(
            stage_contracts_dir=str(stage_dir),
            pipeline_config_dir=str(config_dir),
        )
        assert pb.stage_contracts_dir == stage_dir
        assert pb.pipeline_config_dir == config_dir

    @pytest.mark.asyncio
    async def test_init_missing_stage_dir(self, tmp_path):
        """Test initialization fails when stage contracts dir missing."""
        with pytest.raises(ValueError, match="Stage contracts directory not found"):
            PromptBuilder(stage_contracts_dir=str(tmp_path / "nonexistent"))

    @pytest.mark.asyncio
    async def test_init_missing_config_dir(self, tmp_path):
        """Test initialization fails when pipeline config dir missing."""
        stage_dir = tmp_path / "stages"
        stage_dir.mkdir()

        with pytest.raises(ValueError, match="Pipeline config directory not found"):
            PromptBuilder(
                stage_contracts_dir=str(stage_dir),
                pipeline_config_dir=str(tmp_path / "nonexistent"),
            )


class TestStageContractLoading:
    """Tests for loading stage contracts."""

    @pytest.mark.asyncio
    async def test_load_all_stage_contracts(self, prompt_builder):
        """Test loading all 9 stage contracts."""
        for stage_key in prompt_builder.STAGE_CONTRACTS.keys():
            contract = await prompt_builder.load_stage_contract(stage_key)
            assert len(contract) > 100, f"Stage {stage_key} contract is too short"
            assert isinstance(contract, str)

    @pytest.mark.asyncio
    async def test_load_stage_onboarding(self, prompt_builder):
        """Test loading stage 0 onboarding contract."""
        contract = await prompt_builder.load_stage_contract("stage_0_onboarding")
        assert len(contract) > 1000
        assert "onboard" in contract.lower() or "client" in contract.lower()

    @pytest.mark.asyncio
    async def test_load_stage_research(self, prompt_builder):
        """Test loading stage 1.2 research contract."""
        contract = await prompt_builder.load_stage_contract("stage_1_2_research")
        assert len(contract) > 1000
        assert "research" in contract.lower()

    @pytest.mark.asyncio
    async def test_load_stage_seo(self, prompt_builder):
        """Test loading stage 5 SEO contract."""
        contract = await prompt_builder.load_stage_contract("stage_5_seo")
        assert len(contract) > 1000
        assert "seo" in contract.lower() or "keyword" in contract.lower()

    @pytest.mark.asyncio
    async def test_load_nonexistent_stage(self, prompt_builder):
        """Test loading nonexistent stage raises KeyError."""
        with pytest.raises(KeyError):
            await prompt_builder.load_stage_contract("stage_99_invalid")

    @pytest.mark.asyncio
    async def test_load_missing_stage_file(self, prompt_builder, tmp_path, monkeypatch):
        """Test loading missing stage file raises FileNotFoundError."""
        # Create empty stage contracts dir
        monkeypatch.setattr(
            prompt_builder, "stage_contracts_dir", tmp_path / "empty"
        )
        (tmp_path / "empty").mkdir()

        with pytest.raises(FileNotFoundError):
            await prompt_builder.load_stage_contract("stage_0_onboarding")


class TestConfigFileLoading:
    """Tests for loading pipeline config files."""

    @pytest.mark.asyncio
    async def test_load_all_config_files(self, prompt_builder):
        """Test loading all 4 config files."""
        for config_key in prompt_builder.GLOBAL_CONFIGS.keys():
            config = await prompt_builder.load_config_file(config_key)
            assert len(config) > 100, f"Config {config_key} is too short"
            assert isinstance(config, str)

    @pytest.mark.asyncio
    async def test_load_anti_ai_checklist(self, prompt_builder):
        """Test loading anti-AI checklist."""
        config = await prompt_builder.load_config_file("anti_ai_checklist")
        assert len(config) > 1000
        assert "ai" in config.lower()

    @pytest.mark.asyncio
    async def test_load_search_quality_rubric(self, prompt_builder):
        """Test loading search quality rubric."""
        config = await prompt_builder.load_config_file("search_quality_rubric")
        assert len(config) > 1000
        assert "quality" in config.lower() or "rubric" in config.lower()

    @pytest.mark.asyncio
    async def test_load_source_validation_framework(self, prompt_builder):
        """Test loading source validation framework."""
        config = await prompt_builder.load_config_file("source_validation_framework")
        assert len(config) > 1000
        assert "source" in config.lower() or "validation" in config.lower()

    @pytest.mark.asyncio
    async def test_config_caching(self, prompt_builder):
        """Test that config files are cached after first load."""
        # First load
        config1 = await prompt_builder.load_config_file("anti_ai_checklist")
        assert len(prompt_builder._config_cache) == 1

        # Second load should use cache
        config2 = await prompt_builder.load_config_file("anti_ai_checklist")
        assert config1 == config2
        assert len(prompt_builder._config_cache) == 1

    @pytest.mark.asyncio
    async def test_load_nonexistent_config(self, prompt_builder):
        """Test loading nonexistent config raises KeyError."""
        with pytest.raises(KeyError):
            await prompt_builder.load_config_file("config_invalid")


class TestSystemPromptBuilding:
    """Tests for building complete system prompts."""

    @pytest.mark.asyncio
    async def test_build_system_prompt_defaults(self, prompt_builder):
        """Test building system prompt includes all configs by default."""
        prompt = await prompt_builder.build_system_prompt("stage_1_2_research")
        assert len(prompt) > 30000  # Should include stage + all configs
        assert "anti" in prompt.lower() or "ai" in prompt.lower()

    @pytest.mark.asyncio
    async def test_build_system_prompt_selective_configs(self, prompt_builder):
        """Test building system prompt with selective configs."""
        prompt = await prompt_builder.build_system_prompt(
            "stage_1_2_research",
            include_configs=["anti_ai_checklist"],
        )
        assert len(prompt) > 15000
        assert len(prompt) < 50000  # Smaller than with all configs

    @pytest.mark.asyncio
    async def test_build_system_prompt_all_stages(self, prompt_builder):
        """Test building system prompts for all stages."""
        for stage_key in prompt_builder.STAGE_CONTRACTS.keys():
            prompt = await prompt_builder.build_system_prompt(stage_key)
            assert len(prompt) > 10000, f"Prompt for {stage_key} is too short"

    @pytest.mark.asyncio
    async def test_system_prompt_starts_with_stage_contract(self, prompt_builder):
        """Test system prompt includes stage contract content."""
        stage_contract = await prompt_builder.load_stage_contract("stage_3_writing")
        system_prompt = await prompt_builder.build_system_prompt("stage_3_writing")

        # Stage contract should be included in system prompt (after separator)
        # Extract first 200 chars to account for separator lines
        assert stage_contract[:100] in system_prompt


class TestPromptBuilderStateDictionaries:
    """Tests for PromptBuilder state dictionaries."""

    def test_stage_contracts_dict(self, prompt_builder):
        """Test STAGE_CONTRACTS dictionary structure."""
        assert isinstance(prompt_builder.STAGE_CONTRACTS, dict)
        assert len(prompt_builder.STAGE_CONTRACTS) == 9
        assert "stage_0_onboarding" in prompt_builder.STAGE_CONTRACTS
        assert "stage_7_blog_formatting" in prompt_builder.STAGE_CONTRACTS

    def test_global_configs_dict(self, prompt_builder):
        """Test GLOBAL_CONFIGS dictionary structure."""
        assert isinstance(prompt_builder.GLOBAL_CONFIGS, dict)
        assert len(prompt_builder.GLOBAL_CONFIGS) == 4
        assert "anti_ai_checklist" in prompt_builder.GLOBAL_CONFIGS
        assert "source_validation_framework" in prompt_builder.GLOBAL_CONFIGS
