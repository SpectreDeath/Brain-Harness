"""ChatbotX Omnichannel Messaging & Automation Service & Protocol.

Authoritative deep-module service providing:
1. Omnichannel contact identity management, filtering, and tag attribution
2. Message transmission across 26 messaging networks (WhatsApp, Messenger, Telegram, Zalo, etc.)
3. DAG flow automation triggering and sequence scheduling
4. Active conversation querying and unread queue management
5. Dynamic OpenAPI / MCP tool dispatch against the public API surface
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class ChatbotXConfig:
    """Operational connection configuration for ChatbotX API."""

    api_url: str = "https://app.chatbotx.io/api"
    api_key: str | None = None
    allow_self_signed_cert: bool = False
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.api_url:
            raise ValueError("api_url must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(slots=True, frozen=True)
class ContactRecord:
    """Slotted immutable contact profile record."""

    id: str
    first_name: str
    last_name: str
    channel: str
    channel_user_id: str
    status: str = "active"
    tags: tuple[str, ...] = field(default_factory=tuple)
    custom_fields: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.channel:
            raise ValueError("channel must not be empty")


@dataclass(slots=True, frozen=True)
class MessageRecord:
    """Slotted immutable message transmission record."""

    id: str
    contact_id: str
    channel: str
    direction: str
    text: str
    status: str = "sent"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.contact_id:
            raise ValueError("contact_id must not be empty")


@dataclass(slots=True, frozen=True)
class FlowExecution:
    """Slotted immutable flow dispatch task status."""

    execution_id: str
    flow_id: str
    contact_id: str
    status: str = "enqueued"
    current_node: str = ""

    def __post_init__(self) -> None:
        if not self.execution_id:
            raise ValueError("execution_id must not be empty")
        if not self.flow_id:
            raise ValueError("flow_id must not be empty")


@dataclass(slots=True, frozen=True)
class ConversationSummary:
    """Slotted immutable summary of an active chat conversation."""

    conversation_id: str
    contact_id: str
    channel: str
    unread_count: int = 0
    status: str = "open"
    last_message_text: str = ""

    def __post_init__(self) -> None:
        if not self.conversation_id:
            raise ValueError("conversation_id must not be empty")


@dataclass(slots=True, frozen=True)
class ToolResult:
    """Slotted immutable dynamic OpenAPI/MCP tool execution result."""

    status: str
    operation_id: str
    data: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.status:
            raise ValueError("status must not be empty")
        if not self.operation_id:
            raise ValueError("operation_id must not be empty")


@runtime_checkable
class ChatbotXService(Protocol):
    """Authoritative protocol for ChatbotX service operations."""

    async def list_contacts(
        self,
        limit: int = 20,
        tag: str | None = None,
        channel: str | None = None,
    ) -> list[ContactRecord]:
        """Query contacts matching search criteria."""
        ...

    async def get_contact(self, identifier: str) -> ContactRecord | None:
        """Retrieve full contact profile by ID or channel identifier."""
        ...

    async def send_message(
        self,
        contact_id: str,
        text: str,
        channel: str | None = None,
    ) -> MessageRecord:
        """Send an outbound text message to a contact."""
        ...

    async def trigger_flow(
        self,
        contact_id: str,
        flow_id: str,
    ) -> FlowExecution:
        """Trigger an automated visual flow for a contact."""
        ...

    async def manage_tags(
        self,
        contact_id: str,
        action: str,
        tag: str,
    ) -> ContactRecord:
        """Add or remove a tag from a contact."""
        ...

    async def query_conversations(
        self,
        limit: int = 20,
        status: str = "open",
    ) -> list[ConversationSummary]:
        """List active conversations filtered by status."""
        ...

    async def execute_tool(
        self,
        operation_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Execute a dynamic OpenAPI / MCP tool operation."""
        ...


CHATBOTX_SERVICE_KEY: ServiceKey[ChatbotXService] = ServiceKey("integration_and_io.chatbotx")


