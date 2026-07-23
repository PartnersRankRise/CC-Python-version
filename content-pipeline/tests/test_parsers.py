# Created: Thursday Jul 23, 2026, 1:08 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:27 PM (UTC-6)

"""Tests for parsing layer — all six parsers against reference run files."""

import pytest
from pathlib import Path

from content_pipeline.parsing.brief_parser import BriefParser
from content_pipeline.parsing.editorial_note_parser import EditorialNoteParser
from content_pipeline.parsing.seo_annotation_parser import SEOAnnotationParser
from content_pipeline.parsing.qa_signoff_parser import QASignoffParser
from content_pipeline.parsing.dossier_parser import DossierParser
from content_pipeline.domain.enums import QADecision, QAIssueType


@pytest.fixture
def reference_run_dir():
    """Path to reference_run directory."""
    return Path(__file__).parent.parent / 'reference_run'


@pytest.fixture
def brief_content(reference_run_dir):
    """Load reference brief from 02_Content_Brief.md."""
    brief_file = reference_run_dir / '02_Content_Brief.md'
    return brief_file.read_text()


@pytest.fixture
def humanized_draft_content(reference_run_dir):
    """Load reference humanized draft from 04_Humanized_Draft.md."""
    draft_file = reference_run_dir / '04_Humanized_Draft.md'
    return draft_file.read_text()


@pytest.fixture
def seo_draft_content(reference_run_dir):
    """Load reference SEO draft from 05_SEO_Draft.md."""
    draft_file = reference_run_dir / '05_SEO_Draft.md'
    return draft_file.read_text()


@pytest.fixture
def qa_signoff_content(reference_run_dir):
    """Load reference QA signoff from 06_QA_Signoff.md."""
    signoff_file = reference_run_dir / '06_QA_Signoff.md'
    return signoff_file.read_text()


@pytest.fixture
def dossier_content(reference_run_dir):
    """Load reference dossier from 01_Research_Dossier.md."""
    dossier_file = reference_run_dir / '01_Research_Dossier.md'
    return dossier_file.read_text()


class TestBriefParser:
    """Test BriefParser against reference run."""

    def test_brief_parser_preserves_table(self, brief_content):
        """CRITICAL: The content types table must survive BRIEF token stripping."""
        parser = BriefParser()
        stripped = parser.strip_brief_tokens(brief_content)
        
        # The content types table must survive stripping
        assert '| Content Type |' in stripped, "Content types table header was removed by BRIEF stripping"
        assert '| Blog posts' in stripped, "Blog posts row was removed"
        assert '| What It Does for Your Local Presence |' in stripped, "Table subheader removed"
        
        # No BRIEF tokens should remain
        assert '<!--BRIEF:' not in stripped, "BRIEF token found after stripping"
        # Verify no malformed HTML comments are left
        assert '<!--' not in stripped or '-->' not in stripped, "Incomplete comment markers found"

    def test_brief_parser_section_count(self, brief_content):
        """Verify parser extracts main brief sections."""
        parser = BriefParser()
        parsed = parser.parse(brief_content)
        
        # Verify required sections were extracted
        assert parsed.keyword_strategy is not None, "keyword_strategy is None"
        assert parsed.keyword_strategy, "keyword_strategy is empty"
        assert parsed.audience_definition != "", "audience_definition is empty"
        assert parsed.who_how_why is not None, "who_how_why is None"
        assert parsed.post_structure is not None, "post_structure is None"
        assert parsed.cta_direction is not None, "cta_direction is None"

    def test_brief_parser_content_table_extraction(self, brief_content):
        """Verify content types table is captured separately."""
        parser = BriefParser()
        parsed = parser.parse(brief_content)
        
        # Content table should be extracted
        assert parsed.content_table is not None, "content_table is None"
        assert len(parsed.content_table) > 0, "content_table is empty"
        assert '| Content Type |' in parsed.content_table, "Table header not in extracted content_table"
        assert '| Blog posts' in parsed.content_table, "Blog posts row not in extracted content_table"

    def test_brief_parser_keyword_extraction(self, brief_content):
        """Verify keyword strategy is properly extracted."""
        parser = BriefParser()
        parsed = parser.parse(brief_content)
        
        # Keyword strategy should have primary keyword
        assert 'primary_keyword' in parsed.keyword_strategy, "primary_keyword not extracted"
        primary = parsed.keyword_strategy['primary_keyword']
        assert 'content marketing' in primary.lower(), "primary_keyword missing expected term"

    def test_brief_parser_audience_definition(self, brief_content):
        """Verify audience definition section is extracted."""
        parser = BriefParser()
        parsed = parser.parse(brief_content)
        
        # Audience should be non-empty and contain expected context
        assert len(parsed.audience_definition) > 100, "audience_definition is too short"
        assert 'home service' in parsed.audience_definition.lower(), "audience_definition missing context"

    def test_brief_parser_who_how_why(self, brief_content):
        """Verify WHO/HOW/WHY section is extracted."""
        parser = BriefParser()
        parsed = parser.parse(brief_content)
        
        # WHO/HOW/WHY should be present
        assert parsed.who_how_why, "who_how_why is empty"
        assert 'who' in parsed.who_how_why or 'how' in parsed.who_how_why or 'why' in parsed.who_how_why, \
            "who_how_why missing expected keys"

    def test_brief_parser_no_token_leakage(self, brief_content):
        """Verify no internal tokens leak into stripped content."""
        parser = BriefParser()
        stripped = parser.strip_brief_tokens(brief_content)
        
        # No internal tokens should remain
        forbidden_tokens = ['<!--BRIEF:', 'BEGIN_BLOG_REQUEST', 'END_BLOG_REQUEST']
        for token in forbidden_tokens:
            assert token not in stripped, f"Token leakage detected: {token}"


