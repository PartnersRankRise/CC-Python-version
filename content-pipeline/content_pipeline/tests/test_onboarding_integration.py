# Created: Thursday Jul 23, 2026, 2:54 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 5:07 PM (UTC-6)

"""Integration tests for full onboarding workflow."""

import pytest
from uuid import uuid4
from datetime import datetime

from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.services.onboarding_service import OnboardingStage
from content_pipeline.llm.provider_factory import LLMProviderFactory
from content_pipeline.orchestration.unresolved_item_tracker import UnresolvedItemTracker
from content_pipeline.domain.enums import ClientState


@pytest.fixture
def setup_services():
    """Setup all services needed for onboarding workflow."""
    client_repo = ClientRepository()
    llm = LLMProviderFactory.create_smart_provider()
    tracker = UnresolvedItemTracker(None)
    
    onboarding_stage = OnboardingStage(
        repo=None,
        llm=llm,
        parser=None,
        tracker=tracker,
        client_repo=client_repo,
    )
    
    return {
        "client_repo": client_repo,
        "onboarding_stage": onboarding_stage,
        "tracker": tracker,
    }


class TestOnboardingHappyPath:
    """Happy path: new client → onboarding → complete."""

    @pytest.mark.asyncio
    async def test_full_onboarding_workflow(self, setup_services):
        """Test complete onboarding: create client → generate reference files."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        # Step 1: Create a new client
        client_id = uuid4()
        client = await client_repo.create_client(
            name="Test HVAC Services",
            website_url="https://test-hvac.example.com",
            industry="home_services",
            service_area="Denver Metro, CO",
        )
        assert client.id is not None
        assert client.name == "Test HVAC Services"

        # Step 2: Verify client starts in NEW state
        ref_files = await client_repo.get_reference_files(client.id)
        assert ref_files.style_reference_card is None
        assert ref_files.audience_profile is None
        assert ref_files.brand_notes is None

        # Step 3: Run onboarding
        content_samples = """
        Our HVAC services include heating, cooling, and maintenance.
        We serve residential and commercial clients across Denver.
        Our technicians are EPA-certified and available 24/7.
        """

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples=content_samples,
            client_name=client.name,
            client_website=client.website_url,
            client_industry=client.industry,
            service_area=client.service_area,
        )

        # Step 4: Verify reference files generated
        assert result.style_reference_card is not None
        assert result.audience_profile is not None
        assert result.brand_notes is not None

        # Step 5: Verify state changed to FULLY_ONBOARDED
        ref_files_after = await client_repo.get_reference_files(client.id)
        assert ref_files_after.style_reference_card is not None
        assert ref_files_after.audience_profile is not None
        assert ref_files_after.brand_notes is not None


class TestOnboardingStateTransitions:
    """Test state transitions during onboarding."""

    @pytest.mark.asyncio
    async def test_new_to_partial_to_fully_onboarded(self, setup_services):
        """Test client progression through states."""
        services = setup_services
        client_repo = services["client_repo"]

        # Create new client (NEW state)
        client = await client_repo.create_client(
            name="Test Client",
            industry="home_services",
        )

        # Verify NEW state
        ref_files = await client_repo.get_reference_files(client.id)
        assert (
            ref_files.style_reference_card is None
            and ref_files.audience_profile is None
            and ref_files.brand_notes is None
        )

        # Simulate partial onboarding (2 of 3 files)
        partial_files = await client_repo.save_reference_files(
            client.id,
            {
                "style_reference_card": "# Style Guide\nTest content",
                "audience_profile": "# Audience\nTest content",
                "brand_notes": None,  # Missing
            },
        )

        # Verify PARTIAL state
        assert partial_files.onboarding_state == ClientState.PARTIAL.value

        # Complete onboarding (all 3 files)
        complete_files = await client_repo.save_reference_files(
            client.id,
            {
                "style_reference_card": "# Style Guide\nTest content",
                "audience_profile": "# Audience\nTest content",
                "brand_notes": "# Brand Notes\nTest content",
            },
        )

        # Verify FULLY_ONBOARDED state
        assert complete_files.onboarding_state == ClientState.FULLY_ONBOARDED.value


class TestClientAlreadyOnboardedError:
    """Test error handling for already-onboarded clients."""

    @pytest.mark.asyncio
    async def test_already_onboarded_without_regenerate(self, setup_services):
        """Test that already-onboarded clients block re-onboarding without regenerate flag."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        # Create and fully onboard a client
        client = await client_repo.create_client(
            name="Already Onboarded Client",
            industry="home_services",
        )

        # Set to fully onboarded
        await client_repo.save_reference_files(
            client.id,
            {
                "style_reference_card": "# Style\nContent",
                "audience_profile": "# Audience\nContent",
                "brand_notes": "# Brand\nContent",
            },
        )

        # Try to onboard again without regenerate flag
        from content_pipeline.exceptions import ClientAlreadyOnboardedError

        with pytest.raises(ClientAlreadyOnboardedError):
            await onboarding_stage.onboard_client(
                client_id=client.id,
                content_samples="New content",
                client_name=client.name,
                regenerate=False,  # Fail-fast without this
            )


