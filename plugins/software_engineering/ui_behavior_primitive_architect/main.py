"""UI Behavior Primitive Architect Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.ui_behavior_architect import (  # noqa: E402
    UI_BEHAVIOR_ARCHITECT_KEY,
    AgentBridgeStepDecision,
    ExpertScopeRoute,
    PrimitiveAuditReport,
    TriModalVerificationReport,
    UIBehaviorArchitectProtocol,
)

try:
    from .service import DefaultUIBehaviorArchitectService
except ImportError:
    from service import DefaultUIBehaviorArchitectService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class UIBehaviorPrimitiveArchitectPlugin(HarnessPlugin, UIBehaviorArchitectProtocol):
    """HarnessPlugin providing UIBehaviorArchitectProtocol in the IoC container (Rule 45)."""

    name = "plugin.ui_behavior_primitive_architect"
    version = "1.0.0"
    description = (
        "Headless UI primitive auditor, WebMCP agent bridge evaluator, "
        "WAI-ARIA/SSR/RTL tri-modal verifier, and framework expert router"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultUIBehaviorArchitectService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [UI_BEHAVIOR_ARCHITECT_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(UI_BEHAVIOR_ARCHITECT_KEY, self, provider=self.name)
        logger.info("UIBehaviorPrimitiveArchitectPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def audit_primitive_definition(
        self,
        name: str,
        *,
        state_keys: tuple[str, ...] = (),
        live_keys: tuple[str, ...] = (),
        controlled_keys: tuple[str, ...] | None = None,
        provided_options: tuple[str, ...] = (),
        api_methods: tuple[str, ...] = (),
        agent_actions: tuple[str, ...] = (),
        has_asleep_predicate: bool = False,
        has_render_as_prop: bool = False,
    ) -> PrimitiveAuditReport:
        return self._service.audit_primitive_definition(
            name,
            state_keys=state_keys,
            live_keys=live_keys,
            controlled_keys=controlled_keys,
            provided_options=provided_options,
            api_methods=api_methods,
            agent_actions=agent_actions,
            has_asleep_predicate=has_asleep_predicate,
            has_render_as_prop=has_render_as_prop,
        )

    def evaluate_agent_bridge_step(
        self,
        ref: str,
        component: str,
        action: str,
        *,
        available_actions: tuple[str, ...] = (),
        value: Any = None,
        confirm_attr: str | None = None,
        hidden: bool = False,
        secret: bool = False,
        person_approved: bool | None = None,
        tool_name: str = "act",
    ) -> AgentBridgeStepDecision:
        return self._service.evaluate_agent_bridge_step(
            ref,
            component,
            action,
            available_actions=available_actions,
            value=value,
            confirm_attr=confirm_attr,
            hidden=hidden,
            secret=secret,
            person_approved=person_approved,
            tool_name=tool_name,
        )

    def evaluate_tri_modal_check(
        self,
        pattern: str,
        *,
        aria_violations: tuple[str, ...] = (),
        ssr_globals_accessed: tuple[str, ...] = (),
        ltr_focus: str = "",
        rtl_focus: str = "",
        ltr_state: dict[str, Any] | None = None,
        rtl_state: dict[str, Any] | None = None,
    ) -> TriModalVerificationReport:
        return self._service.evaluate_tri_modal_check(
            pattern,
            aria_violations=aria_violations,
            ssr_globals_accessed=ssr_globals_accessed,
            ltr_focus=ltr_focus,
            rtl_focus=rtl_focus,
            ltr_state=ltr_state,
            rtl_state=rtl_state,
        )

    def plan_expert_scope(
        self,
        changed_files: tuple[str, ...],
    ) -> tuple[ExpertScopeRoute, ...]:
        return self._service.plan_expert_scope(changed_files)


plugin = UIBehaviorPrimitiveArchitectPlugin()


def ui_audit_primitive(
    name: str,
    state_keys: list[str] | None = None,
    live_keys: list[str] | None = None,
    controlled_keys: list[str] | None = None,
    provided_options: list[str] | None = None,
    api_methods: list[str] | None = None,
    agent_actions: list[str] | None = None,
    has_asleep_predicate: bool = False,
    has_render_as_prop: bool = False,
) -> dict[str, Any]:
    """Audit a headless definePrimitive specification."""
    return asdict(
        plugin.audit_primitive_definition(
            name,
            state_keys=tuple(state_keys or ()),
            live_keys=tuple(live_keys or ()),
            controlled_keys=(tuple(controlled_keys) if controlled_keys is not None else None),
            provided_options=tuple(provided_options or ()),
            api_methods=tuple(api_methods or ()),
            agent_actions=tuple(agent_actions or ()),
            has_asleep_predicate=has_asleep_predicate,
            has_render_as_prop=has_render_as_prop,
        )
    )


def ui_evaluate_agent_step(
    ref: str,
    component: str,
    action: str,
    available_actions: list[str] | None = None,
    value: Any = None,
    confirm_attr: str | None = None,
    hidden: bool = False,
    secret: bool = False,
    person_approved: bool | None = None,
    tool_name: str = "act",
) -> dict[str, Any]:
    """Evaluate a WebMCP agent bridge step with DOM boundary enforcement."""
    return asdict(
        plugin.evaluate_agent_bridge_step(
            ref,
            component,
            action,
            available_actions=tuple(available_actions or ()),
            value=value,
            confirm_attr=confirm_attr,
            hidden=hidden,
            secret=secret,
            person_approved=person_approved,
            tool_name=tool_name,
        )
    )


def ui_verify_tri_modal(
    pattern: str,
    aria_violations: list[str] | None = None,
    ssr_globals_accessed: list[str] | None = None,
    ltr_focus: str = "",
    rtl_focus: str = "",
    ltr_state: dict[str, Any] | None = None,
    rtl_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run WAI-ARIA, SSR isolation, and RTL direction checks."""
    return asdict(
        plugin.evaluate_tri_modal_check(
            pattern,
            aria_violations=tuple(aria_violations or ()),
            ssr_globals_accessed=tuple(ssr_globals_accessed or ()),
            ltr_focus=ltr_focus,
            rtl_focus=rtl_focus,
            ltr_state=ltr_state,
            rtl_state=rtl_state,
        )
    )


def ui_plan_expert_scope(changed_files: list[str]) -> dict[str, Any]:
    """Compute triggered framework experts from changed file paths."""
    routes = plugin.plan_expert_scope(tuple(changed_files))
    return {
        "routes": [asdict(r) for r in routes],
        "triggered_frameworks": [r.framework for r in routes if r.triggered],
    }
