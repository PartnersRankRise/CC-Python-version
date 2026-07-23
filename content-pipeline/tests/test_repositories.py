# Created: Thursday Jul 23, 2026, 1:53 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:53 PM (UTC-6)

"""Integration tests for repository layer — client repository operations."""

import pytest
from uuid import UUID

from content_pipeline.domain.client import Client, ClientReferenceFiles
from content_pipeline.domain.enums import ClientState
from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.repositories.exceptions import ClientNotFoundError


@pytest.fixture
async def client_repo():
    """Provide a ClientRepository instance for testing."""
    return ClientRepository()


@pytest.fixture
async def cleanup_test_clients(client_repo):
    """Cleanup test clients after test completes."""
    test_clients = []
    yield test_clients
    for client_id in test_clients:
        try:
            client_repo.supabase.table("clients").delete().eq("id", str(client_id)).execute()
            client_repo.supabase.table("client_reference_files").delete().eq("client_id", str(client_id)).execute()
            client_repo.supabase.table("client_contexts").delete().eq("client_id", str(client_id)).execute()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_create_and_retrieve_client(client_repo, cleanup_test_clients):
    """Test creating a client, saving it, and retrieving it."""
    # Create a test client
    created = await client_repo.create_client(
        name="TEST_ClientRepo_Basic",
        website_url="https://test.example.com",
        industry="home_services",
        service_area="Colorado",
    )
    cleanup_test_clients.append(created.id)

    assert created.name == "TEST_ClientRepo_Basic"
    assert created.website_url == "https://test.example.com"
    assert created.industry == "home_services"
    assert created.service_area == "Colorado"

    # Retrieve it by ID
    retrieved = await client_repo.get_client(created.id)

    assert retrieved.id == created.id
    assert retrieved.name == created.name
    assert retrieved.website_url == created.website_url
    assert retrieved.industry == created.industry
    assert retrieved.service_area == created.service_area


@pytest.mark.asyncio
async def test_get_nonexistent_client_raises_error(client_repo):
    """Test that retrieving a nonexistent client raises ClientNotFoundError."""
    fake_id = UUID("00000000-0000-0000-0000-000000000000")
    with pytest.raises(ClientNotFoundError):
        await client_repo.get_client(fake_id)


@pytest.mark.asyncio
async def test_save_reference_files_state_detection(client_repo, cleanup_test_clients):
    """Test saving reference files with state detection (NEW -> PARTIAL -> FULLY_ONBOARDED)."""
    # Create a client
    client = await client_repo.create_client(name="TEST_RefFiles_States")
    cleanup_test_clients.append(client.id)

    # Test 1: NEW state — no files yet
    files = await client_repo.get_reference_files(client.id)
    assert files.style_reference_card is None
    assert files.audience_profile is None
    assert files.brand_notes is None

    # Test 2: PARTIAL state — only style reference card
    files.style_reference_card = "# Style Reference Card\n\nPrimary: #1B3D6F"
    await client_repo.save_reference_files(client.id, files)

    # Retrieve and verify state
    stored = await client_repo.get_reference_files(client.id)
    assert stored.style_reference_card == "# Style Reference Card\n\nPrimary: #1B3D6F"
    assert stored.audience_profile is None
    assert stored.brand_notes is None

    # Test 3: FULLY_ONBOARDED state — all three files
    files.audience_profile = "# Audience Profile\n\nTarget: SMBs"
    files.brand_notes = "# Brand Notes\n\n6 sections..."
    await client_repo.save_reference_files(client.id, files)

    stored = await client_repo.get_reference_files(client.id)
    assert stored.style_reference_card == "# Style Reference Card\n\nPrimary: #1B3D6F"
    assert stored.audience_profile == "# Audience Profile\n\nTarget: SMBs"
    assert stored.brand_notes == "# Brand Notes\n\n6 sections..."


@pytest.mark.asyncio
async def test_save_reference_files_with_brand_colors(client_repo, cleanup_test_clients):
    """Test saving reference files with parsed brand colors as JSONB."""
    client = await client_repo.create_client(name="TEST_RefFiles_Colors")
    cleanup_test_clients.append(client.id)

    files = ClientReferenceFiles(
        style_reference_card="# Style Card",
        brand_colors={
            "primary": "#1B3D6F",
            "primary_2": "#1E4F8A",
            "primary_soft": "#EEF3FA",
            "primary_glow": "rgba(27, 61, 111, 0.08)",
            "primary_rgb": "27, 61, 111",
            "accent": "#E8762B",
            "accent_2": "#D4621E",
            "accent_soft": "#FDF1E8",
            "accent_rgb": "232, 118, 43",
            "ink": "#1C1C1A",
            "line_strong": "rgba(27, 61, 111, 0.22)",
        },
    )
    await client_repo.save_reference_files(client.id, files)

    stored = await client_repo.get_reference_files(client.id)
    assert stored.brand_colors["primary"] == "#1B3D6F"
    assert stored.brand_colors["primary_rgb"] == "27, 61, 111"
    assert stored.brand_colors["accent_rgb"] == "232, 118, 43"
    # Verify no # prefix on RGB values
    assert not stored.brand_colors["primary_rgb"].startswith("#")
    assert not stored.brand_colors["accent_rgb"].startswith("#")


@pytest.mark.asyncio
async def test_save_and_retrieve_client_context(client_repo, cleanup_test_clients):
    """Test saving and retrieving client engagement context."""
    client = await client_repo.create_client(name="TEST_ClientContext")
    cleanup_test_clients.append(client.id)

    context = {
        "engagement_notes": "Active client, regular updates",
        "last_run_date": "2026-07-20",
        "posts_published": 15,
        "approved_topics": ["SEO", "Home Services"],
    }
    await client_repo.save_client_context(client.id, context)

    retrieved = await client_repo.get_client_context(client.id)
    assert retrieved == context
    assert retrieved["engagement_notes"] == "Active client, regular updates"
    assert retrieved["posts_published"] == 15


@pytest.mark.asyncio
async def test_get_nonexistent_client_context_returns_none(client_repo):
    """Test that retrieving nonexistent context returns None."""
    fake_id = UUID("00000000-0000-0000-0000-000000000000")
    result = await client_repo.get_client_context(fake_id)
    assert result is None


@pytest.mark.asyncio
async def test_list_clients(client_repo, cleanup_test_clients):
    """Test listing all clients."""
    # Create 3 test clients
    for i in range(3):
        client = await client_repo.create_client(name=f"TEST_List_{i}")
        cleanup_test_clients.append(client.id)

    clients = await client_repo.list_clients()
    assert len(clients) > 0
    # Verify at least our test clients exist
    test_names = {c.name for c in clients if c.name.startswith("TEST_List_")}
    assert len(test_names) >= 3
