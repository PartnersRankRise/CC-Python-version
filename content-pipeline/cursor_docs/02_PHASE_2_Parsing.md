# Phase 2 — Parsing Layer
**Weeks 3–4 | Gate: All six parsers pass tests against reference run files**

The parsing layer is the most critical infrastructure in the project. Every stage service depends on these parsers to correctly separate article content from appended sections. Build and test all six before writing any stage service.

The reference run files in `reference_run/` are your test fixtures. Every parser test uses real pipeline output as input.

---

## Step 2.1 — BriefParser

```
Create content_pipeline/parsing/brief_parser.py.

This parser has one critical constraint discovered from the reference run:
The content types table in 02_Content_Brief.md sits BETWEEN two <!--BRIEF: ... --> blocks.
It must survive stripping. strip_brief_tokens() must remove BRIEF blocks but preserve
everything else including tables that appear adjacent to those blocks.

Read BUILD_GUIDE.md — the "BriefParser" section contains the core implementation.

The parser must:
1. strip_brief_tokens(markdown: str) -> str
   - Removes all <!--BRIEF: ... --> blocks (multi-line; use re.DOTALL)
   - Preserves all other content including markdown tables
   - Cleans up extra blank lines left behind

2. extract_content_table(section: str) -> Optional[str]
   - Extracts the first markdown table from a section
   - Returns the raw markdown table string

3. parse(brief_markdown: str) -> ParsedBrief
   - Splits by "## N. SECTION NAME" headings
   - Returns a ParsedBrief dataclass with all 10 sections

Create ParsedBrief in content_pipeline/domain/stage.py if not already there.

Then create tests/test_parsers.py with this test:

def test_brief_parser_preserves_table():
    brief_content = open("reference_run/02_Content_Brief.md").read()
    parser = BriefParser()
    stripped = parser.strip_brief_tokens(brief_content)
    
    # The content types table must survive stripping
    assert "| Content Type |" in stripped, "Content types table was removed by BRIEF stripping"
    assert "| Blog posts" in stripped, "Blog posts row was removed"
    
    # No BRIEF tokens should remain
    assert "<!--BRIEF:" not in stripped, "BRIEF token found after stripping"
    assert "-->" not in stripped or "<!--" not in stripped  # no remaining comment blocks

def test_brief_parser_section_count():
    brief_content = open("reference_run/02_Content_Brief.md").read()
    parser = BriefParser()
    parsed = parser.parse(brief_content)
    
    assert parsed.keyword_strategy is not None
    assert parsed.audience_definition != ""
    assert parsed.cta_direction is not None

Run the tests. Show me the output. Fix until both pass.
```

---

## Step 2.2 — EditorialNoteParser

```
Create content_pipeline/parsing/editorial_note_parser.py.

This is the simplest parser. It splits 04_Humanized_Draft.md at "## Editorial Note".

The parser must:
1. split(humanized_draft: str) -> tuple[str, Optional[str]]
   - Returns (article_body, editorial_note)
   - Splits on the exact string "\n## Editorial Note\n"
   - If separator not found, returns (full_content, None)
   - article_body should not have trailing whitespace

Add to tests/test_parsers.py:

def test_editorial_note_splits_correctly():
    draft = open("reference_run/04_Humanized_Draft.md").read()
    parser = EditorialNoteParser()
    article, note = parser.split(draft)
    
    # Article body must not contain the editorial note
    assert "## Editorial Note" not in article
    
    # Editorial note must contain all 5 confirmed sub-sections
    assert note is not None
    assert "Structural changes" in note
    assert "Rhythm" in note
    assert "Experience additions" in note
    assert "E-E-A-T" in note
    assert "QA concern" in note
    
    # Critical: article body must not be empty
    assert len(article) > 1000, f"Article body seems too short: {len(article)} chars"

def test_editorial_note_body_has_no_token_leakage():
    draft = open("reference_run/04_Humanized_Draft.md").read()
    parser = EditorialNoteParser()
    article, note = parser.split(draft)
    
    assert "<!--BRIEF:" not in article
    assert "BEGIN_BLOG_REQUEST" not in article

Run the tests. Show me the output.
```

---

## Step 2.3 — SEOAnnotationParser

