# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:24 PM (UTC-6)

"""Parses Stage 5 SEO output — splits article body from SEO annotation sheet."""

import re
from typing import Optional

from content_pipeline.domain.stage import SEOAnnotation


class SEOAnnotationParser:
    """Parse Stage 5 SEO Draft by splitting article body from annotation sheet.
    
    The SEO draft appends "## SEO Annotation Sheet" after the article body.
    This parser separates them so:
    - article_body is passed to Stage 6 (QA)
    - annotation_sheet is parsed into SEOAnnotation domain object
    - The annotation sheet is stored separately in stage_outputs.seo_annotation
    """

    SEPARATOR = "\n## SEO Annotation Sheet\n"
    WORD_COUNT_PATTERN = re.compile(
        r'(\d+) words \| target: (\d+)-(\d+) \| (WITHIN TARGET|OVER TARGET|UNDER TARGET)'
    )

    def split(self, seo_draft: str) -> tuple[str, str]:
        """Split SEO draft into article body and annotation sheet.
        
        Args:
            seo_draft: Full Stage 5 output from SEO service
            
        Returns:
            Tuple of (article_body, annotation_sheet). If no separator found,
            returns (full_content, "").
        """
        if self.SEPARATOR in seo_draft:
            parts = seo_draft.split(self.SEPARATOR, 1)
            return parts[0].rstrip(), parts[1]
        return seo_draft, ""

    def parse_word_count(self, annotation: str) -> dict:
        """Parse word count line into structured data.
        
        Expected format: "2776 words | target: 2200-2800 | WITHIN TARGET"
        Converted to: {"count": 2776, "target_min": 2200, "target_max": 2800, "status": "within_target"}
        
        Args:
            annotation: Annotation sheet text
            
        Returns:
            Dict with count, target_min, target_max, status keys. Empty dict if not found.
        """
        m = self.WORD_COUNT_PATTERN.search(annotation)
        if m:
            return {
                "count": int(m.group(1)),
                "target_min": int(m.group(2)),
                "target_max": int(m.group(3)),
                "status": m.group(4).lower().replace(" ", "_"),
            }
        return {}

    def parse_qa_flags(self, annotation: str) -> list[str]:
        """Extract bulleted list under "Flags for QA Agent:".
        
        Args:
            annotation: Annotation sheet text
            
        Returns:
            List of flag strings (without bullet point markers)
        """
        flags = []
        
        # Find the "Flags for QA Agent:" section
        if "Flags for QA Agent:" not in annotation:
            return flags
        
        # Extract everything after "Flags for QA Agent:"
        flags_section = annotation.split("Flags for QA Agent:", 1)[1]
        
        # Split by lines and extract bullets
        for line in flags_section.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                # Remove the bullet and leading dash
                flag = line[2:].strip()
                if flag:
                    flags.append(flag)
        
        return flags

    def parse_summary_of_changes(self, annotation: str) -> list[str]:
        """Extract bulleted list under "Summary of Changes:".
        
        Args:
            annotation: Annotation sheet text
            
        Returns:
            List of change summaries (without bullet markers)
        """
        changes = []
        
        if "Summary of Changes:" not in annotation:
            return changes
        
        # Extract section after "Summary of Changes:"
        start_idx = annotation.find("Summary of Changes:")
        if start_idx == -1:
            return changes
        
        # Find the next section marker (**)
        start_idx += len("Summary of Changes:")
        end_idx = annotation.find("\n**", start_idx)
        if end_idx == -1:
            summary_section = annotation[start_idx:]
        else:
            summary_section = annotation[start_idx:end_idx]
        
        # Extract bullet points
        for line in summary_section.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                change = line[2:].strip()
                if change:
                    changes.append(change)
        
        return changes

    def parse_annotation(self, annotation_text: str) -> SEOAnnotation:
        """Parse annotation sheet into SEOAnnotation domain object.
        
        Args:
            annotation_text: Raw annotation sheet text
            
        Returns:
            SEOAnnotation with all fields populated
        """
        # Parse word count
        word_count_data = self.parse_word_count(annotation_text)
        
        # Extract meta title and description
        meta_title = self._extract_meta_field(annotation_text, "Meta Title:")
        meta_description = self._extract_meta_field(annotation_text, "Meta Description:")
        
        # Extract keyword density info
        keyword_density = self._extract_keyword_density(annotation_text)
        
        # Extract schema recommendation
        schema_recommendation = self._extract_schema(annotation_text)
        
        # Extract internal links
        internal_links = self._extract_internal_links(annotation_text)
        
        # Extract readability note
        readability_note = self._extract_readability(annotation_text)
        
        # Extract AI search alignment
        ai_search_alignment = self._extract_ai_alignment(annotation_text)
        
        # Extract summary of changes
        changes_summary = self.parse_summary_of_changes(annotation_text)
        
        # Extract QA flags
        qa_flags = self.parse_qa_flags(annotation_text)
        
        return SEOAnnotation(
            changes_summary=changes_summary,
            keyword_density=keyword_density,
            meta_title=meta_title,
            meta_description=meta_description,
            schema_recommendation=schema_recommendation,
            internal_links=internal_links,
            readability_note=readability_note,
            word_count=word_count_data,
            ai_search_alignment=ai_search_alignment,
            qa_flags=qa_flags,
        )

    def _extract_meta_field(self, annotation: str, field_name: str) -> dict:
        """Extract a meta field (title or description) from annotation.
        
        Args:
            annotation: Full annotation text
            field_name: Field name to search for (e.g., "Meta Title:")
            
        Returns:
            Dict with 'content' and 'status' keys if found, empty dict otherwise
        """
        if field_name not in annotation:
            return {}
        
        # Extract line after field name
        start = annotation.find(field_name)
        if start == -1:
            return {}
        
        # Get text after field name
        content_start = start + len(field_name)
        content = annotation[content_start:].split('\n')[0].strip()
        
        # Extract any PASS/FAIL status
        status = "unknown"
        if "PASS" in content:
            status = "pass"
            content = content.replace(" — PASS", "").replace("— PASS", "").strip()
        elif "FAIL" in content:
            status = "fail"
            content = content.replace(" — FAIL", "").replace("— FAIL", "").strip()
        
        return {"content": content, "status": status}

    def _extract_keyword_density(self, annotation: str) -> dict:
        """Extract keyword density report section.
        
        Args:
            annotation: Full annotation text
            
        Returns:
            Dict with keyword density information
        """
        if "Keyword Density Report:" not in annotation:
            return {}
        
        # Extract section
        start = annotation.find("Keyword Density Report:")
        end = annotation.find("\n**", start)
        if end == -1:
            end = annotation.find("\n\n", start)
        
        if end == -1:
            section = annotation[start:]
        else:
            section = annotation[start:end]
        
        return {"content": section.strip()}

    def _extract_schema(self, annotation: str) -> str:
        """Extract schema recommendation.
        
        Args:
            annotation: Full annotation text
            
        Returns:
            Schema recommendation text or empty string
        """
        if "Schema Recommendation:" not in annotation:
            return ""
        
        start = annotation.find("Schema Recommendation:")
        content_start = start + len("Schema Recommendation:")
        content = annotation[content_start:].split('\n\n')[0].split("**")[0].strip()
        
        return content

    def _extract_internal_links(self, annotation: str) -> list[dict]:
        """Extract internal link placements.
        
        Args:
            annotation: Full annotation text
            
        Returns:
            List of dicts with anchor, destination, section
        """
        links = []
        
        if "Internal Link Placements:" not in annotation:
            return links
        
        # Extract section
        start = annotation.find("Internal Link Placements:")
        end = annotation.find("\n**", start)
        if end == -1:
            end = annotation.find("\n\nReadability", start)
        
        if end == -1:
            section = annotation[start:]
        else:
            section = annotation[start:end]
        
        # Parse numbered links
        for line in section.split('\n'):
            if line.strip().startswith(('1.', '2.', '3.')):
                # Extract components
                link_dict = self._parse_link_line(line)
                if link_dict:
                    links.append(link_dict)
        
        return links

    def _parse_link_line(self, line: str) -> Optional[dict]:
        """Parse a single internal link line.
        
        Format: "1. Anchor: "..." | Destination: "..." | Section: ..."
        
        Args:
            line: Single link line
            
        Returns:
            Dict with anchor, destination, section keys or None
        """
        # Remove numbering
        line = re.sub(r'^\d+\.\s+', '', line).strip()
        
        # Extract components
        anchor_match = re.search(r'Anchor:\s*"([^"]*)"', line)
        dest_match = re.search(r'Destination:\s*([^\s|]+)', line)
        section_match = re.search(r'Section:\s*(.+?)(?:\s*\||$)', line)
        
        if anchor_match and dest_match:
            return {
                "anchor": anchor_match.group(1),
                "destination": dest_match.group(1),
                "section": section_match.group(1).strip() if section_match else "",
            }
        
        return None

    def _extract_readability(self, annotation: str) -> dict:
        """Extract readability note.
        
        Args:
            annotation: Full annotation text
            
        Returns:
            Dict with readability information
        """
        if "Readability Note:" not in annotation:
            return {}
        
        start = annotation.find("Readability Note:")
        content_start = start + len("Readability Note:")
        content = annotation[content_start:].split('\n\n')[0].split("**")[0].strip()
        
        return {"content": content}

    def _extract_ai_alignment(self, annotation: str) -> str:
        """Extract AI-Search Alignment section.
        
        Args:
            annotation: Full annotation text
            
        Returns:
            AI-Search Alignment text or empty string
        """
        if "AI-Search Alignment:" not in annotation:
            return ""
        
        start = annotation.find("AI-Search Alignment:")
        content_start = start + len("AI-Search Alignment:")
        content = annotation[content_start:].split('\n')[0].strip()
        
        return content
