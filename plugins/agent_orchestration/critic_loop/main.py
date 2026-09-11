"""Critic Evaluation & Safety Gatekeeper Plugin for Brain Harness.

Provides an authoritative, typed evaluation seam unifying:
1. Rubric scoring and heuristic criteria assessment
2. Destructive shell command screening
3. AST static code analysis and anti-pattern detection
4. Plan feasibility and risk mitigation review
5. Dialectical multi-agent debate and arbiter verdict synthesis
6. Autonomous generate-critique-revise loops
"""

from __future__ import annotations

import ast
import json
import re
import sys
import types
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

# Dangerous shell patterns for safety gatekeeping
_DANGEROUS_PATTERNS = [
    (r"\brm\s+-[rfRF]{1,4}\s+[/~]", "Recursive root or home directory removal"),
    (r"\brm\s+-[rfRF]{1,4}\s+\*", "Wildcard file deletion"),
    (r"\bdel\s+/[fFqQsS]{1,4}\s+[cC]:\\", "System drive deletion"),
    (r"\bformat\s+[a-zA-Z]:", "Disk format operation"),
    (r"\bgit\s+reset\s+--hard\b", "Destructive hard git reset (discards all uncommitted work)"),
    (r"\bgit\s+clean\s+-[fFxd]{1,4}\b", "Forced git directory purge"),
    (r"\bgit\s+push\s+.*--force\b", "Forced git push (overwrites remote commit history)"),
    (r"\bdrop\s+(database|schema|table)\b", "Database object destruction"),
    (r"\bdd\s+if=.*of=/dev/[a-z]+", "Raw disk block overwrite"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb definition"),
    (r"\b(shutdown|reboot|init\s+0|halt)\b", "System termination command"),
]


@runtime_checkable
class CriticEvaluationService(Protocol):
    """Authoritative protocol for critic, safety evaluation, and dialectical debate."""

    def evaluate_rubric(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Score content against a criteria checklist with breakdown."""
        ...

    def evaluate(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Score content against a criteria checklist (unified evaluation seam)."""
        ...

    def check_command_safety(self, command: str) -> dict[str, Any]:
        """Scan shell commands for dangerous or irreversible operations."""
        ...

    def evaluate_code_ast(self, code: str, language: str = "python") -> dict[str, Any]:
        """Statically inspect syntax, AST complexity, and anti-patterns."""
        ...

    def review_plan_feasibility(self, goal: str, steps: list[str]) -> dict[str, Any]:
        """Evaluate plan steps for verification steps, risks, and mitigations."""
        ...

    def conduct_dialectical_debate(
        self,
        topic: str,
        pro_arguments: list[str],
        con_arguments: list[str],
    ) -> dict[str, Any]:
        """Orchestrate dialectical argument rounds between Proposer and Challenger."""
        ...

    def synthesize_debate_verdict(self, debate_summary: dict[str, Any]) -> dict[str, Any]:
        """Synthesize an impartial arbiter decision based on debate rounds."""
        ...

    async def refine(
        self,
        task: str,
        draft: str,
        *,
        rubric: list[str] | None = None,
        max_iterations: int = 3,
        threshold: float = 0.85,
        llm_service: Any | None = None,
    ) -> dict[str, Any]:
        """Run iterative multi-turn critique and refinement until threshold is achieved."""
        ...


CRITIC_EVALUATION_SERVICE_KEY = ServiceKey[CriticEvaluationService]("service.critic_evaluation")
CRITIC_LOOP_KEY = CRITIC_EVALUATION_SERVICE_KEY  # Backward-compatible alias


class CriticEvaluationServiceImpl:
    """Consolidated implementation of the Critic & Safety Evaluation Gate."""

    def evaluate(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Unified evaluation entrypoint alias delegating to evaluate_rubric."""
        return self.evaluate_rubric(content, rubric)

    def evaluate_rubric(self, content: str, rubric: list[str]) -> dict[str, Any]:
        scores: list[dict[str, Any]] = []
        total_score = 0.0

        for item in rubric:
            item_lower = item.lower()
            score = 0.5
            reasons: list[str] = []

            if "type" in item_lower or "typing" in item_lower:
                has_types = bool(re.search(r":\s*[a-zA-Z0-9_|\[\]]+\b|->\s*[a-zA-Z0-9_|\[\]]+", content))
                score = 1.0 if has_types else 0.3
                reasons.append("Type annotations verified" if has_types else "Missing explicit type annotations")
            elif "docstring" in item_lower or "documentation" in item_lower or "comment" in item_lower:
                has_docs = '"""' in content or "'''" in content or "#" in content
                score = 1.0 if has_docs else 0.4
                reasons.append("Docstrings present" if has_docs else "Missing docstrings / comments")
            elif "error" in item_lower or "exception" in item_lower or "try" in item_lower:
                has_err = "try:" in content or "except" in content or "raise" in content
                score = 1.0 if has_err else 0.4
                reasons.append("Error handling verified" if has_err else "No exception handling detected")
            elif "clean" in item_lower or "style" in item_lower:
                lines = content.splitlines()
                long_lines = sum(1 for ln in lines if len(ln) > 120)
                score = max(0.2, 1.0 - (long_lines * 0.1))
                reasons.append(f"Line length acceptable ({long_lines} long lines)" if long_lines == 0 else f"{long_lines} lines exceed 120 chars")
            else:
                tokens = [t for t in re.findall(r"\w+", item_lower) if len(t) > 3]
                matches = sum(1 for t in tokens if t in content.lower())
                ratio = matches / len(tokens) if tokens else 0.5
                score = min(1.0, 0.4 + (ratio * 0.6))
                reasons.append(f"Keyword alignment: {int(ratio * 100)}%")

            scores.append({
                "criterion": item,
                "score": round(score, 2),
                "feedback": "; ".join(reasons),
            })
            total_score += score

        overall = total_score / len(rubric) if rubric else 1.0
        return {
            "score": round(overall, 2),
            "overall_score": round(overall, 2),
            "criteria_count": len(rubric),
            "breakdown": scores,
            "passed": overall >= 0.80,
        }

    def check_command_safety(self, command: str) -> dict[str, Any]:
        cleaned = command.strip()
        violations: list[str] = []

        for pattern, description in _DANGEROUS_PATTERNS:
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                violations.append(description)

        is_safe = len(violations) == 0
        risk_level = "low"
        if violations:
            risk_level = "critical" if any("destruction" in v or "removal" in v or "overwrite" in v for v in violations) else "high"

        return {
            "status": "ok",
            "command": command,
            "is_safe": is_safe,
            "risk_level": risk_level,
            "violations_count": len(violations),
            "violations": violations,
        }

    def evaluate_code_ast(self, code: str, language: str = "python") -> dict[str, Any]:
        lang = language.lower()

        if lang == "json":
            try:
                parsed = json.loads(code)
                return {
                    "status": "ok",
                    "language": "json",
                    "valid": True,
                    "score": 100,
                    "type": type(parsed).__name__,
                    "keys_count": len(parsed) if isinstance(parsed, dict) else len(parsed) if isinstance(parsed, list) else 1,
                    "issues": [],
                }
            except json.JSONDecodeError as exc:
                return {
                    "status": "error",
                    "language": "json",
                    "valid": False,
                    "score": 0,
                    "error": str(exc),
                    "issues": [f"Invalid JSON syntax at line {exc.lineno}, column {exc.colno}"],
                }

        if lang != "python":
            return {
                "status": "ok",
                "language": lang,
                "valid": True,
                "score": 100,
                "message": f"Syntax parsing not supported for language '{language}', skipped.",
                "issues": [],
            }

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {
                "status": "error",
                "language": "python",
                "valid": False,
                "score": 0,
                "syntax_error": {
                    "line": exc.lineno,
                    "offset": exc.offset,
                    "message": str(exc.msg),
                    "text": exc.text,
                },
                "issues": [f"SyntaxError on line {exc.lineno}: {exc.msg}"],
            }

        functions = []
        classes = []
        anti_patterns = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                arg_count = len(node.args.args)
                has_return = node.returns is not None

                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args_count": arg_count,
                    "has_docstring": docstring is not None,
                    "has_return_type": has_return,
                })
                if arg_count > 7:
                    anti_patterns.append(f"Function '{node.name}' has {arg_count} arguments (exceeds recommended max 7).")
                if docstring is None and not node.name.startswith("_"):
                    anti_patterns.append(f"Function '{node.name}' lacks a docstring.")
                if not has_return and not node.name.startswith("_"):
                    anti_patterns.append(f"Function '{node.name}' lacks a return type annotation.")

            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": ast.get_docstring(node) is not None,
                })

            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    anti_patterns.append(f"Bare 'except:' handler detected at line {node.lineno} (catches SystemExit/KeyboardInterrupt).")

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "eval":
                    anti_patterns.append(f"Use of 'eval()' detected at line {node.lineno} (security risk).")
                elif isinstance(node.func, ast.Name) and node.func.id == "exec":
                    anti_patterns.append(f"Use of 'exec()' detected at line {node.lineno} (security risk).")

        loc = len([ln for ln in code.splitlines() if ln.strip() and not ln.strip().startswith("#")])
        score = max(0, 100 - len(anti_patterns) * 15) if anti_patterns else 100

        return {
            "status": "ok",
            "language": "python",
            "valid": True,
            "score": score,
            "metrics": {
                "lines_of_code": loc,
                "functions_count": len(functions),
                "classes_count": len(classes),
            },
            "functions": functions,
            "classes": classes,
            "issues": anti_patterns,
        }

    def review_plan_feasibility(self, goal: str, steps: list[str]) -> dict[str, Any]:
        if not steps:
            return {
                "status": "ok",
                "goal": goal,
                "score": 0,
                "feasible": False,
                "risks": ["Plan has no action steps defined."],
                "recommendations": ["Add sequential action steps to achieve the stated goal."],
            }

        risks: list[str] = []
        recommendations: list[str] = []
        has_verification = False
        has_backup_or_test = False

        for step in steps:
            s_lower = step.lower()
            if any(w in s_lower for w in ("verify", "test", "check", "validate", "assert", "inspect")):
                has_verification = True
            if any(w in s_lower for w in ("backup", "rollback", "fallback", "dry-run", "dry run")):
                has_backup_or_test = True

        if not has_verification:
            risks.append("No explicit verification, testing, or validation step in plan.")
            recommendations.append("Append an automated test or verification step at the end of the plan.")

        if len(steps) < 2:
            recommendations.append("Break the single monolithic step into atomic, testable sub-steps.")

        if len(steps) > 12:
            recommendations.append("Plan exceeds 12 steps; consider decomposing into sub-phases.")

        score = 100
        if not has_verification:
            score -= 25
        if not has_backup_or_test and any("delete" in s.lower() or "drop" in s.lower() or "replace" in s.lower() for s in steps):
            score -= 20
            risks.append("Destructive modifications planned without explicit backup/rollback precaution.")

        return {
            "status": "ok",
            "goal": goal,
            "total_steps": len(steps),
            "score": max(0, score),
            "feasible": score >= 50,
            "has_verification_step": has_verification,
            "risks": risks,
            "recommendations": recommendations,
        }

    def conduct_dialectical_debate(
        self,
        topic: str,
        pro_arguments: list[str],
        con_arguments: list[str],
    ) -> dict[str, Any]:
        rounds: list[dict[str, Any]] = []
        max_rounds = max(len(pro_arguments), len(con_arguments))

        for i in range(max_rounds):
            pro_claim = pro_arguments[i] if i < len(pro_arguments) else "No further supporting arguments."
            con_claim = con_arguments[i] if i < len(con_arguments) else "No further counter-arguments."

            rounds.append({
                "round_number": i + 1,
                "proposer_claim": pro_claim,
                "challenger_counter": con_claim,
            })

        return {
            "status": "ok",
            "topic": topic,
            "total_rounds": len(rounds),
            "pro_points_count": len(pro_arguments),
            "con_points_count": len(con_arguments),
            "rounds": rounds,
        }

    def synthesize_debate_verdict(self, debate_summary: dict[str, Any]) -> dict[str, Any]:
        topic = debate_summary.get("topic", "General Proposal")
        rounds = debate_summary.get("rounds", [])
        pro_count = debate_summary.get("pro_points_count", 0)
        con_count = debate_summary.get("con_points_count", 0)

        verdict_lines = [
            f"### ⚖️ Arbiter Verdict on '{topic}'",
            f"- **Rounds Evaluated:** {len(rounds)}",
            f"- **Thesis Arguments:** {pro_count}",
            f"- **Antithesis Counter-Points:** {con_count}",
        ]

        recommendation = "PROCEED_WITH_MITIGATIONS" if con_count > 0 else "PROCEED_DIRECTLY"
        if con_count > pro_count * 2:
            recommendation = "REJECT_OR_RETHINK"

        verdict_lines.append(f"- **Final Recommendation:** **{recommendation}**")

        return {
            "status": "ok",
            "topic": topic,
            "recommendation": recommendation,
            "verdict_markdown": "\n".join(verdict_lines),
        }

    async def refine(
        self,
        task: str,
        draft: str,
        *,
        rubric: list[str] | None = None,
        max_iterations: int = 3,
        threshold: float = 0.85,
        llm_service: Any | None = None,
    ) -> dict[str, Any]:
        active_rubric = rubric or [
            "Include strict type annotations on all function signatures",
            "Provide clear docstrings with parameters and return descriptions",
            "Implement robust error handling and input validation",
            "Adhere to clean code style without bloated lines",
        ]

        current_draft = draft
        trajectory: list[dict[str, Any]] = []

        for step in range(1, max_iterations + 1):
            eval_result = self.evaluate_rubric(current_draft, active_rubric)
            score = eval_result["overall_score"]

            trajectory.append({
                "iteration": step,
                "score": score,
                "passed": eval_result["passed"],
                "feedback": [b["feedback"] for b in eval_result["breakdown"] if b["score"] < 0.8],
            })

            if score >= threshold:
                logger.info("Critic loop converged", iteration=step, score=score)
                break

            if llm_service is not None and hasattr(llm_service, "generate"):
                try:
                    feedback_str = "\n".join(trajectory[-1]["feedback"])
                    prompt = (
                        f"Task: {task}\n\n"
                        f"Current Draft:\n{current_draft}\n\n"
                        f"Critic Feedback:\n{feedback_str}\n\n"
                        f"Please provide an improved revision addressing all feedback:"
                    )
                    refined = await llm_service.generate(prompt)
                    if refined:
                        current_draft = str(refined)
                except Exception as e:
                    logger.warning("LLM refinement step failed", step=step, error=str(e))
                    break

        final_eval = self.evaluate_rubric(current_draft, active_rubric)
        return {
            "status": "ok",
            "task": task,
            "iterations_completed": len(trajectory),
            "initial_score": trajectory[0]["score"] if trajectory else 0.0,
            "final_score": final_eval["overall_score"],
            "converged": final_eval["overall_score"] >= threshold,
            "trajectory": trajectory,
            "final_draft": current_draft,
        }


