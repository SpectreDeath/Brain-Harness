"""Exercise 02.02: Stdio JSON-RPC Sandboxing (Problem)."""

from __future__ import annotations

from typing import Any

# Python worker snippet that echoes JSON-RPC requests
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
    # TODO: Create StdioJsonRpcTransport with command=sys.executable and args=["-c", RPC_ECHO_SCRIPT]
    # TODO: Start transport
    # TODO: Call method "echo" with payload
    # TODO: Stop transport
    # TODO: Return result dictionary
    raise NotImplementedError
