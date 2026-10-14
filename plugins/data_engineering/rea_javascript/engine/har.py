"""Offline HAR 1.2 and mitmproxy capture archive inspector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import HarEntryInfo


class HarInspector:
    """Inspects offline HAR 1.2 or native mitmproxy capture records."""

    def inspect(
        self,
        har_path: str,
        filter_status: int | None = None,
    ) -> dict[str, Any]:
        """Inspect offline HAR archive entries without contacting recorded servers."""
        p = Path(har_path)
        if not p.exists():
            return {
                "status": "error",
                "error": f"HAR archive file not found: {har_path}",
                "har_path": har_path,
                "entries_count": 0,
                "entries": [],
            }

        try:
            content = json.loads(p.read_text(encoding="utf-8"))
            log_obj = content.get("log") or {}
            raw_entries = log_obj.get("entries") or []

            parsed_entries: list[dict[str, Any]] = []
            for entry in raw_entries:
                req = entry.get("request") or {}
                res = entry.get("response") or {}
                status_code = res.get("status", 0)

                if filter_status is not None and status_code != filter_status:
                    continue

                info = HarEntryInfo(
                    method=req.get("method", "GET"),
                    url=req.get("url", ""),
                    status=status_code,
                    mime_type=(res.get("content") or {}).get("mimeType", ""),
                    response_size=(res.get("content") or {}).get("size", 0),
                )
                parsed_entries.append({
                    "method": info.method,
                    "url": info.url,
                    "status": info.status,
                    "mime_type": info.mime_type,
                    "response_size": info.response_size,
                })

            return {
                "status": "ok",
                "har_path": str(p),
                "entries_count": len(raw_entries),
                "filtered_entries_count": len(parsed_entries),
                "entries": parsed_entries,
                "error": None,
            }
        except json.JSONDecodeError as err:
            return {
                "status": "error",
                "error": f"Malformed HAR JSON format: {err}",
                "har_path": str(p),
                "entries_count": 0,
                "entries": [],
            }
