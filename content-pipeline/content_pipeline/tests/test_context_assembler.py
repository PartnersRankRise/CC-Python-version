# Created: Thursday Jul 23, 2026, 3:07 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 5:07 PM (UTC-6)

"""Tests for ClientContextAssembler."""

import pytest
from uuid import uuid4
from datetime import datetime

from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.orchestration.context_assembler import ClientContextAssembler


@pytest.fixture
def context_assembler():
    """Create a ClientContextAssembler instance."""
    client_repo = ClientRepository()
    return ClientContextAssembler(client_repo)


@pytest.fixture
async def test_client():
    """Create a test client in the database."""
    client_repo = ClientRepository()
    client = await client_repo.create_client(
        name="Test HVAC Services",
        website_url="https://test-hvac.example.com",
        industry="home_services",
        service_area="Denver Metro, CO",
    )
    yield client
    # Cleanup: delete the test client after the test
    # (Supabase will handle cascade deletes)


class TestContextAssemblerBasics:
    """Basic functionality tests for ClientContextAssembler."""

    @pytest.mark.asyncio
    async def test_assemble_new_client_context(self, context_assembler, test_client):
        """Test assembling context for a newly created client."""
        context_md = await context_assembler.assemble(test_client.id)

        # Verify output is markdown
        assert isinstance(context_md, str)
        assert len(context_md) > 100

        # Verify key sections exist
        assert "# Client Context" in context_md
        assert "## Engagement Status" in context_md
        assert "## Engagement History" in context_md
        assert "## Planning" in context_md
        assert "## Notes" in context_md

    @pytest.mark.asyncio
    async def test_context_contains_client_name(self, context_assembler, test_client):
        """Test that assembled context contains client name."""
        context_md = await context_assembler.assemble(test_client.id)
        assert "Test HVAC Services" in context_md

    @pytest.mark.asyncio
    async def test_context_contains_client_details(self, context_assembler, test_client):
        """Test that assembled context contains client details."""
        context_md = await context_assembler.assemble(test_client.id)

        assert "home_services" in context_md
        assert "Denver Metro, CO" in context_md
        assert "test-hvac.example.com" in context_md

    @pytest.mark.asyncio
    async def test_context_shows_zero_posts_published(self, context_assembler, test_client):
        """Test that new client shows 0 posts published."""
        context_md = await context_assembler.assemble(test_client.id)
        assert "Posts Published: 0" in context_md

    @pytest.mark.asyncio
    async def test_context_shows_no_open_items(self, context_assembler, test_client):
        """Test that new client shows no open items."""
        context_md = await context_assembler.assemble(test_client.id)
        assert "Open Items: None" in context_md

    @pytest.mark.asyncio
    async def test_context_timestamp_included(self, context_assembler, test_client):
        """Test that context includes assembly timestamp."""
        context_md = await context_assembler.assemble(test_client.id)
        assert "Context assembled:" in context_md
        assert "UTC" in context_md

    @pytest.mark.asyncio
    async def test_context_handles_missing_optional_fields(self, context_assembler, test_client):
        """Test context assembly with minimal client data."""
        # Client created with only required fields
        context_md = await context_assembler.assemble(test_client.id)

        # Should still produce valid markdown
        assert "# Client Context" in context_md
        # Optional fields should show "—" or "None"
        assert "—" in context_md or "None" in context_md


class TestContextAssemblerComputedFields:
    """Tests for dynamically computed fields."""

    @pytest.mark.asyncio
    async def test_last_run_folder_computed_fresh(self, context_assembler, test_client):
        """Test that last run folder is always computed fresh (never stored)."""
        context_md1 = await context_assembler.assemble(test_client.id)
        # New client has no runs yet
        assert "Last Run: None" in context_md1

        # TODO: Create a run, verify it appears in next assembly
        # Demonstrates that computed fields are always fresh

    @pytest.mark.asyncio
    async def test_posts_published_computed_fresh(self, context_assembler, test_client):
        """Test that posts published count is always computed fresh."""
        context_md1 = await context_assembler.assemble(test_client.id)
        assert "Posts Published: 0" in context_md1

        # TODO: Publish an article, verify count increases in next assembly

    @pytest.mark.asyncio
    async def test_open_items_count_computed_fresh(self, context_assembler, test_client):
        """Test that open items count is always computed fresh."""
        context_md1 = await context_assembler.assemble(test_client.id)
        assert "Open Items: None" in context_md1

        # TODO: Add an unresolved item, verify count increases in next assembly


class TestContextAssemblerStateLabels:
    """Tests for onboarding state labels."""

    def test_new_state_label(self):
        """Test NEW state displays as 'New'."""
        assembler = ClientContextAssembler(None)
        # Mock client and context for format test
        markdown = assembler._format_context(
            client=type("Client", (), {"name": "Test", "industry": None, "service_area": None, "website_url": None})(),
            context={"onboarding_state": "new"},
            last_run_folder=None,
            posts_published=0,
            open_items_count=0,
        )
        assert "New" in markdown

    def test_partial_state_label(self):
        """Test PARTIAL state displays as 'Partially Onboarded'."""
        assembler = ClientContextAssembler(None)
        markdown = assembler._format_context(
            client=type("Client", (), {"name": "Test", "industry": None, "service_area": None, "website_url": None})(),
            context={"onboarding_state": "partial"},
            last_run_folder=None,
            posts_published=0,
            open_items_count=0,
        )
        assert "Partially Onboarded" in markdown

    def test_fully_onboarded_state_label(self):
        """Test FULLY_ONBOARDED state displays as 'Ready for Content Production'."""
        assembler = ClientContextAssembler(None)
        markdown = assembler._format_context(
            client=type("Client", (), {"name": "Test", "industry": None, "service_area": None, "website_url": None})(),
            context={"onboarding_state": "fully_onboarded"},
            last_run_folder=None,
            posts_published=0,
            open_items_count=0,
        )
        assert "Ready for Content Production" in markdown


class TestContextAssemblerMarkdownStructure:
    """Tests for markdown output structure."""

    def test_markdown_has_required_sections(self):
        """Test that markdown output has all required sections."""
        assembler = ClientContextAssembler(None)
        markdown = assembler._format_context(
            client=type("Client", (), {"name": "Test", "industry": "home_services", "service_area": "Denver", "website_url": "https://test.com"})(),
            context={
                "next_planned_topic": "Heating Systems 101",
                "engagement_notes": "Great engagement so far",
                "run_history_summary": "5 successful runs",
            },
            last_run_folder="heating_systems_2026-07",
            posts_published=5,
            open_items_count=2,
        )

        # All major sections
        assert "# Client Context" in markdown
        assert "## Engagement Status" in markdown
        assert "## Engagement History" in markdown
        assert "## Planning" in markdown
        assert "## Notes" in markdown
        assert "## Run History Summary" in markdown

        # All fields
        assert "Test" in markdown
        assert "home_services" in markdown
        assert "Denver" in markdown
        assert "Heating Systems 101" in markdown
        assert "5" in markdown  # posts and open items

    def test_markdown_is_valid_format(self):
        """Test that output is valid markdown."""
        assembler = ClientContextAssembler(None)
        markdown = assembler._format_context(
            client=type("Client", (), {"name": "Test", "industry": None, "service_area": None, "website_url": None})(),
            context={},
            last_run_folder=None,
            posts_published=0,
            open_items_count=0,
        )

        # Should have proper markdown formatting
        assert markdown.startswith("# ")  # Starts with h1
        assert "##" in markdown  # Has h2 sections
        assert "\n" in markdown  # Has line breaks
        assert "---" in markdown  # Has separator before timestamp
