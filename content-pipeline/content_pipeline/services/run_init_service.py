# Created: Thursday Jul 23, 2026, 3:22 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 3:22 PM (UTC-6)

"""Run Init Service — Pre-Stage 1 implementation for run initialization."""

import json
import logging
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from content_pipeline.domain.client import RunContext, UnresolvedItem
from content_pipeline.domain.run import Run
from content_pipeline.domain.run_models import (
    OverlapConflict,
    PublishedArticle,
    TopicRecommendation,
)
from content_pipeline.domain.stage import StageOutput
from content_pipeline.exceptions import (
    MissingReferenceFilesError,
    OverlapDetectedError,
    RunCreationFailedError,
)
from content_pipeline.llm.provider_factory import LLMProviderFactory
from content_pipeline.llm.prompt_builder import PromptBuilder
from content_pipeline.orchestration.context_assembler import ClientContextAssembler
from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.repositories.run_repository import RunRepository

logger = logging.getLogger(__name__)


class RunInitService:
    """Pre-Stage 1: Run Initialization service.

    Handles two paths for starting a new run:
    - Path A: User provides topic + keyword → overlap check → create run
    - Path B: No topic → ideation (4-6 recommendations) → user selects → overlap check → create run
    """

    def __init__(
        self,
        client_repo: ClientRepository,
        run_repo: RunRepository,
        llm: Optional[object] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        context_assembler: Optional[ClientContextAssembler] = None,
    ):
        """Initialize Run Init Service.

        Args:
            client_repo: ClientRepository instance
            run_repo: RunRepository instance
            llm: LLM provider (default: smart model from factory)
            prompt_builder: PromptBuilder instance (default: new instance)
            context_assembler: ClientContextAssembler instance (default: new instance)
        """
        self.client_repo = client_repo
        self.run_repo = run_repo
        self.llm = llm or LLMProviderFactory.create_smart_provider()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.context_assembler = context_assembler or ClientContextAssembler(client_repo)

    # ========== Helper Methods ==========

    def _generate_folder_slug(self, topic: str) -> str:
        """Generate run folder slug from topic.

        "Content Marketing for Home Service Businesses" + 2026-06
        → "Content_Marketing_Home_Services_2026-06"

        Args:
            topic: Topic string

        Returns:
            Folder slug in Title_Case_Topic_YYYY-MM format
        """
        import re
        from datetime import datetime

        # Lowercase, strip non-alphanumeric (keep spaces)
        slug = re.sub(r"[^a-z0-9\s]", "", topic.lower())

        # Title case each word
        words = slug.split()
        slug_words = [word.capitalize() for word in words if word]
        slug = "_".join(slug_words)

        # Append YYYY-MM
        today = datetime.now()
        month_year = today.strftime("%Y-%m")

        return f"{slug}_{month_year}"

    def _sanitize_angle_notes(self, notes: Optional[str]) -> Optional[str]:
        """Sanitize angle notes: remove promotional/instruction-shaped content.

        Args:
            notes: Raw angle notes from CRM or user input

        Returns:
            Sanitized angle notes or None
        """
        if not notes:
            return None

        # Remove promotional phrases
        sanitized = re.sub(
            r"(Please write|Write about|Create content|Include|Focus on).*?\.?\s*",
            "",
            notes,
            flags=re.IGNORECASE,
        )

        # Remove instruction-shaped content (all caps directives)
        sanitized = re.sub(r"[A-Z]{5,}.*?[\.\!]", "", sanitized)

        sanitized = sanitized.strip()
        return sanitized if sanitized else None

    def _topics_are_similar(self, topic1: str, topic2: str) -> bool:
        """Check if two topics are semantically similar.

        Simple approach: Compare first 3 words + check for keyword overlap.
        If 2+ words overlap in first 3 words, topics are similar.

        Args:
            topic1: First topic
            topic2: Second topic

        Returns:
            True if similar, False otherwise
        """
        words1 = set(topic1.lower().split()[:3])
        words2 = set(topic2.lower().split()[:3])

        overlap = len(words1 & words2)
        return overlap >= 2

    def _extract_brand_notes_open_questions(self, brand_notes: str) -> list[str]:
        """Extract [CONFIRM WITH CLIENT] placeholders from Brand Notes.

        Args:
            brand_notes: Brand Notes markdown

        Returns:
            List of open question strings
        """
        pattern = r"\[CONFIRM WITH CLIENT\][^\[]*"
        matches = re.findall(pattern, brand_notes, re.DOTALL)
        return [m.strip() for m in matches]

    async def check_overlap(
        self, client_id: UUID, topic: str, keyword: str
    ) -> Optional[OverlapConflict]:
        """Check for overlap with published articles (keyword + title similarity).

        Args:
            client_id: Client UUID
            topic: Proposed topic
            keyword: Proposed primary keyword

        Returns:
            OverlapConflict if found, None otherwise
        """
        logger.info(f"Checking overlap for client {client_id}: {topic} / {keyword}")

        published = await self.run_repo.get_published_articles(client_id)

        for article in published:
            # Check 1: Keyword ILIKE
            if keyword.lower() in article.primary_keyword.lower() or (
                article.primary_keyword.lower() in keyword.lower()
            ):
                logger.warning(f"Keyword overlap detected: {article.primary_keyword}")
                return OverlapConflict(
                    existing_slug=article.slug,
                    conflict_type="keyword_overlap",
                    existing_keyword=article.primary_keyword,
                    suggestion="This keyword is already covered. Choose a different angle or keyword.",
                )

            # Check 2: Title similarity
            if self._topics_are_similar(topic, article.title):
                logger.warning(f"Title similarity detected: {article.title}")
                return OverlapConflict(
                    existing_slug=article.slug,
                    conflict_type="title_similarity",
                    existing_title=article.title,
                    suggestion="Very similar topic already published. Differentiate the angle or scope.",
                )

        logger.info(f"No overlap detected for {topic}")
        return None

    # ========== Path A: User-Provided Topic ==========

    async def validate_user_topic(
        self, client_id: UUID, topic: str, keyword: str
    ) -> Optional[OverlapConflict]:
        """Validate user-provided topic against overlap.

        Args:
            client_id: Client UUID
            topic: Topic string
            keyword: Primary keyword

        Returns:
            OverlapConflict if found, None otherwise
        """
        return await self.check_overlap(client_id, topic, keyword)

    async def create_run_from_user_topic(
        self,
        client_id: UUID,
        topic: str,
        keyword: str,
        angle_notes: Optional[str] = None,
    ) -> Run:
        """Create run from user-provided topic (Path A).

        Args:
            client_id: Client UUID
            topic: Topic string
            keyword: Primary keyword
            angle_notes: Optional strategic direction

        Returns:
            Created Run object

        Raises:
            MissingReferenceFilesError: If reference files incomplete
            OverlapDetectedError: If overlap detected
            RunCreationFailedError: If run creation fails
        """
        logger.info(f"Creating run for client {client_id} with user topic: {topic}")

        # Check prerequisites
        if not await self.client_repo.get_reference_files_complete(client_id):
            raise MissingReferenceFilesError(
                f"Client {client_id} is missing reference files. Run Stage 0 (Onboarding) first."
            )

        # Check overlap
        overlap = await self.check_overlap(client_id, topic, keyword)
        if overlap:
            raise OverlapDetectedError(f"Overlap detected: {overlap.suggestion}")

        # Get client + brand notes for open questions
        client = await self.client_repo.get_client(client_id)
        ref_files = await self.client_repo.get_reference_files(client_id)
        context_md = await self.context_assembler.assemble(client_id)

        # Extract open questions
        open_questions = self._extract_brand_notes_open_questions(
            ref_files.brand_notes or ""
        )

        # Create RunContext
        run_context = RunContext(
            client_id=client_id,
            topic=topic,
            primary_keyword=keyword,
            topic_path="user_provided",
            angle_notes_sanitized=self._sanitize_angle_notes(angle_notes),
        )

        # Generate folder slug
        folder_slug = self._generate_folder_slug(topic)

        # Create run in database
        run = await self.run_repo.create_run(
            client_id=client_id,
            folder_slug=folder_slug,
            context=run_context,
            status="initiated",
        )

        logger.info(f"Run created: {run.id} with slug {folder_slug}")

        # TODO: Create run folder and write handoff brief to filesystem

        return run

    # ========== Path B: Ideation ==========

    def _build_ideation_prompt(
        self,
        client_name: str,
        audience_profile: str,
        style_card: str,
        brand_notes: str,
        published_slugs: list[str],
        count: int = 5,
    ) -> str:
        """Build LLM prompt for topic ideation using Content Gap Analysis.

        Args:
            client_name: Client name
            audience_profile: Audience Profile markdown
            style_card: Style Reference Card markdown
            brand_notes: Brand Notes markdown
            published_slugs: List of published article slugs
            count: Number of recommendations to generate

        Returns:
            LLM prompt string
        """
        inventory = (
            "\n".join([f"- {slug}" for slug in published_slugs])
            if published_slugs
            else "- (No articles published yet)"
        )

        prompt = f"""You are the ideation assistant for {client_name}.

## CLIENT CONTEXT

**Audience Profile:**
{audience_profile}

**Style Reference Card:**
{style_card}

**Brand Notes:**
{brand_notes}

## PUBLISHED CONTENT INVENTORY

{inventory}

## TASK

Generate {count} topic recommendations using Content Gap Analysis:

1. Identify pain points and interests from the Audience Profile
2. Scan the Published Content Inventory for gaps
3. Recommend topics that:
   - Fill identified gaps
   - Serve audience needs
   - Are distinct from existing content (no keyword overlap)
   - Align with brand voice and style guidelines
   - Have high search intent and commercial value

## RESPONSE FORMAT

Return a JSON array with this structure (no markdown, raw JSON only):

[
  {{
    "topic": "How to Fix a Leaking Furnace (Without Calling an HVAC Tech First)",
    "primary_keyword": "leaking furnace repair",
    "why_now": "Seasonal heating problems spike in fall; users search for DIY solutions before spending $300+ on service calls",
    "audience_intent": "Homeowner wants to diagnose/fix furnace leak, or understand if they need professional help",
    "eeat_angle": "Frame as experienced HVAC tech sharing troubleshooting wisdom, not replacement for professional service when needed"
  }},
  ...
]

Important:
- Each recommendation must have a unique primary_keyword
- No topic should duplicate any slug in the Published Content Inventory
- Focus on keywords with search volume but manageable competition
- Consider seasonal relevance and content freshness
- Return exactly {count} recommendations"""

        return prompt

    async def generate_topic_recommendations(
        self, client_id: UUID, count: int = 5
    ) -> list[TopicRecommendation]:
        """Generate topic recommendations using LLM ideation (Path B).

        Args:
            client_id: Client UUID
            count: Number of recommendations (default 5)

        Returns:
            List of TopicRecommendation objects

        Raises:
            MissingReferenceFilesError: If reference files incomplete
        """
        logger.info(f"Generating {count} topic recommendations for client {client_id}")

        # Check prerequisites
        if not await self.client_repo.get_reference_files_complete(client_id):
            raise MissingReferenceFilesError(
                f"Client {client_id} is missing reference files. Run Stage 0 (Onboarding) first."
            )

        # Get client data
        client = await self.client_repo.get_client(client_id)
        ref_files = await self.client_repo.get_reference_files(client_id)
        published_slugs = await self.run_repo.get_published_slugs(client_id)

        # Build prompt
        prompt = self._build_ideation_prompt(
            client_name=client.name,
            audience_profile=ref_files.audience_profile or "",
            style_card=ref_files.style_reference_card or "",
            brand_notes=ref_files.brand_notes or "",
            published_slugs=published_slugs,
            count=count,
        )

        # Call LLM
        logger.debug(f"Calling LLM for ideation with {count} recommendations")
        response = await self.llm.call(
            system_prompt="You are a content strategy expert. Generate topic recommendations as raw JSON only.",
            user_message=prompt,
        )

        # Parse JSON response
        try:
            # Extract JSON from response (may have surrounding text)
            json_match = re.search(r"\[\s*\{.*\}\s*\]", response, re.DOTALL)
            if not json_match:
                logger.error(f"Failed to extract JSON from LLM response: {response[:200]}")
                return []

            json_str = json_match.group(0)
            data = json.loads(json_str)

            recommendations = []
            for item in data:
                recommendations.append(
                    TopicRecommendation(
                        topic=item.get("topic", ""),
                        primary_keyword=item.get("primary_keyword", ""),
                        why_now=item.get("why_now", ""),
                        audience_intent=item.get("audience_intent", ""),
                        eeat_angle=item.get("eeat_angle", ""),
                    )
                )

            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return []

    async def confirm_recommendation(
        self, client_id: UUID, recommendation: TopicRecommendation
    ) -> Run:
        """Confirm a recommendation and create run (Path B).

        Same as create_run_from_user_topic but topic/keyword from recommendation.

        Args:
            client_id: Client UUID
            recommendation: TopicRecommendation to confirm

        Returns:
            Created Run object

        Raises:
            MissingReferenceFilesError: If reference files incomplete
            OverlapDetectedError: If overlap detected
            RunCreationFailedError: If run creation fails
        """
        return await self.create_run_from_user_topic(
            client_id=client_id,
            topic=recommendation.topic,
            keyword=recommendation.primary_keyword,
            angle_notes=recommendation.why_now,
        )
