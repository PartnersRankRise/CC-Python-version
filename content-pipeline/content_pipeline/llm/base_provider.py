# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from enum import Enum


class ProviderType(Enum):
    """LLM provider type enumeration."""
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self, prompt: str, system: str = "", **kwargs
    ) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: User-facing prompt/question
            system: Optional system prompt/instructions
            **kwargs: Provider-specific options

        Returns:
            Complete response text

        Raises:
            LLMAPIError: API request failed
            LLMProviderNotConfiguredError: Provider not properly configured
        """
        pass

    @abstractmethod
    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ) -> AsyncIterator[str]:
        """Generate a completion with streaming.

        Yields text delta chunks as they arrive from the LLM.

        Args:
            prompt: User-facing prompt/question
            system: Optional system prompt/instructions
            **kwargs: Provider-specific options

        Yields:
            Text delta chunks

        Raises:
            LLMAPIError: API request failed
            LLMProviderNotConfiguredError: Provider not properly configured
        """
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Provider type identifier."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model name in use."""
        pass
