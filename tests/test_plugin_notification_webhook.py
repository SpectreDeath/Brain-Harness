"""Tests for notification_webhook plugin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from plugins.integration_and_io.notification_webhook.main import (
    notify_chat_channel,
    notify_task_event,
    notify_webhook,
)


@pytest.mark.unit
class TestNotificationWebhookPlugin:
    def test_notify_webhook_success(self) -> None:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"ok": true}'

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            res = notify_webhook("https://webhook.site/test", {"event": "ping"})
            assert res["status"] == "ok"
            assert res["delivered"] is True
            assert res["status_code"] == 200

    def test_notify_chat_channel_slack(self) -> None:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b"ok"

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            res = notify_chat_channel(
                platform="slack",
                webhook_url="https://hooks.slack.com/services/T00/B00/X00",
                title="Task Succeeded",
                message="All 12 plugins loaded.",
                status="success",
                fields={"Duration": "4.2s", "Tests": "165 passed"},
            )
            assert res["status"] == "ok"
            assert res["delivered"] is True

    def test_notify_chat_channel_discord(self) -> None:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 204
        mock_response.read.return_value = b""

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            res = notify_chat_channel(
                platform="discord",
                webhook_url="https://discord.com/api/webhooks/00/xx",
                title="System Alert",
                message="Warning event observed.",
                status="warning",
            )
            assert res["status"] == "ok"
            assert res["delivered"] is True

    def test_notify_task_event_local(self) -> None:
        res = notify_task_event(
            event_type="TASK_COMPLETED",
            task_name="Index repository code",
            details={"chunks_indexed": 42},
        )
        assert res["status"] == "ok"
        assert res["event"]["event_type"] == "TASK_COMPLETED"
        assert res["event"]["task_name"] == "Index repository code"
        assert res["event"]["details"]["chunks_indexed"] == 42
