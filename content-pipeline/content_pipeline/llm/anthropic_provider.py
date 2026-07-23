# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Anthropic LLM provider implementation."""

import os
from typing import AsyncIterator, Optional

from content_pipeline.llm.base_provider import LLMProvider, ProviderType
from content_pipeline.llm.exceptions import LLMAPIError, LLMProviderNotConfiguredError


class AnthropicProvider(LLMProvider):
    """LLM provider using Anthropic API."""

    def __init__(self, model: Optional[str] = None) -> None:
        """Initialize Anthropic provider.

        Args:
            model: Model name (default: claude-sonnet-4-6)

        Raises:
            LLMProviderNotConfiguredError: ANTHROPIC_API_KEY not set
        """
        try:
            import anthropic
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "anthropic library not installed. Run: pip install anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMProviderNotConfiguredError(
                "ANTHROPIC_API_KEY environment variable not set"
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self._model = model or "claude-sonnet-4-6"

    @property
    def provider_type(self) -> ProviderType:
        """Provider type identifier."""
        return ProviderType.ANTHROPIC

    @property
    def model_name(self) -> str:
        """Model name in use."""
        return self._model

    async def complete(
        self, prompt: str, system: str = "", **kwargs
    ) -> str:
        """Generate a completion using Anthropic API.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Complete response text

        Raises:
            LLMAPIError: API request failed
        """
        try:
            import anthropic
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "anthropic library not installed"
            )

        messages = [{"role": "user", "content": prompt}]
        params = {
            "model": self._model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "messages": messages,
        }

        if system:
            params["system"] = system

        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]

        try:
            response = self.client.messages.create(**params)
            return response.content[0].text
        except anthropic.APIError as e:
            raise LLMAPIError(f"Anthropic API error: {str(e)}") from e

    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ) -> AsyncIterator[str]:
        """Generate a completion with streaming from Anthropic API.

        Yields text delta chunks as they arrive.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Yields:
            Text delta chunks

        Raises:
            LLMAPIError: API request failed
        """
        try:
            import anthropic
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "anthropic library not installed"
            )

        messages = [{"role": "user", "content": prompt}]
        params = {
            "model": self._model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "messages": messages,
        }

        if system:
            params["system"] = system

        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]

        try:
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        except anthropic.APIError as e:
            raise LLMAPIError(f"Anthropic API error: {str(e)}") from e
