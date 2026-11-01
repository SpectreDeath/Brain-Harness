"""TokenEconomizer Plugin.

Provides experience-driven black-box cost control for coding agents:
1. Micro-skills lifecycle & asymmetric contradiction eviction
2. Dynamic evidence-based tool pruning with protected work surfaces
3. 3-tier failure-loop turn guard with non-destructive mirroring
4. Unified multi-agent trajectory trace and pricing ledger federation
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any
import structlog

# Ensure skill scripts directory is on sys.path
_SCRIPTS_DIR = (
    Path(__file__).parent.parent.parent.parent
    / ".agents"
    / "skills"
    / "token-economizer"
    / "scripts"
)
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.token_economizer import (
    TOKEN_ECONOMIZER_SERVICE_KEY,
    MicroSkillFact,
    TokenEconomizerService,
    TokenLedgerMetrics,
    ToolPrunePolicy,
    TrajectoryTrace,
    TurnGuardDecision,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry
from token_economizer_engine import TokenEconomizerEngine

logger = structlog.get_logger(__name__)


class TokenEconomizerPlugin(HarnessPlugin, TokenEconomizerService):
    """Plugin wrapper registering TokenEconomizer services into Brain Harness IoC."""

    def __init__(self) -> None:
        super().__init__()
        self._engine: TokenEconomizerEngine = TokenEconomizerEngine()
        self._context: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "plugin.token_economizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [TOKEN_ECONOMIZER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    @property
    def engine(self) -> TokenEconomizerEngine:
        return self._engine

    # TokenEconomizerService protocol implementation delegating to engine
    def record_micro_skill_observation(
        self,
        key: str,
        success: bool,
        edited_files: list[str] | None = None,
        is_high_stakes: bool = False,
        assertion: str = "",
    ) -> MicroSkillFact:
        return self._engine.record_micro_skill_observation(
            key=key,
            success=success,
            edited_files=edited_files,
            is_high_stakes=is_high_stakes,
            assertion=assertion,
        )

    def get_active_micro_skills(self) -> tuple[MicroSkillFact, ...]:
        return self._engine.get_active_micro_skills()

    def evaluate_tool_pruning(
        self,
        loaded_tools: list[str],
        session_tool_history: list[dict[str, int]],
        protected_tools: list[str] | None = None,
        inapplicable_tools: list[str] | None = None,
        evidence_sessions_threshold: int = 2,
    ) -> ToolPrunePolicy:
        return self._engine.evaluate_tool_pruning(
            loaded_tools=loaded_tools,
            session_tool_history=session_tool_history,
            protected_tools=protected_tools,
            inapplicable_tools=inapplicable_tools,
            evidence_sessions_threshold=evidence_sessions_threshold,
        )

    def evaluate_turn_guard(
        self,
        turn_history: list[dict[str, Any]],
        envelope_turn_p90: int = 20,
        envelope_margin: float = 1.25,
        level: str = "default",
    ) -> TurnGuardDecision:
        return self._engine.evaluate_turn_guard(
            turn_history=turn_history,
            envelope_turn_p90=envelope_turn_p90,
            envelope_margin=envelope_margin,
            level=level,
        )

    def parse_trajectory(
        self,
        raw_log: str | dict[str, Any],
        agent_format: str = "generic_jsonl",
    ) -> TrajectoryTrace:
        return self._engine.parse_trajectory(raw_log=raw_log, agent_format=agent_format)

    def get_token_ledger(self, reset: bool = False) -> TokenLedgerMetrics:
        return self._engine.get_token_ledger(reset=reset)

    async def on_load(self, ctx: ServiceContext) -> None:
        self._context = ctx
        ctx.provide(TOKEN_ECONOMIZER_SERVICE_KEY, self, provider=self.name)
        logger.info("token_economizer_loaded", service_key=TOKEN_ECONOMIZER_SERVICE_KEY.name)

    async def on_enable(self) -> None:
        if self._context and self._context.has(TOOL_REGISTRY_KEY):
            registry: ToolRegistry = self._context.require(TOOL_REGISTRY_KEY)

            registry.register(
                name="te_record_micro_skill",
                description="Record observation of a repository micro-skill fact to update its lifecycle and firing gate",
                executor=lambda key, success, edited_files=None, is_high_stakes=False, assertion="": (
                    asdict(
                        self.record_micro_skill_observation(
                            key=key,
                            success=success,
                            edited_files=edited_files,
                            is_high_stakes=is_high_stakes,
                            assertion=assertion,
                        )
                    )
                ),
                provider=self.name,
            )

            registry.register(
                name="te_get_active_micro_skills",
                description="Retrieve all active micro-skills that have passed confirmation and cleared the 40% firing gate",
                executor=lambda: [asdict(f) for f in self.get_active_micro_skills()],
                provider=self.name,
            )

            registry.register(
                name="te_evaluate_tool_pruning",
                description="Evaluate loaded tool definitions against session usage history and determine which tools to prune from prompt context",
                executor=lambda loaded_tools, session_tool_history, protected_tools=None, inapplicable_tools=None, evidence_sessions_threshold=2: (
                    asdict(
                        self.evaluate_tool_pruning(
                            loaded_tools=loaded_tools,
                            session_tool_history=session_tool_history,
                            protected_tools=protected_tools,
                            inapplicable_tools=inapplicable_tools,
                            evidence_sessions_threshold=evidence_sessions_threshold,
                        )
                    )
                ),
                provider=self.name,
            )

            registry.register(
                name="te_evaluate_turn_guard",
                description="Evaluate ongoing turn trajectory against 3-tier failure-loop heuristics",
                executor=lambda turn_history, envelope_turn_p90=20, envelope_margin=1.25, level="default": (
                    asdict(
                        self.evaluate_turn_guard(
                            turn_history=turn_history,
                            envelope_turn_p90=envelope_turn_p90,
                            envelope_margin=envelope_margin,
                            level=level,
                        )
                    )
                ),
                provider=self.name,
            )

            registry.register(
                name="te_get_token_ledger",
                description="Retrieve cumulative token savings, net USD cost reduction, and intervention statistics",
                executor=lambda reset=False: asdict(self.get_token_ledger(reset=reset)),
                provider=self.name,
            )

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass


# Module-level singleton (Rule 45)
plugin = TokenEconomizerPlugin()


# Top-level functional entrypoints
def te_record_micro_skill(
    key: str,
    success: bool,
    edited_files: list[str] | None = None,
    is_high_stakes: bool = False,
    assertion: str = "",
) -> dict[str, Any]:
    return asdict(
        plugin.record_micro_skill_observation(
            key=key,
            success=success,
            edited_files=edited_files,
            is_high_stakes=is_high_stakes,
            assertion=assertion,
        )
    )


def te_get_active_micro_skills() -> list[dict[str, Any]]:
    return [asdict(f) for f in plugin.get_active_micro_skills()]


def te_evaluate_tool_pruning(
    loaded_tools: list[str],
    session_tool_history: list[dict[str, int]],
    protected_tools: list[str] | None = None,
    inapplicable_tools: list[str] | None = None,
    evidence_sessions_threshold: int = 2,
) -> dict[str, Any]:
    return asdict(
        plugin.evaluate_tool_pruning(
            loaded_tools=loaded_tools,
            session_tool_history=session_tool_history,
            protected_tools=protected_tools,
            inapplicable_tools=inapplicable_tools,
            evidence_sessions_threshold=evidence_sessions_threshold,
        )
    )


def te_evaluate_turn_guard(
    turn_history: list[dict[str, Any]],
    envelope_turn_p90: int = 20,
    envelope_margin: float = 1.25,
    level: str = "default",
) -> dict[str, Any]:
    return asdict(
        plugin.evaluate_turn_guard(
            turn_history=turn_history,
            envelope_turn_p90=envelope_turn_p90,
            envelope_margin=envelope_margin,
            level=level,
        )
    )


def te_get_token_ledger(reset: bool = False) -> dict[str, Any]:
    return asdict(plugin.get_token_ledger(reset=reset))
