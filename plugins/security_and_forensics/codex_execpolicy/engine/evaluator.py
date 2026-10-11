"""Command policy evaluation against active prefix rules and danger patterns."""

from __future__ import annotations

import sys
from typing import Any

from plugins.security_and_forensics.codex_execpolicy.engine.ast_parser import _tokenize_command
from plugins.security_and_forensics.codex_execpolicy.engine.models import PrefixRule
from plugins.security_and_forensics.codex_execpolicy.engine.rules import (
    _check_danger_patterns,
    amend_prefix_rule,
    get_active_rules,
    reset_active_rules,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def evaluate_command_policy(
    command: str,
    working_dir: str | None = None,
    custom_rules: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate a candidate shell command against active prefix rules and danger patterns."""
    clean_cmd = command.strip()
    if not clean_cmd:
        return {
            "status": "ok",
            "decision": "allow",
            "matched_rule": "empty_command",
            "risk_score": 0.0,
            "rationale": "Empty command requires no action.",
        }

    # 1. Check for immediate danger patterns on full raw command string
    danger = _check_danger_patterns(clean_cmd)
    if danger:
        pattern, desc, action = danger
        return {
            "status": "ok",
            "command": clean_cmd,
            "decision": action,
            "matched_rule": f"danger_pattern:{pattern}",
            "risk_score": 1.0 if action == "deny" else 0.85,
            "rationale": f"Triggered security rule: {desc}",
            "requires_elevation": True,
        }

    # 2. Tokenize and parse recursive AST
    parsed = _tokenize_command(clean_cmd)

    # Check custom rules first if supplied
    active_pool = get_active_rules()
    if custom_rules:
        for cr in custom_rules:
            parts = cr.split()
            if parts:
                active_pool.insert(0, PrefixRule(parts, "allow", "Custom override rule"))

    # 3. Check for danger patterns or rules inside extracted nested subshells
    for subshell in parsed.get("subshells", []):
        sub_raw = subshell.get("raw", "")
        sub_danger = _check_danger_patterns(sub_raw)
        if sub_danger:
            pattern, desc, action = sub_danger
            return {
                "status": "ok",
                "command": clean_cmd,
                "decision": action,
                "matched_rule": f"danger_pattern_in_subshell:{pattern}",
                "risk_score": 1.0 if action == "deny" else 0.85,
                "rationale": f"Subshell triggered security rule: {desc}",
                "requires_elevation": True,
            }

    # 4. Evaluate each subcommand in compound chain
    subcommand_decisions: list[dict[str, Any]] = []

    for sc in parsed["subcommands"]:
        if not sc["binary"]:
            subcommand_decisions.append({
                "subcommand": sc["raw_command"],
                "decision": "allow",
                "matched_rule": "variable_assignment_only",
            })
            continue

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

    # 5. Synthesize compound decision
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
        "is_compound": parsed["is_compound"],
        "subcommand_evaluations": subcommand_decisions,
        "rationale": f"Evaluated {len(parsed['subcommands'])} subcommand(s); final verdict: {final_decision.upper()}",
    }


__all__ = [
    "amend_prefix_rule",
    "evaluate_command_policy",
    "get_active_rules",
    "reset_active_rules",
]
