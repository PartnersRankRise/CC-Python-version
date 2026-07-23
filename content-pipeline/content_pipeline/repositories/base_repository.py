# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:55 PM (UTC-6)

"""Base repository class with Supabase client initialization."""

import os
from typing import Any, Optional


class BaseRepository:
    """Base repository providing Supabase client initialization."""

    def __init__(self) -> None:
        """Initialize Supabase client from environment variables."""
        supabase_url = os.getenv("SUPABASE_URL")
        # Try SERVICE_ROLE_KEY first (preferred for server), fall back to SERVICE_KEY
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
            )

        try:
            import supabase as supabase_module
            create_client = supabase_module.create_client
            self.supabase: Any = create_client(supabase_url, supabase_key)
        except (ImportError, AttributeError) as e:
            raise ImportError(
                "supabase library not installed or incorrect version. Run: pip install supabase"
            ) from e
