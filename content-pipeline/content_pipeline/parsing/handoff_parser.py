# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:42 PM (UTC-6)

"""Parses handoff markdown files — extracts structured fields."""

import re
from typing import Optional, Tuple

from content_pipeline.domain.enums import AuthorityMode
from content_pipeline.domain.stage import ParsedHandoff


class HandoffParser:
    """Parse handoff documents into structured fields.
    
    Handoff documents have a consistent structure across all stages.
    They include metadata, next stage info, load instructions, and carry-forward context.
    """

    def parse(self, handoff_text: str) -> ParsedHandoff:
        """Parse handoff document into structured ParsedHandoff.
        
        Args:
            handoff_text: Full handoff markdown
            
        Returns:
            ParsedHandoff with all fields extracted
        """
        # Extract basic metadata
        status = self._extract_field(handoff_text, "Status")
        created_by = self._extract_field(handoff_text, "Created by")
        created = self._extract_field(handoff_text, "Created")
        client = self._extract_field(handoff_text, "Client")
        run = self._extract_field(handoff_text, "Run")
        
        # Extract next stage info
        next_stage_number, next_stage_name = self._extract_next_stage(handoff_text)
        expected_output = self._extract_expected_output(handoff_text)
        
        # Extract carry forward context
        carry_forward = self._extract_carry_forward(handoff_text)
        
        # Extract auto-run settings
        auto_run = self._extract_auto_run(handoff_text)
        auto_run_reason = self._extract_auto_run_reason(handoff_text)
        
        return ParsedHandoff(
            status=status,
            created_by=created_by,
            created=created,
            client=client,
            run=run,
            next_stage_number=next_stage_number,
            next_stage_name=next_stage_name,
            expected_output=expected_output,
            carry_forward=carry_forward,
            auto_run=auto_run,
            auto_run_reason=auto_run_reason,
        )

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a simple field value (field: value format).
        
        Args:
            text: Full text
            field_name: Field name to search for
            
        Returns:
            Field value or empty string if not found
        """
        pattern = rf'{field_name}:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_next_stage(self, text: str) -> Tuple[int, str]:
        """Extract next stage number and name.
        
        Expected format: "- Stage: N - Stage Name"
        
        Args:
            text: Full text
            
        Returns:
            Tuple of (stage_number, stage_name)
        """
        pattern = r'- Stage:\s+(\d+)\s+-\s+(.+?)(?:\n|$)'
        match = re.search(pattern, text)
        if match:
            stage_num = int(match.group(1))
            stage_name = match.group(2).strip()
            return stage_num, stage_name
        return 0, ""

    def _extract_expected_output(self, text: str) -> str:
        """Extract expected output filename.
        
        Expected format: "- Expected output: filename.md"
        
        Args:
            text: Full text
            
        Returns:
            Expected output filename
        """
        pattern = r'- Expected output:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_carry_forward(self, text: str) -> dict:
        """Extract carry forward context section.
        
        Extracts all bullet points under "## Carry Forward Context".
        Maps to dict with keys: topic, primary_keyword, angle_notes,
        priority_sources, internal_links, published_overlap, unresolved_items.
        
        Args:
            text: Full text
            
        Returns:
            Dict with carry-forward fields
        """
        carry_forward = {
            "topic": "",
            "primary_keyword": "",
            "angle_notes": "",
            "priority_sources": "",
            "internal_links": "",
            "published_overlap": "",
            "unresolved_items": "",
            "authority_mode": "normal",
        }
        
        if "## Carry Forward Context" not in text:
            return carry_forward
        
        # Extract section
        start_idx = text.find("## Carry Forward Context")
        # Find next section or end
        next_section_idx = text.find("##", start_idx + 1)
        if next_section_idx == -1:
            next_section_idx = len(text)
        
        section = text[start_idx:next_section_idx]
        
        # Parse bullet points
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                line = line[2:].strip()
                
                # Parse by key: value format
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    if key in carry_forward:
                        carry_forward[key] = value
        
        return carry_forward

    def _extract_auto_run(self, text: str) -> bool:
        """Extract auto-run setting.
        
        Looks for "Auto-run:" or "Dry run:" fields.
        
        Args:
            text: Full text
            
        Returns:
            True if auto-run is enabled, False otherwise
        """
        # Check for "Auto-run: true" pattern
        if re.search(r'Auto-run:\s*true', text, re.IGNORECASE):
            return True
        
        # Check for "Dry run: false" (which means auto-run is true)
        if re.search(r'Dry run:\s*false', text, re.IGNORECASE):
            return False  # Dry run false = not auto-running
        
        return False

    def _extract_auto_run_reason(self, text: str) -> Optional[str]:
        """Extract reason for auto-run if present.
        
        Args:
            text: Full text
            
        Returns:
            Reason text or None if not auto-running
        """
        pattern = r'Auto-run reason:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def extract_authority_mode(self, handoff_text: str) -> Tuple[AuthorityMode, Optional[dict]]:
        """Extract authority mode and fallback settings if present.
        
        Returns (NORMAL, None) if no Authority_Mode section.
        Returns (EXPERT_FALLBACK, fallback_fields_dict) if fallback present.
        
        Args:
            handoff_text: Full handoff text
            
        Returns:
            Tuple of (AuthorityMode, Optional[fallback_dict])
        """
        # Check for Authority_Mode section
        if "Authority_Mode" not in handoff_text and "## Authority Mode" not in handoff_text:
            return AuthorityMode.NORMAL, None
        
        # Look for EXPERT_FALLBACK indicator
        if "EXPERT_FALLBACK" in handoff_text or "expert_fallback" in handoff_text.lower():
            # Extract fallback section if present
            fallback_dict = self._extract_fallback_section(handoff_text)
            return AuthorityMode.EXPERT_FALLBACK, fallback_dict
        
        # Otherwise, normal mode
        return AuthorityMode.NORMAL, None

    def _extract_fallback_section(self, text: str) -> Optional[dict]:
        """Extract EXPERT_FALLBACK section details.
        
        Args:
            text: Full text
            
        Returns:
            Dict with fallback fields or None
        """
        fallback_dict = {}
        
        # Find Authority_Mode or EXPERT_FALLBACK section
        for marker in ["Authority_Mode", "## Authority Mode", "EXPERT_FALLBACK"]:
            if marker in text:
                start_idx = text.find(marker)
                # Find next section
                next_section = text.find("##", start_idx + 1)
                if next_section == -1:
                    next_section = len(text)
                
                section = text[start_idx:next_section]
                
                # Extract key-value pairs
                for line in section.split('\n'):
                    line = line.strip()
                    if ':' in line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        fallback_dict[key] = value
                
                return fallback_dict if fallback_dict else None
        
        return None
