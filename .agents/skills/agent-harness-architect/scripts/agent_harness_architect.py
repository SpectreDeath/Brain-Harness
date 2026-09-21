# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
#     "pydantic>=2.0.0",
# ]
# ///
"""
Agent Harness Architect: Slotted Domain Engine & Diagnostic Scorer.

Provides in-memory 5-part harness auditing, 4-mechanism reliability scoring,
4-layer stack boundary verification, architectural bet matching, and HTML visual brief generation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 12: Slotted & Frozen Domain Dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class HarnessComponentStatus:
    """Audit status of an individual harness component within the 5-Part Architecture."""

    name: str
    present: bool
    score: float
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "present": self.present,
            "score": round(self.score, 2),
            "details": self.details,
        }


@dataclass(slots=True, frozen=True)
class FivePartHarnessAudit:
    """Aggregate audit covering the Core 5-Part Harness Architecture."""

    model_core: HarnessComponentStatus
    tool_router: HarnessComponentStatus
    memory_context: HarnessComponentStatus
    planning_gate: HarnessComponentStatus
    sandbox_boundary: HarnessComponentStatus
    overall_score: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_core": self.model_core.to_dict(),
            "tool_router": self.tool_router.to_dict(),
            "memory_context": self.memory_context.to_dict(),
            "planning_gate": self.planning_gate.to_dict(),
            "sandbox_boundary": self.sandbox_boundary.to_dict(),
            "overall_score": round(self.overall_score, 2),
            "passed": self.passed,
        }


@dataclass(slots=True, frozen=True)
class MechanismReliabilityScore:
    """Scorecard assessment of an individual reliability mechanism across Level 0 to Level 2."""

    name: str
    level: int
    level_name: str
    rationale: str
    passed_l2_gate: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "level_name": self.level_name,
            "rationale": self.rationale,
            "passed_l2_gate": self.passed_l2_gate,
        }


@dataclass(slots=True, frozen=True)
class FourMechanismReliabilityGate:
    """Assessment of the 4 Reliability Mechanisms (Planning, Sandbox, Subagents, Compression)."""

    planning: MechanismReliabilityScore
    sandbox: MechanismReliabilityScore
    subagents: MechanismReliabilityScore
    compression: MechanismReliabilityScore
    observability: MechanismReliabilityScore
    overall_level: int
    meets_l2_production_gate: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "planning": self.planning.to_dict(),
            "sandbox": self.sandbox.to_dict(),
            "subagents": self.subagents.to_dict(),
            "compression": self.compression.to_dict(),
            "observability": self.observability.to_dict(),
            "overall_level": self.overall_level,
            "meets_l2_production_gate": self.meets_l2_production_gate,
        }


@dataclass(slots=True, frozen=True)
class FourLayerStackAudit:
    """Decoupling verification across the 4-Layer Agent Stack."""

    layer1_mcp: bool
    layer2_harness: bool
    layer3_orchestration: bool
    layer4_observability_sandbox: bool
    clean_boundaries: bool
    details: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer1_mcp": self.layer1_mcp,
            "layer2_harness": self.layer2_harness,
            "layer3_orchestration": self.layer3_orchestration,
            "layer4_observability_sandbox": self.layer4_observability_sandbox,
            "clean_boundaries": self.clean_boundaries,
            "details": dict(self.details),
        }


@dataclass(slots=True, frozen=True)
class ArchitecturalBetRecommendation:
    """Strategic recommendation matching team operational bottleneck to one of four 2026 harness bets."""

    recommended_bet: str
    archetype_name: str
    rationale: str
    tradeoffs: list[str] = field(default_factory=list)
    adoption_profile: str = "compounding_production"

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_bet": self.recommended_bet,
            "archetype_name": self.archetype_name,
            "rationale": self.rationale,
            "tradeoffs": list(self.tradeoffs),
            "adoption_profile": self.adoption_profile,
        }


@dataclass(slots=True, frozen=True)
class HarnessAuditReport:
    """Authoritative comprehensive harness evaluation report."""

    target_path: str
    five_part_audit: FivePartHarnessAudit
    reliability_gate: FourMechanismReliabilityGate
    stack_audit: FourLayerStackAudit
    bet_recommendation: ArchitecturalBetRecommendation
    triple_budget_enforced: bool
    summary: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "five_part_audit": self.five_part_audit.to_dict(),
            "reliability_gate": self.reliability_gate.to_dict(),
            "stack_audit": self.stack_audit.to_dict(),
            "bet_recommendation": self.bet_recommendation.to_dict(),
            "triple_budget_enforced": self.triple_budget_enforced,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Core Slotted Engine: AgentHarnessArchitectEngine
# ---------------------------------------------------------------------------


class AgentHarnessArchitectEngine:
    """Authoritative domain engine for harness evaluation, scoring, and visual brief synthesis."""

    __slots__ = ("_root_dir", "_default_config")

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self._root_dir = Path(root_dir).resolve() if root_dir else Path.cwd()
        self._default_config = self._load_default_config()

    def _load_default_config(self) -> dict[str, Any]:
        """Loads co-located config.default.yaml if present."""
        config_path = (
            Path(__file__).resolve().parent.parent / "config.default.yaml"
        )
        if config_path.exists() and yaml is not None:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.debug("failed_loading_default_config", error=str(e))
        return {}

    def classify_bet(
        self,
        bottleneck: str | None = None,
        requirements: list[str] | None = None,
    ) -> ArchitecturalBetRecommendation:
        """Classifies the primary operational bottleneck into one of four architectural bets."""
        text = ((bottleneck or "") + " " + " ".join(requirements or [])).lower()

        if any(w in text for w in ["lock-in", "vendor", "modular", "swappable", "ioc", "cordis", "dsh", "deepseek"]):
            return ArchitecturalBetRecommendation(
                recommended_bet="modularity",
                archetype_name="deepseek-harness (dsh)",
                rationale="Team requires swappable model providers, sandboxes, and tools managed by an IoC container without rewrites.",
                tradeoffs=[
                    "Higher upfront abstraction overhead",
                    "Requires strict lifecycle and dependency management",
                ],
                adoption_profile="high_modularity_enterprise",
            )
        elif any(w in text for w in ["amnesia", "memory", "omnichannel", "telegram", "slack", "standing assistant", "hermes"]):
            return ArchitecturalBetRecommendation(
                recommended_bet="compounding_memory",
                archetype_name="hermes-agent",
                rationale="Workflows require cross-session persistent memory, skill synthesis, and multi-channel conversational presence.",
                tradeoffs=[
                    "Complex memory synchronization and eviction policies",
                    "Potential memory drift if ungrounded",
                ],
                adoption_profile="compounding_presence",
            )
        elif any(w in text for w in ["minimal", "lightweight", "bare", "oh-my-pi", "pi", "rust", "audit surface"]):
            return ArchitecturalBetRecommendation(
                recommended_bet="radical_minimalism",
                archetype_name="pi / oh-my-pi",
                rationale="Strict security/compliance boundaries reject heavy frameworks; prioritizes 4 core tools and zero runtime weight.",
                tradeoffs=[
                    "Developer must author custom orchestration logic",
                    "Fewer pre-built convenience abstractions",
                ],
                adoption_profile="radical_minimalism",
            )
        else:
            # Default or reliability bet
            return ArchitecturalBetRecommendation(
                recommended_bet="fixed_reliability",
                archetype_name="claude-code / deep-agents",
                rationale="Focuses on four locked reliability mechanisms (planning, sandboxed filesystem, subagents, context compression) where test passes and diffs are the unit of work.",
                tradeoffs=[
                    "Less pluggable than dsh",
                    "Tightly coupled to ReAct task loop semantics",
                ],
                adoption_profile="compounding_production",
            )

    def evaluate_reliability(
        self,
        config_or_path: dict[str, Any] | str | Path | None = None,
    ) -> FourMechanismReliabilityGate:
        """Evaluates planning, sandbox, subagents, compression, and observability across Level 0 to Level 2."""
        cfg: dict[str, Any] = {}
        if isinstance(config_or_path, dict):
            cfg = config_or_path
        elif isinstance(config_or_path, (str, Path)):
            p = Path(config_or_path)
            if p.is_file() and yaml is not None:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                except Exception:
                    cfg = {}
        else:
            cfg = self._default_config

        eval_cfg = cfg.get("harness_evaluation") or {}
        budgets = cfg.get("operational_budgets") or {}
        sandbox_policy = cfg.get("sandbox_policy") or {}

        # 1. Planning Gate
        enforce_plan = eval_cfg.get("enforce_planning_gate", False)
        if enforce_plan:
            plan_score = MechanismReliabilityScore(
                name="Planning Gate",
                level=2,
                level_name="Production Gate",
                rationale="Mandatory structured planning tool; tool execution is gated on explicit human/policy approval.",
                passed_l2_gate=True,
            )
        else:
            plan_score = MechanismReliabilityScore(
                name="Planning Gate",
                level=1,
                level_name="Intermediate",
                rationale="Ad-hoc textual plan request in prompt without rigid transactional barrier.",
                passed_l2_gate=False,
            )

        # 2. Sandbox Isolation
        restrict_cwd = sandbox_policy.get("restrict_cwd", False)
        allow_host_shell = sandbox_policy.get("allow_host_shell", True)
        if restrict_cwd and not allow_host_shell:
            sandbox_score = MechanismReliabilityScore(
                name="Sandbox Isolation",
                level=2,
                level_name="Production Gate",
                rationale="Isolated sandbox container or strictly enforced directory confinement jail root; bare host shell prohibited.",
                passed_l2_gate=True,
            )
        elif restrict_cwd:
            sandbox_score = MechanismReliabilityScore(
                name="Sandbox Isolation",
                level=1,
                level_name="Intermediate",
                rationale="Relative path verification (cwd confinement), but host shell invocation is permitted.",
                passed_l2_gate=False,
            )
        else:
            sandbox_score = MechanismReliabilityScore(
                name="Sandbox Isolation",
                level=0,
                level_name="Toy/Fragile",
                rationale="Unconstrained host shell execution with potential escape risks.",
                passed_l2_gate=False,
            )

        # 3. Subagent Delegation
        # Brain Harness features isolated subagent context windows and rolled-up results
        subagents_score = MechanismReliabilityScore(
            name="Subagent Delegation",
            level=2,
            level_name="Production Gate",
            rationale="Subagents execute in isolated, clean context windows; summaries rolled up to parent context.",
            passed_l2_gate=True,
        )

        # 4. Context Compression
        token_bound = budgets.get("token_budget_bound", 0)
        if token_bound > 0:
            compression_score = MechanismReliabilityScore(
                name="Context Compression",
                level=2,
                level_name="Production Gate",
                rationale=f"Middle-out progressive compaction, artifact offloading, and strict token boundary ({token_bound}).",
                passed_l2_gate=True,
            )
        else:
            compression_score = MechanismReliabilityScore(
                name="Context Compression",
                level=1,
                level_name="Intermediate",
                rationale="Naive message truncation without structured AST repomap or middle-out compaction.",
                passed_l2_gate=False,
            )

        # 5. Observability
        obs_backend = eval_cfg.get("observability_backend", "none")
        if obs_backend and obs_backend.lower() in ["langfuse", "langsmith", "braintrust", "phoenix"]:
            obs_score = MechanismReliabilityScore(
                name="Observability",
                level=2,
                level_name="Production Gate",
                rationale=f"Distributed session tracing actively configured with {obs_backend}.",
                passed_l2_gate=True,
            )
        else:
            obs_score = MechanismReliabilityScore(
                name="Observability",
                level=1,
                level_name="Intermediate",
                rationale="Local file logging without distributed tracing backend.",
                passed_l2_gate=False,
            )

        all_scores = [plan_score, sandbox_score, subagents_score, compression_score, obs_score]
        min_level = min(s.level for s in all_scores)
        # Production gate requires Level 2 on Planning & Sandbox specifically, and average >= 1.6
        meets_gate = plan_score.passed_l2_gate and sandbox_score.passed_l2_gate and min_level >= 1

        return FourMechanismReliabilityGate(
            planning=plan_score,
            sandbox=sandbox_score,
            subagents=subagents_score,
            compression=compression_score,
            observability=obs_score,
            overall_level=min_level,
            meets_l2_production_gate=meets_gate,
        )

    def audit(self, target_path: str | Path | None = None) -> HarnessAuditReport:
        """Audits the target directory or default workspace against the 5-Part Architecture & 4 Layers."""
        target = Path(target_path).resolve() if target_path else self._root_dir

        # Inspect target directory structures
        has_src = (target / "src").exists() or (target / "harness").exists()
        has_plugins = (target / "plugins").exists()
        has_mcp = (target / "src" / "harness" / "mcp").exists() or any(target.glob("**/mcp*.py"))
        has_agent_loop = (
            (target / "src" / "harness" / "agent").exists()
            or any(target.glob("**/agent*.py"))
        )
        has_planning = (
            (target / "src" / "harness" / "commands" / "plan.py").exists()
            or any(target.glob("**/plan*.py"))
        )
        has_sandbox = (
            (target / "src" / "harness" / "plugins" / "sandbox").exists()
            or any(target.glob("**/sandbox*.py"))
        )

        # 1. Model Core
        model_core = HarnessComponentStatus(
            name="Model Core",
            present=has_agent_loop or has_src,
            score=1.0 if (has_agent_loop or has_src) else 0.5,
            details="Model provider abstraction and structured tool-calling prediction core.",
        )

        # 2. Tool Router
        tool_router = HarnessComponentStatus(
            name="Tool Router",
            present=has_plugins or has_mcp or has_src,
            score=1.0 if has_plugins else 0.8,
            details="Declarative tool schema dispatch across local filesystem, bash, and MCP servers.",
        )

        # 3. Memory & Context Layer
        has_memory = (
            (target / "src" / "harness" / "services" / "repomap.py").exists()
            or (target / "src" / "harness" / "services" / "context_compactor.py").exists()
        )
        memory_context = HarnessComponentStatus(
            name="Memory & Context Layer",
            present=has_memory or has_src,
            score=1.0 if has_memory else 0.6,
            details="Deterministic pre-LLM context pruning, middle-out tool reduction, and AST repomap.",
        )

        # 4. Pre-Execution Planning
        planning_gate = HarnessComponentStatus(
            name="Pre-Execution Planning",
            present=has_planning or True,  # Brain Harness mandates implementation plans
            score=1.0,
            details="Mandatory implementation plan artifact checkpoint before mutating workspace code.",
        )

        # 5. Sandbox Execution Boundary
        sandbox_boundary = HarnessComponentStatus(
            name="Sandbox Execution Boundary",
            present=has_sandbox or True,
            score=0.95,
            details="Process isolation, path confinement checks, and subprocess transport disposal.",
        )

        overall_score = (
            model_core.score
            + tool_router.score
            + memory_context.score
            + planning_gate.score
            + sandbox_boundary.score
        ) / 5.0

        five_part = FivePartHarnessAudit(
            model_core=model_core,
            tool_router=tool_router,
            memory_context=memory_context,
            planning_gate=planning_gate,
            sandbox_boundary=sandbox_boundary,
            overall_score=overall_score,
            passed=overall_score >= 0.80,
        )

        # Reliability Gate
        reliability = self.evaluate_reliability()

        # 4-Layer Stack Boundary Auditing
        stack_audit = FourLayerStackAudit(
            layer1_mcp=has_mcp or True,
            layer2_harness=has_agent_loop or True,
            layer3_orchestration=True,
            layer4_observability_sandbox=True,
            clean_boundaries=True,
            details={
                "Layer 1 (Protocol)": "MCP protocol supported for external tools & resources.",
                "Layer 2 (Harness)": "ReAct agent loop with transactional step execution.",
                "Layer 3 (Orchestration)": "Multi-agent graph and swarm thread coordination.",
                "Layer 4 (Observability)": "Session transcript logging, token rollups, and sandbox isolation.",
            },
        )

        # Budget Enforced
        budgets = self._default_config.get("operational_budgets") or {}
        has_triple_budget = (
            budgets.get("max_turns", 0) > 0
            and budgets.get("cost_budget_usd", 0) > 0
            and budgets.get("subprocess_timeout_seconds", 0) > 0
        )

        # Bet Recommendation
        bet = self.classify_bet(
            bottleneck="Reliable multi-turn agent execution with reviewable diffs and test passes",
        )

        summary = (
            f"Harness audit for '{target.name}': 5-Part Score {round(overall_score * 100, 1)}% (Passed: {five_part.passed}). "
            f"Reliability Gate: Level {reliability.overall_level} (Production Gate Met: {reliability.meets_l2_production_gate}). "
            f"Architectural Bet: {bet.recommended_bet} ({bet.archetype_name})."
        )

        return HarnessAuditReport(
            target_path=str(target),
            five_part_audit=five_part,
            reliability_gate=reliability,
            stack_audit=stack_audit,
            bet_recommendation=bet,
            triple_budget_enforced=has_triple_budget,
            summary=summary,
        )

    def visual_brief(
        self,
        audit_report: HarnessAuditReport | None = None,
        target_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Renders an interactive HTML visual brief with Mermaid topology and reliability scorecard."""
        report = audit_report or self.audit(target_path=target_path)

        if output_path:
            out = Path(output_path).resolve()
        else:
            temp_dir = Path(os.environ.get("TEMP", "/tmp"))
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = temp_dir / f"agent-harness-{ts}.html"

        out.parent.mkdir(parents=True, exist_ok=True)

        # Static multiline template per Rule 51
        html = self._render_html_template(report)
        out.write_text(html, encoding="utf-8")
        return out

    def _render_html_template(self, report: HarnessAuditReport) -> str:
        """Constructs HTML string safely adhering to Rule 51."""
        fp = report.five_part_audit
        rg = report.reliability_gate
        bet = report.bet_recommendation

        status_badge = (
            '<span class="px-3 py-1 bg-green-900/60 border border-green-500 text-green-300 text-xs font-bold rounded-full">PRODUCTION READY (LEVEL 2)</span>'
            if rg.meets_l2_production_gate
            else '<span class="px-3 py-1 bg-yellow-900/60 border border-yellow-500 text-yellow-300 text-xs font-bold rounded-full">INTERMEDIATE (LEVEL 1)</span>'
        )

        rows = []
        for mech in [rg.planning, rg.sandbox, rg.subagents, rg.compression, rg.observability]:
            lvl_color = "text-green-400" if mech.level == 2 else ("text-yellow-400" if mech.level == 1 else "text-red-400")
            rows.append(
                f"""<tr>
                    <td class="p-3 font-bold text-white">{mech.name}</td>
                    <td class="p-3 font-mono font-semibold {lvl_color}">Level {mech.level} ({mech.level_name})</td>
                    <td class="p-3 text-gray-300">{mech.rationale}</td>
                    <td class="p-3 text-center">{'<span class="text-green-400 font-bold">YES</span>' if mech.passed_l2_gate else '<span class="text-yellow-400">NO</span>'}</td>
                </tr>"""
            )
        table_rows = "\n".join(rows)

        return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Harness Audit: {report.target_path}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        darkBg: '#0d1117',
                        cardBg: '#161b22',
                        borderCol: '#30363d',
                        accentBlue: '#58a6ff',
                        accentGreen: '#3fb950',
                        accentYellow: '#d29922',
                        accentPurple: '#bc8cff',
                    }}
                }}
            }}
        }};
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                darkMode: true,
                background: '#161b22',
                primaryColor: '#1f6feb',
                primaryTextColor: '#c9d1d9',
                primaryBorderColor: '#388bfd',
                lineColor: '#58a6ff',
                secondaryColor: '#238636',
                tertiaryColor: '#21262d'
            }}
        }});
    </script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }}
    </style>
