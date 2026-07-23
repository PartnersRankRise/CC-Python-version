# Stage 7: Blog Formatting

Converts the QA-approved markdown draft into a fully self-contained, mobile-responsive branded HTML blog page.

## Load Before Starting

```
Pre-flight gate (check before loading anything else):
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Approved_Draft.md` must exist
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_Stage_7_Handoff.md` must exist
- `Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Revision_Required.md` must NOT exist
  - If it exists: stop. Do not run Stage 7. Report: "QA revision is pending. Resolve the revision and re-run Stage 6 before formatting."

Load in full:
- Clients/[CLIENT]/Reference/Style_Reference_Card.md
- Clients/[CLIENT]/Reference/Brand_Notes.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_QA_Approved_Draft.md
- Clients/[CLIENT]/Runs/[RUN_FOLDER]/06_Stage_7_Handoff.md

If 06_QA_Approved_Draft.md does not exist: stop.
Tell the user Stage 6 must be completed and approved first.

Do not load:
- Earlier drafts (03, 04, 05)
- 01_Research_Dossier.md
- 02_Content_Brief.md
- Any _config/ files
```

## Defensive Parsing (Never Render Internal Tokens)

**Critical:** If any internal-only tokens or blocks are still present in the approved draft (ideally Stage 6 should have caught these), Stage 7 must not publish them:

- **Never render**: `<!--BRIEF: ... -->` blocks, `BEGIN_BLOG_REQUEST` / `END_BLOG_REQUEST` delimiters, or similar non-publishable tokens
- **If found**: stop and report a QA failure upstream. Do not proceed with formatting. (Stage 6 should have caught and failed this already, so finding any indicates a breach in the earlier pipeline.)

## File Output

Write to: `Clients/[CLIENT]/Runs/[RUN_FOLDER]/07_Blog_Final.html`

Also write to: `Clients/[CLIENT]/Published/[ARTICLE_SLUG].html`

Also write to: `Clients/[CLIENT]/Published/[ARTICLE_SLUG].md`

Before stopping, if Stage 11 is enabled for the run, also write:

`Clients/[CLIENT]/Runs/[RUN_FOLDER]/07_Stage_11_Handoff.md`

### Markdown Companion File Requirements

The markdown companion file for Stage 7 must:

- Start with exactly three single-line fields, in this order, followed by a blank line:
  - `Target Keyword: [PRIMARY_KEYWORD]`
  - `Title Tag: [HTML_TITLE_TAG]`
  - `Meta Description: [HTML_META_DESCRIPTION]`
- Use the same primary keyword that drives the run's SEO brief (the one used in Stage 5's SEO draft header).
- Match the final HTML `<title>` element for the Title Tag value.
- Match the final HTML `<meta name="description">` content for the Meta Description value.
- After the three lines and a single blank line, include the complete final article body in markdown (H1, H2, H3, paragraphs, lists, links), mirroring the approved draft and the HTML structure, while still excluding internal-only sections (approval annotations, SEO annotation sheets, editorial notes, etc.).

Example header format:

```markdown
Target Keyword: TPO vs EPDM commercial roofing Colorado
Title Tag: TPO vs EPDM Commercial Roofing Colorado Decision Guide
Meta Description: TPO vs EPDM commercial roofing Colorado decisions should start with hail risk, seams, drainage, and a documented inspection before the budget gets approved.
```

**Non-negotiable rules for this file:**
- MUST be a fully self-contained, mobile-responsive HTML document
- MUST contain the complete approved prose converted to semantic HTML
- All internal and external links from the approved draft MUST be preserved
- MUST NOT be a shell, placeholder, or set of instructions
- MUST be the final publish-ready HTML for this run

---

## CSS Design System

The canonical CSS lives in `templates/blog_integration_base.css`. Do not duplicate it here. The template uses `{{PLACEHOLDER}}` tokens for brand colors replaced at build time from the client's `Style_Reference_Card.md`.

