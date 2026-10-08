"""Active runtime interceptor evaluating proposed agent actions against skill anti-patterns and AST gates."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    InvariantViolation,
    SkillCardDefinition,
)


class AntiPatternGuard:
    """Active runtime interceptor evaluating proposed agent actions against skill anti-patterns."""

    @classmethod
    def evaluate_action(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> list[AntiPatternViolation]:
        """Authoritative action evaluator checking proposed tool calls and arguments.

        Performs:
        1. Parameter flattening across strings, dicts, and nested collections.
        2. AST syntax tree scanning for blocked calls (eval, exec, input, __import__) in codeblocks or raw arguments.
        3. Fallback regex analysis for direct invocation patterns.
        4. Active skill anti-pattern symptom and keyword detection.
        """
        violations: list[AntiPatternViolation] = []

        # 1. Collect all textual content from action_name and action_input
        text_parts: list[str] = [action_name]
        for val in action_input.values():
            if isinstance(val, str):
                text_parts.append(val)
            elif isinstance(val, (dict, list)):
                try:
                    text_parts.append(json.dumps(val))
                except Exception:
                    text_parts.append(str(val))
        combined_text = "\n".join(text_parts)

        # 2. Blocked AST call checks (eval, exec, input, __import__)
        blocked_calls = {"eval", "exec", "input", "__import__"}
        code_blocks = re.findall(
            r"```(?:python)?\s*\n(.*?)\n```", combined_text, re.DOTALL
        )
        if not code_blocks:
            code_blocks = [combined_text]

        system_guard_name = active_skills[0] if active_skills else "system_guard"

        for block in code_blocks:
            try:
                tree = ast.parse(block)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func_name = None
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        if func_name and func_name in blocked_calls:
                            violations.append(
                                AntiPatternViolation(
                                    skill_name=system_guard_name,
                                    anti_pattern=f"Blocked Call: {func_name}()",
                                    symptom=f"Direct call to {func_name}() detected in proposed action parameters",
                                    remedy="Use sandboxed execution or approved kernel tools instead",
                                    matched_phrase=f"{func_name}()",
                                )
                            )
            except Exception:
                pass

            # Fallback regex search for direct blocked call patterns (eval(...) etc.)
            for call in blocked_calls:
                pattern = rf"(?:^|[^\w.]){re.escape(call)}\s*\("
                if re.search(pattern, block):
                    match_already_found = any(call in v.anti_pattern for v in violations)
                    if not match_already_found:
                        violations.append(
                            AntiPatternViolation(
                                skill_name=system_guard_name,
                                anti_pattern=f"Blocked Call: {call}()",
                                symptom=f"Direct invocation of {call}() detected in action input",
                                remedy="Use sandboxed execution or approved kernel tools instead",
                                matched_phrase=f"{call}()",
                            )
                        )

        # 3. Rule 15 Credential Exposure Guard
        if re.search(r"(?:ghp_[A-Za-z0-9_]{10,}|github_pat_[A-Za-z0-9_]{10,})", combined_text):
            violations.append(
                AntiPatternViolation(
                    skill_name=system_guard_name,
                    anti_pattern="Rule 15: Credential Exposure in Action Parameters",
                    symptom="Plaintext access token detected in proposed action parameters",
                    remedy="Pass authenticated credentials via isolated runner script with in-memory log redaction",
                    matched_phrase="[REDACTED_TOKEN_DETECTED]",
                )
            )

        # 4. Rule 30 PowerShell Glob Non-Expansion Guard
        if action_name in ("run_command", "bash", "execute_command"):
            cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
            if re.search(r"pytest\s+[^\s]*\*", cmd_val):
                violations.append(
                    AntiPatternViolation(
                        skill_name=system_guard_name,
                        anti_pattern="Rule 30: PowerShell Glob Non-Expansion in pytest",
                        symptom="Glob wildcard '*' in pytest target path will not be expanded by PowerShell",
                        remedy='Use pytest -k "<pattern>" keyword filtering or explicit file lists instead of glob paths',
                        matched_phrase="pytest * glob",
                    )
                )

        # 5. Check declared anti-patterns and invariants for active skills
        if active_skills and skill_lookup:
            for skill_name in active_skills:
                skill = (
                    skill_lookup(skill_name)
                    if callable(skill_lookup)
                    else (
                        skill_lookup.get(skill_name)
                        if isinstance(skill_lookup, dict)
                        else None
                    )
                )
                if skill:
                    violations.extend(cls.check_proposal(skill, combined_text))
                    violations.extend(
                        cls.check_invariants(
                            skill=skill,
                            action_name=action_name,
                            action_input=action_input,
                            combined_text=combined_text,
                        )
                    )

        return violations

    @classmethod
    def evaluate_action_gate(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> ActionGateResult:
        """Authoritative action gate evaluation returning a slotted ActionGateResult."""
        violations = cls.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=skill_lookup,
        )
        if not violations:
            return ActionGateResult(
                action_name=action_name,
                is_blocked=False,
                violations=(),
                observation={"status": "ok"},
            )
        obs = cls.format_self_repair_observation(violations)
        return ActionGateResult(
            action_name=action_name,
            is_blocked=True,
            violations=tuple(violations),
            observation=obs,
        )

    @classmethod
    def check_invariants(
        cls,
        skill: SkillCardDefinition,
        action_name: str,
        action_input: dict[str, Any],
        combined_text: str,
    ) -> list[InvariantViolation]:
        """Scan proposed action and input against declared mandatory invariants for a skill."""
        violations: list[InvariantViolation] = []
        text_lower = combined_text.lower()

        for inv in getattr(skill, "invariants", []) or []:
            inv_rule = getattr(inv, "rule", "") or ""
            if not inv_rule:
                continue
            inv_lower = inv_rule.lower()

            # Invariant: Artifact Metadata Restricted (Rule 31)
            if (
                "artifact metadata" in inv_lower
                and ("restricted" in inv_lower or "only accepts" in inv_lower)
                and action_name in ("write_to_file", "write_file", "create_file")
                and (
                    "artifactmetadata" in text_lower
                    or any("artifactmetadata" in str(k).lower() for k in action_input)
                )
            ):
                target_path = str(
                    action_input.get("target_file")
                    or action_input.get("TargetFile")
                    or action_input.get("path")
                    or action_input.get("file_path")
                    or ""
                ).replace("\\", "/")
                if target_path and not ("brain" in target_path or ".gemini" in target_path or "artifact" in target_path):
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="ArtifactMetadata on workspace file",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy="Omit ArtifactMetadata when writing files outside the artifact directory",
                        )
                    )

            # Invariant: Scratch File Execution over Inline -c Strings (Rule 29)
            if (
                ("scratch file execution" in inv_lower or "inline -c" in inv_lower)
                and "never" in inv_lower
                and (
                    action_name in ("run_command", "bash", "execute_command")
                    or "command" in action_input
                    or "CommandLine" in action_input
                )
            ):
                cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
                if "python -c" in cmd_val or 'python -c "' in cmd_val or "python -c '" in cmd_val:
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="python -c inline string",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy="Write logic to a scratch script and execute via python <path>",
                        )
                    )

            # Invariant: PowerShell Glob Non-Expansion (Rule 30)
            if (
                ("powershell glob" in inv_lower or "non-expansion" in inv_lower or "rule 30" in inv_lower)
                and (
                    action_name in ("run_command", "bash", "execute_command")
                    or "command" in action_input
                    or "CommandLine" in action_input
                )
            ):
                cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
                if re.search(r"pytest\s+[^\s]*\*", cmd_val):
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="pytest glob path in PowerShell",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy='Use pytest -k "<pattern>" keyword filtering or explicit file lists instead of glob paths',
                        )
                    )

            # Invariant: Secure Credential Injection & Runner Isolation (Rule 15)
            if (
                ("credential" in inv_lower or "token" in inv_lower or "rule 15" in inv_lower or "runner isolation" in inv_lower)
                and (
                    action_name in ("run_command", "bash", "execute_command")
                    or "command" in action_input
                    or "CommandLine" in action_input
                )
            ):
                cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
                if "git push" in cmd_val and ("ghp_" in cmd_val or "github_pat_" in cmd_val):
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="authenticated git push via shell expansion",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy="Execute authenticated git push via isolated python runner script using standard input pipe",
                        )
                    )

            # Invariant: Windows UTF-8 Stream Codec Entrypoint (Rule 23 & Rule 50)
            if (
                ("utf-8" in inv_lower or "reconfigure" in inv_lower or "rule 23" in inv_lower or "rule 50" in inv_lower)
                and action_name in ("write_to_file", "write_file", "create_file")
            ):
                target_path = str(
                    action_input.get("target_file")
                    or action_input.get("TargetFile")
                    or action_input.get("path")
                    or action_input.get("file_path")
                    or ""
                ).replace("\\", "/")
                code_content = str(
                    action_input.get("CodeContent")
                    or action_input.get("content")
                    or action_input.get("code")
                    or combined_text
                )
                if "scratch" in target_path and target_path.endswith(".py"):
                    if "sys.stdout.reconfigure" not in code_content:
                        violations.append(
                            InvariantViolation(
                                skill_name=skill.name,
                                rule=inv_rule,
                                matched_phrase="Missing sys.stdout.reconfigure(encoding='utf-8') in scratch runner",
                                is_blocking=getattr(inv, "is_blocking", True),
                                remedy="Add sys.stdout.reconfigure(encoding='utf-8') at module entry to prevent cp1252 charmap crashes",
                            )
                        )

            # Invariant: Canonical Knowledge Vault Dual-File Directory (Rule 40)
            if (
                ("knowledge vault" in inv_lower or "dual-file" in inv_lower or "rule 40" in inv_lower)
                and action_name in ("write_to_file", "write_file", "create_file")
            ):
                target_path = str(
                    action_input.get("target_file")
                    or action_input.get("TargetFile")
                    or action_input.get("path")
                    or action_input.get("file_path")
                    or ""
                ).replace("\\", "/")
                if ".harness/knowledge" in target_path or "harness/knowledge" in target_path:
                    p = target_path.split("knowledge/")[-1].strip("/")
                    parts = p.split("/")
                    if len(parts) == 1 and parts[0].endswith(".json"):
                        violations.append(
                            InvariantViolation(
                                skill_name=skill.name,
                                rule=inv_rule,
                                matched_phrase="Flat JSON file in knowledge vault root",
                                is_blocking=getattr(inv, "is_blocking", True),
                                remedy="Persist items in directory structure: .harness/knowledge/<ki_id>/ (metadata.json + summary.md)",
                            )
                        )

        return violations

    @classmethod
    def _check_code_ast(
        cls, code_block: str, skill: SkillCardDefinition
    ) -> list[AntiPatternViolation]:
        """Run AST visitor on fenced python codeblock to catch blocked library calls."""
        violations: list[AntiPatternViolation] = []
        try:
            tree = ast.parse(code_block)
        except Exception:
            return violations

        blocked_calls = {"eval", "exec", "input", "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name and func_name in blocked_calls:
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=f"Blocked Call: {func_name}()",
                            symptom=f"Direct call to {func_name}() detected in proposed code block",
                            remedy="Use sandboxed execution or approved kernel tools instead",
                            matched_phrase=f"{func_name}()",
                        )
                    )
        return violations

    @classmethod
    def format_self_repair_observation(
        cls, violations: list[Any]
    ) -> dict[str, Any]:
        """Format violations into an actionable ReAct observation dictionary for in-flight self-repair."""
        if not violations:
            return {"status": "ok"}
        v = violations[0]
        if isinstance(v, InvariantViolation) or hasattr(v, "is_blocking"):
            return {
                "status": "error",
                "invariant_violation": f"{getattr(v, 'rule', '')} ({getattr(v, 'skill_name', '')})",
                "rule": getattr(v, "rule", ""),
                "is_blocking": getattr(v, "is_blocking", True),
                "prescribed_remedy": getattr(v, "remedy", "Adhere strictly to the skill invariant rule"),
                "matched_phrase": getattr(v, "matched_phrase", ""),
                "corrective_action_required": True,
            }
        return {
            "status": "error",
            "anti_pattern_violation": f"{v.anti_pattern} ({v.skill_name})",
            "symptom": v.symptom,
            "prescribed_remedy": v.remedy,
            "matched_phrase": v.matched_phrase,
            "corrective_action_required": True,
        }

    @classmethod
    def check_proposal(
        cls,
        skill: SkillCardDefinition,
        proposed_action_or_plan: str,
    ) -> list[AntiPatternViolation]:
        """Scan proposed plan or tool arguments for symptoms of declared anti-patterns."""
        violations: list[AntiPatternViolation] = []
        text_lower = proposed_action_or_plan.lower()
        negation_markers = ("avoid", "do not", "don't", "prevent", "never", "without")

        # AST analysis on fenced code blocks
        code_blocks = re.findall(
            r"```(?:python)?\s*\n(.*?)\n```", proposed_action_or_plan, re.DOTALL
        )
        for block in code_blocks:
            violations.extend(cls._check_code_ast(block, skill))

        for ap in skill.anti_patterns:
            ap_name_lower = ap.name.lower()
            ap_tokens = [
                tok.lower() for tok in re.findall(r"\w+", ap.name) if len(tok) > 3
            ]

            if ap_name_lower in text_lower:
                match_idx = text_lower.find(ap_name_lower)
                window = text_lower[max(0, match_idx - 50) : match_idx]
                if not any(marker in window for marker in negation_markers):
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=ap.name,
                            symptom=ap.symptom,
                            remedy=ap.remedy,
                            matched_phrase=ap.name,
                        )
                    )
            elif ap_tokens and all(t in text_lower for t in ap_tokens):
                min_idx = min(
                    text_lower.find(t) for t in ap_tokens if text_lower.find(t) != -1
                )
                window = text_lower[max(0, min_idx - 50) : min_idx]
                if not any(marker in window for marker in negation_markers):
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=ap.name,
                            symptom=ap.symptom,
                            remedy=ap.remedy,
                            matched_phrase=" ".join(ap_tokens),
                        )
                    )

        return violations


__all__ = ["AntiPatternGuard"]
