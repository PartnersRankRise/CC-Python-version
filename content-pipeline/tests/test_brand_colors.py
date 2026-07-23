# Created: Thursday Jul 23, 2026, 2:00 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 2:02 PM (UTC-6)

"""Tests for brand color extraction and validation."""

import pytest
from content_pipeline.config.brand_color_extractor import (
    BrandColorExtractor,
    MissingBrandColorError,
)


@pytest.fixture
def extractor():
    """Provide BrandColorExtractor instance."""
    return BrandColorExtractor()


@pytest.fixture
def rankrise_reference_colors():
    """Known correct brand colors from Rankrise reference run."""
    return {
        "primary": "#1B3D6F",
        "primary_2": "#1E4F8A",
        "primary_soft": "#EEF3FA",
        "primary_glow": "rgba(27, 61, 111, 0.08)",
        "primary_rgb": "27, 61, 111",
        "accent": "#E8762B",
        "accent_2": "#D4621E",
        "accent_soft": "#FDF1E8",
        "accent_rgb": "232, 118, 43",
        "ink": "#1C1C1A",
        "line_strong": "rgba(27, 61, 111, 0.22)",
    }


@pytest.fixture
def rankrise_style_card():
    """Style Reference Card markdown with Rankrise colors."""
    return """# Style Reference Card

## VISUAL BRAND THEME

### Observed Site Palette
- **Primary color:** `#1B3D6F`
- **Primary 2:** `#1E4F8A`
- **Primary soft:** `#EEF3FA`
- **Primary glow:** `rgba(27, 61, 111, 0.08)`
- **Primary RGB:** `27, 61, 111`
- **Accent color:** `#E8762B`
- **Accent 2:** `#D4621E`
- **Accent soft:** `#FDF1E8`
- **Accent RGB:** `232, 118, 43`
- **Neutral ink:** `#1C1C1A`
- **Line strong:** `rgba(27, 61, 111, 0.22)`

### Typography Direction
- **Display/Heading font:** Open Sans Bold
- **Body font:** Open Sans Regular
"""


def test_rgb_triplets_have_no_hash_prefix(extractor, rankrise_reference_colors):
    """PRIMARY_RGB and ACCENT_RGB must NOT have # prefix.

    They are used inside rgba() in the CSS. A # prefix breaks the function.
    """
    colors = rankrise_reference_colors
    errors = extractor.validate(colors)

    for key in ["primary_rgb", "accent_rgb"]:
        assert not colors[key].startswith("#"), (
            f"{key} must not start with #, got: {colors[key]}"
        )


def test_all_11_keys_required(extractor):
    """All 11 keys must be present."""
    incomplete = {"primary": "#1B3D6F"}  # missing 10 keys
    errors = extractor.validate(incomplete)
    # Should have one error listing all missing keys
    assert len(errors) >= 1, f"Expected at least 1 error, got {len(errors)}: {errors}"
    assert any("Missing required keys" in e for e in errors), (
        f"Expected missing keys error, got: {errors}"
    )


def test_validate_rankrise_reference_colors(extractor, rankrise_reference_colors):
    """Rankrise reference colors pass validation."""
    errors = extractor.validate(rankrise_reference_colors)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_hex_colors_must_have_hash_prefix(extractor):
    """Hex colors must start with #."""
    colors = {
        "primary": "1B3D6F",  # missing # prefix
        "primary_2": "#1E4F8A",
        "primary_soft": "#EEF3FA",
        "primary_glow": "rgba(27, 61, 111, 0.08)",
        "primary_rgb": "27, 61, 111",
        "accent": "#E8762B",
        "accent_2": "#D4621E",
        "accent_soft": "#FDF1E8",
        "accent_rgb": "232, 118, 43",
        "ink": "#1C1C1A",
        "line_strong": "rgba(27, 61, 111, 0.22)",
    }
    errors = extractor.validate(colors)
    assert any("primary" in e and "hex" in e for e in errors), (
        f"Expected hex format error for primary, got: {errors}"
    )


def test_rgba_format_validation(extractor):
    """RGBA values must be valid rgba() format."""
    colors = {
        "primary": "#1B3D6F",
        "primary_2": "#1E4F8A",
        "primary_soft": "#EEF3FA",
        "primary_glow": "rgb(27, 61, 111)",  # wrong format
        "primary_rgb": "27, 61, 111",
        "accent": "#E8762B",
        "accent_2": "#D4621E",
        "accent_soft": "#FDF1E8",
        "accent_rgb": "232, 118, 43",
        "ink": "#1C1C1A",
        "line_strong": "rgba(27, 61, 111, 0.22)",
    }
    errors = extractor.validate(colors)
    assert any("primary_glow" in e for e in errors), (
        f"Expected primary_glow error, got: {errors}"
    )


def test_rgb_triplet_format_validation(extractor):
    """RGB triplets must be 'r, g, b' format."""
    colors = {
        "primary": "#1B3D6F",
        "primary_2": "#1E4F8A",
        "primary_soft": "#EEF3FA",
        "primary_glow": "rgba(27, 61, 111, 0.08)",
        "primary_rgb": "#27, 61, 111",  # has # prefix (invalid)
        "accent": "#E8762B",
        "accent_2": "#D4621E",
        "accent_soft": "#FDF1E8",
        "accent_rgb": "232, 118, 43",
        "ink": "#1C1C1A",
        "line_strong": "rgba(27, 61, 111, 0.22)",
    }
    errors = extractor.validate(colors)
    assert any("primary_rgb" in e for e in errors), (
        f"Expected primary_rgb error, got: {errors}"
    )


def test_extract_rankrise_colors_from_markdown(extractor, rankrise_style_card):
    """Extract all 11 colors from markdown."""
    colors = extractor.extract(rankrise_style_card)

    assert len(colors) == 11, f"Expected 11 colors, got {len(colors)}"
    assert colors["primary"] == "#1B3D6F"
    assert colors["primary_rgb"] == "27, 61, 111"
    assert colors["accent_rgb"] == "232, 118, 43"
    assert colors["primary_glow"] == "rgba(27, 61, 111, 0.08)"


def test_extract_missing_color_raises_error(extractor):
    """Extract raises error if required color missing."""
    incomplete_card = """# Style Reference Card
## VISUAL BRAND THEME
- **Primary color:** `#1B3D6F`
"""
    with pytest.raises(MissingBrandColorError) as exc_info:
        extractor.extract(incomplete_card)
    assert "primary_2" in str(exc_info.value) or "Could not extract" in str(exc_info.value)


def test_valid_hex_color_acceptance(extractor):
    """Valid hex colors are accepted."""
    colors = {
        "primary": "#000000",
        "primary_2": "#FFFFFF",
        "primary_soft": "#AaBbCc",
        "primary_glow": "rgba(0, 0, 0, 0.5)",
        "primary_rgb": "0, 0, 0",
        "accent": "#123456",
        "accent_2": "#654321",
        "accent_soft": "#AABBCC",
        "accent_rgb": "100, 200, 50",
        "ink": "#333333",
        "line_strong": "rgba(255, 255, 255, 0.1)",
    }
    errors = extractor.validate(colors)
    assert errors == [], f"Expected no errors, got: {errors}"