```
Create content_pipeline/parsing/seo_annotation_parser.py.

This parser splits 05_SEO_Draft.md at "## SEO Annotation Sheet" and then parses
the annotation sheet into structured fields.

The parser must:
1. split(seo_draft: str) -> tuple[str, str]
   - Returns (article_body, annotation_text)
   - Splits on "\n## SEO Annotation Sheet\n"

2. parse_word_count(annotation: str) -> dict
   - Parses the word count line: "2776 words | target: 2200-2800 | WITHIN TARGET"
   - Returns: {"count": 2776, "target_min": 2200, "target_max": 2800, "status": "within_target"}
   - status values: "within_target", "over_target", "under_target"

3. parse_qa_flags(annotation: str) -> list[str]
   - Extracts the bulleted list under "Flags for QA Agent:"
   - Returns list of flag strings

4. parse_annotation(annotation_text: str) -> SEOAnnotation
   - Returns a fully populated SEOAnnotation domain object

Add to tests/test_parsers.py:

def test_seo_annotation_splits_correctly():
    draft = open("reference_run/05_SEO_Draft.md").read()
    parser = SEOAnnotationParser()
    article, annotation = parser.split(draft)
    
    assert "## SEO Annotation Sheet" not in article
    assert "Summary of Changes" in annotation
    assert "Word Count Note" in annotation

def test_seo_word_count_parses_to_structured_data():
    draft = open("reference_run/05_SEO_Draft.md").read()
    parser = SEOAnnotationParser()
    _, annotation = parser.split(draft)
    wc = parser.parse_word_count(annotation)
    
    # Confirmed values from reference run
    assert wc["count"] == 2776
    assert wc["target_min"] == 2200
    assert wc["target_max"] == 2800
    assert wc["status"] == "within_target"

def test_seo_qa_flags_extracted():
    draft = open("reference_run/05_SEO_Draft.md").read()
    parser = SEOAnnotationParser()
    _, annotation = parser.split(draft)
    flags = parser.parse_qa_flags(annotation)
    
    assert len(flags) >= 4, f"Expected at least 4 QA flags, got {len(flags)}"
    # Confirmed flags from reference run
    assert any("local-seo" in f.lower() or "services/local-seo" in f for f in flags)
    assert any("byline" in f.lower() for f in flags)

Run the tests. Show me the output.
```

---

## Step 2.4 — QASignoffParser

```
Create content_pipeline/parsing/qa_signoff_parser.py.

This parser reads 06_QA_Signoff.md and produces a QAResult domain object.

The parser must:
1. parse(signoff_text: str) -> QAResult
   - Extracts: decision (APPROVED/REVISION REQUIRED)
   - Extracts: checklist_score as tuple[int, int] (e.g., (38, 39))
   - Extracts: ai_risk_score as int (e.g., 5)
   - Extracts: section_results as dict {"A": "pass", "B": "pass", "F": "flag", ...}
   - Extracts: issues as list[QAIssue] — each with section, description, issue_type, stage_responsible
   - Extracts: human_review_flag (None or string)
   - Computes: revision_stage (None if APPROVED)

2. classify_issue(stage_responsible_text: str) -> QAIssueType
   - "client/publisher decision" or "publisher" in text → CLIENT_DECISION
   - A stage number (3, 4, 5) in text → PIPELINE_FAILURE
   - None or "minor" → MINOR_OBSERVATION

Add to tests/test_parsers.py:

def test_qa_signoff_parses_reference_run():
    signoff = open("reference_run/06_QA_Signoff.md").read()
    parser = QASignoffParser()
    result = parser.parse(signoff)
    
    # Confirmed from reference run
    assert result.decision == QADecision.APPROVED
    assert result.checklist_score == (38, 39)
    assert result.ai_risk_score == 5
    assert result.section_results["A"] == "pass"
    assert result.section_results["F"] == "flag"
    assert result.human_review_flag is None

def test_qa_section_f_classified_as_client_decision():
    signoff = open("reference_run/06_QA_Signoff.md").read()
    parser = QASignoffParser()
    result = parser.parse(signoff)
    
    section_f_issues = [i for i in result.issues if i.section == "F"]
    assert len(section_f_issues) >= 1
    assert section_f_issues[0].issue_type == QAIssueType.CLIENT_DECISION
    assert section_f_issues[0].stage_responsible is None

def test_qa_approved_has_no_revision_stage():
    signoff = open("reference_run/06_QA_Signoff.md").read()
    parser = QASignoffParser()
    result = parser.parse(signoff)
    
    assert result.revision_stage is None

Run the tests. Show me the output.
```

---

## Step 2.5 — DossierParser

