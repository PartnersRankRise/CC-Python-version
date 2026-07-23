# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:42 AM (UTC-6)

"""Tests for LLM provider implementations."""

import pytest
import os
import asyncio

from content_pipeline.llm.anthropic_provider import AnthropicProvider
from content_pipeline.llm.exceptions import LLMProviderNotConfiguredError


def test_anthropic_provider_complete():
    """Test AnthropicProvider.complete() with real API."""
    # Skip if API key not available
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    provider = AnthropicProvider()
    
    # Run async function
    response = asyncio.run(provider.complete(
        prompt="Say hello in one sentence.",
        max_tokens=100,
    ))
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert "hello" in response.lower() or "hi" in response.lower()


def test_anthropic_provider_complete_with_stream():
    """Test AnthropicProvider.complete_with_stream() with real API."""
    # Skip if API key not available
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    provider = AnthropicProvider()
    
    async def stream_test():
        chunks = []
        async for chunk in provider.complete_with_stream(
            prompt="Say hello in one sentence.",
            max_tokens=100,
        ):
            chunks.append(chunk)
        
        assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
        concatenated = "".join(chunks)
        assert len(concatenated) > 0
        assert "hello" in concatenated.lower() or "hi" in concatenated.lower()
    
    asyncio.run(stream_test())


def test_anthropic_provider_missing_api_key(monkeypatch):
    """Test AnthropicProvider raises error when API key missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    
    with pytest.raises(LLMProviderNotConfiguredError):
        AnthropicProvider()


def test_anthropic_provider_with_system_prompt():
    """Test AnthropicProvider.complete() with system prompt."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    provider = AnthropicProvider()
    
    response = asyncio.run(provider.complete(
        prompt="What is the capital of France?",
        system="You are a helpful geography assistant. Answer very briefly in one word.",
        max_tokens=50,
    ))
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Paris" in response or "paris" in response.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

