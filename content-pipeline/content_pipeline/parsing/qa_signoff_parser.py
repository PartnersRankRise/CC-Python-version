# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:30 PM (UTC-6)

"""Parses Stage 6 QA signoff markdown — extracts QAResult domain object."""

import re
from typing import Optional

from content_pipeline.domain.enums import QADecision, QAIssueType
from content_pipeline.domain.stage import QAIssue, QAResult


class QASignoffParser:
    """Parse Stage 6 QA Signoff markdown into a QAResult domain object.
    
    The QA signoff contains:
    - Approval status (APPROVED or REVISION REQUIRED)
    - Checklist score (e.g., 38 of 39)
    - AI risk score (e.g., 5/15)
    - Section results (A–I: PASS or FLAG)
    - Issues (with type classification)
    - Human review flag
    """

    def parse(self, signoff_text: str) -> QAResult:
        """Parse QA signoff into structured QAResult.
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            QAResult domain object with all fields populated
        """
        # Extract decision
        decision = self._extract_decision(signoff_text)
        
        # Extract checklist score
        checklist_score = self._extract_checklist_score(signoff_text)
        
        # Extract AI risk score
        ai_risk_score = self._extract_ai_risk_score(signoff_text)
        
        # Extract section results
        section_results = self._extract_section_results(signoff_text)
        
        # Extract issues
        issues = self._extract_issues(signoff_text)
        
        # Extract human review flag
        human_review_flag = self._extract_human_review_flag(signoff_text)
        
        # Compute revision stage
        revision_stage = self._compute_revision_stage(decision, issues)
        
        return QAResult(
            decision=decision,
            checklist_score=checklist_score,
            ai_risk_score=ai_risk_score,
            section_results=section_results,
            issues=issues,
            human_review_flag=human_review_flag,
            revision_stage=revision_stage,
        )

    def _extract_decision(self, signoff_text: str) -> QADecision:
        """Extract approval decision from signoff.
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            QADecision.APPROVED or QADecision.REVISION_REQUIRED
        """
        if "Approval Status: APPROVED" in signoff_text:
            return QADecision.APPROVED
        return QADecision.REVISION_REQUIRED

    def _extract_checklist_score(self, signoff_text: str) -> tuple[int, int]:
        """Extract checklist score from signoff.
        
        Expected format: "Checklist Score: 38 of 39 items PASSED"
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            Tuple of (passed, total)
        """
        pattern = r'Checklist Score:\s*(\d+)\s+of\s+(\d+)'
        match = re.search(pattern, signoff_text)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0)

    def _extract_ai_risk_score(self, signoff_text: str) -> int:
        """Extract AI risk score from signoff.
        
        Expected format: "AI Detection Risk Score: 5/15"
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            Risk score as integer (out of 15)
        """
        pattern = r'AI Detection Risk Score:\s*(\d+)/15'
        match = re.search(pattern, signoff_text)
        if match:
            return int(match.group(1))
        return 0

    def _extract_section_results(self, signoff_text: str) -> dict[str, str]:
        """Extract section-by-section results (A–I).
        
        Expected format:
        ```
        Section Results:
          A. Factual Accuracy: PASS
          B. E-E-A-T Compliance: PASS
          ...
          F. SEO and Technical: FLAG (minor, non-blocking)
        ```
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            Dict like {"A": "PASS", "F": "FLAG", ...}
        """
        results = {}
        
        # Find Section Results section
        if "Section Results:" not in signoff_text:
            return results
        
        start_idx = signoff_text.find("Section Results:")
        # Find next section or end
        end_markers = ["Issues Requiring Resolution:", "Minor Observations:", "---"]
        end_idx = len(signoff_text)
        for marker in end_markers:
            idx = signoff_text.find(marker, start_idx)
            if idx != -1 and idx < end_idx:
                end_idx = idx
        
        section = signoff_text[start_idx:end_idx]
        
        # Extract each line (A. through I.)
        for line in section.split('\n'):
            match = re.search(r'([A-I])\.\s+[^:]+:\s+(PASS|FLAG)', line)
            if match:
                section_letter = match.group(1)
                status = match.group(2).lower()
                results[section_letter] = status
        
        return results

    def _extract_issues(self, signoff_text: str) -> list[QAIssue]:
        """Extract all issues (both blocking and non-blocking).
        
        Issues can be under:
        - "Issues Requiring Resolution:"
        - "Minor Observations for Future Improvement:"
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            List of QAIssue domain objects
        """
        issues = []
        
        # Extract blocking issues
        if "Issues Requiring Resolution:" in signoff_text:
            start_idx = signoff_text.find("Issues Requiring Resolution:")
            end_idx = signoff_text.find("Minor Observations", start_idx)
            if end_idx == -1:
                end_idx = signoff_text.find("---", start_idx)
            if end_idx == -1:
                end_idx = len(signoff_text)
            
            section = signoff_text[start_idx:end_idx]
            
            # Parse FLAG lines
            for line in section.split('\n'):
                if line.strip().startswith('FLAG'):
                    issue = self._parse_issue_line(line)
                    if issue:
                        issues.append(issue)
        
        # Extract minor observations (these are non-blocking)
        if "Minor Observations" in signoff_text:
            start_idx = signoff_text.find("Minor Observations")
            end_idx = signoff_text.find("---", start_idx)
            if end_idx == -1:
                end_idx = len(signoff_text)
            
            section = signoff_text[start_idx:end_idx]
            
            # Parse bullet points as minor observations
            for line in section.split('\n'):
                if line.strip().startswith('- '):
                    description = line.strip()[2:].strip()
                    if description:
                        issues.append(QAIssue(
                            section="",  # Minor observations don't have a specific section
                            description=description,
                            issue_type=QAIssueType.MINOR_OBSERVATION,
                            stage_responsible=None,
                        ))
        
        return issues

    def _parse_issue_line(self, line: str) -> Optional[QAIssue]:
        """Parse a single FLAG issue line into QAIssue.
        
        Expected format:
        "FLAG — Section F: Third internal link... Stage responsible: client/publisher decision..."
        
        Args:
            line: Single issue line
            
        Returns:
            QAIssue object or None if parsing fails
        """
        if not line.strip().startswith('FLAG'):
            return None
        
        # Extract section letter (A–I)
        section_match = re.search(r'Section\s+([A-I])', line)
        section = section_match.group(1) if section_match else ""
        
        # Extract full description (everything after "FLAG — " until end or "Stage responsible:")
        desc_start = line.find("FLAG — ")
        if desc_start != -1:
            desc_start += len("FLAG — ")
            desc_end = line.find("Stage responsible:", desc_start)
            if desc_end == -1:
                description = line[desc_start:].strip()
            else:
                description = line[desc_start:desc_end].strip()
        else:
            description = line.strip()
        
        # Extract issue type and stage responsible
        stage_match = re.search(r'Stage responsible:\s*(.+?)(?:\.|$)', line)
        stage_text = stage_match.group(1).strip() if stage_match else ""
        
        issue_type = self.classify_issue(stage_text)
        stage_responsible = self._extract_stage_number(stage_text) if issue_type == QAIssueType.PIPELINE_FAILURE else None
        
        return QAIssue(
            section=section,
            description=description,
            issue_type=issue_type,
            stage_responsible=stage_responsible,
        )

    def classify_issue(self, stage_responsible_text: str) -> QAIssueType:
        """Classify issue type based on stage responsible text.
        
        Logic:
        - "client/publisher decision" or "publisher" → CLIENT_DECISION
        - Stage number (3, 4, 5) or "Stage" → PIPELINE_FAILURE
        - None or "minor" → MINOR_OBSERVATION
        
        Args:
            stage_responsible_text: Text describing who is responsible
            
        Returns:
            QAIssueType classification
        """
        text_lower = stage_responsible_text.lower()
        
        # Client decision indicators
        if "client" in text_lower or "publisher" in text_lower or "not a pipeline failure" in text_lower:
            return QAIssueType.CLIENT_DECISION
        
        # Pipeline failure indicators (stage number)
        if re.search(r'[Ss]tage\s+[345]', stage_responsible_text):
            return QAIssueType.PIPELINE_FAILURE
        
        if re.search(r'\b[345]\b', stage_responsible_text):
            return QAIssueType.PIPELINE_FAILURE
        
        # Default to minor observation
        return QAIssueType.MINOR_OBSERVATION

    def _extract_stage_number(self, stage_text: str) -> Optional[int]:
        """Extract stage number (3, 4, or 5) from stage text.
        
        Args:
            stage_text: Text containing stage reference
            
        Returns:
            Stage number or None if not found
        """
        match = re.search(r'[Ss]tage\s+([345])', stage_text)
        if match:
            return int(match.group(1))
        
        # Also check for bare numbers
        match = re.search(r'\b([345])\b', stage_text)
        if match:
            return int(match.group(1))
        
        return None

    def _extract_human_review_flag(self, signoff_text: str) -> Optional[str]:
        """Extract human review flag.
        
        Expected format: "Human Review Flag: NONE" or "Human Review Flag: <reason>"
        
        Args:
            signoff_text: Full QA signoff markdown
            
        Returns:
            Flag text or None if "NONE"
        """
        pattern = r'Human Review Flag:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, signoff_text)
        if match:
            flag_text = match.group(1).strip()
            if flag_text.upper() == "NONE":
                return None
            return flag_text
        return None

    def _compute_revision_stage(self, decision: QADecision, issues: list[QAIssue]) -> Optional[int]:
        """Compute the revision stage based on decision and issues.
        
        Rules:
        - If decision is APPROVED: return None
        - If REVISION_REQUIRED: find earliest stage responsible from PIPELINE_FAILURE issues
        
        Args:
            decision: QA decision (APPROVED or REVISION_REQUIRED)
            issues: List of issues found
            
        Returns:
            Stage number (3, 4, 5) or None
        """
        if decision == QADecision.APPROVED:
            return None
        
        # Find earliest stage from PIPELINE_FAILURE issues
        pipeline_failure_issues = [i for i in issues if i.issue_type == QAIssueType.PIPELINE_FAILURE]
        if pipeline_failure_issues:
            stages = [i.stage_responsible for i in pipeline_failure_issues if i.stage_responsible]
            if stages:
                return min(stages)
        
        return None