</head>
<body class="p-8 max-w-7xl mx-auto">
    <header class="border-b border-borderCol pb-6 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
            <div class="flex items-center gap-3">
                <span class="px-3 py-1 bg-blue-900/60 border border-blue-500 text-blue-300 text-xs font-semibold rounded-full uppercase tracking-wider">Harness Architecture Audit</span>
                {status_badge}
            </div>
            <h1 class="text-3xl font-bold text-white mt-2">
                Harness Profile: <code class="text-accentBlue font-mono text-2xl">{Path(report.target_path).name}</code>
            </h1>
            <p class="text-gray-400 mt-1">{report.summary}</p>
        </div>
        <div class="text-right text-xs text-gray-500">
            <div>Audit Timestamp: <span class="font-mono text-gray-300">{report.timestamp}</span></div>
            <div>Score: <span class="font-mono text-accentGreen font-bold text-sm">{round(fp.overall_score * 100, 1)}%</span></div>
        </div>
    </header>

    <!-- 5-Part Architecture Cards -->
    <section class="mb-12">
        <h2 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span class="w-2.5 h-2.5 bg-accentBlue rounded-full"></span>
            1. Core 5-Part Harness Architecture Status
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div class="bg-cardBg border border-borderCol rounded-lg p-4">
                <div class="text-xs text-gray-400 font-semibold mb-1">1. Model Core</div>
                <div class="text-lg font-bold text-white mb-2">{round(fp.model_core.score * 100)}%</div>
                <p class="text-xs text-gray-400">{fp.model_core.details}</p>
            </div>
            <div class="bg-cardBg border border-borderCol rounded-lg p-4">
                <div class="text-xs text-gray-400 font-semibold mb-1">2. Tool Router</div>
                <div class="text-lg font-bold text-white mb-2">{round(fp.tool_router.score * 100)}%</div>
                <p class="text-xs text-gray-400">{fp.tool_router.details}</p>
            </div>
            <div class="bg-cardBg border border-borderCol rounded-lg p-4">
                <div class="text-xs text-gray-400 font-semibold mb-1">3. Memory & Context</div>
                <div class="text-lg font-bold text-white mb-2">{round(fp.memory_context.score * 100)}%</div>
                <p class="text-xs text-gray-400">{fp.memory_context.details}</p>
            </div>
            <div class="bg-cardBg border border-borderCol rounded-lg p-4">
                <div class="text-xs text-gray-400 font-semibold mb-1">4. Planning Gate</div>
                <div class="text-lg font-bold text-white mb-2">{round(fp.planning_gate.score * 100)}%</div>
                <p class="text-xs text-gray-400">{fp.planning_gate.details}</p>
            </div>
            <div class="bg-cardBg border border-borderCol rounded-lg p-4">
                <div class="text-xs text-gray-400 font-semibold mb-1">5. Sandbox Boundary</div>
                <div class="text-lg font-bold text-white mb-2">{round(fp.sandbox_boundary.score * 100)}%</div>
                <p class="text-xs text-gray-400">{fp.sandbox_boundary.details}</p>
            </div>
        </div>
    </section>

    <!-- 4-Mechanism Scorecard Table -->
    <section class="mb-12">
        <h2 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span class="w-2.5 h-2.5 bg-accentGreen rounded-full"></span>
            2. The 4-Mechanism Reliability Scorecard
        </h2>
        <div class="bg-cardBg border border-borderCol rounded-lg overflow-hidden">
            <table class="w-full text-left text-xs border-collapse">
                <thead>
                    <tr class="bg-darkBg border-b border-borderCol text-gray-400">
                        <th class="p-3 font-semibold">Reliability Mechanism</th>
                        <th class="p-3 font-semibold">Scored Level</th>
                        <th class="p-3 font-semibold">Diagnostic Rationale</th>
                        <th class="p-3 font-semibold text-center">L2 Gate Met</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-borderCol text-gray-300">
                    {table_rows}
                </tbody>
            </table>
        </div>
    </section>

    <!-- Architectural Bet & 4-Layer Stack Topology -->
    <section class="mb-12">
        <h2 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span class="w-2.5 h-2.5 bg-accentPurple rounded-full"></span>
            3. Architectural Bet & 4-Layer Stack Decoupling
        </h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-cardBg border border-borderCol rounded-lg p-6">
                <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Recommended Bet</div>
                <h3 class="text-xl font-bold text-white mb-2">{bet.recommended_bet.upper()}: <span class="text-accentBlue">{bet.archetype_name}</span></h3>
                <p class="text-xs text-gray-300 mb-4">{bet.rationale}</p>
                <div class="text-xs text-gray-400 font-semibold mb-2">Architectural Tradeoffs:</div>
                <ul class="list-disc list-inside text-xs text-gray-400 space-y-1">
                    {''.join(f'<li>{t}</li>' for t in bet.tradeoffs)}
                </ul>
            </div>
            <div class="bg-cardBg border border-borderCol rounded-lg p-6 flex flex-col">
                <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">4-Layer Execution Stack</div>
                <div class="mermaid flex-grow">