class TestEditorialNoteParser:
    """Test EditorialNoteParser against reference run."""

    def test_editorial_note_splits_correctly(self, humanized_draft_content):
        """Verify editorial note is correctly separated from article body."""
        parser = EditorialNoteParser()
        article, note = parser.split(humanized_draft_content)
        
        # Article body must not contain the editorial note
        assert "## Editorial Note" not in article, "Editorial note section still in article body"
        
        # Editorial note must contain all 5 confirmed sub-sections
        assert note is not None, "Editorial note is None"
        assert "Structural changes" in note, "Missing 'Structural changes' section"
        assert "Rhythm" in note, "Missing 'Rhythm' section"
        assert "Experience additions" in note, "Missing 'Experience additions' section"
        assert "E-E-A-T" in note, "Missing 'E-E-A-T' section"
        assert "QA concern" in note, "Missing 'QA concern' section"
        
        # Critical: article body must not be empty
        assert len(article) > 1000, f"Article body seems too short: {len(article)} chars"

    def test_editorial_note_body_has_no_token_leakage(self, humanized_draft_content):
        """Verify article body is clean of internal tokens."""
        parser = EditorialNoteParser()
        article, note = parser.split(humanized_draft_content)
        
        # Article body should not contain internal tokens
        assert "<!--BRIEF:" not in article, "BRIEF token found in article body"
        assert "BEGIN_BLOG_REQUEST" not in article, "BEGIN_BLOG_REQUEST found in article body"
        assert "## Editorial Note" not in article, "Editorial Note header still in article"

    def test_editorial_note_is_clean(self, humanized_draft_content):
        """Verify editorial note content is properly extracted and clean."""
        parser = EditorialNoteParser()
        article, note = parser.split(humanized_draft_content)
        
        # Editorial note should be substantial
        assert len(note) > 500, f"Editorial note seems too short: {len(note)} chars"
        
        # Should not have "## Editorial Note" header in the note content itself
        # (it was the separator, so shouldn't be included)
        lines = note.split('\n')
        assert not lines[0].startswith('## Editorial Note'), "Editorial Note header leaked into note content"

    def test_editorial_note_article_structure_preserved(self, humanized_draft_content):
        """Verify article body structure is preserved during split."""
        parser = EditorialNoteParser()
        article, note = parser.split(humanized_draft_content)
        
        # Article should still have expected sections
        assert "# Content Marketing for Home Service Businesses" in article, "H1 missing from article"
        assert "##" in article, "Section headings missing from article"
        
        # Article should not have trailing whitespace
        assert article == article.rstrip(), "Article body has trailing whitespace"


