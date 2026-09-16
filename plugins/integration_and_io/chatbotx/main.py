"""ChatbotX Omnichannel Messaging & Automation Plugin for Brain Harness.

Provides omnichannel contact identity management, automated flow dispatch,
broadcast transmission, and dynamic OpenAPI/MCP tool integration.
"""

from __future__ import annotations

import asyncio
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.chatbotx import (
    CHATBOTX_SERVICE_KEY,
    ChatbotXConfig,
    ChatbotXService,
    ContactRecord,
    ConversationSummary,
    DefaultChatbotXService,
    FlowExecution,
    MessageRecord,
    ToolResult,
)

logger = structlog.get_logger(__name__)


class ChatbotXPlugin(HarnessPlugin, ChatbotXService):
    """Harness Plugin implementing ChatbotX omnichannel integration."""

    name = "plugin.chatbotx"
    version = "1.0.0"
    description = "ChatbotX omnichannel messaging, contact management, and visual flow automation bridge"
    trusted = True

    def __init__(self, config: ChatbotXConfig | None = None) -> None:
        super().__init__()
        self._engine = DefaultChatbotXService(config or ChatbotXConfig())

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CHATBOTX_SERVICE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(CHATBOTX_SERVICE_KEY, self, provider=self.name)
        logger.info("ChatbotXPlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("ChatbotXPlugin unloaded")

    async def list_contacts(
        self,
        limit: int = 20,
        tag: str | None = None,
        channel: str | None = None,
    ) -> list[ContactRecord]:
        return await self._engine.list_contacts(limit=limit, tag=tag, channel=channel)

    async def get_contact(self, identifier: str) -> ContactRecord | None:
        return await self._engine.get_contact(identifier=identifier)

    async def send_message(
        self,
        contact_id: str,
        text: str,
        channel: str | None = None,
    ) -> MessageRecord:
        return await self._engine.send_message(contact_id=contact_id, text=text, channel=channel)

    async def trigger_flow(
        self,
        contact_id: str,
        flow_id: str,
    ) -> FlowExecution:
        return await self._engine.trigger_flow(contact_id=contact_id, flow_id=flow_id)

    async def manage_tags(
        self,
        contact_id: str,
        action: str,
        tag: str,
    ) -> ContactRecord:
        return await self._engine.manage_tags(contact_id=contact_id, action=action, tag=tag)

    async def query_conversations(
        self,
        limit: int = 20,
        status: str = "open",
    ) -> list[ConversationSummary]:
        return await self._engine.query_conversations(limit=limit, status=status)

    async def execute_tool(
        self,
        operation_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> ToolResult:
        return await self._engine.execute_tool(operation_id=operation_id, parameters=parameters)


# Module-level tool wrappers for direct ReAct step execution
def chatbotx_list_contacts(
    limit: int = 20,
    tag: str | None = None,
    channel: str | None = None,
) -> dict[str, Any]:
    """Search and filter contacts across WhatsApp, Telegram, and Messenger."""
    contacts = asyncio.run(plugin.list_contacts(limit=limit, tag=tag, channel=channel))
    return {
        "status": "ok",
        "count": len(contacts),
        "contacts": [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "channel": c.channel,
                "channel_user_id": c.channel_user_id,
                "status": c.status,
                "tags": list(c.tags),
                "custom_fields": dict(c.custom_fields),
            }
            for c in contacts
        ],
    }


def chatbotx_send_message(
    contact_id: str,
    text: str,
    channel: str | None = None,
) -> dict[str, Any]:
    """Send an outbound text message to a contact."""
    try:
        msg = asyncio.run(plugin.send_message(contact_id=contact_id, text=text, channel=channel))
        return {
            "status": "ok",
            "message_id": msg.id,
            "contact_id": msg.contact_id,
            "channel": msg.channel,
            "direction": msg.direction,
            "text": msg.text,
            "delivery_status": msg.status,
            "created_at": msg.created_at,
        }
    except KeyError as e:
        return {"status": "error", "error": str(e)}


def chatbotx_trigger_flow(
    contact_id: str,
    flow_id: str,
) -> dict[str, Any]:
    """Trigger an automated visual flow DAG for a contact."""
    try:
        execution = asyncio.run(plugin.trigger_flow(contact_id=contact_id, flow_id=flow_id))
        return {
            "status": "ok",
            "execution_id": execution.execution_id,
            "flow_id": execution.flow_id,
            "contact_id": execution.contact_id,
            "flow_status": execution.status,
            "current_node": execution.current_node,
        }
    except KeyError as e:
        return {"status": "error", "error": str(e)}


def chatbotx_manage_tags(
    contact_id: str,
    action: str,
    tag: str,
) -> dict[str, Any]:
    """Add or remove a tag on a contact."""
    try:
        contact = asyncio.run(plugin.manage_tags(contact_id=contact_id, action=action, tag=tag))
        return {
            "status": "ok",
            "contact_id": contact.id,
            "tags": list(contact.tags),
        }
    except (KeyError, ValueError) as e:
        return {"status": "error", "error": str(e)}


def chatbotx_query_conversations(
    limit: int = 20,
    status: str = "open",
) -> dict[str, Any]:
    """List active conversations and unread queue counts."""
    convs = asyncio.run(plugin.query_conversations(limit=limit, status=status))
    return {
        "status": "ok",
        "count": len(convs),
        "conversations": [
            {
                "conversation_id": c.conversation_id,
                "contact_id": c.contact_id,
                "channel": c.channel,
                "unread_count": c.unread_count,
                "status": c.status,
                "last_message_text": c.last_message_text,
            }
            for c in convs
        ],
    }


def chatbotx_broadcast(
    audience_tag: str,
    message_text: str,
    channel: str | None = None,
) -> dict[str, Any]:
    """Dispatch a broadcast message to all contacts matching audience_tag."""
    contacts = asyncio.run(plugin.list_contacts(limit=100, tag=audience_tag, channel=channel))
    dispatched = []
    for c in contacts:
        msg = asyncio.run(plugin.send_message(contact_id=c.id, text=message_text, channel=channel))
        dispatched.append(msg.id)
    return {
        "status": "ok",
        "audience_tag": audience_tag,
        "recipients_count": len(dispatched),
        "dispatched_message_ids": dispatched,
    }


def chatbotx_execute_tool(
    operation_id: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a dynamic OpenAPI / MCP tool operation."""
    res = asyncio.run(plugin.execute_tool(operation_id=operation_id, parameters=parameters))
    return {
        "status": res.status,
        "operation_id": res.operation_id,
        "data": dict(res.data),
        "error": res.error,
    }


# Authoritative module-level singleton per Rule 45
plugin = ChatbotXPlugin()
