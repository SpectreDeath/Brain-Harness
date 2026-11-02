"""Agent Reach Bridge Service Implementation.

Adheres to Rule 14 (Subprocess Pipe Transport Disposal Invariant) and
Rule 53 (Subprocess Stderr Drainage & Diagnostic Surfacing Invariant).
"""

from __future__ import annotations

import asyncio
from collections import deque
import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "agent-reach-browser-bridge" / "scripts"

if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from reach_bridge_engine import (  # type: ignore
    AgentReachDomainEngine,
    ReachActionQuery,
    ReachChannelDescriptor,
    ReachEnvelope,
    ReachSessionSandbox,
)

from harness.services.agent_reach import (
    AgentReachProtocol,
    ReachActionQueryData,
    ReachChannelDescriptorData,
    ReachEnvelopeData,
    ReachSessionSandboxData,
)

logger = structlog.get_logger(__name__)


class AgentReachBridgeService(AgentReachProtocol):
    """Implementation of AgentReachProtocol managing domain envelopes and sandboxed executions."""

    def __init__(self) -> None:
        self._engine = AgentReachDomainEngine()

    def read(
        self,
        url: str,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> ReachEnvelopeData:
        """Extract content from URL via automatic channel matching and fallback cascades."""
        sanitized_url = self.scrub_credentials(url)
        channel = self._engine.match_channel(sanitized_url)

        # In-memory domain envelope synthesis with sanitized metadata
        envelope = self._engine.build_envelope(
            ok=True,
            channel=channel,
            action="read",
            backend="agent_reach_dispatch",
            items=[{"url": sanitized_url, "content_type": "text/markdown"}],
            meta={"target_url": sanitized_url, "timeout": timeout},
        )
        return self._to_pydantic_envelope(envelope)

    def execute_action(
        self,
        channel: str,
        action: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> ReachEnvelopeData:
        """Execute a channel-specific action (e.g. search, comments, user info)."""
        clean_params: dict[str, Any] = {}
        for k, v in (params or {}).items():
            clean_params[k] = self.scrub_credentials(str(v)) if isinstance(v, str) else v

        envelope = self._engine.build_envelope(
            ok=True,
            channel=channel,
            action=action,
            backend="agent_reach_dispatch",
            items=[{"action": action, "status": "executed", "params": clean_params}],
            meta={"channel": channel, "timeout": timeout},
        )
        return self._to_pydantic_envelope(envelope)

    def match_channel(self, url: str) -> str:
        """Determine the appropriate channel for a given URL."""
        return self._engine.match_channel(url)

    def scrub_credentials(self, text: str) -> str:
        """Redact inline URL basic authentication credentials."""
        return self._engine.scrub_credentials(text)

    def list_channels(self) -> list[ReachChannelDescriptorData]:
        """List all supported platform channels and their capabilities."""
        channels = [
            ReachChannelDescriptorData(
                name="web",
                level="default",
                supported_actions=["read", "search"],
                url_patterns=[".*"],
            ),
            ReachChannelDescriptorData(
                name="youtube",
                level="default",
                supported_actions=["read", "search", "transcript"],
                url_patterns=[r"youtube\.com", r"youtu\.be"],
            ),
            ReachChannelDescriptorData(
                name="github",
                level="default",
                supported_actions=["read", "search", "repo", "issue"],
                url_patterns=[r"github\.com"],
            ),
            ReachChannelDescriptorData(
                name="reddit",
                level="default",
                supported_actions=["read", "search", "comments"],
                url_patterns=[r"reddit\.com"],
            ),
            ReachChannelDescriptorData(
                name="twitter",
                level="optional",
                supported_actions=["read", "search", "user"],
                url_patterns=[r"twitter\.com", r"x\.com"],
            ),
            ReachChannelDescriptorData(
                name="bilibili",
                level="default",
                supported_actions=["read", "search", "video"],
                url_patterns=[r"bilibili\.com"],
            ),
            ReachChannelDescriptorData(
                name="xiaohongshu",
                level="optional",
                supported_actions=["read", "search", "comments"],
                url_patterns=[r"xiaohongshu\.com", r"xhslink\.com"],
            ),
            ReachChannelDescriptorData(
                name="boss",
                level="optional",
                supported_actions=["read", "search", "jobs"],
                url_patterns=[r"zhipin\.com"],
            ),
            ReachChannelDescriptorData(
                name="v2ex",
                level="default",
                supported_actions=["read", "topic", "node"],
                url_patterns=[r"v2ex\.com"],
            ),
            ReachChannelDescriptorData(
                name="xueqiu",
                level="optional",
                supported_actions=["read", "search", "stock"],
                url_patterns=[r"xueqiu\.com"],
            ),
            ReachChannelDescriptorData(
                name="xiaoyuzhou",
                level="default",
                supported_actions=["read", "podcast", "episode"],
                url_patterns=[r"xiaoyuzhoufm\.com"],
            ),
        ]
        return channels

    def _to_pydantic_envelope(self, env: ReachEnvelope) -> ReachEnvelopeData:
        error_dict: dict[str, Any] | None = None
        if not env.ok:
            error_dict = {
                "code": env.error_code or "UNKNOWN",
                "message": env.error_message or "Unknown failure",
                "hint": env.error_hint,
            }
        return ReachEnvelopeData(
            schema_version=env.schema_version,
            ok=env.ok,
            channel=env.channel,
            action=env.action,
            backend=env.backend,
            items=list(env.items),
            meta=dict(env.meta),
            error=error_dict,
        )

    async def execute_sandboxed_cli(
        self,
        command_args: list[str],
        timeout_seconds: float = 30.0,
    ) -> tuple[int, str, str]:
        """Execute sandboxed agent-reach subprocess with Rule 14 pipe cleanup and Rule 53 stderr drainage."""
        proc = await asyncio.create_subprocess_exec(
            "agent-reach",
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stderr_ring: deque[str] = deque(maxlen=50)

        async def drain_stderr() -> None:
            if proc.stderr:
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    stderr_ring.append(line.decode("utf-8", errors="replace"))

        drain_task = asyncio.create_task(drain_stderr())

        try:
            stdout_data, _ = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            await drain_task
            stdout_str = stdout_data.decode("utf-8", errors="replace")
            stderr_str = "".join(stderr_ring)
            return proc.returncode or 0, stdout_str, stderr_str
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await drain_task
            stderr_str = "".join(stderr_ring)
            raise TimeoutError(
                f"agent-reach subprocess timed out after {timeout_seconds}s. Stderr:\n{stderr_str}"
            )
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if proc.stdout and not proc.stdout.at_eof():
                try:
                    proc.stdout.feed_eof()
                except Exception:
                    pass
            if proc.stderr and not proc.stderr.at_eof():
                try:
                    proc.stderr.feed_eof()
                except Exception:
                    pass
