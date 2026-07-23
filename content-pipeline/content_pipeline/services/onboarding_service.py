# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:24 PM (UTC-6)

"""Stage 0 — Onboarding service.

Analyzes client content samples and generates three reference artifacts:
- Style Reference Card (voice, tone, structure)
- Audience Profile (demographics, expertise, intent)
- Brand Notes (authority signals, open questions)

Key behaviors:
1. Check client state FIRST (NEW, PARTIAL, FULLY_ONBOARDED)
2. Fail fast if already fully onboarded (unless regenerate=True)
3. Call LLM to generate reference files
4. Extract brand colors, reading level, certifications from output
5. Validate all quality gates
6. Save reference files to database
"""

import logging
import re
from typing import Any, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from content_pipeline.services.base_stage import StageContract
from content_pipeline.domain.run import Run
from content_pipeline.domain.stage import StageOutput
from content_pipeline.domain.enums import StageStatus, ClientState
from content_pipeline.domain.client import ClientReferenceFiles
from content_pipeline.exceptions import (
    ClientAlreadyOnboardedError,
    ValidationError,
)
from content_pipeline.config.brand_color_extractor import (
    BrandColorExtractor,
    MissingBrandColorError,
)

logger = logging.getLogger(__name__)


class OnboardingStage(StageContract):
    """Stage 0 — Generate reference files for a new client.
    
    This stage is NOT part of the Run execution pipeline. It's a one-time
    client setup that happens before any production runs begin.
    """

    def __init__(
        self,
        repo: Any,
        llm: Any,
        parser: Any,
        tracker: Any,
        client_repo: Any,
    ) -> None:
        """Initialize OnboardingStage.
        
        Args:
            repo: Base repository
            llm: LLM provider instance
            parser: Output parser (unused in Stage 0)
            tracker: Unresolved item tracker (unused in Stage 0)
            client_repo: ClientRepository for reference file operations
        """
        super().__init__(repo, llm, parser, tracker)
        self._client_repo = client_repo
        self._brand_extractor = BrandColorExtractor()

    @property
    def stage_number(self) -> int:
        """Stage 0."""
        return 0

    @property
    def stage_name(self) -> str:
        """Onboarding."""
        return "Onboarding"

    def _check_prerequisites(self, run: Run) -> None:
        """Stage 0 has no prerequisites — always passes."""
        pass

    def _load_context(self, run: Run) -> dict:
        """Load user-provided content samples and client info.
        
        In API usage, context is passed by HTTP request, not loaded from database.
        This returns a template structure.
        """
        return {
            "content_samples": None,
            "client_name": None,
            "client_website": None,
            "client_industry": None,
            "service_area": None,
            "off_limits_topics": [],
        }

    def _build_prompt(self, run: Run, context: dict) -> Tuple[str, str]:
        """Build system and user prompts for LLM.
        
        Args:
            run: Run object (unused)
            context: Context dict with client info and samples
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt: the Stage 0 contract
        system_prompt = self._load_stage_contract()

        # User prompt: client info + content samples
        user_prompt = f"""
Client Name: {context.get('client_name', 'Unknown')}
Website: {context.get('client_website', 'N/A')}
Industry: {context.get('client_industry', 'N/A')}
Service Area: {context.get('service_area', 'N/A')}
Off-Limits Topics: {', '.join(context.get('off_limits_topics', []) or [])}

Please analyze the following content samples and generate three reference files:
1. Style Reference Card (voice, tone, structure, SEO patterns)
2. Audience Profile (demographics, expertise, pain points)
3. Brand Notes (authority signals, certifications, open questions)

Content Samples:
{context.get('content_samples', 'No samples provided')}

