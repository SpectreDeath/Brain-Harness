"""Sed-compatible template rendering with mix, gradient, and format interpolators."""

from __future__ import annotations

import re
from typing import Any

from .color import ColorRGB, mix_colors


def render_template(template_content: str, palette: dict[str, str]) -> str:
    """Render template with {{ key }}, {{ key_strip }}, {{ key_rgb }}, and {{ mix ... }}."""
    rendered = template_content

    # 1. Process mix functions: {{ mix[_strip|_rgb] start end amount }}
    mix_pattern = re.compile(
        r"\{\{\s*mix(_strip|_rgb)?\s+([A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)\s+([0-9]+(?:\.[0-9]+)?%?)\s*\}\}"
    )

    def replace_mix(match: re.Match[str]) -> str:
        variant = match.group(1) or ""
        start_key = match.group(2)
        end_key = match.group(3)
        amount = match.group(4)

        start_col = palette.get(start_key, "#000000")
        end_col = palette.get(end_key, "#ffffff")
        mixed_hex = mix_colors(start_col, end_col, amount)

        if variant == "_strip":
            return mixed_hex.lstrip("#")
        elif variant == "_rgb":
            return ColorRGB.from_hex(mixed_hex).to_rgb_str()
        return mixed_hex

    rendered = mix_pattern.sub(replace_mix, rendered)

    # 2. Process gradient functions: {{ hypr_gradient|gradient_start|shell_gradient key fallback }}
    grad_pattern = re.compile(
        r"\{\{\s*(hypr_gradient|gradient_start|shell_gradient)\s+([A-Za-z0-9_]+)(?:\s+([A-Za-z0-9_#]+))?\s*\}\}"
    )

    def replace_gradient(match: re.Match[str]) -> str:
        fn = match.group(1)
        key = match.group(2)
        fallback = match.group(3) or ""
        val = palette.get(key, palette.get(fallback, fallback or key))

        if fn == "gradient_start":
            parts = val.split()
            first = parts[0] if parts else val
            return palette.get(first, first)
        elif fn == "shell_gradient":
            return val
        elif fn == "hypr_gradient":
            parts = [p for p in val.split() if p]
            colors = [palette.get(p, p) for p in parts if not p.endswith("deg")]
            angle = next((p.replace("deg", "") for p in parts if p.endswith("deg")), "")
            if len(colors) <= 1:
                c = colors[0] if colors else val
                return f'"{c}"'
            col_str = ", ".join(f'"{c}"' for c in colors)
            if angle:
                return f"{{ colors = {{ {col_str} }}, angle = {angle} }}"
            return f"{{ colors = {{ {col_str} }} }}"
        return val

    rendered = grad_pattern.sub(replace_gradient, rendered)

    # 3. Process key_strip: {{ key_strip }}
    strip_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)_strip\s*\}\}")

    def replace_strip(match: re.Match[str]) -> str:
        k = match.group(1)
        if k in palette:
            return palette[k].lstrip("#")
        return match.group(0)

    rendered = strip_pattern.sub(replace_strip, rendered)

    # 4. Process key_rgb: {{ key_rgb }}
    rgb_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)_rgb\s*\}\}")

    def replace_rgb(match: re.Match[str]) -> str:
        k = match.group(1)
        if k in palette:
            return ColorRGB.from_hex(palette[k]).to_rgb_str()
        return match.group(0)

    rendered = rgb_pattern.sub(replace_rgb, rendered)

    # 5. Process standard key: {{ key }}
    val_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

    def replace_val(match: re.Match[str]) -> str:
        k = match.group(1)
        if k in palette:
            return palette[k]
        return match.group(0)

    rendered = val_pattern.sub(replace_val, rendered)
    return rendered
