# Created: Thursday Jul 23, 2026, 1:08 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:08 PM (UTC-6)

"""Parses Stage 2 brief markdown — strips BRIEF tokens, preserves tables."""

import re
from typing import Optional

from content_pipeline.domain.stage import ParsedBrief


class BriefParser:
    """Parse Stage 2 Content Brief markdown into structured components.
    
    The content brief contains multi-line <!--BRIEF: ... --> instruction blocks
    that must be stripped before passing to Stage 3. A critical constraint:
    the content types table appears BETWEEN BRIEF blocks and must survive stripping.
    """

    # Multi-line BRIEF blocks — re.DOTALL is required to match across newlines
    BRIEF_PATTERN = re.compile(r'<!--BRIEF:.*?-->', re.DOTALL)
    
    # Markdown tables: |...|...|...|
    TABLE_PATTERN = re.compile(
        r'(\|[^\n]+\|\n\|[-| :]+\|\n(?:\|[^\n]+\|\n)*)', re.MULTILINE
    )

    def strip_brief_tokens(self, markdown: str) -> str:
        """Remove <!--BRIEF: ... --> blocks. Preserve everything else including
        tables that appear between BRIEF blocks.
        
        Confirmed: the content types table in the reference run brief sits
        between two BRIEF blocks and must survive stripping.
        
        Args:
            markdown: Full brief markdown with BRIEF instruction blocks
            
        Returns:
            Markdown with BRIEF blocks removed; all other content preserved
        """
        stripped = self.BRIEF_PATTERN.sub("", markdown)
        # Clean up extra blank lines left behind by token removal
        return re.sub(r'\n{3,}', '\n\n', stripped).strip()

    def extract_content_table(self, markdown: str) -> Optional[str]:
        """Extract the content types table from the brief.
        
        The content types table appears in the "Post Structure Outline" section
        under "H3: The Content Types That Work Best for Home Services".
        It has "Content Type" as the header and describes four content types.
        This is NOT the first table in the document (keywords table appears first).
        
        Args:
            markdown: Full brief markdown
            
        Returns:
            Raw markdown table string for content types, or None if not found
        """
        tables = self.TABLE_PATTERN.findall(markdown)
        
        # Find the table with "Content Type" as header — that's the one we want
        for table in tables:
            if '| Content Type |' in table:
                return table.strip()
        
        # If exact match not found, return None (content table is optional in edge cases)
        return None

    def parse(self, brief_markdown: str) -> ParsedBrief:
        """Parse Stage 2 brief into structured ParsedBrief dataclass.
        
        Extracts 10 main sections from the brief:
        1. KEYWORD STRATEGY
        2. AUDIENCE DEFINITION
        3. WHO / HOW / WHY COMPLIANCE CHECKPOINT
        4. POST STRUCTURE OUTLINE
        5. E-E-A-T INSTRUCTIONS (if present)
        6. STYLE DIRECTIVE (if present)
        7. STRUCTURAL SPECS (if present)
        8. INTERNAL LINKING (if present)
        9. CTA DIRECTION
        10. AUTHOR CREDENTIAL
        
        Also extracts and preserves any markdown tables (e.g., content types table).
        
        Args:
            brief_markdown: Full brief markdown from Stage 2
            
        Returns:
            ParsedBrief with all sections extracted
        """
        # Extract content table before stripping BRIEF tokens
        content_table = self.extract_content_table(brief_markdown)
        
        # Strip BRIEF tokens but preserve tables
        clean_brief = self.strip_brief_tokens(brief_markdown)
        
        # Split by section headings (## N. SECTION NAME)
        sections = {}
        current_section = None
        current_content = []
        
        for line in clean_brief.split('\n'):
            # Match section headings: ## N. SECTION_NAME
            section_match = re.match(r'^##\s+\d+\.\s+(.+)$', line)
            if section_match:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = section_match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Extract data from each section
        keyword_strategy = self._parse_keyword_strategy(sections.get('KEYWORD STRATEGY', ''))
        audience_definition = sections.get('AUDIENCE DEFINITION', '')
        who_how_why = self._parse_who_how_why(sections.get('WHO / HOW / WHY COMPLIANCE CHECKPOINT', ''))
        post_structure = self._parse_post_structure(sections.get('POST STRUCTURE OUTLINE', ''))
        eeat_instructions = self._parse_eeat(sections.get('E-E-A-T INSTRUCTIONS', ''))
        style_directive = self._parse_style(sections.get('STYLE DIRECTIVE', ''))
        structural_specs = self._parse_structural(sections.get('STRUCTURAL SPECS', ''))
        internal_linking = self._parse_internal_linking(sections.get('INTERNAL LINKING', ''))
        cta_direction = self._parse_cta(sections.get('CTA DIRECTION', ''))
        author_credential = sections.get('AUTHOR CREDENTIAL', '')
        
        return ParsedBrief(
            keyword_strategy=keyword_strategy,
            audience_definition=audience_definition,
            who_how_why=who_how_why,
            post_structure=post_structure,
            content_table=content_table,
            eeat_instructions=eeat_instructions,
            style_directive=style_directive,
            structural_specs=structural_specs,
            internal_linking=internal_linking,
            cta_direction=cta_direction,
            author_credential=author_credential,
        )

    def _parse_keyword_strategy(self, section: str) -> dict:
        """Extract keyword strategy section into structured dict."""
        if not section:
            return {}
        
        result = {}
        # Extract primary keyword
        primary_match = re.search(r'\*\*Primary Keyword:\*\*\s*(.+?)(?:\n|$)', section)
        if primary_match:
            result['primary_keyword'] = primary_match.group(1).strip()
        
        # Extract secondary keywords (could be in a table or list)
        if '| Keyword |' in section:
            result['has_secondary_table'] = True
        
        # Extract meta targets
        meta_title_match = re.search(r'\*\*Meta Title Target:\*\*\s*(.+?)(?:\n|$)', section)
        if meta_title_match:
            result['meta_title'] = meta_title_match.group(1).strip()
        
        meta_desc_match = re.search(r'\*\*Meta Description Target.*?:\*\*\s*(.+?)(?:\n|$)', section)
        if meta_desc_match:
            result['meta_description'] = meta_desc_match.group(1).strip()
        
        return result

    def _parse_who_how_why(self, section: str) -> dict:
        """Extract WHO/HOW/WHY compliance section."""
        if not section:
            return {}
        
        result = {}
        who_match = re.search(r'\*\*Who:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', section, re.DOTALL)
        if who_match:
            result['who'] = who_match.group(1).strip()
        
        how_match = re.search(r'\*\*How:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', section, re.DOTALL)
        if how_match:
            result['how'] = how_match.group(1).strip()
        
        why_match = re.search(r'\*\*Why:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', section, re.DOTALL)
        if why_match:
            result['why'] = why_match.group(1).strip()
        
        return result

    def _parse_post_structure(self, section: str) -> list:
        """Extract post structure outline as list of heading levels."""
        if not section:
            return []
        
        structure = []
        for line in section.split('\n'):
            if line.startswith('**H'):
                structure.append(line.strip())
        
        return structure

    def _parse_eeat(self, section: str) -> list[dict]:
        """Extract E-E-A-T instructions if present."""
        if not section:
            return []
        return [{'content': section}]

    def _parse_style(self, section: str) -> dict:
        """Extract style directive if present."""
        if not section:
            return {}
        return {'directive': section}

    def _parse_structural(self, section: str) -> dict:
        """Extract structural specs if present."""
        if not section:
            return {}
        return {'specs': section}

    def _parse_internal_linking(self, section: str) -> list[dict]:
        """Extract internal linking strategy if present."""
        if not section:
            return []
        return [{'strategy': section}]

    def _parse_cta(self, section: str) -> dict:
        """Extract CTA direction if present."""
        if not section:
            return {}
        return {'direction': section}
