# plugin.codex_execpolicy (v1.0.0)

Deterministic AST-level shell command execution policy, approval elevation, and sandbox resolution engine ported from OpenAI Codex

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/codex_execpolicy` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `evaluate_command_policy` | `(command, working_dir, custom_rules)` | Evaluates a candidate shell command against active prefix rules and danger patterns to determine allow, prompt, or deny status |
| `amend_prefix_rule` | `(prefix_pattern, action, comment)` | Dynamically add or update an allowed/prompt/deny prefix rule in the active execution policy |
| `tokenize_shell_ast` | `(command, shell_flavor)` | Parses a shell command string into structured AST components (binary, args, operators, redirections) without executing it |
| `check_sandbox_requirements` | `(command, target_platform)` | Determines platform-native sandboxing requirements (Linux Landlock/Bwrap, macOS Seatbelt, Windows Tokens) for a command |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Deterministic AST-Level Shell Command Execution Policy & Sandbox Resolution Plugin.

Ported from OpenAI Codex (`codex-rs/execpolicy` and `codex-rs/sandboxing`) and enhanced
with pure-language recursive Tree-Sitter Bash AST decompilation from Kimi Code.
Provides deterministic AST parsing, subshell extraction, prefix rule matching, approval elevation,
and platform-native sandbox requirement analysis for agent loops.

#### Classes

- `class PrefixRule` — Deterministic command prefix rule.
- `class AstToken` — Structured AST token representing parsed shell command elements.
- `class CodexExecPolicyService` — Typed service for deterministic execution policy and sandbox analysis.
  - `def evaluate(command) -> dict[str, Any]`
  - `def amend(pattern, action, comment) -> dict[str, Any]`
  - `def tokenize(command) -> dict[str, Any]`
  - `def parse_ast(command) -> BashAstNode`
  - `def check_sandbox(command) -> dict[str, Any]`
- `class CodexExecPolicyPlugin` — Brain Harness Plugin exposing Codex deterministic execpolicy and sandbox analyzer.
  - `def __init__() -> None`
  - `def on_enable(context) -> None` — Register typed service into IoC container on startup.
  - `def on_disable(context) -> None` — Unregister service on shutdown.


#### Functions

- `def parse_bash_ast(command_str) -> BashAstNode` — Recursive pure-language Tree-Sitter style Bash AST parser.
- `def tokenize_shell_ast(command, shell_flavor) -> dict[str, Any]` — Parses a shell command string into structured AST components without executing it.
- `def evaluate_command_policy(command, working_dir, custom_rules) -> dict[str, Any]` — Evaluates a candidate shell command against active prefix rules and danger patterns.
- `def amend_prefix_rule(prefix_pattern, action, comment) -> dict[str, Any]` — Dynamically add or update an allowed/prompt/deny prefix rule in the active execution policy.
- `def check_sandbox_requirements(command, target_platform) -> dict[str, Any]` — Determines platform-native sandboxing requirements for a given command.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.codex_execpolicy.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