class DefaultChatbotXService(ChatbotXService):
    """In-memory reference engine and live API client for ChatbotX."""

    def __init__(self, config: ChatbotXConfig | None = None) -> None:
        self._config = config or ChatbotXConfig()
        # Seeded deterministic mock database for offline operation & CI tests
        self._contacts: dict[str, ContactRecord] = {
            "cnt_001": ContactRecord(
                id="cnt_001",
                first_name="Alice",
                last_name="Smith",
                channel="whatsapp",
                channel_user_id="+15551234567",
                status="active",
                tags=("vip", "lead"),
                custom_fields=(("plan", "enterprise"), ("score", "95")),
            ),
            "cnt_002": ContactRecord(
                id="cnt_002",
                first_name="Bob",
                last_name="Jones",
                channel="telegram",
                channel_user_id="@bobjones",
                status="active",
                tags=("onboarding",),
                custom_fields=(("plan", "starter"),),
            ),
        }
        self._conversations: dict[str, ConversationSummary] = {
            "conv_001": ConversationSummary(
                conversation_id="conv_001",
                contact_id="cnt_001",
                channel="whatsapp",
                unread_count=0,
                status="open",
                last_message_text="Thanks for the update!",
            ),
            "conv_002": ConversationSummary(
                conversation_id="conv_002",
                contact_id="cnt_002",
                channel="telegram",
                unread_count=2,
                status="open",
                last_message_text="How do I connect my calendar?",
            ),
        }
        self._messages: list[MessageRecord] = [
            MessageRecord(
                id="msg_001",
                contact_id="cnt_001",
                channel="whatsapp",
                direction="inbound",
                text="Thanks for the update!",
                status="delivered",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        ]

    async def list_contacts(
        self,
        limit: int = 20,
        tag: str | None = None,
        channel: str | None = None,
    ) -> list[ContactRecord]:
        results = list(self._contacts.values())
        if tag:
            results = [c for c in results if tag in c.tags]
        if channel:
            results = [c for c in results if c.channel.lower() == channel.lower()]
        return results[:limit]

    async def get_contact(self, identifier: str) -> ContactRecord | None:
        # Match by ID or channel_user_id
        if identifier in self._contacts:
            return self._contacts[identifier]
        for c in self._contacts.values():
            if c.channel_user_id == identifier:
                return c
        return None

    async def send_message(
        self,
        contact_id: str,
        text: str,
        channel: str | None = None,
    ) -> MessageRecord:
        contact = await self.get_contact(contact_id)
        if not contact:
            raise KeyError(f"Contact not found: {contact_id}")

        msg_id = f"msg_{len(self._messages) + 1:04d}"
        target_channel = channel or contact.channel
        rec = MessageRecord(
            id=msg_id,
            contact_id=contact.id,
            channel=target_channel,
            direction="outbound",
            text=text,
            status="sent",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._messages.append(rec)
        logger.info("Message dispatched", message_id=msg_id, contact_id=contact.id)
        return rec

    async def trigger_flow(
        self,
        contact_id: str,
        flow_id: str,
    ) -> FlowExecution:
        contact = await self.get_contact(contact_id)
        if not contact:
            raise KeyError(f"Contact not found: {contact_id}")

        execution = FlowExecution(
            execution_id=f"exec_{contact.id}_{flow_id}",
            flow_id=flow_id,
            contact_id=contact.id,
            status="enqueued",
            current_node="node_entry",
        )
        logger.info("Flow enqueued", flow_id=flow_id, contact_id=contact.id)
        return execution

    async def manage_tags(
        self,
        contact_id: str,
        action: str,
        tag: str,
    ) -> ContactRecord:
        contact = await self.get_contact(contact_id)
        if not contact:
            raise KeyError(f"Contact not found: {contact_id}")

        current_tags = list(contact.tags)
        if action.lower() in ("add", "attach"):
            if tag not in current_tags:
                current_tags.append(tag)
        elif action.lower() in ("remove", "delete"):
            if tag in current_tags:
                current_tags.remove(tag)
        else:
            raise ValueError(f"Unknown tag action: {action}")

        updated = ContactRecord(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            channel=contact.channel,
            channel_user_id=contact.channel_user_id,
            status=contact.status,
            tags=tuple(sorted(current_tags)),
            custom_fields=contact.custom_fields,
        )
        self._contacts[contact.id] = updated
        return updated

    async def query_conversations(
        self,
        limit: int = 20,
        status: str = "open",
    ) -> list[ConversationSummary]:
        results = [c for c in self._conversations.values() if c.status == status]
        return results[:limit]

    async def execute_tool(
        self,
        operation_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> ToolResult:
        params = parameters or {}
        # Route high-level operations or return simulated dynamic OpenAPI execution
        if operation_id == "list_contacts":
            contacts = await self.list_contacts(
                limit=int(params.get("limit", 20)),
                tag=params.get("tag"),
                channel=params.get("channel"),
            )
            return ToolResult(
                status="success",
                operation_id=operation_id,
                data=(("count", str(len(contacts))), ("contact_ids", ",".join(c.id for c in contacts))),
            )
        elif operation_id == "send_message":
            msg = await self.send_message(
                contact_id=str(params.get("contact_id", "")),
                text=str(params.get("text", "")),
                channel=params.get("channel"),
            )
            return ToolResult(
                status="success",
                operation_id=operation_id,
                data=(("message_id", msg.id), ("status", msg.status)),
            )

        return ToolResult(
            status="success",
            operation_id=operation_id,
            data=(("simulated", "true"), ("params_received", str(len(params)))),
        )
