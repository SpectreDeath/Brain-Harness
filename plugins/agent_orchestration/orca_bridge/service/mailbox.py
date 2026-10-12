"""FIFO coordinator mailbox, inter-agent messaging, and terminal PTY injection."""

from __future__ import annotations

import time
from typing import Any
import uuid

import structlog

from harness.services.orca_bridge import OrcaDeliveryBatch, OrcaMessageConfig

logger = structlog.get_logger(__name__)


class OrcaMailboxMixin:
    """Provides mailbox inspection, messaging, and terminal input injection."""

    def check_mailbox(
        self,
        terminal: str | None = None,
        wait: bool = False,
        timeout_ms: int = 15000,
        types: str | None = None,
        ack_delivery_id: str | None = None,
    ) -> OrcaDeliveryBatch:
        """Query or await the FIFO coordinator mailbox for incoming agent reports."""
        if self.is_cli_available:
            args = ["orchestration", "check"]
            if terminal:
                args.extend(["--terminal", terminal])
            if wait:
                args.append("--wait")
            if timeout_ms:
                args.extend(["--timeout-ms", str(timeout_ms)])
            if types:
                args.extend(["--types", types])
            if ack_delivery_id:
                args.extend(["--ack", ack_delivery_id])

            data = self._run_cli(args)
            messages = tuple(data.get("messages", []))
            return OrcaDeliveryBatch(
                delivery_id=data.get("deliveryId", f"deliv-{uuid.uuid4().hex[:8]}"),
                messages=messages,
                satisfied=data.get("satisfied", True),
                has_keepalive=data.get("hasKeepalive", False),
            )

        # In-memory fallback
        delivery_id = f"deliv-{uuid.uuid4().hex[:8]}"
        batch = tuple(self._mock_inbox)
        if ack_delivery_id:
            self._mock_inbox.clear()
        return OrcaDeliveryBatch(
            delivery_id=delivery_id,
            messages=batch,
            satisfied=True,
            has_keepalive=False,
        )

    def send_message(self, config: OrcaMessageConfig) -> dict[str, Any]:
        """Send an inter-agent message or post a worker settlement signal."""
        if self.is_cli_available:
            args = ["orchestration", "send", "--subject", config.subject]
            if config.to:
                args.extend(["--to", config.to])
            if config.body:
                args.extend(["--body", config.body])
            if config.message_type:
                args.extend(["--type", config.message_type])
            if config.task_id:
                args.extend(["--task-id", config.task_id])
            if config.dispatch_id:
                args.extend(["--dispatch-id", config.dispatch_id])
            if config.outcome:
                args.extend(["--outcome", config.outcome])
            if config.files_modified:
                args.extend(["--files-modified", config.files_modified])
            if config.report_path:
                args.extend(["--report-path", config.report_path])

            return self._run_cli(args)

        # In-memory fallback
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        record = {
            "id": msg_id,
            "subject": config.subject,
            "to": config.to,
            "body": config.body,
            "type": config.message_type,
            "taskId": config.task_id,
            "dispatchId": config.dispatch_id,
            "outcome": config.outcome,
            "files_modified": config.files_modified,
            "report_path": config.report_path,
            "timestamp": time.time(),
        }
        self._mock_inbox.append(record)
        logger.info(
            "Delivered mock inter-agent message", msg_id=msg_id, subject=config.subject
        )
        return {"status": "ok", "messageId": msg_id, "accepted": True}

    def send_terminal_input(
        self, terminal: str, text: str, enter: bool = True
    ) -> dict[str, Any]:
        """Deliver input directly to an active agent terminal PTY."""
        if self.is_cli_available:
            args = ["terminal", "send", "--terminal", terminal, "--text", text]
            if enter:
                args.append("--enter")
            return self._run_cli(args)

        # In-memory fallback
        logger.info(
            "Sent mock terminal input", terminal=terminal, text=text, enter=enter
        )
        return {"status": "ok", "terminal": terminal, "delivered": True}
