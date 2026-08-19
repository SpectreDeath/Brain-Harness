"""Exercise 02.02: Stdio JSON-RPC Sandboxing (Solution)."""

from __future__ import annotations

import sys
from typing import Any

from harness.plugins.transport import StdioJsonRpcTransport

RPC_ECHO_SCRIPT = """
import sys, json
for line in sys.stdin:
    if not line.strip(): continue
    req = json.loads(line)
    res = {'jsonrpc': '2.0', 'id': req.get('id'), 'result': {'echo': req.get('params', {})}}
    sys.stdout.write(json.dumps(res) + '\\n')
    sys.stdout.flush()
"""


async def run_rpc_echo(payload: dict[str, Any]) -> dict[str, Any]:
    transport = StdioJsonRpcTransport(
        command=sys.executable,
        args=["-c", RPC_ECHO_SCRIPT],
    )
    await transport.start()
    try:
        raw_res = await transport.call("echo", payload, timeout=5.0)
        return raw_res.get("result", raw_res)
    finally:
        await transport.stop()
