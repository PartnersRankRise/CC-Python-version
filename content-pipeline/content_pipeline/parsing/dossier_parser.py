# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:35 PM (UTC-6)

"""Parses Stage 1 research dossier — extracts 8 formal sections + supplemental notes."""

import re
from typing import Optional

from content_pipeline.domain.stage import ParsedDossier


class DossierParser:
    """Parse Stage 1 Research Dossier into structured sections.
    
    The dossier contains 8 formal sections and may have informal supplemental notes.
    All text content is preserved for Stage 2.
    """

    def parse(self, dossier_text: str) -> ParsedDossier:
        """Parse dossier into structured ParsedDossier.
        
        Extracts 8 formal sections (1–8) plus any supplemental notes.
        
        Args:
            dossier_text: Full dossier markdown
            
        Returns:
            ParsedDossier with all sections extracted
        """
        # Extract each numbered section
        topic_and_semantic = self._extract_section(dossier_text, 1, "TOPIC AND SEMANTIC FIELD")
        source_bank = self._extract_section(dossier_text, 2, "SOURCE BANK")
        non_obvious = self._extract_section(dossier_text, 3, "NON-OBVIOUS INSIGHT")
        ymyl = self._extract_section(dossier_text, 4, "YMYL ASSESSMENT")
        content_gap = self._extract_section(dossier_text, 5, "CONTENT GAP ANALYSIS")
        eeat = self._extract_section(dossier_text, 6, "RECOMMENDED E-E-A-T FRAMING")
        search_intent = self._extract_section(dossier_text, 7, "SEARCH INTENT CLASSIFICATION")
        audience_value = self._extract_section(dossier_text, 8, "AUDIENCE VALUE STATEMENT")
        
        # Extract supplemental notes (informal 9th section)
        supplemental = self._extract_supplemental_notes(dossier_text)
        
        return ParsedDossier(
            topic_and_semantic_field=topic_and_semantic,
            source_bank=source_bank,
            non_obvious_insight=non_obvious,
            ymyl_assessment=ymyl,
            content_gap_analysis=content_gap,
            eeat_framing=eeat,
            search_intent=search_intent,
            audience_value_statement=audience_value,
            supplemental_notes=supplemental,
        )

    def _extract_section(self, dossier_text: str, section_num: int, section_title: str) -> str:
        """Extract a single numbered section from the dossier.
        
        Args:
            dossier_text: Full dossier text
            section_num: Section number (1–8)
            section_title: Expected section heading
            
        Returns:
            Section content (trimmed)
        """
        # Look for "## N. SECTION_TITLE" pattern
        pattern = rf'##\s+{section_num}\.\s+{re.escape(section_title)}\s*\n(.*?)(?=##\s+\d+\.|##\s+RESEARCH|$)'
        match = re.search(pattern, dossier_text, re.DOTALL)
        
        if match:
            content = match.group(1).strip()
            return content
        
        return ""

    def _extract_supplemental_notes(self, dossier_text: str) -> Optional[str]:
        """Extract informal 9th section (supplemental research notes).
        
        The "RESEARCH NOTES FOR STAGE 2" section is not numbered but appears
        at the end of the dossier. It contains informal notes for the next stage.
        
        Args:
            dossier_text: Full dossier text
            
        Returns:
            Supplemental notes content or None if not present
        """
        if "RESEARCH NOTES FOR STAGE 2" not in dossier_text:
            return None
        
        # Extract everything after "## RESEARCH NOTES FOR STAGE 2"
        start_idx = dossier_text.find("## RESEARCH NOTES FOR STAGE 2")
        if start_idx == -1:
            return None
        
        # Skip the header line
        start_idx = dossier_text.find('\n', start_idx) + 1
        content = dossier_text[start_idx:].strip()
        
        return content if content else None

    def extract_sources(self, dossier_text: str) -> list[dict]:
        """Extract the source bank as a list of structured dicts.
        
        Each source has:
        - url: Full URL
        - institution: Institution/publication name
        - publication_date: Date published
        - data_points: List of key data points
        
        Args:
            dossier_text: Full dossier text
            
        Returns:
            List of source dicts
        """
        sources = []
        
        # Extract the SOURCE BANK section
        if "## 2. SOURCE BANK" not in dossier_text:
            return sources
        
        start_idx = dossier_text.find("## 2. SOURCE BANK")
        # Find next section
        end_idx = dossier_text.find("## 3.", start_idx)
        if end_idx == -1:
            end_idx = len(dossier_text)
        
        source_bank_section = dossier_text[start_idx:end_idx]
        
        # Find all source headers using a simpler pattern that doesn't depend on em-dash encoding
        # Look for "**Source N" followed by any content until "**"
        source_headers = list(re.finditer(r'\*\*Source\s+(\d+)[^\*]+\*\*', source_bank_section))
        
        # For each header, extract content until next header or end
        for i, header in enumerate(source_headers):
            header_end = header.end()
            
            # Find next header or end of section
            if i + 1 < len(source_headers):
                next_header_start = source_headers[i + 1].start()
            else:
                next_header_start = len(source_bank_section)
            
            # Extract block for this source
            block = source_bank_section[header_end:next_header_start]
            
            source = self._parse_source_block(block)
            if source:
                sources.append(source)
        
        return sources

    def _parse_source_block(self, block: str) -> Optional[dict]:
        """Parse a single source block into structured dict.
        
        Expected format:
        ```
        Institution Name**
        - URL: https://...
        - Institution: Name
        - Publication Date: ...
        - Key Data Points:
          - Point 1
          - Point 2
        ```
        
        Args:
            block: Single source block text
            
        Returns:
            Dict with url, institution, publication_date, data_points
        """
        source = {
            "url": "",
            "institution": "",
            "publication_date": "",
            "data_points": [],
        }
        
        # Extract URL
        url_match = re.search(r'- URL:\s*(.+?)(?:\n|$)', block)
        if url_match:
            source["url"] = url_match.group(1).strip()
        
        # Extract Institution
        inst_match = re.search(r'- Institution:\s*(.+?)(?:\n|$)', block)
        if inst_match:
            source["institution"] = inst_match.group(1).strip()
        
        # Extract Publication Date
        date_match = re.search(r'- Publication Date:\s*(.+?)(?:\n|$)', block)
        if date_match:
            source["publication_date"] = date_match.group(1).strip()
        
        # Extract Key Data Points
        if "- Key Data Points:" in block or "Key Data Points:" in block:
            # Find the start of data points
            dp_start = block.find("Key Data Points:")
            if dp_start != -1:
                # Get everything after "Key Data Points:"
                dp_section = block[dp_start + len("Key Data Points:"):]
                
                # Extract bullet points (lines starting with "  - ")
                for line in dp_section.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        point = line[2:].strip()
                        if point:
                            source["data_points"].append(point)
        
        # Return only if we found key fields
        if source["url"] and source["institution"]:
            return source
        
        return None
