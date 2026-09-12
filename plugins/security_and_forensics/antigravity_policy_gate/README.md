# domain.antigravity_policy_gate (v1.0.0)

Google Antigravity declarative security policy gate enforcing tri-state allow/deny/ask_user tool evaluation

---

## Overview & Metadata

- **Plugin Directory**: `plugins/security_and_forensics/antigravity_policy_gate`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.antigravity.policy_gate`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `evaluate_policy` | `(tool_name, arguments)` | Evaluate tool call against security baseline |
| `add_policy_rule` | `(tool_pattern, decision, rationale)` | Register a new policy rule |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Antigravity Policy Gate Entrypoints.

#### Functions

- `def evaluate_policy(tool_name, arguments) -> dict[str, Any]`
  - Evaluate tool call against security baseline.
- `def add_policy_rule(tool_pattern, decision, rationale) -> dict[str, Any]`
  - Register a new policy rule.


### Module [`service.py`](service.py)

Google Antigravity Declarative Policy Gate Service & Plugin Implementation.

#### Classes

- `class Decision`
- `class PolicyRule`
- `class AntigravityPolicyService`
  Authoritative declarative policy evaluation service.
  - `def __init__() -> None`
  - `def add_rule(tool_pattern, decision, arg_patterns, rationale) -> None`
  - `def evaluate(tool_name, arguments) -> tuple[Decision, str]`
  - `def get_audit_trail() -> list[dict[str, Any]]`
- `class AntigravityPolicyGatePlugin`
  In-process Harness plugin providing Antigravity policy evaluation service.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
