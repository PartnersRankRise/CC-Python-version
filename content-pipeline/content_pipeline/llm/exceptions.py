# Created: Thursday Jul 23, 2026, 11:42 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:42 AM (UTC-6)

"""Custom exceptions for LLM provider operations."""


class LLMProviderError(Exception):
    """Base exception for LLM provider operations."""
    pass


class LLMAPIError(LLMProviderError):
    """LLM API request failed."""
    pass


class LLMProviderNotConfiguredError(LLMProviderError):
    """Required LLM provider configuration is missing."""
    pass
