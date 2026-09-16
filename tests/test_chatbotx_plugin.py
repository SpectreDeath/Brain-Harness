"""Tests for ChatbotX Plugin and IoC Service."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
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
from plugins.integration_and_io.chatbotx.main import (
    ChatbotXPlugin,
    chatbotx_broadcast,
    chatbotx_execute_tool,
    chatbotx_list_contacts,
    chatbotx_manage_tags,
    chatbotx_query_conversations,
    chatbotx_send_message,
    chatbotx_trigger_flow,
    plugin,
)


@pytest.mark.unit
def test_chatbotx_plugin_metadata() -> None:
    """Verify plugin identity, description, and service key contracts."""
    p = ChatbotXPlugin()
    assert p.name == "plugin.chatbotx"
    assert p.version == "1.0.0"
    assert "ChatbotX" in p.description
    assert CHATBOTX_SERVICE_KEY in p.provides
    assert isinstance(p, ChatbotXService)


@pytest.mark.unit
def test_chatbotx_ioc_lifecycle() -> None:
    """Verify registration and resolution inside ServiceContext container."""
    context = ServiceContext()
    p = ChatbotXPlugin()

    p.on_load(context)
    resolved = context.require(CHATBOTX_SERVICE_KEY)
    assert resolved is p
    assert isinstance(resolved, ChatbotXService)

    p.on_unload(context)


@pytest.mark.asyncio
async def test_chatbotx_service_operations() -> None:
    """Verify asynchronous service operations against DefaultChatbotXService."""
    service = DefaultChatbotXService(ChatbotXConfig())

    # 1. List contacts
    contacts = await service.list_contacts()
    assert len(contacts) >= 2
    assert any(c.id == "cnt_001" for c in contacts)

    # 2. Filter contacts by tag
    vip_contacts = await service.list_contacts(tag="vip")
    assert len(vip_contacts) == 1
    assert vip_contacts[0].id == "cnt_001"

    # 3. Get contact
    contact = await service.get_contact("cnt_001")
    assert contact is not None
    assert contact.first_name == "Alice"

    # 4. Send message
    msg = await service.send_message(contact_id="cnt_001", text="Welcome to ChatbotX!")
    assert isinstance(msg, MessageRecord)
    assert msg.contact_id == "cnt_001"
    assert msg.status == "sent"

    # 5. Trigger flow
    flow = await service.trigger_flow(contact_id="cnt_001", flow_id="flow_onboard")
    assert isinstance(flow, FlowExecution)
    assert flow.flow_id == "flow_onboard"
    assert flow.status == "enqueued"

    # 6. Manage tags
    updated = await service.manage_tags(contact_id="cnt_001", action="add", tag="qualified")
    assert "qualified" in updated.tags

    # 7. Query conversations
    convs = await service.query_conversations()
    assert len(convs) >= 2

    # 8. Execute tool
    tool_res = await service.execute_tool(operation_id="list_contacts", parameters={"limit": 10})
    assert isinstance(tool_res, ToolResult)
    assert tool_res.status == "success"


@pytest.mark.unit
def test_chatbotx_module_tool_wrappers() -> None:
    """Verify synchronous tool wrappers exported by the plugin module."""
    # List contacts
    res_list = chatbotx_list_contacts(limit=5)
    assert res_list["status"] == "ok"
    assert res_list["count"] >= 1

    # Send message
    res_send = chatbotx_send_message(contact_id="cnt_001", text="Automated test message")
    assert res_send["status"] == "ok"
    assert "msg_" in res_send["message_id"]

    # Trigger flow
    res_flow = chatbotx_trigger_flow(contact_id="cnt_001", flow_id="flow_sync")
    assert res_flow["status"] == "ok"
    assert res_flow["flow_status"] == "enqueued"

    # Manage tags
    res_tag = chatbotx_manage_tags(contact_id="cnt_001", action="add", tag="test_tag")
    assert res_tag["status"] == "ok"
    assert "test_tag" in res_tag["tags"]

    # Query conversations
    res_conv = chatbotx_query_conversations()
    assert res_conv["status"] == "ok"
    assert res_conv["count"] >= 1

    # Broadcast
    res_bcast = chatbotx_broadcast(audience_tag="vip", message_text="Special VIP Offer")
    assert res_bcast["status"] == "ok"
    assert res_bcast["recipients_count"] >= 1

    # Execute dynamic tool
    res_tool = chatbotx_execute_tool(operation_id="list_contacts", parameters={"limit": 5})
    assert res_tool["status"] == "success"


@pytest.mark.unit
def test_chatbotx_plugin_validator_compliance() -> None:
    """Validate plugin manifest and layout using PluginValidator per Rule 34 and Rule 38."""
    plugin_dir = Path("plugins/integration_and_io/chatbotx").resolve()
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True
    for check in report.checks:
        assert check.passed is True, f"Plugin check '{check.rule}' failed: {check.message}"
