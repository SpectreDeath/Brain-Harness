"""Tests for Deepened Subprocess Sandbox Transport and Pipe Lifecycle Disposal (Cycle 12)."""

from __future__ import annotations

import asyncio
import sys
import pytest

from harness.plugins.transport import StdioJsonRpcTransport, TransportError


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stdio_jsonrpc_transport_lifecycle_and_pipe_disposal() -> None:
    """Test that StdioJsonRpcTransport cleanly initializes, handles calls, and closes pipes on stop."""
    # Start a simple python JSON-RPC echo script
    code = """
import sys, json
for line in sys.stdin:
    req = json.loads(line.strip())
    method = req.get("method")
    req_id = req.get("id", 0)
    if method == "echo":
        res = {"jsonrpc": "2.0", "id": req_id, "result": req.get("params", {})}
    else:
        res = {"jsonrpc": "2.0", "id": req_id, "error": "unknown_method"}
    sys.stdout.write(json.dumps(res) + "\\n")
    sys.stdout.flush()
"""
    transport = StdioJsonRpcTransport(
        sys.executable,
        ["-c", code],
    )

    await transport.start()
    assert transport.is_running is True
    assert transport.pid is not None

    # Call echo method
    resp = await transport.call("echo", {"hello": "world"}, timeout=5.0)
    assert resp.get("result") == {"hello": "world"}

    # Stop transport and verify complete resource disposal
    await transport.stop()
    assert transport.is_running is False

    # Calling after stop must raise TransportError
    with pytest.raises(TransportError):
        await transport.call("echo", {}, timeout=1.0)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stdio_jsonrpc_transport_force_stop() -> None:
    """Test that stop handles already-terminated or unresponsive child processes gracefully."""
    # Python script that exits immediately
    transport = StdioJsonRpcTransport(
        sys.executable,
        ["-c", "import sys; sys.exit(0)"],
    )

    await transport.start()
    await asyncio.sleep(0.2)  # Allow process to terminate

    # stop() should cleanly clean up streams without error
    await transport.stop()
    assert transport.is_running is False