Format your response with ### OUTPUT headers for each file.
"""
        return system_prompt, user_prompt

    def _parse_output(self, raw: str, run: Run) -> StageOutput:
        """Parse LLM output into three reference files.
        
        Extracts:
        - style_reference_card (markdown)
        - audience_profile (markdown)
        - brand_notes (markdown)
        - brand_colors (dict of 11 CSS tokens from Style Reference Card)
        - reading_level_target (from Audience Profile)
        - certifications (from Brand Notes)
        - years_in_business (from Brand Notes)
        
        Args:
            raw: Raw LLM completion text
            run: Run object (unused)
            
        Returns:
            StageOutput with parsed reference files
        """
        logger.info("Parsing onboarding output from LLM")
        
        # Split LLM output by ### OUTPUT markers
        files = self._split_outputs(raw)

        # Create reference files object
        ref_files = ClientReferenceFiles(
            style_reference_card=files.get("style_reference_card"),
            audience_profile=files.get("audience_profile"),
            brand_notes=files.get("brand_notes"),
        )

        # EXTRACT BRAND COLORS immediately after parsing
        # This is a critical step that feeds into validation
        if ref_files.style_reference_card:
            try:
                logger.debug("Extracting brand colors from Style Reference Card")
                ref_files.brand_colors = self._brand_extractor.extract(
                    ref_files.style_reference_card
                )
                logger.info(f"Successfully extracted {len(ref_files.brand_colors)} brand colors")
            except MissingBrandColorError as e:
                logger.warning(f"Brand color extraction failed at parsing: {e}")
                # Don't fail parsing — validation will catch missing colors
                ref_files.brand_colors = {}

        # Extract metadata from Audience Profile
        if ref_files.audience_profile:
            ref_files.reading_level_target = self._extract_reading_level(
                ref_files.audience_profile
            )
            logger.debug(f"Extracted reading level: {ref_files.reading_level_target}")

        # Extract metadata from Brand Notes
        if ref_files.brand_notes:
            ref_files.certifications = self._extract_certifications(ref_files.brand_notes)
            ref_files.years_in_business = self._extract_years_in_business(
                ref_files.brand_notes
            )
            logger.debug(
                f"Extracted {len(ref_files.certifications)} certifications, "
                f"{ref_files.years_in_business} years in business"
            )

        # Create StageOutput
        # Use client_id as both id and run_id (Stage 0 doesn't use Run objects)
        output = StageOutput(
            id=run.id if hasattr(run, 'id') else UUID('00000000-0000-0000-0000-000000000000'),
            run_id=run.id if hasattr(run, 'id') else UUID('00000000-0000-0000-0000-000000000000'),
            stage_number=self.stage_number,
            stage_name=self.stage_name,
            attempt=1,
            status=StageStatus.PENDING,
            article_content=None,
            quality_gate_results={"reference_files": ref_files},
        )

        logger.info("Onboarding output parsed successfully")
        return output

    def _validate_output(self, output: StageOutput, run: Run) -> list[str]:
        """Validate reference files against quality gates.
        
        Gates:
        - All 3 files have content
        - Style Reference Card has required sections
        - Brand Notes has OPEN QUESTIONS FOR CLIENT with [ ] items
        - All 11 brand colors extracted and validated
        
        Args:
            output: StageOutput from _parse_output
            run: Run object (unused)
            
        Returns:
            List of validation error strings (empty = all pass)
        """
        logger.info("Validating onboarding output")
        errors = []

        ref_files = output.quality_gate_results.get("reference_files")
        if not ref_files:
            errors.append("No reference files in output")
            logger.error("Validation failed: no reference files")
            return errors

        # Gate 1: All 3 files have content
        if not ref_files.style_reference_card:
            errors.append("Style Reference Card is empty")
        if not ref_files.audience_profile:
            errors.append("Audience Profile is empty")
        if not ref_files.brand_notes:
            errors.append("Brand Notes is empty")

        # Gate 2: Style Reference Card structure
        if ref_files.style_reference_card:
            required_sections = [
                "WRITING STYLE GUIDELINES",
                "VISUAL BRAND THEME",
                "STRUCTURAL GUIDELINES",
                "SEO & KEYWORD GUIDANCE",
            ]
            for section in required_sections:
                if section not in ref_files.style_reference_card:
                    errors.append(
                        f"Style Reference Card missing required section: {section}"
                    )

        # Gate 3: Brand Notes has open questions
        if ref_files.brand_notes:
            if "OPEN QUESTIONS FOR CLIENT" not in ref_files.brand_notes:
                errors.append("Brand Notes missing: OPEN QUESTIONS FOR CLIENT")
            elif "[ ]" not in ref_files.brand_notes:
                errors.append("Brand Notes: OPEN QUESTIONS must have unchecked items [ ]")

        # Gate 4: Brand colors — all 11 keys present and valid
        if not ref_files.brand_colors or len(ref_files.brand_colors) < 11:
            errors.append(
                f"Brand colors: expected 11 keys, got {len(ref_files.brand_colors or {})}"
            )
        else:
            color_errors = self._brand_extractor.validate(ref_files.brand_colors)
            if color_errors:
                for color_error in color_errors:
                    errors.append(f"Brand color validation: {color_error}")

        if errors:
            logger.error(f"Validation failed with {len(errors)} errors: {errors}")
        else:
            logger.info("All validation gates passed")

        return errors

    def _build_handoff(self, run: Run, output: StageOutput, context: dict) -> str:
        """Build handoff for next stage.
        
        Stage 0 produces no handoff — it outputs reference files directly to database.
        
        Returns:
            Empty string
        """
        return ""

    # ========== HELPER METHODS ==========

    def _load_stage_contract(self) -> str:
        """Load Stage 0 contract as system prompt.
        
        TODO: Load from docs/stage_contracts/stage0_onboarding_CONTEXT.md
        
        Returns:
            System prompt text
        """
        return """You are an expert at analyzing client content and generating reference materials.
