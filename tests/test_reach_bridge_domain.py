"""Contract tests for Agent Reach Domain Engine & Slotted Frozen Models."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure skill scripts directory is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "agent-reach-browser-bridge" / "scripts"

if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from reach_bridge_engine import (
    AgentReachDomainEngine,
    ReachActionQuery,
    ReachChannelDescriptor,
    ReachEnvelope,
    ReachSessionSandbox,
)


@pytest.mark.unit
class TestReachBridgeDomainModels:
    """Validate immutability and contracts of Agent Reach domain models per Rule 12 & Rule 43."""

    def test_action_query_immutability(self) -> None:
        """Verify ReachActionQuery is frozen and validates fields."""
        query = ReachActionQuery(
            channel="reddit",
            action="comments",
            params=(("limit", "10"),),
            timeout=15.0,
        )
        assert query.channel == "reddit"
        assert query.action == "comments"
        assert query.timeout == 15.0

        # Rule 43: direct attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            query.channel = "twitter"  # type: ignore

    def test_envelope_immutability(self) -> None:
        """Verify ReachEnvelope enforces Schema v1 and immutability."""
        env = AgentReachDomainEngine.build_envelope(
            ok=True,
            channel="github",
            action="read",
            backend="public_web",
            items=[{"repo": "Agent-Reach"}],
            meta={"stars": 5000},
        )
        assert env.schema_version == 1
        assert env.ok is True
        assert env.channel == "github"

        with pytest.raises((AttributeError, TypeError)):
            env.ok = False  # type: ignore

    def test_failed_envelope_requires_error_code(self) -> None:
        """Verify failed ReachEnvelope rejects missing error_code."""
        with pytest.raises(ValueError):
            ReachEnvelope(
                schema_version=1,
                ok=False,
                channel="web",
                action="read",
                backend="direct",
                error_code=None,
            )

    def test_channel_descriptor_immutability(self) -> None:
        """Verify ReachChannelDescriptor validation and freezing."""
        desc = ReachChannelDescriptor(
            name="bilibili",
            level="default",
            supported_actions=("read", "search", "video"),
            url_patterns=(r"bilibili\.com",),
        )
        assert desc.name == "bilibili"
        assert desc.level == "default"

        with pytest.raises((AttributeError, TypeError)):
            desc.level = "optional"  # type: ignore

        # Fails on invalid level
        with pytest.raises(ValueError):
            ReachChannelDescriptor(name="test", level="unsupported")

    def test_session_sandbox_immutability(self) -> None:
        """Verify ReachSessionSandbox frozen constraints."""
        sandbox = ReachSessionSandbox(
            tool="gh",
            session_path="~/.agent-reach/sessions/gh",
            home_override="/tmp/sandboxes/gh",
            symlink_safe=True,
        )
        assert sandbox.tool == "gh"
        assert sandbox.symlink_safe is True

        with pytest.raises((AttributeError, TypeError)):
            sandbox.symlink_safe = False  # type: ignore

    def test_engine_operations(self) -> None:
        """Verify domain engine matching, credential scrubbing, and error classification."""
        engine = AgentReachDomainEngine()

        # URL Matching
        assert engine.match_channel("https://www.youtube.com/watch?v=123") == "youtube"
        assert engine.match_channel("https://github.com/Panniantong/Agent-Reach") == "github"
        assert engine.match_channel("https://reddit.com/r/MachineLearning") == "reddit"
        assert engine.match_channel("https://x.com/openai/status/123") == "twitter"
        assert engine.match_channel("https://example.com/blog/article") == "web"

        # Credential scrubbing
        dirty = "http://admin:secretPass123@internal.corp.com/api"
        clean = engine.scrub_credentials(dirty)
        assert clean == "http://***:***@internal.corp.com/api"

        # Error classification
        assert engine.is_final_error("NEED_LOGIN") is True
        assert engine.is_final_error("RATE_LIMITED") is True
        assert engine.is_final_error("TIMEOUT") is False
        assert engine.is_retryable_error("TIMEOUT") is True
        assert engine.is_retryable_error("UPSTREAM_BROKEN") is True

