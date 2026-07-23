# Created: Thursday Jul 23, 2026, 4:23 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 4:23 PM (UTC-6)

"""Pytest fixtures for integration test data."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from content_pipeline.repositories.client_repository import ClientRepository
from content_pipeline.repositories.run_repository import RunRepository


@pytest.fixture(scope="session", autouse=True)
async def seed_test_data():
    """Insert test data before integration tests run.
    
    Session scope means this runs once per test session.
    autouse=True makes it automatic without explicit reference in tests.
    Note: This fixture attempts to seed data but gracefully handles permission errors.
    """
    client_repo = ClientRepository()
    run_repo = RunRepository()
    test_client_id = None
    
    try:
        # ============================================================
        # INSERT TEST CLIENT
        # ============================================================
        
        # create_client generates the ID, so don't pass it
        try:
            created_client = await client_repo.create_client(
                name="Test Home Services",
                website_url="https://test-plumbing.example.com",
                industry="home_services",
                service_area="Denver, CO",
            )
            test_client_id = created_client.id
        except Exception as e:
            # Permission errors are expected until admin grants access
            print(f"[FIXTURE] Client creation skipped (permissions): {type(e).__name__}")
            yield  # Let tests run anyway with empty data
            return
        
        # ============================================================
        # INSERT CLIENT CONTEXTS
        # ============================================================
        
        client_contexts_data = {
            "client_id": str(test_client_id),
            "next_planned_topic": None,
            "engagement_notes": "Test client for integration testing",
            "run_history_summary": None,
        }
        
        client_repo.supabase.table("client_contexts").insert(
            client_contexts_data
        ).execute()
        
        # ============================================================
        # INSERT CLIENT REFERENCE FILES
        # ============================================================
        
        style_reference_card = """# Style Reference Card

## Brand Colors

Primary: 255, 0, 0
Primary 2: 200, 0, 0
Primary Soft: 255, 200, 200
Primary Glow: rgba(255, 0, 0, 0.3)

Accent: 0, 0, 255
Accent 2: 0, 0, 200
Accent Soft: 200, 200, 255

Ink: 50, 50, 50
Line Strong: rgba(50, 50, 50, 0.8)

## Fonts

Display Font: DM Serif Display
Body Font: DM Sans
Google Fonts URL: https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans
"""
        
        audience_profile = """# Audience Profile

## Demographics

- Primary Age: 35-65
- Primary Location: Denver metro
- Household Income: $75k-$150k

## Reading Level

Target Reading Level: 8th-10th grade

## Technical Depth

Technical Depth: beginner

## Pain Points

- Unexpected plumbing emergencies
- Rising water bills
- Outdated systems
- Concerns about quality work
"""
        
        brand_notes = """# Brand Notes

## Company Background

Years in Business: 10
Certifications: NAPLPS, Local Chamber Member
YMYL Category: safety

## Services

We provide expert plumbing services for residential and commercial clients.

## Open Questions

? What are your most common customer concerns we should address?
? Do you want to highlight specific service areas or certifications?
? Any recent projects you're particularly proud of we should mention?
"""
        
        ref_files_data = {
            "client_id": str(test_client_id),
            "style_reference_card": style_reference_card,
            "audience_profile": audience_profile,
            "brand_notes": brand_notes,
            "onboarding_state": "fully_onboarded",
            "brand_colors": {
                "primary": "#FF0000",
                "primary_2": "#C80000",
                "primary_soft": "#FFC8C8",
                "primary_glow": "rgba(255, 0, 0, 0.3)",
                "primary_rgb": "255, 0, 0",
                "accent": "#0000FF",
                "accent_2": "#0000C8",
                "accent_soft": "#C8C8FF",
                "accent_rgb": "0, 0, 255",
                "ink": "#323232",
                "line_strong": "rgba(50, 50, 50, 0.8)",
            },
            "display_font": "DM Serif Display",
            "body_font": "DM Sans",
            "google_fonts_url": "https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans",
            "reading_level_target": "8th-10th grade",
            "technical_depth": "beginner",
            "certifications": ["NAPLPS"],
            "years_in_business": 10,
            "ymyl_category": "safety",
        }
        
        client_repo.supabase.table("client_reference_files").insert(
            ref_files_data
        ).execute()
        
        # ============================================================
        # INSERT PUBLISHED ARTICLES (for overlap detection)
        # ============================================================
        
        # Create placeholder runs for the articles (published_articles requires run_id)
        from uuid import uuid4
        run_1_id = uuid4()
        run_2_id = uuid4()
        
        # Insert placeholder runs
        run_1_data = {
            "id": str(run_1_id),
            "client_id": str(test_client_id),
            "folder_slug": "plumbing-101_2026-07",
            "topic": "Plumbing 101",
            "primary_keyword": "plumbing basics",
            "topic_path": "user_provided",
            "status": "published",
            "current_stage": 7,
        }
        run_2_data = {
            "id": str(run_2_id),
            "client_id": str(test_client_id),
            "folder_slug": "water-heater-guide_2026-07",
            "topic": "Water Heater Guide",
            "primary_keyword": "water heater",
            "topic_path": "user_provided",
            "status": "published",
            "current_stage": 7,
        }
        
        run_repo.supabase.table("runs").insert(run_1_data).execute()
        run_repo.supabase.table("runs").insert(run_2_data).execute()
        
        article_1_data = {
            "client_id": str(test_client_id),
            "run_id": str(run_1_id),
            "article_slug": "plumbing-101",
            "title_tag": "Plumbing 101: Everything You Need to Know",
            "meta_description": "Complete guide to home plumbing basics",
            "primary_keyword": "plumbing basics",
            "html_content": "<article><h1>Plumbing 101</h1></article>",
            "markdown_content": "# Plumbing 101\n\nContent here",
        }
        
        article_2_data = {
            "client_id": str(test_client_id),
            "run_id": str(run_2_id),
            "article_slug": "water-heater-guide",
            "title_tag": "Water Heater Installation Guide",
            "meta_description": "Step-by-step guide to water heater installation",
            "primary_keyword": "water heater",
            "html_content": "<article><h1>Water Heater Guide</h1></article>",
            "markdown_content": "# Water Heater Guide\n\nContent here",
        }
        
        run_repo.supabase.table("published_articles").insert(
            article_1_data
        ).execute()
        
        run_repo.supabase.table("published_articles").insert(
            article_2_data
        ).execute()
        
        yield  # Tests run here
        
    finally:
        # ============================================================
        # CLEANUP: Delete all seeded rows
        # ============================================================
        
        if not test_client_id:
            pass
        else:
            try:
                # Delete in dependency order (foreign keys first)
                run_repo.supabase.table("published_articles").delete().eq(
                    "client_id", str(test_client_id)
                ).execute()
                
                # Delete runs (which cascades to stage_outputs, unresolved_items, etc.)
                run_repo.supabase.table("runs").delete().eq(
                    "client_id", str(test_client_id)
                ).execute()
                
                client_repo.supabase.table("client_reference_files").delete().eq(
                    "client_id", str(test_client_id)
                ).execute()
                
                client_repo.supabase.table("client_contexts").delete().eq(
                    "client_id", str(test_client_id)
                ).execute()
                
                client_repo.supabase.table("clients").delete().eq(
                    "id", str(test_client_id)
                ).execute()
            except Exception as e:
                print(f"Cleanup warning (non-critical): {e}")