**Token placeholders** (replaced at build time):
- `{{PRIMARY}}` — client primary hex
- `{{PRIMARY_2}}` — client primary-2 hex
- `{{PRIMARY_SOFT}}` — client primary-soft hex
- `{{PRIMARY_GLOW}}` — client primary-glow rgba
- `{{PRIMARY_RGB}}` — client primary r, g, b triplet
- `{{ACCENT}}` — client accent hex
- `{{ACCENT_2}}` — client accent-2 hex
- `{{ACCENT_SOFT}}` — client accent-soft hex
- `{{ACCENT_RGB}}` — client accent r, g, b triplet
- `{{INK}}` — client ink hex
- `{{LINE_STRONG}}` — client line-strong rgba

**CSS unit discipline:**
- `rem` for font sizes, margins, padding, spacing, border-radius, max-width, shadows
- `clamp()` for fluid values that scale with viewport
- `px` only for borders (1px) with `/* px: structural */` comment
- `%` or viewport units for layout widths in `min()` functions
- Breakpoints at `42rem` (tablet) and `58rem` (desktop)

---

## Prose Conversion Rules

**H1:** Rendered inside the `.header` card as the `<h1>` element.

**H2:** `<h2>` inside `.prose` section. Each H2 opens a new `<section class="prose">`.

**H3:** `<h3>` inside the same `.prose` section as its parent H2.

**Paragraphs:** `<p>` tags with all inline content preserved.

**Links:** Preserved as `<a>` tags with exact anchor text and href values from the approved draft.

**Bullet lists:** `<ul>` with `<li>` items.

**Ordered lists:** `<ol>` with `<li>` items, preserving nesting.

**Blockquotes:** `<blockquote>` or `<p class="callout-text">` where contextually appropriate.

**Bold:** `<strong>`. **Italic:** `<em>`.

**CTA:** Final section uses brand contact info from `Brand_Notes.md` (phone, contact URL, service area). Rendered as a `.cta-card` block as the last element.

**Internal-only sections:** Do NOT render any heading titled `APPROVAL ANNOTATION`, `SEO Annotation Sheet`, `Editorial Note`, or similar internal diagnostics. Publication-facing content ends with the last reader-facing CTA section.

---

## Build Process

1. Read `Style_Reference_Card.md` — extract brand color tokens
2. Read `templates/blog_integration_base.css`
3. Replace all `{{PLACEHOLDER}}` tokens with corresponding brand values
4. Read `06_QA_Approved_Draft.md` — parse markdown into semantic HTML per Prose Conversion Rules
5. Read `Brand_Notes.md` — extract CTA contact info (phone, URL, service area)
6. Derive `[ARTICLE_SLUG]` from the H1 in `06_QA_Approved_Draft.md`:
   - lowercase
   - remove characters that are not letters, numbers, or spaces
   - convert spaces to single hyphens
   - trim leading/trailing hyphens
7. Assemble `07_Blog_Final.html` as a single self-contained document:
   - `<head>` containing meta viewport, title, and single `<style>` block
   - `<body>` with skip link and `<article class="blog-wrap" id="main-content">` wrapper
   - Header card with H1 title
   - All prose sections in document order
   - CTA card as final element
8. Write to `Clients/[CLIENT]/Runs/[RUN_FOLDER]/07_Blog_Final.html`
9. Copy the same final HTML to `Clients/[CLIENT]/Published/[ARTICLE_SLUG].html`
10. Assemble the markdown companion file `07_Blog_Final.md`:
    - Use the same H1/H2/H3 hierarchy and prose as the approved draft, excluding internal-only sections.
    - Set the first three lines exactly as:
      - `Target Keyword: [PRIMARY_KEYWORD]`
      - `Title Tag: [HTML_TITLE_TAG]`
      - `Meta Description: [HTML_META_DESCRIPTION]`
    - Leave a single blank line after the meta block, then include the full article body in markdown.
