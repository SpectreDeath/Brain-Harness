# Plugin Summary Card: `plugin.codex_execpolicy`

```
┌────────────────────────────────────────────────────────┐
│               PLUGIN SUMMARY CARD                      │
├────────────────────────────────────────────────────────┤
│ Name:        plugin.codex_execpolicy                   │
│ Category:    security_and_forensics                    │
│ Version:     1.0.0                                     │
│ Isolation:   in_process / subprocess                   │
│ Archetype:   tool_provider / service_provider          │
│ ServiceKey:  ServiceKey[CodexExecPolicyService]        │
│              ("security.codex_execpolicy")             │
├────────────────────────────────────────────────────────┤
│ Target:      Deterministic AST command authorization,  │
│              prefix rule matching & sandbox resolution │
└────────────────────────────────────────────────────────┘
```

---

## 🧰 Entrypoints & Tools

| Entrypoint | Description | Primary Parameters | Returns |
|---|---|---|---|
| `evaluate_command_policy` | Evaluate command against active prefix & danger rules | `command: str`, `working_dir?: str`, `custom_rules?: list[str]` | `decision: "allow" \| "prompt" \| "deny"`, `risk_score: float` |
| `amend_prefix_rule` | Dynamically amend allowed/prompt prefix rule | `prefix_pattern: str`, `action: str`, `comment?: str` | `status: "ok"`, `total_active_rules: int` |
| `tokenize_shell_ast` | Parse shell command into AST binary/args/operators | `command: str`, `shell_flavor?: str` | `binary: str`, `arguments: list[str]`, `operators: list[str]` |
| `check_sandbox_requirements`| Resolve platform sandbox (Landlock/Seatbelt/Tokens) | `command: str`, `target_platform?: str` | `requires_sandbox: bool`, `sandbox_type: str`, `paths: list` |

---

## 🛡️ Provenance & Lineage
- **Origin Repository**: `openai/codex` (`D:\GitHub\cloned\codex-main\codex-main`)
- **Source Modules**: `codex-rs/execpolicy` and `codex-rs/sandboxing`
- **Ported Engine**: PrefixPattern AST Tokenizer + Platform Sandbox Manager
