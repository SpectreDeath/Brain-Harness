"""Prompt construction, AST RepoMap injection, and multi-pass action parsing for ReAct loops."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from harness.agent.context_optimizer import AgentContextOptimizer
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage
from harness.services.tools import ToolRegistry


def build_react_initial_messages(
    task: str,
    tools: ToolRegistry,
    optimizer: AgentContextOptimizer | None = None,
    context: ServiceContext | None = None,
) -> tuple[list[LLMMessage], list[str]]:
    """Construct the standard ReAct system prompt and user task message.

    Applies dynamic AST RepoMap injection (Rule 9) and skill intelligence guidance.
    Returns (messages, active_skills).
    """
    schemas = tools.get_schemas()
    messages = [
        LLMMessage(
            role="system",
            content=(
                "You are an autonomous AI assistant running inside the Harness micro-kernel.\n"
                "You solve tasks by reasoning and calling tools available to you.\n"
                "Available tools:\n"
                f"{json.dumps(schemas, indent=2)}\n\n"
                "When deciding what to do, you can choose to call a tool or provide a final answer.\n"
                "If providing a final answer, prefix with 'FINAL ANSWER: <your answer>'."
            ),
        ),
        LLMMessage(role="user", content=f"Task: {task}"),
    ]

    active_skills: list[str] = []

    # Rule 9: Deterministic AST RepoMap injection if configured
    if optimizer is not None:
        cfg = getattr(optimizer, "config", None)
        if cfg and cfg.repo_map_root:
            messages = optimizer.inject_repo_map(
                messages, query_context=task, config=cfg
            )

    # Knowledge Graph & Skill Guidance injection via authoritative SkillIntelligenceService
    if context is not None:
        try:
            from harness.services.skill_graph import resolve_skill_intelligence

            intel = resolve_skill_intelligence(context)
            guidance = intel.compile_execution_guidance(task, max_skills=4)
            if guidance and guidance.should_inject:
                active_skills = list(guidance.selected_skills)
                messages[0] = guidance.inject_into_message(messages[0])
        except Exception:
            pass

    return messages, active_skills


def _parse_json_safe(s: str) -> dict[str, Any] | None:
    """Attempt strict JSON parse, then conservative auto-repair fallback (Rule 21)."""
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Auto-repair: strip trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", s)
    # Auto-repair: close any unclosed braces
    open_count = repaired.count("{") - repaired.count("}")
    if open_count > 0:
        repaired += "}" * open_count

    try:
        parsed = json.loads(repaired)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    try:
        obj = ast.literal_eval(repaired)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _extract_from_dict(d: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    if "action" in d:
        inp = d.get("input") or {}
        return d["action"], inp if isinstance(inp, dict) else {}
    return None, {}


def extract_action_from_thought(thought: str) -> tuple[str | None, dict[str, Any]]:
    """Extract action name and input parameters from thought text.

    Applies a four-pass parser (JSON fences -> XML tool_call -> raw JSON -> auto-repair)
    conforming to Rule 21 in-flight stream normalization invariant.
    """
    # Pass 1: Markdown JSON fence
    if "```json" in thought:
        raw = thought.split("```json", 1)[1].split("```", 1)[0].strip()
        parsed = _parse_json_safe(raw)
        if parsed:
            res = _extract_from_dict(parsed)
            if res[0] is not None:
                return res

    # Pass 2: XML <tool_call> tag (Rule 21)
    xml_match = re.search(r"<tool_call>(.*?)</tool_call>", thought, re.DOTALL)
    if xml_match:
        parsed = _parse_json_safe(xml_match.group(1).strip())
        if parsed:
            res = _extract_from_dict(parsed)
            if res[0] is not None:
                return res

    # Pass 3: Raw JSON object or outermost {...} block
    candidate = thought.strip()
    if not (candidate.startswith("{") and candidate.endswith("}")):
        brace_match = re.search(r"\{[\s\S]*\}", thought)
        if brace_match:
            candidate = brace_match.group(0).strip()
    if candidate.startswith("{"):
        parsed = _parse_json_safe(candidate)
        if parsed:
            res = _extract_from_dict(parsed)
            if res[0] is not None:
                return res

    return None, {}