```
Create content_pipeline/parsing/dossier_parser.py.

This parser reads 01_Research_Dossier.md and extracts its sections.

The Research Dossier has 8 formal sections:
1. TOPIC AND SEMANTIC FIELD
2. SOURCE BANK
3. NON-OBVIOUS INSIGHT
4. YMYL ASSESSMENT
5. CONTENT GAP ANALYSIS
6. RECOMMENDED E-E-A-T FRAMING
7. SEARCH INTENT CLASSIFICATION
8. AUDIENCE VALUE STATEMENT

IMPORTANT: The reference run dossier also has a 9th informal section
"RESEARCH NOTES FOR STAGE 2" that is NOT in the spec but exists in real output.
Store it in supplemental_notes. Do not discard it.

The parser must:
1. parse(dossier_text: str) -> ParsedDossier
   Returns a dataclass with fields for all 8 sections plus supplemental_notes

2. extract_sources(dossier_text: str) -> list[dict]
   Extracts the Source Bank as a list of dicts with fields:
   {url, institution, publication_date, data_points: list[str]}

Add to tests/test_parsers.py:

def test_dossier_parser_extracts_all_sections():
    dossier = open("reference_run/01_Research_Dossier.md").read()
    parser = DossierParser()
    parsed = parser.parse(dossier)
    
    assert parsed.topic_and_semantic_field != ""
    assert parsed.source_bank != ""
    assert parsed.non_obvious_insight != ""
    assert parsed.ymyl_assessment != ""
    assert parsed.content_gap_analysis != ""
    assert parsed.eeat_framing != ""
    assert parsed.search_intent != ""
    assert parsed.audience_value_statement != ""

def test_dossier_parser_captures_supplemental_notes():
    dossier = open("reference_run/01_Research_Dossier.md").read()
    parser = DossierParser()
    parsed = parser.parse(dossier)
    
    # The 9th informal section must be captured, not discarded
    assert parsed.supplemental_notes is not None
    assert "Stage 2" in parsed.supplemental_notes or "internal link" in parsed.supplemental_notes.lower()

def test_dossier_source_extraction():
    dossier = open("reference_run/01_Research_Dossier.md").read()
    parser = DossierParser()
    sources = parser.extract_sources(dossier)
    
    # Reference run has 5 sources
    assert len(sources) == 5
    assert all("url" in s for s in sources)
    assert all("institution" in s for s in sources)

Run the tests. Show me the output.
```

---

## Step 2.6 — HandoffParser

```
Create content_pipeline/parsing/handoff_parser.py.

Handoff documents have a consistent structure across all stages.
This parser extracts the structured fields.

The parser must:
1. parse(handoff_text: str) -> ParsedHandoff
   Returns a dataclass with fields:
   - status: str
   - created_by: str
   - created: str
   - client: str
   - run: str
   - next_stage_number: int
   - next_stage_name: str
   - expected_output: str
   - carry_forward: dict (topic, primary_keyword, angle_notes, priority_sources,
                          internal_links, unresolved_items, authority_mode)
   - auto_run: bool
   - auto_run_reason: Optional[str]

2. extract_authority_mode(handoff_text: str) -> tuple[AuthorityMode, Optional[dict]]
   - Returns (NORMAL, None) if no Authority_Mode section
   - Returns (EXPERT_FALLBACK, fallback_fields_dict) if fallback section present

Add to tests/test_parsers.py:

def test_handoff_parser_stage_1_handoff():
    handoff = open("reference_run/00_Stage_1_Handoff_Brief.md").read()
    parser = HandoffParser()
    parsed = parser.parse(handoff)
    
    assert parsed.next_stage_number == 1
    assert parsed.next_stage_name.lower() == "research"
    assert parsed.carry_forward["topic"] != ""
    assert parsed.carry_forward["primary_keyword"] == "content marketing for home service businesses"
    assert parsed.auto_run == False

def test_handoff_parser_authority_mode_normal():
    handoff = open("reference_run/01_Stage_2_Handoff.md").read()
    parser = HandoffParser()
    mode, fallback = parser.extract_authority_mode(handoff)
    
    # Reference run had no fallback
    assert mode == AuthorityMode.NORMAL
    assert fallback is None

Run the tests. Show me the output.
```

---

## Phase 2 Gate Check

```
Phase 2 gate check. Run the full test suite and show me results for all parser tests.

Then answer these questions from the actual test output:

1. How many tests are in tests/test_parsers.py and how many pass?

2. Does BriefParser.strip_brief_tokens() preserve the content types table?
   Show me the first 3 rows of the table in the stripped output.

3. Does SEOAnnotationParser.parse_word_count() return exactly:
   {"count": 2776, "target_min": 2200, "target_max": 2800, "status": "within_target"}?

4. Does QASignoffParser classify the Section F issue as CLIENT_DECISION
   with stage_responsible = None?

5. Does DossierParser capture supplemental_notes (the informal 9th section)?
   Show me the first 50 characters of supplemental_notes.

All five must be confirmed before moving to Phase 3.
```

**Human:** Verify the gate check output yourself. The QA Signoff parser is the trickiest — confirm Section F is CLIENT_DECISION by reading `reference_run/06_QA_Signoff.md` and checking that "client/publisher decision" appears in the issue text.
