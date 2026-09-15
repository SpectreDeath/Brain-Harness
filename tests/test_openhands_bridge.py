"""Test suite for OpenHands Bridge plugin and service."""

from harness.kernel.context import ServiceContext
from harness.services.openhands_bridge import (
    OPENHANDS_BRIDGE_KEY,
    OpenHandsAction,
    OpenHandsBridgeService,
    OpenHandsObservation,
)
from plugins.software_engineering.openhands_bridge.main import (
    OpenHandsBridgePlugin,
    plugin,
)


def test_plugin_singleton_and_manifest():
    assert isinstance(plugin, OpenHandsBridgePlugin)
    assert plugin.name == "plugin.openhands_bridge"
    assert OPENHANDS_BRIDGE_KEY in plugin.provides


def test_ioc_registration():
    ctx = ServiceContext()
    p = OpenHandsBridgePlugin()
    p.on_load(ctx)

    service = ctx.require(OPENHANDS_BRIDGE_KEY)
    assert isinstance(service, OpenHandsBridgeService)


def test_action_observation_event_stream():
    p = OpenHandsBridgePlugin()
    stream_id = "test_stream_001"

    action = OpenHandsAction(
        action_type="run_command",
        payload={"command": "ls -la"},
    )
    p.record_action(stream_id, action)

    observation = OpenHandsObservation(
        action_type="run_command",
        observation_type="command_output",
        content="file1.txt\nfile2.txt",
        success=True,
    )
    p.record_observation(stream_id, observation)

    events = p.get_stream_events(stream_id)
    assert len(events) == 2
    assert events[0]["kind"] == "action"
    assert events[0]["type"] == "run_command"
    assert events[1]["kind"] == "observation"
    assert events[1]["observation_type"] == "command_output"
    assert events[1]["content"] == "file1.txt\nfile2.txt"
