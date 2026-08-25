"""Notification and webhook dispatch service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class WebhookDeliveryResult(BaseModel):
    """Result of dispatching a webhook payload."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    delivered: bool = Field(default=False, description="Whether webhook was delivered (HTTP 2xx)")
    status_code: int | None = Field(default=None, description="HTTP status code received")
    response: str | None = Field(default=None, description="Response snippet from target server")
    error: str | None = Field(default=None, description="Error message if delivery failed")


class TaskEventResult(BaseModel):
    """Result of formatting and broadcasting an agent task event."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    event: dict[str, Any] = Field(default_factory=dict, description="Structured event payload")
    dispatched: bool = Field(default=False, description="Whether event was forwarded to a remote webhook")
    dispatch: WebhookDeliveryResult | dict[str, Any] | None = Field(default=None, description="Remote dispatch outcome")


@runtime_checkable
class NotificationService(Protocol):
    """Protocol for webhook notifications, chat channel cards, and task lifecycle events."""

    def notify_webhook(
        self,
        url: str,
        payload: dict[str, Any],
        timeout: float = 10.0,
    ) -> WebhookDeliveryResult:
        """Send JSON payload to a target webhook URL synchronously."""
        ...

    async def notify_webhook_async(
        self,
        url: str,
        payload: dict[str, Any],
        timeout: float = 10.0,
    ) -> WebhookDeliveryResult:
        """Send JSON payload to a target webhook URL asynchronously without blocking the event loop."""
        ...

    def notify_chat_channel(
        self,
        platform: str,
        webhook_url: str,
        title: str,
        message: str,
        status: str = "info",
        fields: dict[str, Any] | None = None,
    ) -> WebhookDeliveryResult:
        """Format and dispatch a rich message card to Slack or Discord synchronously."""
        ...

    async def notify_chat_channel_async(
        self,
        platform: str,
        webhook_url: str,
        title: str,
        message: str,
        status: str = "info",
        fields: dict[str, Any] | None = None,
    ) -> WebhookDeliveryResult:
        """Format and dispatch a rich message card to Slack or Discord asynchronously."""
        ...

    def notify_task_event(
        self,
        event_type: str,
        task_name: str,
        details: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> TaskEventResult:
        """Format and broadcast an agent task lifecycle event synchronously."""
        ...

    async def notify_task_event_async(
        self,
        event_type: str,
        task_name: str,
        details: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> TaskEventResult:
        """Format and broadcast an agent task lifecycle event asynchronously."""
        ...


NOTIFICATION_SERVICE_KEY: ServiceKey[NotificationService] = ServiceKey("service.notification_webhook")
