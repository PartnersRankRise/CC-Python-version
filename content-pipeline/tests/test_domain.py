# Created: Thursday Jul 23, 2026, 11:32 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:32 AM (UTC-6)

"""Tests for domain models — enums, clients, runs, and stages."""

import pytest
from uuid import UUID

from content_pipeline.domain.client import UnresolvedItem, RunContext, Client
from content_pipeline.domain.enums import TopicPath, AuthorityMode
from content_pipeline.domain.run import Run
from content_pipeline.domain.stage import (
    QAIssue,
    QAResult,
    QADecision,
    QAIssueType,
    SEOAnnotation,
    StageOutput,
    StageStatus,
)


def test_unresolved_item_creation():
    """Test UnresolvedItem can be created with required fields."""
    item = UnresolvedItem(
        description="Citation needed for claim",
        blocks_run=False,
        source_stage=2,
    )
    assert item.description == "Citation needed for claim"
    assert item.blocks_run is False
    assert item.source_stage == 2
    assert item.resolved is False
    assert item.resolved_at_stage is None


def test_run_context_creation(test_uuid):
    """Test RunContext with UnresolvedItem tracking."""
    client_id = test_uuid
    
    context = RunContext(
        client_id=client_id,
        topic="How to Fix Air Conditioning Issues",
        primary_keyword="ac repair home",
        topic_path=TopicPath.USER_PROVIDED,
    )
    
    assert context.client_id == client_id
    assert context.topic == "How to Fix Air Conditioning Issues"
    assert context.primary_keyword == "ac repair home"
    assert context.topic_path == TopicPath.USER_PROVIDED
    assert context.authority_mode == AuthorityMode.NORMAL
    assert len(context.unresolved_items) == 0


def test_run_context_with_unresolved_items(test_uuid):
    """Test adding UnresolvedItems to RunContext."""
    context = RunContext(
        client_id=test_uuid,
        topic="Test Topic",
        primary_keyword="test keyword",
        topic_path=TopicPath.USER_PROVIDED,
    )
    
    item1 = UnresolvedItem(
        description="Verify licensing information",
        blocks_run=False,
        source_stage=1,
    )
    item2 = UnresolvedItem(
        description="Missing service area coverage",
        blocks_run=True,
        source_stage=2,
    )
    
    context.unresolved_items.append(item1)
    context.unresolved_items.append(item2)
    
    assert len(context.unresolved_items) == 2
    assert context.unresolved_items[0].description == "Verify licensing information"
    assert context.unresolved_items[0].blocks_run is False
    assert context.unresolved_items[1].description == "Missing service area coverage"
    assert context.unresolved_items[1].blocks_run is True


def test_run_creation(test_uuid):
    """Test Run model with RunContext."""
    from datetime import datetime
    from content_pipeline.domain.enums import RunStatus
    
    context = RunContext(
        client_id=test_uuid,
        topic="Test Article",
        primary_keyword="test",
        topic_path=TopicPath.USER_PROVIDED,
    )
    
    run = Run(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        client_id=test_uuid,
        folder_slug="Test_Article_2026-07",
        status=RunStatus.INITIATED,
        context=context,
        current_stage=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    assert run.status == RunStatus.INITIATED
    assert run.current_stage == 0
    assert run.context.topic == "Test Article"
    assert run.dry_run is False


def test_seo_annotation_creation():
    """Test SEOAnnotation can be created and populated."""
    annotation = SEOAnnotation(
        changes_summary=["Added internal links", "Optimized headings"],
        keyword_density={
            "ac repair": {"occurrences": 5, "density_pct": 2.1, "status": "optimal"}
        },
        meta_title={
            "text": "Best AC Repair Services | Company Name",
            "char_count": 45,
            "status": "valid",
        },
        schema_recommendation="LocalBusiness",
    )
    
    assert len(annotation.changes_summary) == 2
    assert annotation.keyword_density["ac repair"]["status"] == "optimal"
    assert annotation.meta_title["status"] == "valid"
    assert annotation.schema_recommendation == "LocalBusiness"


def test_qa_result_creation():
    """Test QAResult with issues."""
    issue1 = QAIssue(
        section="A",
        description="Claim lacks proper citation",
        issue_type=QAIssueType.PIPELINE_FAILURE,
        stage_responsible=1,
    )
    
    result = QAResult(
        decision=QADecision.REVISION_REQUIRED,
        checklist_score=(35, 39),
        ai_risk_score=8,
        section_results={"A": "FAIL", "B": "PASS", "C": "PASS"},
        issues=[issue1],
        revision_stage=3,
    )
    
    assert result.decision == QADecision.REVISION_REQUIRED
    assert result.checklist_score == (35, 39)
    assert result.ai_risk_score == 8
    assert len(result.issues) == 1
    assert result.issues[0].stage_responsible == 1
    assert result.revision_stage == 3


def test_stage_output_creation(test_uuid):
    """Test StageOutput model."""
    from datetime import datetime
    
    output = StageOutput(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        run_id=test_uuid,
        stage_number=3,
        stage_name="Writing",
        attempt=1,
        status=StageStatus.COMPLETE,
        article_content="This is the article content...",
        created_at=datetime.now(),
    )
    
    assert output.stage_number == 3
    assert output.stage_name == "Writing"
    assert output.status == StageStatus.COMPLETE
    assert output.article_content is not None
    assert output.editorial_note is None
    assert output.seo_annotation is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
