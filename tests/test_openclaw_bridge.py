"""Unit and integration tests for OpenClaw bridge services and domain-partitioned plugins."""

import pytest
from harness.kernel.context import ServiceContext
from harness.services.openclaw_bridge import (
    OPENCLAW_A2A_KEY,
    OPENCLAW_GATEWAY_KEY,
    OPENCLAW_TOOL_REPAIR_KEY,
    OpenClawA2AService,
    OpenClawA2ATask,
    OpenClawGatewayService,
    OpenClawGatewaySession,
    OpenClawToolBlock,
    OpenClawToolRepairService,
)
from plugins.agent_orchestration.openclaw_gateway.main import (
    OpenClawGatewayPlugin,
    OpenClawGatewayServiceImpl,
)
from plugins.agent_orchestration.openclaw_tool_repair.main import (
    OpenClawToolRepairPlugin,
    OpenClawToolRepairServiceImpl,
)
from plugins.agent_orchestration.openclaw_a2a.main import (
    OpenClawA2APlugin,
    OpenClawA2AServiceImpl,
)


@pytest.mark.unit
def test_openclaw_service_keys_typed():
    """Verify that all OpenClaw service keys use typed ServiceKey instances."""
    assert OPENCLAW_GATEWAY_KEY.name == "service.openclaw.gateway"
    assert OPENCLAW_TOOL_REPAIR_KEY.name == "service.openclaw.tool_repair"
    assert OPENCLAW_A2A_KEY.name == "service.openclaw.a2a"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_openclaw_gateway_service_lifecycle():
    """Verify session creation, connection, and tool calling via OpenClaw Gateway service."""
    service = OpenClawGatewayServiceImpl()

    # 1. Connect
    conn_res = await service.connect("ws://127.0.0.1:18789", token="secret_token")
    assert conn_res["status"] == "connected"
    assert conn_res["gateway_url"] == "ws://127.0.0.1:18789"
    assert conn_res["server_capabilities"]["sessions"] is True

    # 2. Create session
    session = await service.create_session(channel="telegram", permission_mode="prompt")
    assert isinstance(session, OpenClawGatewaySession)
    assert session.channel == "telegram"
    assert session.permission_mode == "prompt"
    assert session.status == "active"

    # 3. List sessions
    sessions = await service.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].session_id == session.session_id

    # 4. Call tool
    tool_res = await service.call_tool(session.session_id, "bash", {"command": "echo test"})
    assert tool_res["status"] == "success"
    assert tool_res["tool_name"] == "bash"
    assert "call_id" in tool_res

    # 5. Send message
    msg_res = await service.send_message("slack", "Hello Slack channel", recipient_id="#general")
    assert msg_res["status"] == "delivered"
    assert msg_res["channel"] == "slack"


@pytest.mark.unit
def test_openclaw_tool_repair_parsing_and_recovery():
    """Verify plain-text tool-call recovery across JSON fences, XML tags, and malformed syntax."""
    service = OpenClawToolRepairServiceImpl()

    # 1. JSON Codeblock extraction with trailing commas
    codeblock_text = """I will run the command now:
```json
{
  "tool": "git_status",
  "arguments": {
    "verbose": true,
  }
}
```
Please wait.
"""
    blocks = service.parse_plain_text_tool_blocks(codeblock_text)
    assert len(blocks) == 1
    assert blocks[0].tool_name == "git_status"
    assert blocks[0].arguments == {"verbose": True}
    assert blocks[0].is_repaired is True

    # 2. XML Tag parsing
    xml_text = """<tool_call name="read_file">
{"file_path": "src/main.py"}
</tool_call>"""
    xml_blocks = service.parse_plain_text_tool_blocks(xml_text)
    assert len(xml_blocks) == 1
    assert xml_blocks[0].tool_name == "read_file"
    assert xml_blocks[0].arguments == {"file_path": "src/main.py"}

    # 3. Stream normalization
    chunk = 'Thinking... ```json {"tool": "search", "arguments": {"q": "openclaw"}} ``` Done.'
    stripped, promoted = service.normalize_stream_chunk(chunk)
    assert len(promoted) == 1
    assert promoted[0].tool_name == "search"
    assert "```json" not in stripped
    assert "Thinking..." in stripped


@pytest.mark.unit
@pytest.mark.asyncio
async def test_openclaw_a2a_task_federation():
    """Verify A2A v1.0 task dispatching, polling, and observation completion."""
    service = OpenClawA2AServiceImpl()

    # 1. Resolve capabilities
    lead_caps = service.resolve_agent_capabilities("harness_lead")
    assert lead_caps["archetype"] == "orchestrator"

    # 2. Send task
    task = await service.send_task(
        recipient_agent="openclaw_worker",
        task_payload={"objective": "run_regression_suite", "suite": "e2e"},
        sender_agent="harness_lead",
    )
    assert isinstance(task, OpenClawA2ATask)
    assert task.status == "pending"
    assert task.recipient_agent == "openclaw_worker"

    # 3. Poll task
    polled = await service.poll_task(task.task_id)
    assert polled.task_id == task.task_id
    assert polled.status == "pending"

    # 4. Complete task
    completed = await service.complete_task(
        task_id=task.task_id,
        observation={"passed": 42, "failed": 0},
        tokens_used=1250,
    )
    assert completed.status == "completed"
    assert completed.tokens_used == 1250
    assert completed.observation == {"passed": 42, "failed": 0}
    assert completed.completed_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_openclaw_plugin_registration_in_ioc_context():
    """Verify IoC container registration and tool handler dispatch across all 3 plugins."""
    context = ServiceContext()

    gw_plugin = OpenClawGatewayPlugin()
    tr_plugin = OpenClawToolRepairPlugin()
    a2a_plugin = OpenClawA2APlugin()

    gw_plugin.register_services(context)
    tr_plugin.register_services(context)
    a2a_plugin.register_services(context)

    # Resolve from context
    resolved_gw = context.require(OPENCLAW_GATEWAY_KEY)
    resolved_tr = context.require(OPENCLAW_TOOL_REPAIR_KEY)
    resolved_a2a = context.require(OPENCLAW_A2A_KEY)

    assert resolved_gw is not None
    assert resolved_tr is not None
    assert resolved_a2a is not None

    # Test plugin tool entrypoint wrappers
    sess_dict = await gw_plugin.openclaw_gateway_create_session(channel="web", permission_mode="auto")
    assert "session_id" in sess_dict

    repair_res = await tr_plugin.openclaw_repair_tool_call('{"name": "fetch", "parameters": {"url": "https://test.com",}}')
    assert repair_res["tool_name"] == "fetch"

    a2a_dict = await a2a_plugin.openclaw_a2a_send_task("worker_node", {"step": 1})
    assert a2a_dict["status"] == "pending"
