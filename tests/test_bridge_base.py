"""Contract tests for foreign agent bridge scaffold and error taxonomy."""

from __future__ import annotations

import os
import time
from typing import Any

import pytest

from harness.services.bridge_base import (
    BaseForeignAgentBridge,
    BridgeAuthConfig,
    BridgeAuthMethod,
    BridgeError,
    BridgeErrorCode,
    BridgeToolMapping,
    BridgeTransportKind,
)


@pytest.mark.unit
class TestBridgeBaseContracts:
    """Validate shared foreign-agent bridge scaffolding contracts."""

    def test_auth_config_bearer_resolution_and_header_injection(self) -> None:
        """Verify Bearer token auth header formatting."""
        cfg = BridgeAuthConfig(method=BridgeAuthMethod.BEARER_TOKEN, token="secret-token-123")
        assert cfg.resolve_token() == "secret-token-123"

        headers = cfg.inject_headers({"Content-Type": "application/json"})
        assert headers["Authorization"] == "Bearer secret-token-123"
        assert headers["Content-Type"] == "application/json"

    def test_auth_config_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify dynamic token resolution from environment variables."""
        monkeypatch.setenv("PEER_API_KEY", "env-secret-456")
        cfg = BridgeAuthConfig(
            method=BridgeAuthMethod.API_KEY,
            header_name="X-API-Key",
            env_var="PEER_API_KEY",
        )
        assert cfg.resolve_token() == "env-secret-456"

        headers = cfg.inject_headers({})
        assert headers["X-API-Key"] == "env-secret-456"

    def test_bridge_tool_mapping_translation(self) -> None:
        """Verify input argument transformations and output deserialization."""
        def transform_in(args: dict[str, Any]) -> dict[str, Any]:
            return {"query_text": args["query"]}

        def transform_out(result: Any) -> Any:
            return {"matches": result["items"]}

        mapping = BridgeToolMapping(
            local_name="search_docs",
            remote_name="peer_search",
            transform_input=transform_in,
            transform_output=transform_out,
        )

        bridge = BaseForeignAgentBridge(
            peer_name="test_peer",
            transport_kind=BridgeTransportKind.HTTP,
        )
        bridge.register_tool_mapping(mapping)

        peer_tool, peer_args = bridge.map_tool_input("search_docs", {"query": "micro-kernel"})
        assert peer_tool == "peer_search"
        assert peer_args == {"query_text": "micro-kernel"}

        final_res = bridge.map_tool_output("search_docs", {"items": [1, 2, 3]})
        assert final_res == {"matches": [1, 2, 3]}

        # Unmapped tool passes through unchanged
        raw_name, raw_args = bridge.map_tool_input("unknown_tool", {"a": 1})
        assert raw_name == "unknown_tool"
        assert raw_args == {"a": 1}

    def test_bridge_error_taxonomy(self) -> None:
        """Verify standardized error formatting and attributes."""
        err = BridgeError(
            code=BridgeErrorCode.NETWORK_TIMEOUT,
            message="Connection dropped after 3000ms",
            peer_name="orca_node",
            details={"endpoint": "http://127.0.0.1:8080/rpc"},
        )
        assert err.code == BridgeErrorCode.NETWORK_TIMEOUT
        assert err.peer_name == "orca_node"
        assert "[orca_node][NETWORK_TIMEOUT]" in str(err)
        assert err.details["endpoint"] == "http://127.0.0.1:8080/rpc"

    def test_bridge_latency_instrumentation(self) -> None:
        """Verify execution timing and structured call recording."""
        bridge = BaseForeignAgentBridge(
            peer_name="claude_code",
            transport_kind=BridgeTransportKind.SUBPROCESS_STDIO,
        )
        start = time.perf_counter()
        time.sleep(0.01)
        latency_ms = bridge.record_call("execute_step", start, success=True)
        assert latency_ms >= 5.0
