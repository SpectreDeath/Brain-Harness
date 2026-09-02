"""OpenClaw Bridge Service — typed schemas, tool repair AST, WebSocket RPC gateway contracts, and A2A swarm federation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)

OPENCLAW_GATEWAY_KEY = ServiceKey["OpenClawGatewayService"]("service.openclaw.gateway")
OPENCLAW_TOOL_REPAIR_KEY = ServiceKey["OpenClawToolRepairService"]("service.openclaw.tool_repair")
OPENCLAW_A2A_KEY = ServiceKey["OpenClawA2AService"]("service.openclaw.a2a")


@dataclass(slots=True, frozen=True)
class OpenClawToolBlock:
    """Slotted and frozen representation of an extracted or repaired plain-text tool call."""

    tool_name: str
    arguments: dict[str, Any]
    raw_block: str
    call_id: str = ""
    is_repaired: bool = False
    repair_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize tool block to dictionary."""
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "raw_block": self.raw_block,
            "call_id": self.call_id,
            "is_repaired": self.is_repaired,
            "repair_reason": self.repair_reason,
        }


@dataclass(slots=True, frozen=True)
class OpenClawGatewaySession:
    """Slotted and frozen model representing an active OpenClaw Gateway session."""

    session_id: str
    status: str  # "active", "idle", "closed", "suspended"
    permission_mode: str = "prompt"  # "auto", "prompt", "strict", "read_only"
    created_actor: str = "user"
    channel: str = "cli"
    parent_id: str | None = None
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize gateway session to dictionary."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "permission_mode": self.permission_mode,
            "created_actor": self.created_actor,
            "channel": self.channel,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass(slots=True, frozen=True)
class OpenClawA2ATask:
    """Slotted and frozen model representing an A2A v1.0 Agent-to-Agent task envelope."""

    task_id: str
    sender_agent: str
    recipient_agent: str
    task_payload: dict[str, Any]
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    observation: dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize A2A task to dictionary."""
        return {
            "task_id": self.task_id,
            "sender_agent": self.sender_agent,
            "recipient_agent": self.recipient_agent,
            "task_payload": self.task_payload,
            "status": self.status,
            "observation": self.observation,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass(slots=True, frozen=True)
class OpenClawApprovalRequest:
    """Slotted and frozen model representing a security approval gate evaluation."""

    approval_id: str
    tool_name: str
    command: str
    reason: str
    status: str = "pending"  # "pending", "approved", "rejected"
    requested_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize approval request to dictionary."""
        return {
            "approval_id": self.approval_id,
            "tool_name": self.tool_name,
            "command": self.command,
            "reason": self.reason,
            "status": self.status,
            "requested_at": self.requested_at,
        }


@runtime_checkable
class OpenClawGatewayService(Protocol):
    """Protocol defining OpenClaw WebSocket JSON-RPC Gateway bridge capabilities."""

    async def connect(self, gateway_url: str, token: str | None = None) -> dict[str, Any]:
        """Connects and authenticates with OpenClaw Gateway."""
        ...

    async def list_sessions(self) -> list[OpenClawGatewaySession]:
        """Lists active session catalog on the gateway."""
        ...

    async def create_session(
        self,
        channel: str = "cli",
        permission_mode: str = "prompt",
        metadata: dict[str, Any] | None = None,
    ) -> OpenClawGatewaySession:
        """Creates a new session placement on the gateway."""
        ...

    async def call_tool(
        self,
        session_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatches tool execution through the OpenClaw Gateway."""
        ...

    async def send_message(
        self,
        channel: str,
        message: str,
        recipient_id: str | None = None,
    ) -> dict[str, Any]:
        """Routes message to external chat channels via OpenClaw Gateway."""
        ...


@runtime_checkable
class OpenClawToolRepairService(Protocol):
    """Protocol defining in-flight plain-text tool-call recovery and stream normalization."""

    def parse_plain_text_tool_blocks(self, text: str) -> list[OpenClawToolBlock]:
        """Parses model-emitted plain-text tool call blocks and code fences."""
        ...

    def repair_json_call(self, raw_call: str | dict[str, Any]) -> OpenClawToolBlock:
        """Repairs trailing commas, unbalanced brackets, and unescaped strings in JSON arguments."""
        ...

    def normalize_stream_chunk(self, chunk: str) -> tuple[str, list[OpenClawToolBlock]]:
        """Filters stream chunks, stripping plain-text blocks and returning promoted tool events."""
        ...


@runtime_checkable
class OpenClawA2AService(Protocol):
    """Protocol defining A2A v1.0 Agent-to-Agent multi-agent swarm federation."""

    async def send_task(
        self,
        recipient_agent: str,
        task_payload: dict[str, Any],
        sender_agent: str = "harness_lead",
    ) -> OpenClawA2ATask:
        """Dispatches an asynchronous task to a remote A2A agent."""
        ...

    async def poll_task(self, task_id: str) -> OpenClawA2ATask:
        """Polls the execution status and observation of an A2A task."""
        ...

    async def complete_task(
        self,
        task_id: str,
        observation: dict[str, Any],
        tokens_used: int = 0,
    ) -> OpenClawA2ATask:
        """Marks a local or federated task as completed with observation payload."""
        ...

    def resolve_agent_capabilities(self, agent_id: str) -> dict[str, Any]:
        """Resolves registered capabilities and tool archetypes for an agent."""
        ...
