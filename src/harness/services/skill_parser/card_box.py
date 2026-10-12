"""ASCII summary box and metadata extraction for CARD.md files."""

from __future__ import annotations

import re
from typing import Any


def extract_ascii_card(content: str) -> dict[str, Any]:
    """Extract metadata from ASCII summary box or table in CARD.md."""
    meta: dict[str, Any] = {}
    triggers: list[str] = []

    last_field: str | None = None
    for line in content.splitlines():
        clean = line.strip().strip("│").strip()
        if not clean:
            continue

        if clean.startswith(("Name:", "SKILL:")):
            meta["name"] = clean.split(":", 1)[1].strip()
            last_field = "name"
        elif clean.startswith(("Category:", "Domain:")):
            meta["category"] = clean.split(":", 1)[1].strip()
            last_field = "category"
        elif clean.startswith("Invocation:"):
            meta["invocation"] = clean.split(":", 1)[1].strip()
            last_field = "invocation"
        elif clean.startswith("Version:"):
            meta["version"] = clean.split(":", 1)[1].strip()
            last_field = "version"
        elif clean.startswith(("Trigger:", "Triggers:")):
            val = clean.split(":", 1)[1].strip()
            extracted = re.findall(r'"([^"]+)"', val)
            if extracted:
                triggers.extend(extracted)
            else:
                triggers.append(val.strip('"'))
            last_field = "triggers"
        elif clean.startswith(("Requires:", "Require:")):
            val = clean.split(":", 1)[1].strip()
            extracted = re.findall(r'"([^"]+)"|\'([^\']+)\'', val)
            req_list = [t[0] or t[1] for t in extracted if (t[0] or t[1])]
            if not req_list:
                req_list = [
                    t.strip().strip('"').strip("'")
                    for t in val.split(",")
                    if t.strip()
                ]
            meta["requires"] = req_list
            last_field = "requires"
        elif clean.startswith(("Provides:", "Provide:")):
            val = clean.split(":", 1)[1].strip()
            extracted = re.findall(r'"([^"]+)"|\'([^\']+)\'', val)
            prov_list = [t[0] or t[1] for t in extracted if (t[0] or t[1])]
            if not prov_list:
                prov_list = [
                    t.strip().strip('"').strip("'")
                    for t in val.split(",")
                    if t.strip()
                ]
            meta["provides"] = prov_list
            last_field = "provides"
        elif clean.startswith("Target:"):
            meta["target"] = clean.split(":", 1)[1].strip()
            last_field = "target"
        elif last_field == "triggers" and '"' in clean:
            extracted = re.findall(r'"([^"]+)"', clean)
            if extracted:
                triggers.extend(extracted)
        elif last_field == "requires" and ('"' in clean or "'" in clean):
            extracted = re.findall(r'"([^"]+)"|\'([^\']+)\'', clean)
            req_list = [t[0] or t[1] for t in extracted if (t[0] or t[1])]
            if req_list:
                meta.setdefault("requires", []).extend(req_list)
        else:
            table_match = re.match(
                r"^\|\s*\*{0,2}([a-zA-Z]+)\*{0,2}\s*\|\s*(.*?)\s*\|?$", clean
            )
            if table_match:
                k_norm = table_match.group(1).lower()
                v_val = table_match.group(2).strip().strip("`")
                if k_norm in ("name", "skill"):
                    meta["name"] = v_val
                elif k_norm in ("category", "domain"):
                    meta["category"] = v_val
                elif k_norm == "invocation":
                    meta["invocation"] = v_val
                elif k_norm == "version":
                    meta["version"] = v_val
                elif k_norm in ("requires", "require"):
                    meta["requires"] = [
                        t.strip().strip('"').strip("'")
                        for t in v_val.split(",")
                        if t.strip()
                    ]
                elif k_norm in ("provides", "provide"):
                    meta["provides"] = [
                        t.strip().strip('"').strip("'")
                        for t in v_val.split(",")
                        if t.strip()
                    ]
                elif k_norm in ("trigger", "triggers"):
                    extracted = re.findall(r'"([^"]+)"', v_val)
                    if extracted:
                        triggers.extend(extracted)
                    else:
                        triggers.extend(
                            [
                                t.strip().strip('"')
                                for t in v_val.split(",")
                                if t.strip()
                            ]
                        )
                elif k_norm == "target":
                    meta["target"] = v_val

    if triggers:
        meta["triggers"] = triggers
    return meta
