"""Slotted color representation, linear mixing, and contrast calculation (Rule 12)."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ColorRGB:
    """Slotted immutable representation of 8-bit sRGB color (Rule 12)."""

    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex_str: str) -> ColorRGB:
        """Parse hex color string to ColorRGB instance."""
        clean = hex_str.strip().lstrip("#")
        if len(clean) == 3:
            clean = "".join(c * 2 for c in clean)
        if len(clean) < 6:
            return cls(0, 0, 0)
        try:
            return cls(
                r=int(clean[0:2], 16),
                g=int(clean[2:4], 16),
                b=int(clean[4:6], 16),
            )
        except ValueError:
            return cls(0, 0, 0)

    def to_hex(self) -> str:
        """Format as 7-character hexadecimal string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_rgb_str(self) -> str:
        """Format as comma-separated RGB string."""
        return f"{self.r},{self.g},{self.b}"

    def relative_luminance(self) -> float:
        """Compute WCAG 2.1 relative luminance."""
        def channel_lum(val: int) -> float:
            c = val / 255.0
            return c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

        return (
            0.2126 * channel_lum(self.r)
            + 0.7152 * channel_lum(self.g)
            + 0.0722 * channel_lum(self.b)
        )


def mix_colors(start_hex: str, end_hex: str, amount: float | str) -> str:
    """Interpolate two hex colors linearly, exactly matching Omarchy's awk algorithm."""
    start = ColorRGB.from_hex(start_hex)
    end = ColorRGB.from_hex(end_hex)

    if isinstance(amount, str):
        amt_clean = amount.strip()
        if amt_clean.endswith("%"):
            pct = float(amt_clean[:-1]) / 100.0
        else:
            pct = float(amt_clean)
            if pct > 1.0:
                pct = pct / 100.0
    else:
        pct = float(amount)
        if pct > 1.0:
            pct = pct / 100.0

    pct = max(0.0, min(1.0, pct))

    # Match awk: int(start * (1 - amount) + end * amount + 0.5)
    red = int(start.r * (1.0 - pct) + end.r * pct + 0.5)
    green = int(start.g * (1.0 - pct) + end.g * pct + 0.5)
    blue = int(start.b * (1.0 - pct) + end.b * pct + 0.5)

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return f"#{red:02x}{green:02x}{blue:02x}"


def compute_contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two colors."""
    lum_a = ColorRGB.from_hex(hex_a).relative_luminance()
    lum_b = ColorRGB.from_hex(hex_b).relative_luminance()
    l1 = max(lum_a, lum_b)
    l2 = min(lum_a, lum_b)
    return round((l1 + 0.05) / (l2 + 0.05), 2)
