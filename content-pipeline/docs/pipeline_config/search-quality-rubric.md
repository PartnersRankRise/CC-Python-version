# Search Quality Rubric

Canonical search quality, AI-content, and AI-search standards for the content pipeline. Each stage loads only the sections relevant to its work. If a stage CONTEXT.md and this rubric diverge, this rubric governs.

**Section loading guide:**
- Stages 1–4 (Research, Brief, Writing, Humanization): load Sections 1–4
- Stage 5 (SEO): load Sections 1, 5–6
- Stage 6 (QA): load all sections (or use the anti-ai-checklist.md which operationalizes Sections 1–4)
- Stages 7–10 (HTML, Schema, Publication): load Section 5 only if needed for AI-search anti-pattern checks
- This file is NOT loaded by default — load only the sections listed for the current stage

---

## SECTION 1: PEOPLE-FIRST CONTENT STANDARD

Content exists to help a real audience, not primarily to rank.

- The post must serve an existing or intended audience who would find it useful if they came directly to the site.
- After reading, the reader must have learned enough to make a meaningful decision or take a meaningful action independently.
- The reader must leave feeling satisfied, not needing to search again for better information.
- The H1 must accurately describe the value delivered — never misleading or shock-driven.
- Content must not withhold genuinely useful guidance to force conversion.
- The post must have a clear primary purpose aligned with the client's area of authority.

Red flags (any "yes" requires revision):
- Was this topic chosen primarily because it trends, not because the client's audience needs it?
- Does the post mainly summarize what others have already said without adding value?
- Would swapping the client name for a competitor's name make no difference to the content?
- Does the content promise to answer a question it cannot actually resolve?

---

## SECTION 2: E-E-A-T EXECUTION RULES

Trust is the primary bar. The other pillars contribute to it.

**EXPERIENCE**
- At least one named case, practitioner observation, verifiable local detail, or source-cited statistic that could only come from direct exposure to this industry or topic.
- No section may rely entirely on hypothetical scenarios as its only evidence.

**EXPERTISE**
- Mechanism-level understanding demonstrated: not just what, but why and how.
- At least one direct opinion or professional assertion per major section.
- At least one counterintuitive or non-obvious insight present.

**AUTHORITATIVENESS**
- The post must establish why this client has standing on this topic.
- External sources must be authoritative: government, peer-reviewed, industry standards, or major media with named data.
- No unsourced superlatives without evidence.

**TRUSTWORTHINESS**
- Every empirical claim cites a source inline. Empirical claims include statistics, study findings, regulatory requirements, and specific numerical thresholds. Industry-consensus ranges, firsthand practitioner observations, and common professional knowledge do not require external citation but should be framed as experience-based rather than presented as research findings.
- Sources accessible, current within 3 years unless foundational, and support the specific claim made.
- YMYL topics require credentialed sources or explicit acknowledgment of limits.
- No guarantees the client cannot support.

**Authorship and authority signals:**
- Byline or author attribution where readers would expect it.
- Reviewer or credential note for YMYL topics when available.
- Business authority signal (years of experience, certifications, service area) surfaced where natural.

---

## SECTION 3: ORIGINALITY AND NON-COMMODITY STANDARD

Content must provide value that generic coverage cannot.

- Require at least one non-commodity angle: firsthand experience, proprietary process detail, expert judgment, local knowledge, or original analysis.
- Commodity content (generic tips, common knowledge listicles, "7 things everyone already knows") must be rejected or substantially differentiated.
- The post must provide substantial value compared to other pages currently ranking for the target keyword.
- Do not create separate pages for every query variation; one strong, comprehensive page beats many thin variants.

Non-commodity test: if a generative AI model could produce substantially the same article without any client-specific input, the angle is too generic.

---

## SECTION 4: AI-CONTENT SAFEGUARDS

AI assistance in content creation is allowed. Scaled low-value output is not.

**Permitted:**
- Using AI tools for research, outlining, structuring, and drafting.
- Using AI to improve clarity, grammar, and organization.

**Prohibited:**
- Using automation primarily to manipulate search rankings or AI responses.
- Mass-producing content across many topics with little originality, effort, or user benefit.
- Generating content that could not pass the non-commodity test in Section 3.

**Disclosure:**
- AI-use disclosure is appropriate when readers would reasonably ask "how was this created?" and the answer materially affects their trust.
- Disclosure is not required on every post. Apply judgment based on topic sensitivity and audience expectations.
- When disclosure is appropriate, it belongs in the publish layer (author bio, footer note, or about page), not as an inline caveat in every section.

**Metadata:**
- Auto-generated titles, descriptions, structured data, and image alt text must meet the same accuracy and quality bar as manually written copy.

---

## SECTION 5: AI-SEARCH MYTHBUSTING (ANTI-REQUIREMENTS)

Things the pipeline must NOT do. These are either unsupported by how Google Search works or actively counterproductive.

- Do NOT create `llms.txt` files or any AI-specific machine-readable files.
- Do NOT add special schema markup for AI Overviews or AI Mode. Standard structured data for rich results is sufficient.
- Do NOT "chunk" content into small pieces for AI systems. Write for readers; Google can extract relevant segments from well-structured pages.
- Do NOT rewrite content in a specific way "for AI systems." AI systems understand synonyms and general meanings.
- Do NOT create multiple near-duplicate pages to capture every long-tail keyword variation or fan-out query.
- Do NOT seek inauthentic "mentions" across the web.
- Do NOT change page dates without substantive content updates.
- Do NOT promise or imply that any technique guarantees appearance in AI Overviews, AI Mode, or any specific search feature.
- Do NOT treat "AEO" (answer engine optimization) or "GEO" (generative engine optimization) as separate disciplines. For Google Search, optimizing for AI features is optimizing for Search, and that is still SEO.

---

## SECTION 6: STAGE RESPONSIBILITIES

Content-quality guidance and technical/indexing validation are separate concerns. Each stage owns only its domain.

**Content stages (Research, Brief, Writing, Humanization)**
Own: originality, audience value, E-E-A-T signals, source quality, voice, helpfulness, non-commodity angle.
Do not own: crawlability, indexation, schema markup, HTML structure, Search Console.

**Review stages (SEO, QA)**
Own: keyword placement, metadata quality, header hierarchy, internal linking strategy, content-quality validation, people-first compliance, AI-detection risk.
Do not own: HTML rendering, schema injection, publication mechanics.

**Technical stages (Schema, HTML Finalization, Publication)**
Own: structured data implementation, HTML validity, indexability prerequisites, snippet eligibility, metadata alignment with body content.
Do not own: editorial voice, originality, E-E-A-T depth.

**Onboarding**
Own: capturing durable client authority signals, evidence types, authorship model, trust assets, and topic constraints that downstream stages need.

This separation ensures that writing stages are not cluttered with technical SEO checklists, and that publication stages do not second-guess editorial decisions.
