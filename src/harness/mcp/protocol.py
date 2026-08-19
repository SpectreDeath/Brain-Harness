"""Model Context Protocol (MCP) — unified codec and message protocol seam.

Provides authoritative serialization, deserialization, JSON-RPC 2.0 framing,
error envelope isolation, and ToolSpec ↔ MCP schema translation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import structlog

from harness.services.tools import ToolSpec

logger = structlog.get_logger()

# Standard JSON-RPC 2.0 Error Codes
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603

DEFAULT_PROTOCOL_VERSION = "2024-11-05"


@dataclass(frozen=True)
class MCPRequest:
    """Parsed JSON-RPC 2.0 MCP request."""

    id: Any | None
    method: str
    params: dict[str, Any]


class MCPProtocolCodec:
    """Authoritative codec for MCP JSON-RPC 2.0 requests, responses, and schema translation."""

    @classmethod
    def parse_request(cls, raw_text: str | bytes) -> MCPRequest:
        """Parse raw JSON-RPC string or bytes into a structured MCPRequest.

        Raises:
            ValueError: If JSON is malformed or invalid JSON-RPC 2.0.
        """
        if isinstance(raw_text, bytes):
            raw_text = raw_text.decode("utf-8")

        try:
            data = json.loads(raw_text)
        except Exception as e:
            raise ValueError(f"JSON parse error: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Invalid JSON-RPC: payload must be a JSON object")

        req_id = data.get("id")
        method = str(data.get("method", ""))
        params = data.get("params") or {}
        if not isinstance(params, dict):
            params = {"value": params}

        return MCPRequest(id=req_id, method=method, params=params)

    @classmethod
    def encode_response(cls, req_id: Any, result: Any) -> dict[str, Any]:
        """Encode a successful JSON-RPC 2.0 response object."""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    @classmethod
    def encode_error(
        cls,
        req_id: Any,
        code: int,
        message: str,
        data: Any | None = None,
    ) -> dict[str, Any]:
        """Encode a JSON-RPC 2.0 error response object."""
        error_obj: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error_obj["data"] = data

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": error_obj,
        }

    @classmethod
    def encode_request(
        cls,
        method: str,
        params: dict[str, Any] | None = None,
        req_id: Any | None = 1,
    ) -> dict[str, Any]:
        """Encode an outgoing JSON-RPC 2.0 request payload."""
        req: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        if req_id is not None:
            req["id"] = req_id
        return req

    @classmethod
    def build_initialize_response(
        cls,
        req_id: Any,
        server_name: str = "harness-mcp",
        version: str = "0.1.0",
        protocol_version: str = DEFAULT_PROTOCOL_VERSION,
    ) -> dict[str, Any]:
        """Build standard MCP initialize response payload."""
        return cls.encode_response(
            req_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                },
                "serverInfo": {"name": server_name, "version": version},
            },
        )

    @classmethod
    def build_tools_list_response(
        cls, req_id: Any, tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build standard MCP tools/list response."""
        return cls.encode_response(req_id, {"tools": tools})

    @classmethod
    def build_tool_call_response(
        cls,
        req_id: Any,
        result: Any,
        is_error: bool = False,
    ) -> dict[str, Any]:
        """Build standard MCP tools/call response envelope."""
        content_text = (
            result
            if isinstance(result, str)
            else json.dumps(result, ensure_ascii=False)
        )
        return cls.encode_response(
            req_id,
            {
                "content": [{"type": "text", "text": content_text}],
                "isError": is_error,
            },
        )

    @classmethod
    def build_resources_list_response(
        cls, req_id: Any, resources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build standard MCP resources/list response."""
        return cls.encode_response(req_id, {"resources": resources})

    @classmethod
    def build_resource_read_response(
        cls,
        req_id: Any,
        uri: str,
        contents: str | dict[str, Any] | list[Any],
        mime_type: str = "application/json",
    ) -> dict[str, Any]:
        """Build standard MCP resources/read response."""
        text = contents if isinstance(contents, str) else json.dumps(contents, ensure_ascii=False, indent=2)
        return cls.encode_response(
            req_id,
            {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": mime_type,
                        "text": text,
                    }
                ]
            },
        )

    @classmethod
    def build_prompts_list_response(
        cls, req_id: Any, prompts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build standard MCP prompts/list response."""
        return cls.encode_response(req_id, {"prompts": prompts})

    @classmethod
    def build_prompt_get_response(
        cls,
        req_id: Any,
        description: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build standard MCP prompts/get response."""
        return cls.encode_response(
            req_id,
            {
                "description": description,
                "messages": messages,
            },
        )

    @classmethod
    def tool_spec_to_mcp(cls, spec: ToolSpec) -> dict[str, Any]:
        """Convert a native ToolSpec to standard MCP Tool object definition."""
        return {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.parameters_schema or {"type": "object", "properties": {}},
        }

    @classmethod
    def mcp_tool_to_spec(
        cls,
        tool_meta: dict[str, Any],
        provider: str = "",
        executor: Callable[..., Any] | None = None,
    ) -> ToolSpec:
        """Convert an external MCP Tool definition into a native Harness ToolSpec."""
        raw_name = tool_meta.get("name", "")
        name = f"{provider}.{raw_name}" if provider and not raw_name.startswith(f"{provider}.") else raw_name
        description = tool_meta.get("description", "")
        schema = tool_meta.get("inputSchema") or {"type": "object", "properties": {}}

        return ToolSpec(
            name=name,
            description=description,
            parameters_schema=schema,
            provider=provider,
            executor=executor,
            enabled=True,
        )


@dataclass
class MCPResource:
    """A resource exposed via MCP."""

    uri: str
    name: str
    description: str = ""
    mime_type: str = "application/json"
    handler: Callable[[], Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass
class MCPPrompt:
    """A prompt template exposed via MCP."""

    name: str
    description: str = ""
    arguments: list[dict[str, Any]] | None = None
    template_handler: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments or [],
        }

