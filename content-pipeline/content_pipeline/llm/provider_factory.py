# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""LLM provider factory — constructs correct provider from environment configuration."""

import os

from content_pipeline.llm.base_provider import LLMProvider, ProviderType
from content_pipeline.llm.anthropic_provider import AnthropicProvider
from content_pipeline.llm.openrouter_provider import OpenRouterProvider
from content_pipeline.llm.ollama_provider import OllamaProvider
from content_pipeline.llm.lmstudio_provider import LMStudioProvider
from content_pipeline.llm.exceptions import LLMProviderNotConfiguredError


class LLMProviderFactory:
    """Constructs the correct LLMProvider from environment configuration.

    LLM_PROVIDER env var controls which provider is used for pipeline stages.
    This is separate from gpt-researcher's SMART_LLM/FAST_LLM env vars,
    which control the research engine only.

    Valid values for LLM_PROVIDER:
      anthropic    → AnthropicProvider (default)
      openrouter   → OpenRouterProvider
      ollama       → OllamaProvider
      lm_studio    → LMStudioProvider

    Model is set via PIPELINE_SMART_MODEL and PIPELINE_FAST_MODEL env vars.
    Provider-specific vars (API keys, base URLs) follow each provider's convention.
    """

    @staticmethod
    def create_smart_provider() -> LLMProvider:
        """High-quality provider for complex tasks: writing, humanization, QA.

        Returns:
            LLMProvider instance for smart/complex tasks

        Raises:
            LLMProviderNotConfiguredError: Provider not configured or invalid
        """
        return LLMProviderFactory._create(
            provider_env="LLM_PROVIDER",
            model_env="PIPELINE_SMART_MODEL",
        )

    @staticmethod
    def create_fast_provider() -> LLMProvider:
        """Faster/cheaper provider for structured tasks: brief, SEO, onboarding.

        Returns:
            LLMProvider instance for fast/structured tasks

        Raises:
            LLMProviderNotConfiguredError: Provider not configured or invalid
        """
        return LLMProviderFactory._create(
            provider_env="LLM_PROVIDER",
            model_env="PIPELINE_FAST_MODEL",
        )

    @staticmethod
    def _create(provider_env: str, model_env: str) -> LLMProvider:
        """Create provider instance based on environment configuration.

        Args:
            provider_env: Environment variable name for provider type
            model_env: Environment variable name for model name

        Returns:
            LLMProvider instance

        Raises:
            ValueError: Unknown provider type
            LLMProviderNotConfiguredError: Provider library not installed
        """
        provider_type = os.environ.get(provider_env, "anthropic").lower()
        model = os.environ.get(model_env, "")

        if provider_type == "anthropic":
            return AnthropicProvider(
                model=model or "claude-sonnet-4-6"
            )
        elif provider_type == "openrouter":
            return OpenRouterProvider(
                model=model or "anthropic/claude-sonnet-4-5"
            )
        elif provider_type == "ollama":
            return OllamaProvider(
                model=model or "llama3.1:70b",
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                num_ctx=int(os.environ.get("OLLAMA_NUM_CTX", "8192")),
            )
        elif provider_type == "lm_studio":
            return LMStudioProvider(
                model=model or "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
                base_url=os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            )
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{provider_type}'. "
                f"Valid values: anthropic, openrouter, ollama, lm_studio"
            )
