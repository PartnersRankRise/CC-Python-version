# Created: Thursday Jul 23, 2026, 2:00 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:02 PM (UTC-6)

"""Brand color extraction from Style Reference Card markdown."""

import re
from typing import Optional


class MissingBrandColorError(Exception):
    """Raised when required brand color cannot be extracted."""
    pass


class BrandColorExtractor:
    """Extract and validate 11 required CSS token values from Style Reference Card."""

    # The 11 required keys
    REQUIRED_KEYS = {
        "primary",
        "primary_2",
        "primary_soft",
        "primary_glow",
        "primary_rgb",
        "accent",
        "accent_2",
        "accent_soft",
        "accent_rgb",
        "ink",
        "line_strong",
    }

    # Pattern for hex colors: #RRGGBB
    HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

    # Pattern for rgba values: rgba(r, g, b, a)
    RGBA_PATTERN = re.compile(r"^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)$")

    # Pattern for RGB triplet: r, g, b (no hash)
    RGB_TRIPLET_PATTERN = re.compile(r"^\d+\s*,\s*\d+\s*,\s*\d+$")

    def extract(self, style_reference_card: str) -> dict[str, str]:
        """Extract 11 brand color tokens from Style Reference Card markdown.

        The markdown should contain sections like:
        - **Primary color:** `#1B3D6F`
        - **Primary RGB:** `27, 61, 111`
        - **Primary Glow:** `rgba(27, 61, 111, 0.08)`

        Args:
            style_reference_card: Markdown content of Style Reference Card

        Returns:
            dict with all 11 keys and their values

        Raises:
            MissingBrandColorError: If any required key cannot be extracted
        """
        colors = {}

        # Patterns to extract each color value from markdown
        # Focus on the backtick-wrapped value after the bold label (with colon INSIDE bold)
        patterns = {
            "primary": r"\*\*Primary color:\*\*\s*`([^`]+)`",
            "primary_2": r"\*\*Primary 2:\*\*\s*`([^`]+)`",
            "primary_soft": r"\*\*Primary soft:\*\*\s*`([^`]+)`",
            "primary_glow": r"\*\*Primary glow:\*\*\s*`([^`]+)`",
            "primary_rgb": r"\*\*Primary RGB:\*\*\s*`([^`]+)`",
            "accent": r"\*\*Accent color:\*\*\s*`([^`]+)`",
            "accent_2": r"\*\*Accent 2:\*\*\s*`([^`]+)`",
            "accent_soft": r"\*\*Accent soft:\*\*\s*`([^`]+)`",
            "accent_rgb": r"\*\*Accent RGB:\*\*\s*`([^`]+)`",
            "ink": r"\*\*(?:Neutral )?[Ii]nk:\*\*\s*`([^`]+)`",
            "line_strong": r"\*\*Line strong:\*\*\s*`([^`]+)`",
        }

        for key, pattern_str in patterns.items():
            match = re.search(pattern_str, style_reference_card, re.IGNORECASE)
            if match:
                colors[key] = match.group(1).strip()
            else:
                raise MissingBrandColorError(
                    f"Could not extract brand color '{key}' from Style Reference Card"
                )

        return colors

    def validate(self, brand_colors: dict) -> list[str]:
        """Validate brand color dict for correctness.

        Checks:
        - All 11 required keys are present
        - Hex values are valid (#RRGGBB format)
        - RGBA values are valid
        - RGB triplets have NO # prefix
        - Primary and accent values are in correct format

        Args:
            brand_colors: Dict of brand colors to validate

        Returns:
            List of validation errors (empty list = all valid)
        """
        errors = []

        # Check all required keys present
        missing = self.REQUIRED_KEYS - set(brand_colors.keys())
        if missing:
            errors.append(f"Missing required keys: {', '.join(sorted(missing))}")

        # Validate each color value
        for key, value in brand_colors.items():
            if key not in self.REQUIRED_KEYS:
                errors.append(f"Unknown key: {key}")
                continue

            if key in ["primary_glow", "line_strong"]:
                # Must be rgba()
                if not self.RGBA_PATTERN.match(value):
                    errors.append(
                        f"{key}: must be rgba(r, g, b, a) format, got: {value}"
                    )
            elif key in ["primary_rgb", "accent_rgb"]:
                # Must be "r, g, b" with NO # prefix
                if not self.RGB_TRIPLET_PATTERN.match(value):
                    errors.append(
                        f"{key}: must be 'r, g, b' format (no # prefix), got: {value}"
                    )
                if value.startswith("#"):
                    errors.append(f"{key}: must NOT have # prefix, got: {value}")
            else:
                # All others (primary, primary_2, primary_soft, accent, accent_2, accent_soft, ink)
                # Must be hex
                if not self.HEX_PATTERN.match(value):
                    errors.append(f"{key}: must be hex format (#RRGGBB), got: {value}")

        return errors
