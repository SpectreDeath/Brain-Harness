"""UI Behavior Primitive Architect Service — headless primitives, agent bridge, tri-modal verification & expert scope.

Distilled from vercel-labs/ui @ 220c1a0d (@ui-sdk/core):
- Headless definePrimitive lifecycle, asleep deferral, controlled collision checks, and agent action binding
- Agent bridge (snapshot/act/query), DOM boundary marks (data-agent-confirm/hidden/secret), and WebMCP hints
- Tri-modal deterministic verification: 15 WAI-ARIA APG patterns, SSR clock/DOM isolation, and mirrored RTL parity
- Git-diff framework expert scope routing (react, vue, svelte, solid, web)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

RETIRED_REF_LIMIT = 500
CONFIRM_MAX_CHARS = 200

SUPPORTED_ARIA_PATTERNS: tuple[str, ...] = (
    "listbox",
    "menu",
    "menubar",
    "tabs",
    "radio-group",
    "toolbar",
    "tree",
    "dialog",
    "alertdialog",
    "disclosure",
    "accordion",
    "combobox",
    "slider",
    "switch",
    "checkbox",
)

FORBIDDEN_SSR_GLOBALS: tuple[str, ...] = (
    "document",
    "window",
    "navigator",
    "location",
    "localStorage",
    "sessionStorage",
    "matchMedia",
    "Date.now",
    "new Date()",
    "performance.now",
    "Math.random",
    "crypto.randomUUID",
    "crypto.getRandomValues",
)

FRAMEWORK_EXPERTS: tuple[str, ...] = ("react", "vue", "svelte", "solid", "web")

ACTION_SYNONYMS: dict[str, tuple[str, ...]] = {
    "open": ("setOpen",),
    "close": ("setOpen",),
    "show": ("setOpen",),
    "hide": ("setOpen",),
    "toggle": ("setOpen", "setChecked", "setPressed"),
    "select": ("setValue",),
}

_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MIRRORED_DIRECTIONS: dict[str, str] = {"left": "right", "right": "left"}


@dataclass(slots=True, frozen=True)
class PrimitiveAuditReport:
    """Immutable audit result for a headless definePrimitive specification."""

    name: str
    root_data_slot: str
    valid: bool
    asleep_deferred: bool
    controlled_collisions: tuple[str, ...] = ()
    missing_agent_actions: tuple[str, ...] = ()
    live_controlled_overlaps: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("PrimitiveAuditReport.name cannot be empty")
        if not self.root_data_slot or not self.root_data_slot.strip():
            raise ValueError("PrimitiveAuditReport.root_data_slot cannot be empty")


@dataclass(slots=True, frozen=True)
class AgentBridgeStepDecision:
    """Immutable admissibility and redaction decision for an agent bridge / WebMCP step."""

    ref: str
    component: str
    action: str
    resolved_action: str
    allowed: bool
    needs_person: bool
    visible_in_snapshot: bool
    redacted_value: Any
    confirm_prompt: str | None = None
    reason: str = "allowed"
    read_only_hint: bool = False
    untrusted_content_hint: bool = True
    consequential_hint: bool = True

    def __post_init__(self) -> None:
        if not self.ref or not self.ref.strip():
            raise ValueError("AgentBridgeStepDecision.ref cannot be empty")
        if not self.component or not self.component.strip():
            raise ValueError("AgentBridgeStepDecision.component cannot be empty")
        if not self.action or not self.action.strip():
            raise ValueError("AgentBridgeStepDecision.action cannot be empty")
        if self.confirm_prompt is not None and len(self.confirm_prompt) > CONFIRM_MAX_CHARS:
            raise ValueError(f"confirm_prompt exceeds {CONFIRM_MAX_CHARS} chars")


@dataclass(slots=True, frozen=True)
class TriModalVerificationReport:
    """Immutable tri-modal verification report covering WAI-ARIA, SSR isolation, and RTL parity."""

    pattern: str
    passed: bool
    aria_passed: bool
    ssr_passed: bool
    rtl_passed: bool
    problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.pattern or not self.pattern.strip():
            raise ValueError("TriModalVerificationReport.pattern cannot be empty")


@dataclass(slots=True, frozen=True)
class ExpertScopeRoute:
    """Immutable framework expert review routing plan computed from changed file paths."""

    framework: str
    own_files: tuple[str, ...] = ()
    shared_files: tuple[str, ...] = ()
    triggered: bool = False

    def __post_init__(self) -> None:
        if self.framework not in FRAMEWORK_EXPERTS:
            raise ValueError(f"ExpertScopeRoute.framework must be one of {FRAMEWORK_EXPERTS}, got {self.framework!r}")


@runtime_checkable
class UIBehaviorArchitectProtocol(Protocol):
    """Typed service contract for UI behavior primitive auditing, bridge safety, verification, and routing."""

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
    ) -> PrimitiveAuditReport: ...

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
    ) -> AgentBridgeStepDecision: ...

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
    ) -> TriModalVerificationReport: ...

    def plan_expert_scope(
        self,
        changed_files: tuple[str, ...],
    ) -> tuple[ExpertScopeRoute, ...]: ...


class UIBehaviorArchitectEngine(UIBehaviorArchitectProtocol):
    """Deterministic engine implementing headless UI primitive, WebMCP, tri-modal, and expert scope rules."""

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
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Primitive name cannot be empty")

        violations: list[str] = []
        if not _KEBAB_RE.match(clean_name):
            violations.append(f"Primitive name '{clean_name}' must be kebab-case matching definePrimitive convention.")

        if has_render_as_prop:
            violations.append("A part must change its element through `render`, never an `as` prop.")

        effective_controlled = (
            controlled_keys
            if controlled_keys is not None
            else tuple(k for k in ("open", "value", "checked") if k in state_keys)
        )

        option_set = set(provided_options)
        collisions: list[str] = []
        for key in effective_controlled:
            if not key:
                continue
            default_key = f"default{key[0].upper()}{key[1:]}"
            if key in option_set and default_key in option_set:
                collisions.append(key)
                violations.append(f"Controlled option '{key}' collides with '{default_key}' on initial options.")

        overlaps = tuple(sorted(set(live_keys).intersection(effective_controlled)))
        if overlaps:
            violations.append(f"Keys {list(overlaps)} cannot be both `live` (non-rendering) and `controlled`.")

        api_set = set(api_methods)
        missing_actions = tuple(act for act in agent_actions if act not in api_set)
        for act in missing_actions:
            violations.append(f"Lists `{act}` in `agent.actions`, but its api has no such method.")

        return PrimitiveAuditReport(
            name=clean_name,
            root_data_slot=clean_name,
            valid=len(violations) == 0,
            asleep_deferred=bool(has_asleep_predicate),
            controlled_collisions=tuple(collisions),
            missing_agent_actions=missing_actions,
            live_controlled_overlaps=overlaps,
            violations=tuple(violations),
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
        if not ref.strip() or not component.strip() or not action.strip():
            raise ValueError("ref, component, and action must be non-empty strings")

        read_only_hint = tool_name != "act"
        untrusted_content_hint = True
        consequential_hint = tool_name == "act"

        redacted_value = "[redacted]" if secret else value
        visible_in_snapshot = not hidden

        avail_set = set(available_actions)
        resolved_action = action
        action_available = True
        if avail_set:
            if action in avail_set:
                resolved_action = action
            else:
                matched = next(
                    (cand for cand in ACTION_SYNONYMS.get(action, ()) if cand in avail_set),
                    None,
                )
                if matched is not None:
                    resolved_action = matched
                else:
                    action_available = False
        elif action in ACTION_SYNONYMS:
            resolved_action = ACTION_SYNONYMS[action][0]

        confirm_prompt: str | None = None
        if confirm_attr is not None:
            clipped = confirm_attr.strip()[:CONFIRM_MAX_CHARS]
            confirm_prompt = clipped or "This needs a person."

        if hidden:
            allowed = False
            needs_person = False
            reason = "hidden_off_limits"
        elif not action_available:
            allowed = False
            needs_person = False
            reason = "action_not_available"
        elif confirm_prompt is not None and person_approved is not True:
            allowed = False
            needs_person = True
            reason = "needs_person"
        else:
            allowed = True
            needs_person = confirm_prompt is not None
            reason = "allowed"

        return AgentBridgeStepDecision(
            ref=ref,
            component=component,
            action=action,
            resolved_action=resolved_action,
            allowed=allowed,
            needs_person=needs_person,
            visible_in_snapshot=visible_in_snapshot,
            redacted_value=redacted_value,
            confirm_prompt=confirm_prompt,
            reason=reason,
            read_only_hint=read_only_hint,
            untrusted_content_hint=untrusted_content_hint,
            consequential_hint=consequential_hint,
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
        clean_pattern = pattern.strip()
        if not clean_pattern:
            raise ValueError("pattern cannot be empty")

        problems: list[str] = []

        # 1. WAI-ARIA pattern compliance (check-pattern.ts)
        aria_problems: list[str] = []
        if clean_pattern not in SUPPORTED_ARIA_PATTERNS:
            aria_problems.append(f'checkPattern does not support "{clean_pattern}" yet.')
        for violation in aria_violations:
            if violation and violation.strip():
                aria_problems.append(f"ARIA: {violation.strip()}")
        problems.extend(aria_problems)
        aria_passed = len(aria_problems) == 0

        # 2. SSR isolation (check-server.ts)
        ssr_problems: list[str] = []
        forbidden_set = set(FORBIDDEN_SSR_GLOBALS)
        for g in ssr_globals_accessed:
            clean_g = g.strip()
            if not clean_g:
                continue
            if clean_g in forbidden_set:
                ssr_problems.append(f"SSR: `{clean_g}` isn't available on a server.")
            else:
                ssr_problems.append(f"SSR: disallowed global access `{clean_g}`.")
        problems.extend(ssr_problems)
        ssr_passed = len(ssr_problems) == 0

        # 3. Mirrored LTR vs RTL parity (check-direction.ts)
        rtl_problems: list[str] = []
        if ltr_focus != rtl_focus:
            rtl_problems.append(
                f"RTL: ArrowLeft focuses {rtl_focus or 'nothing'}, where ArrowRight in LTR focuses {ltr_focus or 'nothing'}."
            )

        norm_ltr = _normalize_direction_state(ltr_state or {}, dir_mode="ltr")
        norm_rtl = _normalize_direction_state(rtl_state or {}, dir_mode="rtl")
        if norm_ltr != norm_rtl:
            rtl_problems.append(f"RTL: mirrored RTL state {norm_rtl!r} diverges from LTR state {norm_ltr!r}.")
        problems.extend(rtl_problems)
        rtl_passed = len(rtl_problems) == 0

        return TriModalVerificationReport(
            pattern=clean_pattern,
            passed=aria_passed and ssr_passed and rtl_passed,
            aria_passed=aria_passed,
            ssr_passed=ssr_passed,
            rtl_passed=rtl_passed,
            problems=tuple(problems),
        )

    def plan_expert_scope(
        self,
        changed_files: tuple[str, ...],
    ) -> tuple[ExpertScopeRoute, ...]:
        normalized = [f.replace("\\", "/").lstrip("./") for f in changed_files if f.strip()]
        shared_hits = tuple(f for f in normalized if _is_shared_file(f))

        routes: list[ExpertScopeRoute] = []
        for framework in FRAMEWORK_EXPERTS:
            own_hits = tuple(f for f in normalized if _owns_framework_file(framework, f))
            routes.append(
                ExpertScopeRoute(
                    framework=framework,
                    own_files=own_hits,
                    shared_files=shared_hits,
                    triggered=bool(own_hits or shared_hits),
                )
            )
        return tuple(routes)


def _normalize_direction_state(state: dict[str, Any], *, dir_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in sorted(state.keys()):
        if key == "id":
            continue
        val = state[key]
        if dir_mode == "rtl" and key in ("direction", "side") and isinstance(val, str) and val in _MIRRORED_DIRECTIONS:
            out[key] = _MIRRORED_DIRECTIONS[val]
        else:
            out[key] = val
    return out


def _is_shared_file(path: str) -> bool:
    return path.startswith("packages/core/") or path.startswith("tests/specs/") or path == "tests/fixtures.ts"


def _owns_framework_file(framework: str, path: str) -> bool:
    docs_name = "web-components" if framework == "web" else framework
    if path.startswith(f"packages/{framework}/"):
        return True
    if path.startswith(f"apps/docs/content/docs/{docs_name}/"):
        return True
    if re.match(rf"^examples/(components/)?[^/]+/{framework}/", path):
        return True
    if re.match(rf"^apps/playground/src/fixtures/[^/]+/{framework}[.-]", path):
        return True
    if framework == "vue" and re.match(r"^apps/playground/src/fixtures/.+\.vue$", path):
        return True
    if framework == "svelte" and re.match(r"^apps/playground/src/fixtures/.+\.svelte$", path):
        return True
    return False


UI_BEHAVIOR_ARCHITECT_KEY: ServiceKey[UIBehaviorArchitectProtocol] = ServiceKey(
    "service.ui_behavior_primitive_architect"
)
