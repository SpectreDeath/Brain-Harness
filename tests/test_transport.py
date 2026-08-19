"""Tests for StdioJsonRpcTransport."""

from __future__ import annotations

import sys

import pytest

from harness.plugins.transport import StdioJsonRpcTransport, TransportError


@pytest.mark.unit
@pytest.mark.asyncio
class TestStdioJsonRpcTransport:
    async def test_start_stop_lifecycle(self) -> None:
        transport = StdioJsonRpcTransport(
            sys.executable,
            ["-c", "import time; time.sleep(10)"],
        )
        assert not transport.is_running
        assert transport.pid is None

        await transport.start()
        assert transport.is_running
        assert transport.pid is not None

        await transport.stop(timeout=1.0)
        assert not transport.is_running

    async def test_call_and_notification(self) -> None:
        # Python script echoing method and params as JSON-RPC response
        server_code = """
import sys
import json

for line in sys.stdin:
    req = json.loads(line.strip())
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})
    if req_id is not None:
        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"echo_method": method, "echo_params": params}}
        sys.stdout.write(json.dumps(resp) + "\\n")
        sys.stdout.flush()
"""
        transport = StdioJsonRpcTransport(
            sys.executable,
            ["-c", server_code],
        )
        await transport.start()

        # Send notification
        await transport.send_notification("ping", {"foo": "bar"})

        # Send call
        res = await transport.call("add", {"a": 10, "b": 20})
        assert res.get("result") == {"echo_method": "add", "echo_params": {"a": 10, "b": 20}}

        await transport.stop()

    async def test_call_when_not_running(self) -> None:
        transport = StdioJsonRpcTransport("python")
        with pytest.raises(TransportError):
            await transport.call("test")

        with pytest.raises(TransportError):
            await transport.send_notification("test")

    async def test_call_timeout(self) -> None:
        # Process that never responds
        transport = StdioJsonRpcTransport(
            sys.executable,
            ["-c", "import time; time.sleep(10)"],
        )
        await transport.start()

        res = await transport.call("slow", timeout=0.1)
        assert "error" in res
        assert "timed out" in res["error"]

        await transport.stop()