_EVAL_INSTANCE = CriticEvaluationServiceImpl()


# Top-level tool entrypoints
def evaluate(content: str, rubric: list[str]) -> dict[str, Any]:
    return _EVAL_INSTANCE.evaluate(content, rubric)


def evaluate_rubric(content: str, rubric: list[str]) -> dict[str, Any]:
    return _EVAL_INSTANCE.evaluate_rubric(content, rubric)


async def run_critic_loop(
    task: str,
    draft: str,
    *,
    rubric: list[str] | None = None,
    max_iterations: int = 3,
    threshold: float = 0.85,
    llm_service: Any | None = None,
) -> dict[str, Any]:
    return await _EVAL_INSTANCE.refine(
        task=task,
        draft=draft,
        rubric=rubric,
        max_iterations=max_iterations,
        threshold=threshold,
        llm_service=llm_service,
    )


def critic_check_safety(command: str) -> dict[str, Any]:
    return _EVAL_INSTANCE.check_command_safety(command)


def critic_evaluate_code(code: str, language: str = "python") -> dict[str, Any]:
    return _EVAL_INSTANCE.evaluate_code_ast(code, language)


def critic_review_plan(goal: str, steps: list[str]) -> dict[str, Any]:
    return _EVAL_INSTANCE.review_plan_feasibility(goal, steps)


def conduct_dialectical_debate(
    topic: str,
    pro_arguments: list[str],
    con_arguments: list[str],
) -> dict[str, Any]:
    return _EVAL_INSTANCE.conduct_dialectical_debate(topic, pro_arguments, con_arguments)


def synthesize_debate_verdict(debate_summary: dict[str, Any]) -> dict[str, Any]:
    return _EVAL_INSTANCE.synthesize_debate_verdict(debate_summary)


# Backward compatibility class alias
CriticLoopService = CriticEvaluationServiceImpl


class CriticLoopPlugin(HarnessPlugin):
    """Authoritative plugin providing critic evaluation, safety gating, and dialectical debate."""

    @property
    def name(self) -> str:
        return "plugin.critic_loop"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Authoritative critic, rubric evaluation, destructive command safety gate, "
            "and dialectical debate arbiter."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CRITIC_EVALUATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CRITIC_EVALUATION_SERVICE_KEY, _EVAL_INSTANCE, provider=self.name)
        logger.info("CriticEvaluationService provided", plugin=self.name)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = CriticLoopPlugin()
