"""Notification and webhook dispatching plugin for Brain Harness."""

from __future__ import annotations

import asyncio
import datetime
import json
import urllib.error
import urllib.request
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.notification import (
    NOTIFICATION_SERVICE_KEY,
    NotificationService,
    TaskEventResult,
    WebhookDeliveryResult,
)

logger = structlog.get_logger(__name__)

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


class NotificationWebhookPlugin(HarnessPlugin, NotificationService):
    """Harness Plugin providing webhook dispatch, chat cards, and event notifications."""

    name = "plugin.notification_webhook"
    version = "1.0.0"
    description = "Webhook notification dispatcher, Slack & Discord card builder, and agent event broadcaster"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [NOTIFICATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(NOTIFICATION_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # NotificationService Protocol Implementation
    # -------------------------------------------------------------------------

    def notify_webhook(
        self,
        url: str,
        payload: dict[str, Any],
        timeout: float = 10.0,
    ) -> WebhookDeliveryResult:
        res = notify_webhook(url=url, payload=payload, timeout=timeout)
        return WebhookDeliveryResult(
            status=res["status"],
            delivered=res.get("delivered", False),
            status_code=res.get("status_code"),
            response=res.get("response"),
            error=res.get("error"),
        )

    async def notify_webhook_async(
        self,
        url: str,
        payload: dict[str, Any],
        timeout: float = 10.0,
    ) -> WebhookDeliveryResult:
        return await asyncio.to_thread(self.notify_webhook, url, payload, timeout)

    def notify_chat_channel(
        self,
        platform: str,
        webhook_url: str,
        title: str,
        message: str,
        status: str = "info",
        fields: dict[str, Any] | None = None,
    ) -> WebhookDeliveryResult:
        res = notify_chat_channel(
            platform=platform,
            webhook_url=webhook_url,
            title=title,
            message=message,
            status=status,
            fields=fields,
        )
        return WebhookDeliveryResult(
            status=res["status"],
            delivered=res.get("delivered", False),
            status_code=res.get("status_code"),
            response=res.get("response"),
            error=res.get("error"),
        )

    async def notify_chat_channel_async(
        self,
        platform: str,
        webhook_url: str,
        title: str,
        message: str,
        status: str = "info",
        fields: dict[str, Any] | None = None,
    ) -> WebhookDeliveryResult:
        return await asyncio.to_thread(
            self.notify_chat_channel, platform, webhook_url, title, message, status, fields
        )

    def notify_task_event(
        self,
        event_type: str,
        task_name: str,
        details: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> TaskEventResult:
        res = notify_task_event(
            event_type=event_type,
            task_name=task_name,
            details=details,
            webhook_url=webhook_url,
        )
        return TaskEventResult(
            status=res["status"],
            event=res.get("event", {}),
            dispatched=res.get("dispatched", bool(webhook_url)),
            dispatch=res.get("dispatch"),
        )

    async def notify_task_event_async(
        self,
        event_type: str,
        task_name: str,
        details: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> TaskEventResult:
        return await asyncio.to_thread(
            self.notify_task_event, event_type, task_name, details, webhook_url
        )
