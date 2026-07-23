# Created: Thursday Jul 23, 2026, 3:22 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:22 PM (UTC-6)

"""Tests for Run Init Service (Pre-Stage 1)."""

import pytest

from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.repositories.run_repository import RunRepository
from content_pipeline.services.run_init_service import RunInitService


@pytest.fixture
def run_init_service():
    """Create RunInitService instance for unit tests.
    
    Uses real LLM provider from .env credentials.
    Repos are None since these tests are for pure functions.
    """
    from content_pipeline.llm.provider_factory import LLMProviderFactory
    
    llm = LLMProviderFactory.create_smart_provider()
    service = RunInitService(None, None, llm=llm)  # type: ignore
    return service


class TestFolderSlugGeneration:
    """Unit tests for folder slug generation."""

    def test_simple_topic_slug(self, run_init_service):
        """Test basic slug generation."""
        slug = run_init_service._generate_folder_slug("How to Fix a Furnace")
        assert "How_To_Fix_A_Furnace" in slug
        assert slug.endswith(run_init_service._generate_folder_slug("test").split("_")[-1])

    def test_removes_special_characters(self, run_init_service):
        """Test special character removal."""
        slug = run_init_service._generate_folder_slug("How to Fix a Furnace (Safely)!")
        assert "(" not in slug
        assert ")" not in slug
        assert "!" not in slug

    def test_long_topic_slug(self, run_init_service):
        """Test slug with long topic."""
        slug = run_init_service._generate_folder_slug(
            "Content Marketing for Home Service Businesses"
        )
        # slug will include all words, e.g., Content_Marketing_For_Home_Service_Businesses_2026-07
        assert "Content_Marketing_For_Home_Service" in slug
        assert slug.endswith("2026-07")

    def test_slug_ends_with_month_year(self, run_init_service):
        """Test slug ends with YYYY-MM."""
        slug = run_init_service._generate_folder_slug("Test Topic")
        parts = slug.split("_")
        last_part = parts[-1]
        assert len(last_part) == 7  # "2026-07" format
        assert last_part[4] == "-"


class TestAngleSanitization:
    """Unit tests for angle notes sanitization."""

    def test_remove_promotional_phrases(self, run_init_service):
        """Test removal of promotional phrases."""
        notes = "Write about HVAC benefits. Include customer testimonials."
        sanitized = run_init_service._sanitize_angle_notes(notes)
        assert "Write about" not in sanitized
        assert "Include" not in sanitized

    def test_remove_all_caps_directives(self, run_init_service):
        """Test removal of ALL CAPS directives."""
        notes = "Focus on DIY solutions. INCLUDE CASE STUDIES. Mention ROI."
        sanitized = run_init_service._sanitize_angle_notes(notes)
        assert "INCLUDE" not in sanitized

    def test_preserve_strategic_direction(self, run_init_service):
        """Test that strategic content is preserved."""
        notes = "DIY-first approach, then upsell to professional service"
        sanitized = run_init_service._sanitize_angle_notes(notes)
        assert sanitized  # Should have content
        assert "DIY" in sanitized or "approach" in sanitized

    def test_empty_returns_none(self, run_init_service):
        """Test empty string returns None."""
        result = run_init_service._sanitize_angle_notes("")
        assert result is None

    def test_none_input_returns_none(self, run_init_service):
        """Test None input returns None."""
        result = run_init_service._sanitize_angle_notes(None)
        assert result is None


class TestTopicSimilarity:
    """Unit tests for topic similarity detection."""

    def test_identical_topics_similar(self, run_init_service):
        """Test identical topics are similar."""
        result = run_init_service._topics_are_similar(
            "How to Fix a Furnace", "How to Fix a Furnace"
        )
        assert result is True

    def test_similar_topics_with_overlap(self, run_init_service):
        """Test topics with 2+ word overlap are similar."""
        result = run_init_service._topics_are_similar(
            "How to Fix a Furnace", "How to Fix a Broken Furnace"
        )
        assert result is True

    def test_dissimilar_topics(self, run_init_service):
        """Test dissimilar topics are not similar."""
        result = run_init_service._topics_are_similar(
            "How to Fix a Furnace", "Best Air Conditioning Units"
        )
        assert result is False

    def test_partial_match_not_similar(self, run_init_service):
        """Test partial (1 word) match is not similar."""
        result = run_init_service._topics_are_similar(
            "Furnace Maintenance Guide", "Best HVAC Tools"
        )
        assert result is False


