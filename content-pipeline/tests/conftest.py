# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:42 AM (UTC-6)

"""Test fixtures and configuration."""

import pytest
import asyncio
import os
from pathlib import Path

# Load environment variables from .env at project root
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture
def test_uuid():
    """Generate a consistent UUID for testing."""
    from uuid import UUID
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def event_loop():
    """Provide event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


