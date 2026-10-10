"""WCAG 2.1 accessibility and color contrast audit verification."""

from __future__ import annotations

from typing import Any

from .color import ColorRGB, compute_contrast_ratio


def audit_theme_contrast(palette: dict[str, Any], theme_name: str) -> dict[str, Any]:
    """Analyze WCAG 2.1 contrast ratios and accessibility metrics for a theme."""
    if "error" in palette:
        return palette

    bg = palette.get("background", "#000000")
    dark_bg = palette.get("dark_background", "#000000")
    selection = palette.get("selection", "#333333")

    checks = {
        "foreground_on_background": {
            "text": palette.get("foreground", "#ffffff"),
            "surface": bg,
        },
        "dark_foreground_on_background": {
            "text": palette.get("dark_foreground", "#888888"),
            "surface": bg,
        },
        "light_foreground_on_background": {
            "text": palette.get("light_foreground", "#cccccc"),
            "surface": bg,
        },
        "bright_foreground_on_background": {
            "text": palette.get("bright_foreground", "#ffffff"),
            "surface": bg,
        },
        "accent_on_background": {
            "text": palette.get("accent", "#89b4fa"),
            "surface": bg,
        },
        "foreground_on_dark_background": {
            "text": palette.get("foreground", "#ffffff"),
            "surface": dark_bg,
        },
        "selection_foreground_on_selection": {
            "text": palette.get("selection_foreground", "#ffffff"),
            "surface": selection,
        },
    }

    results = {}
    all_aa = True
    for name, pair in checks.items():
        ratio = compute_contrast_ratio(pair["text"], pair["surface"])
        passes_aa = ratio >= 4.5
        passes_aa_large = ratio >= 3.0
        passes_aaa = ratio >= 7.0
        if not passes_aa:
            all_aa = False

        results[name] = {
            "ratio": ratio,
            "text_color": pair["text"],
            "surface_color": pair["surface"],
            "passes_wcag_aa": passes_aa,
            "passes_wcag_aa_large": passes_aa_large,
            "passes_wcag_aaa": passes_aaa,
        }

    return {
        "theme_name": theme_name,
        "mode": palette.get("mode", "dark"),
        "background_luminance": round(ColorRGB.from_hex(bg).relative_luminance(), 4),
        "overall_compliant_wcag_aa": all_aa,
        "checks": results,
    }
