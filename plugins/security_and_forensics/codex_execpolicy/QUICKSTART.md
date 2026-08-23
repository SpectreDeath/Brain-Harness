# Quickstart: `plugin.codex_execpolicy`

Minimal usage examples for evaluating shell commands, tokenizing ASTs, and resolving sandbox requirements.

---

## 1. Evaluate a Shell Command Policy

```python
from plugins.security_and_forensics.codex_execpolicy.main import evaluate_command_policy

# Safe command
res1 = evaluate_command_policy("git status")
print(res1["decision"])  # -> "allow"

# Unknown command requiring user confirmation
res2 = evaluate_command_policy("python script.py --upload")
print(res2["decision"])  # -> "prompt"

# Hazardous command automatically denied
res3 = evaluate_command_policy("rm -rf /")
print(res3["decision"])  # -> "deny"
```

---

## 2. Parse Shell Command AST

```python
from plugins.security_and_forensics.codex_execpolicy.main import tokenize_shell_ast

ast = tokenize_shell_ast("pytest tests/ -v && git status > out.txt")
print(ast["binary"])         # -> "pytest"
print(ast["operators"])      # -> ["&&"]
print(ast["is_compound"])    # -> True
print(ast["subcommands"])    # -> 2 subcommands
```

---

## 3. Dynamically Amend an Allowed Prefix Rule

```python
from plugins.security_and_forensics.codex_execpolicy.main import amend_prefix_rule

# Permanently allow 'docker ps'
amend_prefix_rule("docker ps", "allow", comment="Safe container query")

# Test evaluation
res = evaluate_command_policy("docker ps -a")
print(res["decision"])  # -> "allow"
```

---

## 4. Resolve Platform Sandbox Requirements

```python
from plugins.security_and_forensics.codex_execpolicy.main import check_sandbox_requirements

sb_info = check_sandbox_requirements("npm install", target_platform="linux")
print(sb_info["sandbox_type"])      # -> "linux_landlock_bwrap"
print(sb_info["requires_sandbox"])  # -> True
```
