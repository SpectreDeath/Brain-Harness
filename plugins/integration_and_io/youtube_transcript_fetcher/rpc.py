"""Line-buffered JSON-RPC 2.0 protocol handler and server loop."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from .operations import (
    fetch_transcript,
    get_transcript_text,
    health,
    list_transcripts,
)

RPC_METHODS: dict[str, Any] = {
    "fetch_transcript": fetch_transcript,
    "get_transcript": fetch_transcript,
    "get_transcript_text": get_transcript_text,
    "list_transcripts": list_transcripts,
    "health": health,
    "ping": lambda: {"status": "ok", "pong": True},
}


def handle_rpc_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a parsed JSON-RPC 2.0 request payload and return response object."""
    req_id = request_data.get("id", 0)
    method_name = request_data.get("method", "")
    params = request_data.get("params", {})

    if not isinstance(params, dict):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32602,
                "message": "Invalid params: params must be a JSON object",
            },
        }

    handler = RPC_METHODS.get(method_name)
    if handler is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method_name}'",
            },
        }

    try:
        result = handler(**params)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
    except Exception as handler_err:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32000,
                "message": f"Server execution error in '{method_name}': {handler_err}",
            },
        }


def run_jsonrpc_server(
    stdin_stream: TextIO | None = None,
    stdout_stream: TextIO | None = None,
) -> None:
    """Run line-buffered JSON-RPC 2.0 server reading stdin and writing stdout."""
    stdin = stdin_stream or sys.stdin
    stdout = stdout_stream or sys.stdout

    for raw_line in stdin:
        trimmed = raw_line.strip()
        if not trimmed:
            continue

        try:
            req_json = json.loads(trimmed)
            if not isinstance(req_json, dict):
                resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
                }
            else:
                resp = handle_rpc_request(req_json)
        except json.JSONDecodeError as decode_err:
            resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {decode_err}"},
            }

        stdout.write(json.dumps(resp) + "\n")
        stdout.flush()
