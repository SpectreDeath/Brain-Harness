"""Deterministic AST-Level Shell Command Execution Policy & Sandbox Resolution Plugin.

Ported from OpenAI Codex (`codex-rs/execpolicy` and `codex-rs/sandboxing`).
Provides deterministic AST parsing, prefix rule matching, approval elevation,
and platform-native sandbox requirement analysis for agent loops.
"""

from __future__ import annotations

import os
import platform
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


@dataclass
class PrefixRule:
    """Deterministic command prefix rule."""
    pattern: list[str]
    action: str  # "allow", "prompt", "deny"
    comment: str = ""
    is_regex: bool = False


@dataclass
class AstToken:
    """Structured AST token representing parsed shell command elements."""
    raw: str
    is_operator: bool = False
    is_redirection: bool = False
    is_variable: bool = False


# Global in-memory policy state
_DEFAULT_ALLOW_PREFIXES: list[PrefixRule] = [
    PrefixRule(["git", "status"], "allow", "Safe git status query"),
    PrefixRule(["git", "diff"], "allow", "Safe git diff inspection"),
    PrefixRule(["git", "log"], "allow", "Safe git history inspection"),
    PrefixRule(["git", "branch"], "allow", "Safe git branch listing"),
    PrefixRule(["git", "rev-parse"], "allow", "Safe git commit resolution"),
    PrefixRule(["pytest"], "allow", "Test runner execution"),
    PrefixRule(["python", "-m", "pytest"], "allow", "Python pytest module execution"),
    PrefixRule(["python", "--version"], "allow", "Python version query"),
    PrefixRule(["python3", "--version"], "allow", "Python3 version query"),
    PrefixRule(["node", "--version"], "allow", "Node.js version query"),
    PrefixRule(["npm", "test"], "allow", "NPM test script"),
    PrefixRule(["npm", "run", "test"], "allow", "NPM test script"),
    PrefixRule(["cargo", "check"], "allow", "Cargo compiler check"),
    PrefixRule(["cargo", "test"], "allow", "Cargo test execution"),
    PrefixRule(["ls"], "allow", "Directory listing"),
    PrefixRule(["dir"], "allow", "Windows directory listing"),
    PrefixRule(["echo"], "allow", "Standard echo"),
    PrefixRule(["pwd"], "allow", "Print working directory"),
    PrefixRule(["whoami"], "allow", "User identity query"),
]

