-- Created: Thursday Jul 23, 2026, 4:26 PM (UTC-6)
-- Last edited: Thursday Jul 23, 2026, 4:26 PM (UTC-6)

-- Manual Test Client Data Insert
-- Use this in Supabase SQL Editor if the pytest fixture fails
-- Run after seed_data.sql has been applied

-- ============================================================
-- TEST CLIENT
-- ============================================================

INSERT INTO clients (
  id, name, website_url, industry, service_area, off_limits, engaged_at
) VALUES (
  'a1234567-b89c-d012-e345-f6789abcdef0',
  'Test Home Services',
  'https://test-plumbing.example.com',
  'home_services',
  'Denver, CO',
  '{}',
  NOW()::DATE
);

-- ============================================================
-- CLIENT CONTEXTS
-- ============================================================

INSERT INTO client_contexts (
  id, client_id, next_planned_topic, engagement_notes, run_history_summary
) VALUES (
  'b2345678-c90d-e123-f456-a7890bcdef01',
  'a1234567-b89c-d012-e345-f6789abcdef0',
  NULL,
  'Test client for integration testing',
  NULL
);

-- ============================================================
-- CLIENT REFERENCE FILES
-- ============================================================

INSERT INTO client_reference_files (
  id, client_id, style_reference_card, audience_profile, brand_notes,
  onboarding_state, brand_colors, display_font, body_font, google_fonts_url,
  reading_level_target, technical_depth, certifications, years_in_business, ymyl_category
) VALUES (
  'c3456789-d01e-f234-a567-b8901cdef012',
  'a1234567-b89c-d012-e345-f6789abcdef0',
  '# Style Reference Card

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
Google Fonts URL: https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans',
  '# Audience Profile

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
- Concerns about quality work',
  '# Brand Notes

## Company Background

Years in Business: 10
Certifications: NAPLPS, Local Chamber Member
YMYL Category: safety

## Services

We provide expert plumbing services for residential and commercial clients.

## Open Questions

? What are your most common customer concerns we should address?
? Do you want to highlight specific service areas or certifications?
? Any recent projects you are particularly proud of we should mention?',
  'fully_onboarded',
  jsonb_build_object(
    'primary', '#FF0000',
    'primary_2', '#C80000',
    'primary_soft', '#FFC8C8',
    'primary_glow', 'rgba(255, 0, 0, 0.3)',
    'primary_rgb', '255, 0, 0',
    'accent', '#0000FF',
    'accent_2', '#0000C8',
    'accent_soft', '#C8C8FF',
    'accent_rgb', '0, 0, 255',
    'ink', '#323232',
    'line_strong', 'rgba(50, 50, 50, 0.8)'
  ),
  'DM Serif Display',
  'DM Sans',
  'https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans',
  '8th-10th grade',
  'beginner',
  ARRAY['NAPLPS'],
  10,
  'safety'
);

-- ============================================================
-- PUBLISHED ARTICLES (for overlap detection tests)
-- ============================================================

INSERT INTO published_articles (
  id, client_id, article_slug, title_tag, meta_description, primary_keyword, html_content, markdown_content
) VALUES (
  'd4567890-e12f-a345-b678-c9012def0123',
  'a1234567-b89c-d012-e345-f6789abcdef0',
  'plumbing-101',
  'Plumbing 101: Everything You Need to Know',
  'Complete guide to home plumbing basics',
  'plumbing basics',
  '<article><h1>Plumbing 101</h1></article>',
  '# Plumbing 101

Content here'
);

INSERT INTO published_articles (
  id, client_id, article_slug, title_tag, meta_description, primary_keyword, html_content, markdown_content
) VALUES (
  'e5678901-f234-b456-c789-d0123ef01234',
  'a1234567-b89c-d012-e345-f6789abcdef0',
  'water-heater-guide',
  'Water Heater Installation Guide',
  'Step-by-step guide to water heater installation',
  'water heater',
  '<article><h1>Water Heater Guide</h1></article>',
  '# Water Heater Guide

Content here'
);

-- ============================================================
-- VERIFICATION
-- ============================================================

-- Check test data was inserted:
-- SELECT COUNT(*) FROM clients WHERE name = 'Test Home Services';
-- SELECT COUNT(*) FROM client_reference_files WHERE client_id = (SELECT id FROM clients WHERE name = 'Test Home Services');
-- SELECT COUNT(*) FROM published_articles WHERE client_id = (SELECT id FROM clients WHERE name = 'Test Home Services');

-- Delete test data when done (if manual insert):
-- DELETE FROM published_articles WHERE client_id = 'a1234567-b89c-d012-e345-f6789abcdef0';
-- DELETE FROM client_reference_files WHERE client_id = 'a1234567-b89c-d012-e345-f6789abcdef0';
-- DELETE FROM client_contexts WHERE client_id = 'a1234567-b89c-d012-e345-f6789abcdef0';
-- DELETE FROM clients WHERE id = 'a1234567-b89c-d012-e345-f6789abcdef0';