Your task is to analyze the provided content samples and generate three comprehensive reference files.

Each file must have the structure specified in the Stage 0 contract.
All sections must be specific to this client—no generic templates.

Return your response with clear ### OUTPUT 1, ### OUTPUT 2, and ### OUTPUT 3 headers."""

    def _split_outputs(self, raw: str) -> dict:
        """Split LLM output into three files by ### OUTPUT markers.
        
        Args:
            raw: Raw LLM completion text
            
        Returns:
            Dict with keys: style_reference_card, audience_profile, brand_notes
        """
        files = {
            "style_reference_card": None,
            "audience_profile": None,
            "brand_notes": None,
        }

        # Split by ### OUTPUT markers
        parts = re.split(r"###\s+OUTPUT\s+\d+:", raw)

        # Skip first part (everything before first OUTPUT)
        for i, part in enumerate(parts[1:], 1):
            part = part.strip()
            if not part:
                continue

            if i == 1 or "Style" in part[:100]:
                files["style_reference_card"] = part
            elif i == 2 or "Audience" in part[:100]:
                files["audience_profile"] = part
            elif i == 3 or "Brand" in part[:100]:
                files["brand_notes"] = part

        return files

    def _extract_reading_level(self, audience_profile: str) -> Optional[str]:
        """Extract reading level from Audience Profile markdown.
        
        Looks for patterns like "8th-10th grade" or "college level".
        
        Args:
            audience_profile: Audience Profile markdown
            
        Returns:
            Reading level string or None
        """
        # TODO: Implement markdown parsing
        # Look for: EXPERTISE AND KNOWLEDGE LEVEL section
        # Extract reading level mention
        return None

    def _extract_certifications(self, brand_notes: str) -> list[str]:
        """Extract certifications from Brand Notes markdown.
        
        Looks for certifications mentioned in AUTHORITY AND TRUST SIGNALS section.
        
        Args:
            brand_notes: Brand Notes markdown
            
        Returns:
            List of certification strings
        """
        # TODO: Implement markdown parsing
        # Look for: AUTHORITY AND TRUST SIGNALS section
        # Extract: certifications, licenses, credentials
        return []

    def _extract_years_in_business(self, brand_notes: str) -> Optional[int]:
        """Extract years in business from Brand Notes markdown.
        
        Looks for mentions like "15 years" or "since 2008".
        
        Args:
            brand_notes: Brand Notes markdown
            
        Returns:
            Number of years or None
        """
        # TODO: Implement markdown parsing
        # Look for: AUTHORITY AND TRUST SIGNALS section
        # Extract: years in business / experience
        return None

    async def onboard_client(
        self,
        client_id: UUID,
        content_samples: str,
        client_name: str,
        client_website: Optional[str] = None,
        client_industry: Optional[str] = None,
        service_area: Optional[str] = None,
        off_limits_topics: Optional[list[str]] = None,
        regenerate: bool = False,
    ) -> ClientReferenceFiles:
        """Execute onboarding for a client.
        
        Main entry point for Stage 0. Orchestrates the full flow:
        1. Check client state (FAIL FAST if already fully onboarded)
        2. Load context
        3. Build prompts
        4. Call LLM
        5. Parse output
        6. Validate
        7. Save reference files
        
        Args:
            client_id: Client UUID
            content_samples: Content samples as string
            client_name: Client name
            client_website: Client website URL
            client_industry: Client industry
            service_area: Service area
            off_limits_topics: Topics to avoid
            regenerate: If True, regenerate even if already onboarded
            
        Returns:
            ClientReferenceFiles domain object
            
        Raises:
            ClientAlreadyOnboardedError: Already fully onboarded (unless regenerate=True)
            ValidationError: Output validation failed
        """
        logger.info(f"Starting onboarding for client {client_id}")

        # ========== STEP 1: CHECK CLIENT STATE FIRST ==========
        logger.debug(f"Checking client state for {client_id}")
        existing_files = await self._client_repo.get_reference_files(client_id)

        # Detect state by counting existing files
        present_count = sum([
            existing_files.style_reference_card is not None,
            existing_files.audience_profile is not None,
            existing_files.brand_notes is not None,
        ])

        if present_count == 0:
            state = ClientState.NEW
        elif present_count == 3:
            state = ClientState.FULLY_ONBOARDED
        else:
            state = ClientState.PARTIAL

        logger.info(f"Client state: {state.value} ({present_count}/3 files present)")

        # ========== FAIL FAST: Check if already onboarded ==========
        if state == ClientState.FULLY_ONBOARDED and not regenerate:
            logger.warning(
                f"Client {client_id} is already fully onboarded. "
                "Rejecting onboarding request (regenerate=False)."
            )
            raise ClientAlreadyOnboardedError(
                f"Client {client_id} is already fully onboarded. "
                "Pass regenerate=True to regenerate reference files."
            )

        logger.info(f"Proceeding with onboarding (state={state.value}, regenerate={regenerate})")

        # ========== STEP 2: LOAD CONTEXT ==========
        context = self._load_context(None)
        context.update({
            "content_samples": content_samples,
            "client_name": client_name,
            "client_website": client_website,
            "client_industry": client_industry,
            "service_area": service_area,
            "off_limits_topics": off_limits_topics or [],
        })

        # ========== STEP 3: BUILD PROMPTS ==========
        system_prompt, user_prompt = self._build_prompt(None, context)
        logger.debug("Prompts built successfully")

        # ========== STEP 4: CALL LLM ==========
        logger.info("Calling LLM for onboarding output")
        raw_output = await self._llm.complete(user_prompt, system=system_prompt)
        logger.debug(f"LLM returned {len(raw_output)} characters")

        # ========== STEP 5: PARSE OUTPUT ==========
        # Create mock run object for compatibility with StageContract interface
        mock_run = type('Run', (), {'id': client_id})()
        output = self._parse_output(raw_output, mock_run)

        # ========== STEP 6: VALIDATE OUTPUT ==========
        errors = self._validate_output(output, mock_run)
        if errors:
            logger.error(f"Onboarding validation failed: {errors}")
            raise ValidationError(
                f"Onboarding output validation failed: {'; '.join(errors)}"
            )

        # ========== STEP 7: SAVE REFERENCE FILES ==========
        ref_files = output.quality_gate_results["reference_files"]
        logger.info(f"Saving reference files for client {client_id}")
        await self._client_repo.save_reference_files(client_id, ref_files)
        logger.info(f"Onboarding complete for client {client_id}")

        return ref_files