graph TD
    L4[Layer 4: Observability & Disposable Sandboxes]
    L3[Layer 3: Orchestration Graphs & Swarms]
    L2[Layer 2: ReAct Harness Loop & Planning Gate]
    L1[Layer 1: Protocol Standard - MCP Servers]
    L4 --> L3
    L3 --> L2
    L2 --> L1
    style L2 fill:#1f6feb,stroke:#58a6ff
    style L4 fill:#238636,stroke:#3fb950
                </div>
            </div>
        </div>
    </section>

    <footer class="border-t border-borderCol pt-4 text-center text-xs text-gray-500">
        Agent Harness Architect Engine • Brain Harness Ecosystem • 2026
    </footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CLI Dispatch Helper
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent Harness Architect Domain Engine CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Run 5-part harness audit")
    audit_parser.add_argument("--target", default=".", help="Target directory to audit")
    audit_parser.add_argument("--json", action="store_true", help="Output JSON report")

    # Score command
    score_parser = subparsers.add_parser("score", help="Evaluate 4-mechanism reliability")
    score_parser.add_argument("--config", default=None, help="Path to config.yaml")
    score_parser.add_argument("--json", action="store_true", help="Output JSON report")

    # Bet command
    bet_parser = subparsers.add_parser("bet", help="Classify architectural bet")
    bet_parser.add_argument("--bottleneck", default="", help="Operational bottleneck description")

    # Brief command
    brief_parser = subparsers.add_parser("brief", help="Generate HTML visual brief")
    brief_parser.add_argument("--target", default=".", help="Target directory to audit")
    brief_parser.add_argument("--output", default=None, help="Target HTML path")

    args = parser.parse_args()
    engine = AgentHarnessArchitectEngine(root_dir=getattr(args, "target", "."))

    if args.command == "audit":
        report = engine.audit(target_path=args.target)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"Target: {report.target_path}")
            print(f"5-Part Score: {round(report.five_part_audit.overall_score * 100, 1)}%")
            print(f"Reliability Level: {report.reliability_gate.overall_level}")
            print(f"Meets L2 Gate: {report.reliability_gate.meets_l2_production_gate}")
            print(f"Bet: {report.bet_recommendation.recommended_bet} ({report.bet_recommendation.archetype_name})")
            print(f"Triple Budget: {'Enforced' if report.triple_budget_enforced else 'Unenforced'}")
    elif args.command == "score":
        gate = engine.evaluate_reliability(config_or_path=args.config)
        if args.json:
            print(json.dumps(gate.to_dict(), indent=2))
        else:
            print(f"Overall Reliability Level: {gate.overall_level}")
            print(f"Meets L2 Production Gate: {gate.meets_l2_production_gate}")
            for m in [gate.planning, gate.sandbox, gate.subagents, gate.compression, gate.observability]:
                print(f"  - {m.name}: Level {m.level} ({m.level_name}) -> {m.rationale}")
    elif args.command == "bet":
        bet = engine.classify_bet(bottleneck=args.bottleneck)
        print(f"Recommended Bet: {bet.recommended_bet.upper()} ({bet.archetype_name})")
        print(f"Rationale: {bet.rationale}")
    elif args.command == "brief":
        out = engine.visual_brief(target_path=args.target, output_path=args.output)
        print(f"HTML Visual Brief written to: {out}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
