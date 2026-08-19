"""Notification and webhook dispatching plugin for Brain Harness."""

from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.request
from typing import Any

_STATUS_COLORS_DISCORD = {
    "success": 0x22C55E,  # Green
    "error": 0xEF4444,    # Red
    "warning": 0xF59E0B,  # Amber
    "info": 0x3B82F6,     # Blue
}

_STATUS_EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}


def notify_webhook(
    url: str,
    payload: dict[str, Any],
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Send JSON payload to a target webhook URL."""
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BrainHarness/1.0 (Autonomous Agent Notifier)",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            raw_body = response.read().decode("utf-8", errors="replace")
            return {
                "status": "ok",
                "delivered": 200 <= status_code < 300,
                "status_code": status_code,
                "response": raw_body[:500],
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "delivered": False,
            "status_code": e.code,
            "error": f"HTTP Error {e.code}: {e.reason}",
        }
    except Exception as e:
        return {
            "status": "error",
            "delivered": False,
            "error": f"Webhook delivery failed: {e!s}",
        }


def notify_chat_channel(
    platform: str,
    webhook_url: str,
    title: str,
    message: str,
    status: str = "info",
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format and dispatch a structured notification card to Slack or Discord."""
    plat = platform.lower().strip()
    st = status.lower().strip()
    emoji = _STATUS_EMOJIS.get(st, "ℹ️")

    if plat == "slack":
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {title}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
        ]
        if fields:
            field_elements = [
                {"type": "mrkdwn", "text": f"*{k}:*\n{v}"}
                for k, v in fields.items()
            ]
            blocks.append({
                "type": "section",
                "fields": field_elements[:10],
            })
        payload = {"blocks": blocks}

    elif plat == "discord":
        embed: dict[str, Any] = {
            "title": f"{emoji} {title}",
            "description": message,
            "color": _STATUS_COLORS_DISCORD.get(st, 0x3B82F6),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if fields:
            embed["fields"] = [
                {"name": str(k), "value": str(v), "inline": True}
                for k, v in fields.items()
            ][:10]
        payload = {"embeds": [embed]}

    else:
        payload = {
            "title": title,
            "message": message,
            "status": status,
            "fields": fields or {},
        }

    return notify_webhook(webhook_url, payload)


def notify_task_event(
    event_type: str,
    task_name: str,
    details: dict[str, Any] | None = None,
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Format and broadcast an agent task lifecycle event."""
    event_payload = {
        "event_type": event_type.upper(),
        "task_name": task_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "BrainHarness.Runtime",
        "details": details or {},
    }

    if webhook_url:
        dispatch_res = notify_webhook(webhook_url, event_payload)
        return {
            "status": "ok",
            "event": event_payload,
            "dispatch": dispatch_res,
        }

    return {
        "status": "ok",
        "event": event_payload,
        "dispatched": False,
    }
