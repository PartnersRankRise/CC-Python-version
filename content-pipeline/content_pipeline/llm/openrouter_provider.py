# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""OpenRouter LLM provider implementation via LangChain."""

from typing import AsyncIterator

from content_pipeline.llm.base_provider import LLMProvider, ProviderType
from content_pipeline.llm.exceptions import LLMProviderNotConfiguredError


class OpenRouterProvider(LLMProvider):
    """Pipeline LLM provider via OpenRouter.

    OpenRouter gives access to Anthropic, Google, Meta, Mistral, and more
    through a single API key and endpoint.

    Recommended model assignments:
      SMART tasks (Stage 3 Writing, Stage 4 Humanization, Stage 6 QA):
        anthropic/claude-sonnet-4-5
      FAST tasks (Stage 5 SEO audits, Stage 2 Brief structure):
        google/gemini-2.0-flash-001
    """

    def __init__(
        self, model: str, temperature: float = 0.7, max_tokens: int = 8192
    ) -> None:
        """Initialize OpenRouter provider.

        Args:
            model: Model identifier (e.g., "anthropic/claude-sonnet-4-5")
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        try:
            from langchain_openrouter import ChatOpenRouter
        except ImportError:
            raise LLMProviderNotConfiguredError(
                "langchain-openrouter not installed. Run: pip install langchain-openrouter"
            )

        self._model = model
        self._client = ChatOpenRouter(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=2,
            openrouter_provider={
                "data_collection": "deny",
            },
        )

    @property
    def provider_type(self) -> ProviderType:
        """Provider type identifier."""
        return ProviderType.OPENROUTER

    @property
    def model_name(self) -> str:
        """Model name in use."""
        return self._model

    async def complete(
        self, prompt: str, system: str = "", **kwargs
    ) -> str:
        """Generate a completion using OpenRouter.

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
        """Generate a completion with streaming via OpenRouter.

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