11. Write the markdown companion file to `Clients/[CLIENT]/Published/[ARTICLE_SLUG].md`

Do not inject schema markup. Do not create WordPress body/CSS exports in this stage.

If `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Human_Review_Flag.md` exists, do not block formatting. Carry the flag forward in the completion summary so the batch controller can surface the run for post-pipeline human review.

---

## Handoff Preparation (Before Stopping)

If Stage 11 is enabled, prepare `07_Stage_11_Handoff.md` using `_config/handoff_template.md`.

The handoff must tell Stage 11 to:
- load `_stages/stage_seocial/CONTEXT.md` in full (mandatory first load)
- load `Style_Reference_Card.md` in full
- load `Audience_Profile.md` in full
- load `Brand_Notes.md` in full
- load `06_QA_Approved_Draft.md` in full
- load `07_Stage_11_Handoff.md` in full
- load `01_Research_Dossier.md` sections: Non-Obvious Insight, Source Bank
- load `02_Content_Brief.md` sections: Keyword Strategy, Audience Definition
- optionally use `Clients/[CLIENT]/Published/[ARTICLE_SLUG].html`
- avoid `03_First_Draft.md`, `04_Humanized_Draft.md`, `05_SEO_Draft.md`, and all `_config/` files

Carry forward:
- article slug
- final CTA phrasing
- publish path
- any distribution notes relevant to the finished article

Set `Auto-run next stage: true` only if Stage 11 is enabled for the run. Otherwise set it to `false` with reason `Stage 11 not enabled`.

## Quality Gates

**Content integrity:**
- [ ] All files loaded match the `Load Before Starting` contract in this file (nothing missing, nothing forbidden)
- [ ] `06_QA_Revision_Required.md` absent from the run folder before formatting starts
- [ ] Output is a complete, self-contained HTML document (has html, head, body) and a markdown companion file
- [ ] Single `<article class="blog-wrap" id="main-content">` wrapper present
- [ ] All H2 sections from approved draft present in correct order
- [ ] No prose content removed, summarized, or rewritten
- [ ] All internal links preserved with correct href and anchor text
- [ ] All external links preserved with correct href and anchor text
- [ ] CTA section present with correct brand contact info from Brand_Notes.md
- [ ] Meta description matches approved draft
- [ ] Final slug derived correctly from the approved H1
- [ ] `Clients/[CLIENT]/Published/[ARTICLE_SLUG].html` exists and matches the final HTML
- [ ] `Clients/[CLIENT]/Published/[ARTICLE_SLUG].md` exists and matches the final markdown companion file
**Technical:**
- [ ] CSS uses fluid tokens (no hardcoded px except borders with `/* px: structural */` comment)
- [ ] Page renders correctly from 320px to 1400px viewport width
- [ ] Single unified `<style>` block inlined from template
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1.0">` present
- [ ] `-webkit-text-size-adjust: 100%` on body
- [ ] No external CSS or JS
- [ ] No placeholder text
- [ ] Skip link present for accessibility
- [ ] All responsive breakpoints present (42rem, 58rem, reduced-motion, print)
- [ ] File does NOT contain "presentation shell", "this layout is a shell", "render in your CMS", or any placeholder language
- [ ] No schema markup injected
- [ ] `07_Stage_11_Handoff.md` written if Stage 11 is enabled for the run

Append to `Clients/[CLIENT]/Runs/[RUN_FOLDER]/Run_Log.md`:
```
[YYYY-MM-DD] | Stage 7 | Blog Formatting | Status: COMPLETE
```

Also append once to the client summary index at `Clients/[CLIENT]/Run_Log.md`:
```
[YYYY-MM-DD] | [RUN_FOLDER] | Stages: Pre-1 through 7 | Status: COMPLETE
```

Completion summary to the user must include:
- final run path
- published HTML path
- whether Stage 11 handoff was written
- contents of `Human_Review_Flag.md` if that file exists
