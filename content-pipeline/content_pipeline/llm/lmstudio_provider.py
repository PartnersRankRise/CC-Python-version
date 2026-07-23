# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""LM Studio LLM provider implementation."""

from typing import AsyncIterator

from content_pipeline.llm.base_provider import LLMProvider, ProviderType
from content_pipeline.llm.exceptions import LLMProviderNotConfiguredError


class LMStudioProvider(LLMProvider):
    """Pipeline LLM provider via self-hosted LM Studio.

    LM Studio serves an OpenAI-compatible REST API at localhost:1234.

    Prerequisites:
    - LM Studio running with a model loaded
    - Server started in LM Studio (local server tab)
    - Model name matches exactly what LM Studio reports

    Note: LM Studio's model identifier includes the full GGUF path.
    Check the LM Studio UI for the exact model identifier string.

    Best for: local development with GUI model management,
    experimenting with quantized models, offline operation.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:1234/v1",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> None:
        """Initialize LM Studio provider.

        Args:
            model: Model name (exact identifier from LM Studio UI)
            base_url: LM Studio API base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "openai library not installed. Run: pip install openai"
            )

        self._model = model
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key="lm-studio",
        )
        self._temperature = temperature
        self._max_tokens = max_tokens

    @property
    def provider_type(self) -> ProviderType:
        """Provider type identifier."""
        return ProviderType.LM_STUDIO

    @property
    def model_name(self) -> str:
        """Model name in use."""
        return self._model

    async def complete(
        self, prompt: str, system: str = "", **kwargs
    ) -> str:
        """Generate a completion using LM Studio.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters

        Returns:
            Complete response text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content

    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ) -> AsyncIterator[str]:
        """Generate a completion with streaming via LM Studio.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters

        Yields:
            Text delta chunks
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