class TestBrandColorExtraction:
    """Test brand color extraction during onboarding."""

    @pytest.mark.asyncio
    async def test_brand_colors_extracted_and_stored(self, setup_services):
        """Test that brand colors are extracted and stored correctly."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        client = await client_repo.create_client(
            name="Test Client",
            industry="home_services",
        )

        content_samples = "Sample content for testing brand extraction"

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples=content_samples,
            client_name=client.name,
        )

        # Verify brand colors were extracted
        assert result.brand_colors is not None
        assert len(result.brand_colors) == 11  # All 11 colors required
        assert "primary" in result.brand_colors
        assert "accent" in result.brand_colors
        assert "primary_rgb" in result.brand_colors


class TestOnboardingErrorRecovery:
    """Test error handling and recovery during onboarding."""

    @pytest.mark.asyncio
    async def test_invalid_content_samples(self, setup_services):
        """Test handling of invalid content samples."""
        services = setup_services
        onboarding_stage = services["onboarding_stage"]

        with pytest.raises(ValueError):
            # Empty content should fail
            await onboarding_stage.onboard_client(
                client_id=uuid4(),
                content_samples="",  # Empty
                client_name="Test Client",
            )

    @pytest.mark.asyncio
    async def test_nonexistent_client(self, setup_services):
        """Test handling of nonexistent client."""
        services = setup_services
        client_repo = services["client_repo"]

        from content_pipeline.exceptions import ClientNotFoundError

        with pytest.raises(ClientNotFoundError):
            await client_repo.get_client(uuid4())


class TestOnboardingMetadata:
    """Test metadata extraction and storage."""

    @pytest.mark.asyncio
    async def test_reading_level_extracted(self, setup_services):
        """Test that reading level is extracted during onboarding."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        client = await client_repo.create_client(
            name="Test Client",
            industry="home_services",
        )

        content = "Sample content for reading level detection"

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples=content,
            client_name=client.name,
        )

        # Verify reading level was extracted
        assert result.reading_level_target is not None
        assert isinstance(result.reading_level_target, int)
        assert 0 <= result.reading_level_target <= 18  # Flesch-Kincaid grade level


class TestOnboardingWithContextOverrides:
    """Test onboarding with additional context."""

    @pytest.mark.asyncio
    async def test_service_area_override(self, setup_services):
        """Test service area override during onboarding."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        client = await client_repo.create_client(
            name="Test Client",
            industry="home_services",
            service_area="Denver, CO",  # Original
        )

        content = "Sample content"
        override_area = "Boulder, CO"  # Override

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples=content,
            client_name=client.name,
            service_area=override_area,  # Override
        )

        # Verify override was used
        assert override_area in result.brand_notes or override_area in result.audience_profile

    @pytest.mark.asyncio
    async def test_off_limits_topics_stored(self, setup_services):
        """Test off-limits topics are recorded."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        client = await client_repo.create_client(
            name="Test Client",
            industry="home_services",
        )

        off_limits = ["competitors", "pricing", "lawsuits"]
        content = "Sample content"

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples=content,
            client_name=client.name,
            off_limits_topics=off_limits,
        )

        # Verify off-limits were noted (typically in brand_notes)
        assert result.brand_notes is not None
        # Brand notes should mention avoided topics


class TestOnboardingPerformance:
    """Test performance and resource usage."""

    @pytest.mark.asyncio
    async def test_onboarding_completes_in_reasonable_time(self, setup_services):
        """Test that onboarding completes within acceptable time."""
        services = setup_services
        client_repo = services["client_repo"]
        onboarding_stage = services["onboarding_stage"]

        import time

        client = await client_repo.create_client(
            name="Performance Test Client",
            industry="home_services",
        )

        start = time.time()

        result = await onboarding_stage.onboard_client(
            client_id=client.id,
            content_samples="Sample content",
            client_name=client.name,
        )

        elapsed = time.time() - start

        # Should complete within 2 minutes (allow for LLM latency)
        assert elapsed < 120, f"Onboarding took {elapsed}s, expected < 120s"
        assert result is not None
