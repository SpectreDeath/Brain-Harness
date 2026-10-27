"""Shared scaffold and base contracts for foreign-agent bridges (Rule 12, Rule 18, Rule 49).

Provides a unified architecture for foreign-agent bridges across:
1. Authentication configuration and credential resolution.
2. Transport abstraction (stdio, subprocess, HTTP, WebSocket, local).
3. Standardized error taxonomy and latency instrumentation.
4. Tool mapping and schema translation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


class BridgeAuthMethod(str, Enum):
    """Authentication strategies for foreign agent peer bridges."""

    NONE = "none"
    BEARER_TOKEN = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    ENV_VAR = "env_var"


class BridgeTransportKind(str, Enum):
    """Underlying communication transports used by bridges."""

    LOCAL = "local"
    SUBPROCESS_STDIO = "subprocess_stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class BridgeErrorCode(str, Enum):
    """Standardized error taxonomy across all foreign agent bridges."""

    AUTH_FAILURE = "AUTH_FAILURE"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    PROTOCOL_MISMATCH = "PROTOCOL_MISMATCH"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    PEER_CRASH = "PEER_CRASH"
    TOOL_FAILED = "TOOL_FAILED"


class BridgeError(RuntimeError):
    """Standardized exception raised by foreign agent bridges."""

    def __init__(
        self,
        code: BridgeErrorCode,
        message: str,
        peer_name: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"[{peer_name}][{code.value}] {message}")
        self.code = code
        self.peer_name = peer_name
        self.details = details or {}


@dataclass(slots=True, frozen=True)
class BridgeAuthConfig:
    """Slotted and frozen authentication configuration (Rule 12)."""

    method: BridgeAuthMethod = BridgeAuthMethod.NONE
    token: str | None = None
    header_name: str = "Authorization"
    env_var: str | None = None

    def resolve_token(self) -> str | None:
        """Resolve active secret token from explicit value or environment variable."""
        if self.token:
            return self.token
        if self.env_var:
            import os
            return os.getenv(self.env_var)
        return None

    def inject_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Inject authentication headers into target request mapping."""
        tok = self.resolve_token()
        if not tok:
            return headers
        new_headers = dict(headers)
        if self.method == BridgeAuthMethod.BEARER_TOKEN:
            new_headers[self.header_name] = f"Bearer {tok}"
        elif self.method in (BridgeAuthMethod.API_KEY, BridgeAuthMethod.ENV_VAR):
            new_headers[self.header_name] = tok
        return new_headers


@dataclass(slots=True, frozen=True)
class BridgeToolMapping:
    """Mapping between a local Harness tool and a foreign peer's tool interface."""

    local_name: str
    remote_name: str
    description: str = ""
    transform_input: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    transform_output: Callable[[Any], Any] | None = None


class BaseForeignAgentBridge:
    """Base scaffold providing common lifecycle, telemetry, and error translation for peer bridges."""

    __slots__ = ("_peer_name", "_transport_kind", "_auth", "_tool_mappings", "_is_connected")

    def __init__(
        self,
        peer_name: str,
        transport_kind: BridgeTransportKind,
        auth: BridgeAuthConfig | None = None,
    ) -> None:
        self._peer_name = peer_name
        self._transport_kind = transport_kind
        self._auth = auth or BridgeAuthConfig()
        self._tool_mappings: dict[str, BridgeToolMapping] = {}
        self._is_connected = False

    @property
    def peer_name(self) -> str:
        return self._peer_name

    @property
    def transport_kind(self) -> BridgeTransportKind:
        return self._transport_kind

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def register_tool_mapping(self, mapping: BridgeToolMapping) -> None:
        """Register a bidirectional tool schema translation mapping."""
        self._tool_mappings[mapping.local_name] = mapping

    def map_tool_input(self, local_name: str, args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Map local tool invocation to peer name and translated arguments."""
        mapping = self._tool_mappings.get(local_name)
        if not mapping:
            return local_name, args
        mapped_args = mapping.transform_input(args) if mapping.transform_input else args
        return mapping.remote_name, mapped_args

    def map_tool_output(self, local_name: str, result: Any) -> Any:
        """Map peer execution result back through the registered output transform."""
        mapping = self._tool_mappings.get(local_name)
        if not mapping or not mapping.transform_output:
            return result
        return mapping.transform_output(result)

    def record_call(self, method: str, start_time: float, success: bool, error: str | None = None) -> float:
        """Record execution latency and emit structured logging."""
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        if success:
            logger.debug("Bridge RPC succeeded", peer=self._peer_name, method=method, latency_ms=latency_ms)
        else:
            logger.warning("Bridge RPC failed", peer=self._peer_name, method=method, latency_ms=latency_ms, error=error)
        return latency_ms