class TestSEOAnnotationParser:
    """Test SEOAnnotationParser against reference run."""

    def test_seo_annotation_splits_correctly(self, seo_draft_content):
        """Verify SEO annotation sheet is correctly separated from article body."""
        parser = SEOAnnotationParser()
        article, annotation = parser.split(seo_draft_content)
        
        # Article body must not contain the annotation sheet header
        assert "## SEO Annotation Sheet" not in article, "Annotation sheet header still in article body"
        
        # Annotation must contain key sections
        assert "Summary of Changes" in annotation, "Missing 'Summary of Changes' section"
        assert "Word Count Note" in annotation, "Missing 'Word Count Note' section"
        
        # Critical: article and annotation must not be empty
        assert len(article) > 1000, f"Article body too short: {len(article)} chars"
        assert len(annotation) > 500, f"Annotation too short: {len(annotation)} chars"

    def test_seo_word_count_parses_to_structured_data(self, seo_draft_content):
        """Verify word count parses to structured dict with correct values."""
        parser = SEOAnnotationParser()
        _, annotation = parser.split(seo_draft_content)
        wc = parser.parse_word_count(annotation)
        
        # Confirmed values from reference run
        assert wc["count"] == 2776, f"Expected count 2776, got {wc.get('count')}"
        assert wc["target_min"] == 2200, f"Expected target_min 2200, got {wc.get('target_min')}"
        assert wc["target_max"] == 2800, f"Expected target_max 2800, got {wc.get('target_max')}"
        assert wc["status"] == "within_target", f"Expected status 'within_target', got {wc.get('status')}"

    def test_seo_qa_flags_extracted(self, seo_draft_content):
        """Verify QA flags are extracted from annotation sheet."""
        parser = SEOAnnotationParser()
        _, annotation = parser.split(seo_draft_content)
        flags = parser.parse_qa_flags(annotation)
        
        # Should have at least 4 flags
        assert len(flags) >= 4, f"Expected at least 4 QA flags, got {len(flags)}"
        
        # Confirmed flags from reference run
        assert any("local-seo" in f.lower() or "services/local-seo" in f for f in flags), \
            "Missing local-seo flag"
        assert any("byline" in f.lower() for f in flags), "Missing byline flag"

    def test_seo_annotation_parsing_to_domain_object(self, seo_draft_content):
        """Verify SEOAnnotation domain object is properly populated."""
        parser = SEOAnnotationParser()
        _, annotation = parser.split(seo_draft_content)
        seo_obj = parser.parse_annotation(annotation)
        
        # Verify all major fields are populated
        assert seo_obj.word_count, "word_count is empty"
        assert seo_obj.word_count["count"] == 2776, "Incorrect word count"
        assert seo_obj.meta_title, "meta_title is empty"
        assert seo_obj.meta_description, "meta_description is empty"
        assert seo_obj.changes_summary, "changes_summary is empty"
        assert seo_obj.internal_links, "internal_links is empty"
        assert seo_obj.qa_flags, "qa_flags is empty"

    def test_seo_meta_fields_have_status(self, seo_draft_content):
        """Verify meta title and description include status (PASS/FAIL)."""
        parser = SEOAnnotationParser()
        _, annotation = parser.split(seo_draft_content)
        seo_obj = parser.parse_annotation(annotation)
        
        # Both should have status fields
        assert "status" in seo_obj.meta_title, "meta_title missing status"
        assert seo_obj.meta_title["status"] == "pass", "meta_title status should be 'pass'"
        assert "status" in seo_obj.meta_description, "meta_description missing status"
        assert seo_obj.meta_description["status"] == "pass", "meta_description status should be 'pass'"

    def test_seo_internal_links_have_structure(self, seo_draft_content):
        """Verify internal links have correct structure."""
        parser = SEOAnnotationParser()
        _, annotation = parser.split(seo_draft_content)
        seo_obj = parser.parse_annotation(annotation)
        
        # Each link should have required fields
        assert len(seo_obj.internal_links) >= 2, f"Expected at least 2 links, got {len(seo_obj.internal_links)}"
        
        for link in seo_obj.internal_links:
            assert "anchor" in link, "Link missing 'anchor' field"
            assert "destination" in link, "Link missing 'destination' field"
            assert "section" in link, "Link missing 'section' field"
            assert link["anchor"], "anchor is empty"
            assert link["destination"], "destination is empty"