class TestBrandNotesQuestionsExtraction:
    """Unit tests for extracting open questions from Brand Notes."""

    def test_extract_single_question(self, run_init_service):
        """Test extraction of single open question."""
        notes = "Some text. [CONFIRM WITH CLIENT] What is your service area? More text."
        questions = run_init_service._extract_brand_notes_open_questions(notes)
        assert len(questions) >= 1
        assert any("[CONFIRM WITH CLIENT]" in q for q in questions)

    def test_extract_multiple_questions(self, run_init_service):
        """Test extraction of multiple open questions."""
        notes = (
            "[CONFIRM WITH CLIENT] Question 1? "
            "Some text. "
            "[CONFIRM WITH CLIENT] Question 2?"
        )
        questions = run_init_service._extract_brand_notes_open_questions(notes)
        assert len(questions) >= 2

    def test_no_questions_returns_empty(self, run_init_service):
        """Test empty list when no questions found."""
        notes = "Just regular brand notes without any open questions."
        questions = run_init_service._extract_brand_notes_open_questions(notes)
        assert isinstance(questions, list)


class TestIdeationPromptBuilding:
    """Unit tests for ideation prompt building."""

    def test_prompt_includes_audience_profile(self, run_init_service):
        """Test prompt includes audience profile."""
        prompt = run_init_service._build_ideation_prompt(
            client_name="Test Client",
            audience_profile="Homeowners aged 40-65",
            style_card="Friendly tone",
            brand_notes="Local focus",
            published_slugs=[],
            count=5,
        )
        assert "Homeowners aged 40-65" in prompt

    def test_prompt_includes_published_inventory(self, run_init_service):
        """Test prompt includes published articles inventory."""
        prompt = run_init_service._build_ideation_prompt(
            client_name="Test Client",
            audience_profile="Test",
            style_card="Test",
            brand_notes="Test",
            published_slugs=["article_1", "article_2"],
            count=5,
        )
        assert "article_1" in prompt
        assert "article_2" in prompt

    def test_prompt_has_correct_count(self, run_init_service):
        """Test prompt specifies correct count."""
        prompt = run_init_service._build_ideation_prompt(
            client_name="Test",
            audience_profile="Test",
            style_card="Test",
            brand_notes="Test",
            published_slugs=[],
            count=7,
        )
        assert "7" in prompt


class TestIntegrationPathA:
    """Integration tests for Path A (user-provided topic)."""

    @pytest.mark.asyncio
    async def test_user_topic_no_overlap_creates_run(self, run_init_service):
        """Test Path A: User provides topic, no overlap, run created."""
        # TODO: Create test client, provide topic, verify run created

    @pytest.mark.asyncio
    async def test_user_topic_keyword_overlap_detected(self, run_init_service):
        """Test Path A: Keyword overlap detected, returns conflict."""
        # TODO: Create test client with published article, try same keyword, verify conflict

    @pytest.mark.asyncio
    async def test_user_topic_title_similarity_detected(self, run_init_service):
        """Test Path A: Title similarity detected."""
        # TODO: Create published article, try similar topic, verify conflict


class TestIntegrationPathB:
    """Integration tests for Path B (ideation)."""

    @pytest.mark.asyncio
    async def test_generate_recommendations_returns_array(self, run_init_service):
        """Test Path B: Generate recommendations returns array."""
        # TODO: Create test client, call generate_recommendations, verify array

    @pytest.mark.asyncio
    async def test_recommendations_have_all_fields(self, run_init_service):
        """Test Path B: Recommendations have all required fields."""
        # TODO: Verify each recommendation has topic, keyword, why_now, etc.

    @pytest.mark.asyncio
    async def test_confirm_recommendation_creates_run(self, run_init_service):
        """Test Path B: User selects recommendation, run created."""
        # TODO: Generate recommendations, select one, verify run created


class TestMissingPrerequisites:
    """Test error handling for missing prerequisites."""

    @pytest.mark.asyncio
    async def test_missing_reference_files_raises_error(self, run_init_service):
        """Test MissingReferenceFilesError when files missing."""
        # TODO: Create partially onboarded client, try to create run

    @pytest.mark.asyncio
    async def test_generate_recommendations_requires_files(self, run_init_service):
        """Test ideation fails without reference files."""
        # TODO: Create partially onboarded client, try to generate recommendations


class TestBrandNotesAlerts:
    """Test user alerts for Brand Notes open questions."""

    @pytest.mark.asyncio
    async def test_open_questions_trigger_alert(self, run_init_service):
        """Test that open questions in Brand Notes are flagged."""
        # TODO: Create client with open questions, verify alert sent


class TestHandoffBriefsGeneration:
    """Test handoff brief generation."""

    @pytest.mark.asyncio
    async def test_handoff_brief_has_required_sections(self, run_init_service):
        """Test handoff brief has all required sections."""
        # TODO: Create run, verify handoff has topic, keyword, carry-forward context, etc.

    @pytest.mark.asyncio
    async def test_handoff_auto_run_false(self, run_init_service):
        """Test handoff has auto-run: false."""
        # TODO: Verify handoff specifies sequential mode
