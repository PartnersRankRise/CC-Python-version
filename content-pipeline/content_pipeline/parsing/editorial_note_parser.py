# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 1:19 PM (UTC-6)

"""Parses Stage 4 humanized draft — splits article body from editorial note."""

from typing import Optional


class EditorialNoteParser:
    """Parse Stage 4 Humanized Draft by splitting article body from editorial note.
    
    The humanized draft appends "## Editorial Note" after the article body.
    This parser separates them so:
    - article_body is passed to Stage 5 (SEO)
    - editorial_note is stored separately in stage_outputs.editorial_note
    - The note is NEVER passed downstream to Stage 5, 6, or 7
    """

    SEPARATOR = "\n## Editorial Note\n"

    def split(self, humanized_draft: str) -> tuple[str, Optional[str]]:
        """Split humanized draft into article body and editorial note.
        
        Args:
            humanized_draft: Full Stage 4 output from humanization service
            
        Returns:
            Tuple of (article_body, editorial_note). If no separator found,
            returns (full_content, None).
        """
        if self.SEPARATOR in humanized_draft:
            parts = humanized_draft.split(self.SEPARATOR, 1)
            return parts[0].rstrip(), parts[1].strip()
        return humanized_draft, None
