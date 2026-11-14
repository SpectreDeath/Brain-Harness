---
name: ui-behavior-primitive-architect
description: Architect, audit, and verify zero-dependency headless UI behavior primitives, WebMCP agent bridges, WAI-ARIA/SSR/RTL tri-modal checks, and framework expert routing. Do not use for static CSS theme styling or backend database migrations.
---

# UI Behavior Primitive Architect

`ui-behavior-primitive-architect` distills the headless primitive kernel, WebMCP agent bridge, tri-modal verification harness, and framework expert governance architecture from `vercel-labs/ui` (`@ui-sdk/core` @ `220c1a0d`).

See [CARD.md](CARD.md) for the companion summary card, pipeline stages, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and threshold defaults.

---

## 1. Headless Primitive Definition & Asleep Lifecycle

Isolate state transitions, slot attributes, and ARIA semantics inside a single framework-agnostic primitive before binding any renderer:

1. **Enforce Single-Shape Slot & Naming Contracts (`audit_primitive_definition`)**: Require kebab-case primitive names (`root` slot renders `data-slot="<name>"`), enforce `render` instead of `as` props, and detect simultaneous `controlled` + `default<Key>` initialization collisions.
2. **Partition Live Keys & Lazy Wake-Up**: Mark high-frequency non-rendering state in `live` (never overlapping `controlled`), attach `asleep` predicates so closed overlays defer `api` setup and DOM binds until `wake()`, and verify every entry in `agent.actions` exists on `api`.

> **Completion criterion**: `PrimitiveAuditReport` returns `valid=True` with zero controlled collisions, `live` overlaps, or missing `agent.actions`.

---

## 2. Agent Bridge Marks, Ref Hysteresis & WebMCP Registration

Expose rendered primitives safely to autonomous page agents via `snapshot`, `act`, and `query` while preserving DOM security boundaries:

1. **Enforce DOM Boundary Marks (`evaluate_agent_bridge_step`)**: Strip `data-agent-hidden` subtrees from snapshots (`hidden_off_limits`), scrub `data-agent-secret` values to `"[redacted]"`, and enforce `data-agent-confirm` human approval with prompts capped at `200` characters (`"This needs a person."` fallback).
2. **Resolve Synonyms & WebMCP Safety Hints**: Map verbs (`open`/`close`/`show`/`hide` -> `setOpen`, `toggle` -> `setOpen`/`setChecked`/`setPressed`, `select` -> `setValue`) against live API actions and attach `readOnlyHint`, `untrustedContentHint: true`, and `consequentialHint` for WebMCP registration.

> **Completion criterion**: `AgentBridgeStepDecision` enforces hidden/secret/confirm invariants and resolves WebMCP tool annotations.

---

## 3. Tri-Modal Verification (WAI-ARIA, SSR Isolation, RTL Parity) & Expert Routing

Validate every primitive across accessibility, server rendering, and reading direction, then route diffs to owning framework experts:

1. **Execute Tri-Modal Checks (`evaluate_tri_modal_check`)**: Validate against all `15` WAI-ARIA APG patterns (collecting every violation into one report), verify zero SSR access to browser globals (`document`, `window`, `Date.now`, `Math.random`, `crypto.randomUUID`), and assert `ArrowLeft` in RTL mirrors `ArrowRight` in LTR.
2. **Route Multi-Framework Diffs (`plan_expert_scope`)**: Map package/docs/example paths to individual `react`, `vue`, `svelte`, `solid`, or `web` (`web-components`) experts while fanning out `packages/core/`, `tests/specs/`, and `tests/fixtures.ts` to all five.

> **Completion criterion**: `TriModalVerificationReport` passes across ARIA/SSR/RTL and `ExpertScopeRoute` triggers every affected framework expert.

---

## The Three Foundational Pillars

### 1. Behavior-First, Zero-Dependency Primitives
Keep state machines, focus management, dismissal, and WAI-ARIA logic inside pure framework-free primitives (`definePrimitive`) so every framework adapter stays a thin renderer.

### 2. Guarded Agent Observability & WebMCP Safety
Treat page labels, text, and items as untrusted data, fence secrets and hidden subtrees at the DOM boundary, cap confirmation prompts, and gate consequential `act` steps behind explicit approval predicates.

### 3. Orthogonal Tri-Modal & Diff-Scoped Assurance
Never rely on a single mock DOM test: pair WAI-ARIA keyboard drives, strict clock/entropy-free SSR isolation, mirrored RTL checks, and automatic core-to-adapter expert routing.

---

## Anti-Patterns

- **Colliding Controlled and Default Initial Options** — Passing both `value`/`open`/`checked` and `default<Key>` triggers ambiguous ownership on initial mount and breaks controlled sync.
- **Unbounded Mutable State in Non-Live Render Keys** — Tracking high-frequency hover/drag keys outside `live`, or placing `controlled` keys inside `live`, causes render thrashing or stale props.
- **Bypassing DOM Confirmation or Secret Boundaries** — Exposing `data-agent-secret` values unredacted or invoking `data-agent-confirm` buttons via synthetic clicks violates WebMCP agent safety boundaries.
- **Accepting Core Diffs Without Cross-Framework Review** — Merging changes to shared `packages/core/` or `tests/specs/` files without triggering all five adapter experts breaks cross-framework contract parity.
