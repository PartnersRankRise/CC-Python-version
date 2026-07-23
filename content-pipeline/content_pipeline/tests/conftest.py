# Created: Thursday Jul 23, 2026, 4:01 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 4:25 PM (UTC-6)

"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest


# Load .env at session start before any imports
def pytest_configure(config):
    """Load .env file before collecting tests."""
    from dotenv import load_dotenv
    
    # .env is at project root: CC-Python-version/.env
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        raise FileNotFoundError(f".env not found at {env_path}")


# Import test data fixture
pytest_plugins = ["content_pipeline.tests.fixtures.test_data"]