class TestQASignoffParser:
    """Test QASignoffParser against reference run."""

    def test_qa_signoff_parses_reference_run(self, qa_signoff_content):
        """Verify QA signoff parses into QAResult with correct values."""
        parser = QASignoffParser()
        result = parser.parse(qa_signoff_content)
        
        # Confirmed from reference run
        assert result.decision == QADecision.APPROVED, f"Expected APPROVED, got {result.decision}"
        assert result.checklist_score == (38, 39), f"Expected (38, 39), got {result.checklist_score}"
        assert result.ai_risk_score == 5, f"Expected 5, got {result.ai_risk_score}"
        assert result.section_results["A"] == "pass", f"Expected section A to be 'pass', got {result.section_results['A']}"
        assert result.section_results["F"] == "flag", f"Expected section F to be 'flag', got {result.section_results['F']}"
        assert result.human_review_flag is None, f"Expected human_review_flag None, got {result.human_review_flag}"

    def test_qa_section_f_classified_as_client_decision(self, qa_signoff_content):
        """Verify section F issue is classified as CLIENT_DECISION."""
        parser = QASignoffParser()
        result = parser.parse(qa_signoff_content)
        
        # Find section F issues
        section_f_issues = [i for i in result.issues if i.section == "F"]
        assert len(section_f_issues) >= 1, f"Expected at least 1 section F issue, got {len(section_f_issues)}"
        assert section_f_issues[0].issue_type == QAIssueType.CLIENT_DECISION, \
            f"Expected CLIENT_DECISION, got {section_f_issues[0].issue_type}"
        assert section_f_issues[0].stage_responsible is None, \
            f"Expected stage_responsible None for CLIENT_DECISION, got {section_f_issues[0].stage_responsible}"

    def test_qa_approved_has_no_revision_stage(self, qa_signoff_content):
        """Verify APPROVED decision results in no revision stage."""
        parser = QASignoffParser()
        result = parser.parse(qa_signoff_content)
        
        assert result.decision == QADecision.APPROVED, "Decision should be APPROVED"
        assert result.revision_stage is None, \
            f"Expected revision_stage None for APPROVED decision, got {result.revision_stage}"

    def test_qa_all_sections_present(self, qa_signoff_content):
        """Verify all 9 sections (A–I) are present in results."""
        parser = QASignoffParser()
        result = parser.parse(qa_signoff_content)
        
        expected_sections = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        for section in expected_sections:
            assert section in result.section_results, f"Missing section {section}"
            assert result.section_results[section] in ['pass', 'flag'], \
                f"Section {section} has invalid status: {result.section_results[section]}"

    def test_qa_issue_parsing(self, qa_signoff_content):
        """Verify issues are parsed with complete information."""
        parser = QASignoffParser()
        result = parser.parse(qa_signoff_content)
        
        # Should have at least one issue (the FLAG)
        assert len(result.issues) > 0, "Expected at least one issue"
        
        # Each issue should have required fields
        for issue in result.issues:
            assert issue.description, f"Issue missing description"
            assert issue.issue_type in [QAIssueType.PIPELINE_FAILURE, 
                                       QAIssueType.CLIENT_DECISION, 
                                       QAIssueType.MINOR_OBSERVATION], \
                f"Invalid issue_type: {issue.issue_type}"


class TestDossierParser:
    """Test DossierParser against reference run."""

    def test_dossier_parser_extracts_all_sections(self, dossier_content):
        """Verify all 8 formal sections are extracted."""
        parser = DossierParser()
        parsed = parser.parse(dossier_content)
        
        # All 8 sections should be non-empty
        assert parsed.topic_and_semantic_field != "", "topic_and_semantic_field is empty"
        assert parsed.source_bank != "", "source_bank is empty"
        assert parsed.non_obvious_insight != "", "non_obvious_insight is empty"
        assert parsed.ymyl_assessment != "", "ymyl_assessment is empty"
        assert parsed.content_gap_analysis != "", "content_gap_analysis is empty"
        assert parsed.eeat_framing != "", "eeat_framing is empty"
        assert parsed.search_intent != "", "search_intent is empty"
        assert parsed.audience_value_statement != "", "audience_value_statement is empty"

    def test_dossier_parser_captures_supplemental_notes(self, dossier_content):
        """Verify supplemental notes (9th informal section) are captured."""
        parser = DossierParser()
        parsed = parser.parse(dossier_content)
        
        # The 9th informal section must be captured, not discarded
        assert parsed.supplemental_notes is not None, "supplemental_notes should not be None"
        # Should contain reference to Stage 2 or internal linking (from reference run)
        assert "Stage 2" in parsed.supplemental_notes or "internal link" in parsed.supplemental_notes.lower(), \
            "supplemental_notes missing expected content"

    def test_dossier_source_extraction(self, dossier_content):
        """Verify sources are extracted with correct structure."""
        parser = DossierParser()
        sources = parser.extract_sources(dossier_content)
        
        # Reference run has 5 sources
        assert len(sources) == 5, f"Expected 5 sources, got {len(sources)}"
        
        # Each source must have required fields
        for source in sources:
            assert "url" in source, "Source missing 'url' field"
            assert "institution" in source, "Source missing 'institution' field"
            assert source["url"], "Source url is empty"
            assert source["institution"], "Source institution is empty"

    def test_dossier_source_data_points(self, dossier_content):
        """Verify data points are extracted from each source."""
        parser = DossierParser()
        sources = parser.extract_sources(dossier_content)
        
        # Each source should have data points
        for source in sources:
            assert "data_points" in source, "Source missing 'data_points' field"
            assert len(source["data_points"]) > 0, f"Source {source['institution']} has no data points"

    def test_dossier_content_preservation(self, dossier_content):
        """Verify section content is preserved (not truncated or stripped excessively)."""
        parser = DossierParser()
        parsed = parser.parse(dossier_content)
        
        # Each section should contain substantial content
        for section_name in ['topic_and_semantic_field', 'non_obvious_insight', 'ymyl_assessment',
                             'content_gap_analysis', 'eeat_framing', 'search_intent',
                             'audience_value_statement']:
            section_content = getattr(parsed, section_name)
            assert len(section_content) > 50, f"{section_name} is too short ({len(section_content)} chars)"