_DEFAULT_DENY_PATTERNS: list[tuple[str, str, str]] = [
    # (Regex Pattern, Danger Description, Action)
    (r"\brm\s+-[rR]f\s+(?:/|/\*|~|\$HOME)", "Catastrophic filesystem root deletion", "deny"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\s+", "Filesystem format command", "deny"),
    (r"\bdd\s+if=.*of=/dev/[sh]d", "Direct disk overwrite with dd", "deny"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb denial of service", "deny"),
    (r"\b(?:curl|wget|fetch)\b.*\|\s*(?:bash|sh|zsh|python|perl|powershell)", "Unchecked remote script pipe execution", "prompt"),
    (r"\bchmod\s+(?:-R\s+)?777\b", "Dangerous open permission granting", "prompt"),
    (r"\bsudo\s+", "Privilege escalation request", "prompt"),
    (r"\bshutdown\s+", "System shutdown command", "deny"),
    (r"\breboot\s+", "System reboot command", "deny"),
]

_ACTIVE_RULES: list[PrefixRule] = list(_DEFAULT_ALLOW_PREFIXES)


def _tokenize_command(command_str: str, shell_flavor: str = "bash") -> dict[str, Any]:
    """Tokenize a shell command into binary, arguments, chained operators, and redirections."""
    clean_cmd = command_str.strip()
    if not clean_cmd:
        return {
            "binary": "",
            "arguments": [],
            "operators": [],
            "redirections": [],
            "is_compound": False,
            "subcommands": [],
        }

    # Split by major shell operators: &&, ||, ;, |
    operator_regex = r"(&&|\|\||;|\|)"
    raw_segments = re.split(operator_regex, clean_cmd)

    subcommands: list[dict[str, Any]] = []
    operators: list[str] = []

    for seg in raw_segments:
        s = seg.strip()
        if not s:
            continue
        if s in ("&&", "||", ";", "|"):
            operators.append(s)
        else:
            # Parse individual subcommand
            try:
                tokens = shlex.split(s, posix=(shell_flavor != "cmd"))
            except ValueError:
                tokens = s.split()

            if not tokens:
                continue

            binary = tokens[0]
            args = tokens[1:]
            redirs: list[str] = []
            clean_args: list[str] = []

            for arg in args:
                if arg.startswith(("<", ">", ">>", "2>", "2>&1")):
                    redirs.append(arg)
                else:
                    clean_args.append(arg)

            subcommands.append({
                "binary": binary,
                "arguments": clean_args,
                "redirections": redirs,
                "raw_command": s,
            })

    is_compound = len(subcommands) > 1 or len(operators) > 0
    first_bin = subcommands[0]["binary"] if subcommands else ""
    first_args = subcommands[0]["arguments"] if subcommands else []

    return {
        "binary": first_bin,
        "arguments": first_args,
        "operators": operators,
        "redirections": [r for sc in subcommands for r in sc["redirections"]],
        "is_compound": is_compound,
        "subcommands": subcommands,
    }


def tokenize_shell_ast(command: str, shell_flavor: str = "bash") -> dict[str, Any]:
    """Parses a shell command string into structured AST components without executing it."""
    parsed = _tokenize_command(command, shell_flavor=shell_flavor)
    return {
        "status": "ok",
        "command": command,
        "shell_flavor": shell_flavor,
        "binary": parsed["binary"],
        "arguments": parsed["arguments"],
        "operators": parsed["operators"],
        "redirections": parsed["redirections"],
        "is_compound": parsed["is_compound"],
        "subcommands_count": len(parsed["subcommands"]),
        "subcommands": parsed["subcommands"],
    }


def evaluate_command_policy(
    command: str,
    working_dir: str | None = None,
    custom_rules: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluates a candidate shell command against active prefix rules and danger patterns."""
    clean_cmd = command.strip()
    if not clean_cmd:
        return {
            "status": "ok",
            "decision": "allow",
            "matched_rule": "empty_command",
            "risk_score": 0.0,
            "rationale": "Empty command requires no action.",
        }

    # 1. Check for immediate danger patterns (Deny/Prompt overrides)
    for pattern, desc, action in _DEFAULT_DENY_PATTERNS:
        if re.search(pattern, clean_cmd, re.IGNORECASE):
            return {
                "status": "ok",
                "decision": action,
                "matched_rule": f"danger_pattern:{pattern}",
                "risk_score": 1.0 if action == "deny" else 0.85,
                "rationale": f"Triggered security rule: {desc}",
                "requires_elevation": True,
            }

    # 2. Tokenize into AST subcommands
    ast = _tokenize_command(clean_cmd)

    # Check custom rules first if supplied
    active_pool = list(_ACTIVE_RULES)
    if custom_rules:
        for cr in custom_rules:
            parts = cr.split()
            if parts:
                active_pool.insert(0, PrefixRule(parts, "allow", "Custom override rule"))

    # 3. Evaluate each subcommand in compound chain
    subcommand_decisions: list[dict[str, Any]] = []

    for sc in ast["subcommands"]:
        sc_tokens = [sc["binary"]] + sc["arguments"]
        matched = False
        sc_decision = "prompt"
        matched_rule_desc = "unmatched_fallback"

        for rule in active_pool:
            rule_len = len(rule.pattern)
            if len(sc_tokens) >= rule_len:
                match_all = True
                for i, r_tok in enumerate(rule.pattern):
                    if r_tok == "*":
                        continue
                    if sc_tokens[i].lower() != r_tok.lower():
                        match_all = False
                        break
                if match_all:
                    matched = True
                    sc_decision = rule.action
                    matched_rule_desc = f"{' '.join(rule.pattern)} ({rule.comment})"
                    break

        subcommand_decisions.append({
            "subcommand": sc["raw_command"],
            "decision": sc_decision,
            "matched_rule": matched_rule_desc,
        })

    # 4. Synthesize compound decision
    # If any is deny -> deny
    # If any is prompt -> prompt
    # If all allow -> allow
    final_decision = "allow"
    highest_risk = 0.1

    for sc_res in subcommand_decisions:
        if sc_res["decision"] == "deny":
            final_decision = "deny"
            highest_risk = 1.0
            break
        elif sc_res["decision"] == "prompt":
            final_decision = "prompt"
            highest_risk = max(highest_risk, 0.5)

    return {
        "status": "ok",
        "command": clean_cmd,
        "decision": final_decision,
        "risk_score": highest_risk,
        "is_compound": ast["is_compound"],
        "subcommand_evaluations": subcommand_decisions,
        "rationale": f"Evaluated {len(ast['subcommands'])} subcommand(s); final verdict: {final_decision.upper()}",
    }


def amend_prefix_rule(
    prefix_pattern: str,
    action: str,
    comment: str = "",
) -> dict[str, Any]:
    """Dynamically add or update an allowed/prompt/deny prefix rule in the active execution policy."""
    global _ACTIVE_RULES

    clean_pat = prefix_pattern.strip()
    clean_action = action.strip().lower()

    if clean_action not in ("allow", "prompt", "deny"):
        return {
            "status": "error",
            "error": f"Invalid action '{action}'. Must be 'allow', 'prompt', or 'deny'.",
        }

    tokens = clean_pat.split()
    if not tokens:
        return {"status": "error", "error": "Prefix pattern cannot be empty."}

    # Check if existing rule exists and update
    updated = False
    for r in _ACTIVE_RULES:
        if r.pattern == tokens:
            r.action = clean_action
            if comment:
                r.comment = comment
            updated = True
            break

    if not updated:
        _ACTIVE_RULES.insert(0, PrefixRule(tokens, clean_action, comment or "User amended rule"))

    return {
        "status": "ok",
        "amended_pattern": clean_pat,
        "action": clean_action,
        "comment": comment,
        "is_update": updated,
        "total_active_rules": len(_ACTIVE_RULES),
    }


def check_sandbox_requirements(
    command: str,
    target_platform: str | None = None,
) -> dict[str, Any]:
    """Determines platform-native sandboxing requirements for a given command."""
    plat = (target_platform or platform.system()).lower()
    if "win" in plat:
        plat_name = "windows"
        sandbox_type = "windows_restricted_token"
    elif "darwin" in plat or "mac" in plat:
        plat_name = "macos"
        sandbox_type = "macos_seatbelt"
    else:
        plat_name = "linux"
        sandbox_type = "linux_landlock_bwrap"

    ast = _tokenize_command(command)
    binary = ast["binary"].lower()

    # Determine read and write path recommendations
    is_write_heavy = any(
        kw in command.lower()
        for kw in ["install", "build", "compile", "mkdir", "touch", "cp", "mv", "rm", "write"]
    )
    is_network_heavy = any(
        kw in command.lower()
        for kw in ["curl", "wget", "git clone", "git push", "npm install", "pip install", "fetch"]
    )

    recommended_reads = ["."]
    recommended_writes = ["."] if is_write_heavy else []

    requires_sandbox = True
    # Pure read-only info queries can run with minimum restrictions
    if binary in ("echo", "pwd", "whoami", "uname", "hostname"):
        requires_sandbox = False

    return {
        "status": "ok",
        "command": command,
        "target_platform": plat_name,
        "sandbox_type": sandbox_type,
        "requires_sandbox": requires_sandbox,
        "is_network_allowed": is_network_heavy,
        "recommended_read_paths": recommended_reads,
        "recommended_write_paths": recommended_writes,
        "security_recommendations": [
            f"Enforce {sandbox_type} isolation boundary on {plat_name}",
            "Block access to /etc, C:\\Windows\\System32, and user home root outside workspace",
        ],
    }


class CodexExecPolicyService:
    """Typed service for deterministic execution policy and sandbox analysis."""

    def evaluate(self, command: str) -> dict[str, Any]:
        return evaluate_command_policy(command)

    def amend(self, pattern: str, action: str, comment: str = "") -> dict[str, Any]:
        return amend_prefix_rule(pattern, action, comment)

    def tokenize(self, command: str) -> dict[str, Any]:
        return tokenize_shell_ast(command)

    def check_sandbox(self, command: str) -> dict[str, Any]:
        return check_sandbox_requirements(command)


EXEC_POLICY_KEY: ServiceKey[CodexExecPolicyService] = ServiceKey("security.codex_execpolicy")


class CodexExecPolicyPlugin(HarnessPlugin):
    """Brain Harness Plugin exposing Codex deterministic execpolicy and sandbox analyzer."""

    name = "plugin.codex_execpolicy"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__()
        self._service = CodexExecPolicyService()

    async def on_enable(self, context: ServiceContext) -> None:
        """Register typed service into IoC container on startup."""
        context.provide(EXEC_POLICY_KEY, self._service, provider=self.name)
        logger.info("CodexExecPolicyPlugin enabled and service registered")

    async def on_disable(self, context: ServiceContext) -> None:
        """Unregister service on shutdown."""
        logger.info("CodexExecPolicyPlugin disabled")
