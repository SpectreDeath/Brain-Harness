"""YAML frontmatter extraction for SKILL.md files."""

from __future__ import annotations

from typing import Any


def extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter between --- markers."""
    frontmatter: dict[str, Any] = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_text = parts[1]
            body = parts[2]
            try:
                import yaml

                parsed = yaml.safe_load(yaml_text)
                if isinstance(parsed, dict):
                    frontmatter = parsed
            except Exception:
                for line in yaml_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip().strip('"').strip("'")

    return frontmatter, body
