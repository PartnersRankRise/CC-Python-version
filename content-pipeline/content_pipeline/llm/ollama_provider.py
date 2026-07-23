# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Ollama LLM provider implementation via LangChain."""

import os
from typing import AsyncIterator

from content_pipeline.llm.base_provider import LLMProvider, ProviderType
from content_pipeline.llm.exceptions import LLMProviderNotConfiguredError


class OllamaProvider(LLMProvider):
    """Pipeline LLM provider via self-hosted Ollama.

    Prerequisites:
    - Ollama running: `ollama serve`
    - Model pulled: `ollama pull llama3.1:70b`
    - OLLAMA_BASE_URL set (default: http://localhost:11434)

    Best for: local development, privacy-sensitive content,
    cost-free iteration on prompts.

    Caveat: Context window and instruction-following quality varies
    significantly by model. The pipeline's quality gates may need
    looser tolerances for some local models.
    """

    def __init__(
        self,
        model: str,
        base_url: str = None,
        temperature: float = 0.7,
        num_ctx: int = 8192,
    ) -> None:
        """Initialize Ollama provider.

        Args:
            model: Model name
            base_url: Ollama base URL (default from OLLAMA_BASE_URL or localhost:11434)
            temperature: Sampling temperature
            num_ctx: Context window size
        """
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "langchain-ollama not installed. Run: pip install langchain-ollama"
            )

        self._model = model
        self._client = ChatOllama(
            model=model,
            base_url=base_url or os.environ.get(
                "OLLAMA_BASE_URL", "http://localhost:11434"
            ),
            temperature=temperature,
            num_ctx=num_ctx,
        )

    @property
    def provider_type(self) -> ProviderType:
        """Provider type identifier."""
        return ProviderType.OLLAMA

    @property
    def model_name(self) -> str:
        """Model name in use."""
        return self._model

    async def complete(
        self, prompt: str, system: str = "", **kwargs
    ) -> str:
        """Generate a completion using Ollama.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters

        Returns:
            Complete response text
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        response = await self._client.ainvoke(messages)
        return response.content

    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ) -> AsyncIterator[str]:
        """Generate a completion with streaming via Ollama.

        Args:
            prompt: User prompt
            system: System instructions
            **kwargs: Additional parameters

        Yields:
            Text delta chunks
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self._client.astream(messages):
            if chunk.content:
                yield chunk.content
