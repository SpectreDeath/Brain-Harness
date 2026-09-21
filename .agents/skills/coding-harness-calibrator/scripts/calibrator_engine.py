"""Empirical Coding Harness Calibration & Staging Engine.

Implements the component-level optimization laws and staged context management
pipeline derived from Fan et al. (arXiv:2609.20804v1, September 2026).
"""

from __future__ import annotations

import datetime
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class HarnessMode(str, Enum):
    """Operational mode calibrated to model capability."""

    SCAFFOLD = "scaffold"  # Weak models: planning + typed tools to prevent collapse
    BALANCED = "balanced"  # Mid models: structured guidance + mixed tools
    EFFICIENCY = (
        "efficiency"  # Strong models: bash composition + stopping-point control
    )


class WorkloadType(str, Enum):
    """Classification of the execution environment and task scope."""

    TERMINAL_CLI = "terminal_cli"  # Command-line centric (Terminal-Bench style)
    CODEBASE_REPO = (
        "codebase_repo"  # Multi-file repository bug fixing (SWE-Bench style)
    )
    MIXED = "mixed"


class ContextTier(str, Enum):
    """Context management tiers from Fan et al. ablation matrix."""

    T0_UNMANAGED = "T0"  # No management (crashes at 32k)
    T1_ELISION_ONLY = "T1"  # Rule-based observation stubbing only
    T2_RECOVERABLE_ELISION = "T2"  # Elision with recall_event (dead machinery)
    T3_SUMMARIZATION_ONLY = "T3"  # LLM summarization only (expensive)
    T4_STAGED = "T4"  # Optimal: M1 elision at B1 + M3 summarization at B2


class ActionSpaceType(str, Enum):
    """Action space interfaces."""

    PREDEFINED_TOOLS = "predefined_tools"  # Typed schemas: read_file, edit_file, etc.
    BASH_ONLY = "bash_only"  # Bare shell: bash + auxiliary planning


@dataclass(slots=True, frozen=True)
class HarnessBudgetConfig:
    """Mathematical context window thresholds and token bounds."""

    usable_window: int = 131072  # e.g. 128k
    soft_threshold_ratio: float = 0.60  # B1: 60% usable context
    hard_threshold_ratio: float = 0.85  # B2: 85% usable context
    recent_window_ratio: float = 0.30  # 30% recent verbatim window
    min_recent_turns: int = 2  # At least 2 full turns pinned

    def __post_init__(self) -> None:
        assert 0.0 < self.soft_threshold_ratio < self.hard_threshold_ratio < 1.0, (
            "Threshold invariant violated: must satisfy 0 < B1 < B2 < 1.0"
        )
        assert self.min_recent_turns >= 2, "Recent turns floor must be >= 2"

    @property
    def b1_tokens(self) -> int:
        """Token count triggering M1 rule-based elision."""
        return int(self.usable_window * self.soft_threshold_ratio)

    @property
    def b2_tokens(self) -> int:
        """Token count triggering M3 structured LLM summarization."""
        return int(self.usable_window * self.hard_threshold_ratio)


@dataclass(slots=True, frozen=True)
class CalibrationRecommendation:
    """Optimal component-level harness configuration for a given model and workload."""

    model_name: str
    harness_mode: HarnessMode
    action_space: ActionSpaceType
    context_tier: ContextTier
    enable_planning: bool
    planning_role: str  # "accuracy_scaffold" vs "stopping_point_controller"
    budget_config: HarnessBudgetConfig
    stuck_warn_threshold: int = 5
    stuck_kill_threshold: int = 8
    deprecation_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        assert self.stuck_warn_threshold < self.stuck_kill_threshold, (
            "Stuck detection invariant: warn_threshold must be strictly less than kill_threshold"
        )


@dataclass(slots=True, frozen=True)
class ContextStagingEvent:
    """An event or message turn within the context history."""

    role: str  # "system", "user", "assistant", "tool_call", "tool_observation"
    content: str
    turn: int
    token_count: int
    is_bulky: bool = False
    tool_name: str = ""


@dataclass(slots=True, frozen=True)
class ContextStagingSimulationResult:
    """Detailed trace and metrics resulting from Two-Tier Context Staging ($T_4$)."""

    usable_window: int
    initial_tokens: int
    final_tokens: int
    b1_elision_triggered: bool
    b2_summary_triggered: bool
    elided_observations_count: int
    pruned_tokens_count: int
    structured_summary: str
    events_after_staging: list[ContextStagingEvent] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RepatchPredictionResult:
    """Empirical prediction of re-patch rate, coarse action ratio, and execution cost reduction."""

    model_scale: str  # "weak_30b", "mid_120b", "strong_550b"
    workload: WorkloadType
    action_space: ActionSpaceType
    predicted_mean_repatches: float  # e.g. 4.6 vs 1.5
    coarse_replace_ratio: float  # e.g. 0.51 vs 0.76
    estimated_cost_reduction_pct: float  # e.g. 30% - 53%
    rationale: str


@dataclass(slots=True, frozen=True)
class HarnessCalibrationReport:
    """Comprehensive calibration assessment combining triage, prediction, and simulation."""

    recommendation: CalibrationRecommendation
    repatch_prediction: RepatchPredictionResult
    staging_simulation: ContextStagingSimulationResult | None = None
    summary_narrative: str = ""


class CodingHarnessCalibrator:
    """Calibrator engine mapping model capabilities and workloads to optimal harness settings."""

    @staticmethod
    def calibrate(
        model_name: str,
        parameter_billions: float,
        workload: WorkloadType,
        context_budget: int = 131072,
    ) -> CalibrationRecommendation:
        """Derive the optimal empirical harness configuration."""
        budget_cfg = HarnessBudgetConfig(usable_window=context_budget)

        # 1. Model Capability Triage
        if parameter_billions <= 40.0:
            mode = HarnessMode.SCAFFOLD
            enable_planning = True
            planning_role = "accuracy_scaffold"
            action_space = ActionSpaceType.PREDEFINED_TOOLS
        elif parameter_billions <= 150.0:
            mode = HarnessMode.BALANCED
            enable_planning = True
            planning_role = "balanced_guidance"
            action_space = (
                ActionSpaceType.BASH_ONLY
                if workload == WorkloadType.TERMINAL_CLI
                else ActionSpaceType.PREDEFINED_TOOLS
            )
        else:
            mode = HarnessMode.EFFICIENCY
            enable_planning = True
            planning_role = "stopping_point_controller"
            action_space = (
                ActionSpaceType.BASH_ONLY
                if workload in (WorkloadType.TERMINAL_CLI, WorkloadType.MIXED)
                else ActionSpaceType.PREDEFINED_TOOLS
            )

        # 2. Context Staging Invariant: Always recommend T4, deprecating M2 recall
        return CalibrationRecommendation(
            model_name=model_name,
            harness_mode=mode,
            action_space=action_space,
            context_tier=ContextTier.T4_STAGED,
            enable_planning=enable_planning,
            planning_role=planning_role,
            budget_config=budget_cfg,
            deprecation_flags=["m2_recoverable_recall_deprecated"],
        )

    @staticmethod
    def predict_repatch_efficiency(
        model_capability: str | float,
        action_space: ActionSpaceType | str,
        workload: WorkloadType | str,
    ) -> RepatchPredictionResult:
        """Predict re-patch churn and cost reductions using Fan et al. empirical laws."""
        # Normalize action space
        if isinstance(action_space, str):
            act_space = (
                ActionSpaceType.BASH_ONLY
                if "bash" in action_space.lower()
                else ActionSpaceType.PREDEFINED_TOOLS
            )
        else:
            act_space = action_space

        # Normalize workload
        if isinstance(workload, str):
            wl_str = workload.lower()
            if "cli" in wl_str or "terminal" in wl_str:
                wl = WorkloadType.TERMINAL_CLI
            elif "repo" in wl_str or "codebase" in wl_str:
                wl = WorkloadType.CODEBASE_REPO
            else:
                wl = WorkloadType.MIXED
        else:
            wl = workload

        # Normalize model capability scale
        if isinstance(model_capability, (int, float)):
            if model_capability <= 40.0:
                scale = "weak_30b"
            elif model_capability <= 150.0:
                scale = "mid_120b"
            else:
                scale = "strong_550b"
        else:
            cap_str = str(model_capability).lower()
            if "weak" in cap_str or "30b" in cap_str or "small" in cap_str:
                scale = "weak_30b"
            elif "mid" in cap_str or "120b" in cap_str:
                scale = "mid_120b"
            else:
                scale = "strong_550b"

        # Apply empirical predictions from Fan et al. (arXiv:2609.20804v1)
        if wl == WorkloadType.TERMINAL_CLI:
            if scale == "strong_550b":
                if act_space == ActionSpaceType.BASH_ONLY:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=1.5,
                        coarse_replace_ratio=0.76,
                        estimated_cost_reduction_pct=42.5,
                        rationale=(
                            "Bash-only action space on terminal workloads cuts mean re-patches from 4.6 down to 1.5, "
                            "shifts file writing to coarse create-or-replace actions (76%), and slashes execution cost by 30%-53%."
                        ),
                    )
                else:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=4.6,
                        coarse_replace_ratio=0.51,
                        estimated_cost_reduction_pct=0.0,
                        rationale=(
                            "Predefined tools on CLI tasks force unnecessary incremental micro-patches (4.6 mean re-patches) "
                            "and restrict composite command execution for strong models."
                        ),
                    )
            elif scale == "mid_120b":
                if act_space == ActionSpaceType.BASH_ONLY:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=2.1,
                        coarse_replace_ratio=0.70,
                        estimated_cost_reduction_pct=28.0,
                        rationale=(
                            "Mid-tier models achieve balanced execution gains with bash chaining on CLI workloads, "
                            "reducing turn churn without severe command syntax failure."
                        ),
                    )
                else:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=3.8,
                        coarse_replace_ratio=0.58,
                        estimated_cost_reduction_pct=5.0,
                        rationale="Predefined tools offer stable execution with moderate micro-patch overhead for mid-tier models.",
                    )
            else:  # weak_30b
                if act_space == ActionSpaceType.PREDEFINED_TOOLS:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=3.2,
                        coarse_replace_ratio=0.60,
                        estimated_cost_reduction_pct=12.0,
                        rationale=(
                            "Predefined typed tools protect weak models from shell syntax collapse, "
                            "boosting SWE-Bench success by +15.0%."
                        ),
                    )
                else:
                    return RepatchPredictionResult(
                        model_scale=scale,
                        workload=wl,
                        action_space=act_space,
                        predicted_mean_repatches=6.5,
                        coarse_replace_ratio=0.35,
                        estimated_cost_reduction_pct=-25.0,
                        rationale=(
                            "Bash-only action space triggers catastrophic interface syntax collapse on small/weak models, "
                            "inducing repetitive failing loops and negative efficiency."
                        ),
                    )
        else:  # CODEBASE_REPO or MIXED
            if act_space == ActionSpaceType.PREDEFINED_TOOLS:
                return RepatchPredictionResult(
                    model_scale=scale,
                    workload=wl,
                    action_space=act_space,
                    predicted_mean_repatches=1.8,
                    coarse_replace_ratio=0.72,
                    estimated_cost_reduction_pct=22.0,
                    rationale=(
                        "Structured file tools (read_file, edit_file) bound edit blast radiuses and eliminate localization "
                        "drift across multi-file codebases."
                    ),
                )
            else:
                return RepatchPredictionResult(
                    model_scale=scale,
                    workload=wl,
                    action_space=act_space,
                    predicted_mean_repatches=3.9,
                    coarse_replace_ratio=0.48,
                    estimated_cost_reduction_pct=-8.0,
                    rationale=(
                        "Bare shell on multi-file repositories creates unbounded grep/cat noise and loose diff tracking, "
                        "elevating localization churn."
                    ),
                )

    @staticmethod
    def simulate_context_staging(
        events: Sequence[ContextStagingEvent],
        usable_window: int = 131072,
        soft_ratio: float = 0.60,
        hard_ratio: float = 0.85,
        recent_ratio: float = 0.30,
        min_recent_turns: int = 2,
    ) -> ContextStagingSimulationResult:
        """Simulate the Two-Tier Context Staging Engine ($T_4$) over an event sequence."""
        budget_cfg = HarnessBudgetConfig(
            usable_window=usable_window,
            soft_threshold_ratio=soft_ratio,
            hard_threshold_ratio=hard_ratio,
            recent_window_ratio=recent_ratio,
            min_recent_turns=min_recent_turns,
        )

        b1_tokens = budget_cfg.b1_tokens
        b2_tokens = budget_cfg.b2_tokens

        initial_tokens = sum(e.token_count for e in events)
        staged_events: list[ContextStagingEvent] = list(events)
        elided_count = 0
        pruned_tokens = 0
        b1_triggered = False
        b2_triggered = False
        summary_text = ""

        # Identify max turn to pin recent window
        max_turn = max((e.turn for e in staged_events), default=0)
        recent_turn_cutoff = max(max_turn - min_recent_turns + 1, 1)

        current_tokens = initial_tokens

        # Stage 1: Check B1 (0.60) Soft Threshold -> M1 Rule-Based Elision
        if current_tokens >= b1_tokens:
            b1_triggered = True
            new_events: list[ContextStagingEvent] = []
            for ev in staged_events:
                # Is in middle region? (Not system preamble turn 0, and turn < recent_turn_cutoff)
                in_middle = ev.turn > 0 and ev.turn < recent_turn_cutoff
                is_bulky_obs = ev.is_bulky or (
                    ev.role == "tool_observation" and ev.token_count > 100
                )
                if in_middle and is_bulky_obs:
                    elided_count += 1
                    lines = len(ev.content.splitlines())
                    chars = len(ev.content)
                    stub_content = (
                        f"[tool output elided: {lines} lines / {chars} chars. "
                        "Re-read or re-run to get it again.]"
                    )
                    stub_tokens = max(len(stub_content) // 4, 15)
                    pruned_tokens += ev.token_count - stub_tokens
                    new_events.append(
                        ContextStagingEvent(
                            role=ev.role,
                            content=stub_content,
                            turn=ev.turn,
                            token_count=stub_tokens,
                            is_bulky=False,
                            tool_name=ev.tool_name,
                        )
                    )
                else:
                    new_events.append(ev)
            staged_events = new_events
            current_tokens = sum(e.token_count for e in staged_events)

        # Stage 2: Check B2 (0.85) Hard Threshold -> M3 Structured 7-Heading Summarization
        if current_tokens >= b2_tokens:
            b2_triggered = True
            summary_text = (
                "## Goal\nComplete calibrated autonomous task execution.\n\n"
                "## Files touched\n- src/harness/kernel/context.py\n- plugins/agent_orchestration/calibrator/main.py\n\n"
                "## Done\n- Triaged model capability and workload constraints\n- Applied M1 rule-based elision\n\n"
                "## Pending\n- Verify convergence and final milestone tests\n\n"
                "## Errors & fixes\n- Resolved context overflow via staged elision\n\n"
                "## Current state\n- Active staged context management with recent turns pinned\n\n"
                "## Next step\n- Execute final tool validation and truncate verification loop."
            )
            summary_tokens = len(summary_text) // 4

            # Summarize middle events into the single summary event
            preamble_events = [
                e for e in staged_events if e.turn == 0 or e.role == "system"
            ]
            recent_events = [
                e
                for e in staged_events
                if e.turn >= recent_turn_cutoff and e.role != "system"
            ]
            middle_events = [
                e
                for e in staged_events
                if e not in preamble_events and e not in recent_events
            ]

            middle_tokens_before = sum(e.token_count for e in middle_events)
            pruned_tokens += max(0, middle_tokens_before - summary_tokens)

            summary_event = ContextStagingEvent(
                role="system",
                content=f"<context-summary>\n{summary_text}\n</context-summary>",
                turn=recent_turn_cutoff - 1,
                token_count=summary_tokens,
                is_bulky=False,
                tool_name="context_summarizer",
            )

            staged_events = preamble_events + [summary_event] + recent_events
            current_tokens = sum(e.token_count for e in staged_events)

        return ContextStagingSimulationResult(
            usable_window=usable_window,
            initial_tokens=initial_tokens,
            final_tokens=current_tokens,
            b1_elision_triggered=b1_triggered,
            b2_summary_triggered=b2_triggered,
            elided_observations_count=elided_count,
            pruned_tokens_count=pruned_tokens,
            structured_summary=summary_text,
            events_after_staging=staged_events,
        )

    @classmethod
    def generate_calibration_report(
        cls,
        model_name: str,
        parameter_billions: float,
        workload: WorkloadType,
        context_budget: int = 131072,
        events: Sequence[ContextStagingEvent] | None = None,
    ) -> HarnessCalibrationReport:
        """Synthesize a complete calibration report including triage, repatch prediction, and staging."""
        rec = cls.calibrate(
            model_name=model_name,
            parameter_billions=parameter_billions,
            workload=workload,
            context_budget=context_budget,
        )
        repatch = cls.predict_repatch_efficiency(
            model_capability=parameter_billions,
            action_space=rec.action_space,
            workload=workload,
        )

        staging_sim: ContextStagingSimulationResult | None = None
        if events:
            staging_sim = cls.simulate_context_staging(
                events=events,
                usable_window=context_budget,
            )

        narrative = (
            f"Calibrated {model_name} ({parameter_billions}B) for {workload.value} workload. "
            f"Configured mode '{rec.harness_mode.value}' with action space '{rec.action_space.value}' "
            f"and context staging tier '{rec.context_tier.value}'. "
            f"Predicted mean re-patches per task: {repatch.predicted_mean_repatches} "
            f"with estimated cost savings of {repatch.estimated_cost_reduction_pct}%."
        )

        return HarnessCalibrationReport(
            recommendation=rec,
            repatch_prediction=repatch,
            staging_simulation=staging_sim,
            summary_narrative=narrative,
        )

    @classmethod
    def generate_visual_brief(
        cls,
        report_or_rec: HarnessCalibrationReport | CalibrationRecommendation,
        output_path: Path | str | None = None,
    ) -> Path:
        """Render an interactive HTML visual brief with Mermaid topology and scorecards."""
        if isinstance(report_or_rec, CalibrationRecommendation):
            rec = report_or_rec
            repatch = cls.predict_repatch_efficiency(
                model_capability=rec.model_name,
                action_space=rec.action_space,
                workload=WorkloadType.CODEBASE_REPO,
            )
            narrative = f"Empirical harness calibration for {rec.model_name}."
        else:
            rec = report_or_rec.recommendation
            repatch = report_or_rec.repatch_prediction
            narrative = report_or_rec.summary_narrative

        if output_path is None:
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
            out_file = (
                Path(tempfile.gettempdir())
                / f"coding-harness-calibrator-brief-{ts}.html"
            )
        else:
            out_file = Path(output_path).resolve()

        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Rule 51: Doubled braces in static HTML/CSS template
        html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coding Harness Calibrator &bull; Visual Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#0f172a',
        primaryColor: '#38bdf8',
        primaryTextColor: '#f8fafc',
        primaryBorderColor: '#0284c7',
        lineColor: '#94a3b8'
      }}
    }});
  </script>
  <style>
    body {{
      background-color: #0b0f19;
      color: #f1f5f9;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .gradient-text {{
      background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .glass-box {{
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(51, 65, 85, 0.6);
    }}
  </style>
</head>
<body class="p-6 md:p-12 max-w-7xl mx-auto">

  <header class="mb-10 pb-6 border-b border-slate-800">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <span class="px-3 py-1 text-xs font-semibold rounded-full bg-sky-950 text-sky-400 border border-sky-800">
          Fan et al. arXiv:2609.20804v1 Calibrator
        </span>
        <h1 class="text-4xl font-black mt-3 mb-2 gradient-text">
          {rec.model_name} &bull; Harness Configuration
        </h1>
        <p class="text-slate-400 text-sm max-w-3xl">
          {narrative}
        </p>
      </div>
      <div class="text-right text-xs text-slate-500 font-mono">
        <div>Mode: <span class="text-sky-400 font-bold">{rec.harness_mode.value.upper()}</span></div>
        <div>Action Space: <span class="text-indigo-400 font-bold">{rec.action_space.value}</span></div>
        <div>Context Tier: <span class="text-emerald-400 font-bold">{rec.context_tier.value}</span></div>
      </div>
    </div>
  </header>

  <!-- Section: 5-Stage Closed-Loop Progression -->
  <section class="mb-12">
    <h2 class="text-2xl font-bold mb-6 text-slate-100">1. The 5-Stage Closed-Loop Calibration Topology</h2>
    <div class="glass-box rounded-xl p-6">
      <pre class="mermaid text-xs">
flowchart LR
    S1["1. Capability & Workload Triage<br/><b>Mode: {rec.harness_mode.value.upper()}</b>"]
    S2["2. Action Space Calibration<br/><b>Interface: {rec.action_space.value}</b>"]
    S3["3. Two-Tier Context Staging<br/><b>B1: {rec.budget_config.b1_tokens} / B2: {rec.budget_config.b2_tokens}</b>"]
    S4["4. In-Flight Safeguards<br/><b>Streak 5 Warn / Streak 8 Kill</b>"]
    S5["5. Trajectory Stopping<br/><b>Role: {rec.planning_role}</b>"]

    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5

    style S1 fill:#0284c7,stroke:#38bdf8
    style S2 fill:#1e1b4b,stroke:#818cf8
    style S3 fill:#064e3b,stroke:#10b981
    style S4 fill:#701a75,stroke:#e879f9
    style S5 fill:#0f172a,stroke:#64748b
      </pre>
    </div>
  </section>

  <!-- Section: Empirical Prediction Scorecards -->
  <section class="mb-12">
    <h2 class="text-2xl font-bold mb-6 text-slate-100">2. Empirical Prediction Scorecard (Fan et al.)</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <div class="glass-box rounded-xl p-6 border-l-4 border-l-sky-500">
        <div class="text-xs text-slate-400 font-mono mb-1 uppercase">Predicted Mean Re-patches</div>
        <div class="text-3xl font-black text-sky-400 mb-2">{repatch.predicted_mean_repatches}</div>
        <div class="text-xs text-slate-300">Bounded re-patch churn per task (target &le; 2.0 for capable models).</div>
      </div>

      <div class="glass-box rounded-xl p-6 border-l-4 border-l-emerald-500">
        <div class="text-xs text-slate-400 font-mono mb-1 uppercase">Coarse Action Ratio</div>
        <div class="text-3xl font-black text-emerald-400 mb-2">{int(repatch.coarse_replace_ratio * 100)}%</div>
        <div class="text-xs text-slate-300">Shifts fine-grained line micro-patches toward coarse replace actions.</div>
      </div>

      <div class="glass-box rounded-xl p-6 border-l-4 border-l-indigo-500">
        <div class="text-xs text-slate-400 font-mono mb-1 uppercase">Estimated Cost Reduction</div>
        <div class="text-3xl font-black text-indigo-400 mb-2">{repatch.estimated_cost_reduction_pct}%</div>
        <div class="text-xs text-slate-300">Overall token expenditure savings versus unmanaged baseline.</div>
      </div>

    </div>
  </section>

  <!-- Section: Staging & Deprecation Notes -->
  <section class="mb-12">
    <h2 class="text-2xl font-bold mb-6 text-slate-100">3. Context Staging Budget &amp; Invariants</h2>
    <div class="glass-box rounded-xl p-6 space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-slate-400">Total Usable Context:</span>
          <span class="font-mono text-white font-bold ml-2">{rec.budget_config.usable_window:,} tokens</span>
        </div>
        <div>
          <span class="text-slate-400">Soft Threshold B1 (0.60):</span>
          <span class="font-mono text-sky-400 font-bold ml-2">{rec.budget_config.b1_tokens:,} tokens (M1 Elision)</span>
        </div>
        <div>
          <span class="text-slate-400">Hard Threshold B2 (0.85):</span>
          <span class="font-mono text-amber-400 font-bold ml-2">{rec.budget_config.b2_tokens:,} tokens (M3 Summary)</span>
        </div>
        <div>
          <span class="text-slate-400">Recent Verbatim Window:</span>
          <span class="font-mono text-emerald-400 font-bold ml-2">30% (Floor: &ge; {rec.budget_config.min_recent_turns} turns)</span>
        </div>
      </div>
      <div class="p-4 bg-slate-900/80 rounded-lg border border-slate-800 text-xs text-slate-300">
        <strong class="text-red-400 font-bold uppercase">Dead Machinery Deprecation Invariant:</strong>
        <p class="mt-1">
          Flags: <code class="text-amber-300">{", ".join(rec.deprecation_flags)}</code>.
          Recoverable elision machinery (M2 recall_event) is deprecated and discarded: Fan et al. proved models invoke recall in &lt;0.1% of turns with zero accuracy gain.
        </p>
      </div>
    </div>
  </section>

  <footer class="pt-6 border-t border-slate-800 text-xs text-slate-500 flex justify-between">
    <div>Coding Harness Calibrator &bull; Fan et al. Empirical Laws</div>
    <div class="font-mono">{out_file.name}</div>
  </footer>

</body>
</html>
"""
        out_file.write_text(html, encoding="utf-8")
        return out_file


@dataclass(slots=True)
class StuckDetector:
    """Sliding streak detector for repeated identical or failing tool actions."""

    warn_threshold: int = 5
    kill_threshold: int = 8
    _last_tool: str = ""
    _last_args_sig: str = ""
    _streak_length: int = 0
    _consecutive_failures: int = 0

    def record_call(
        self, tool_name: str, args_sig: str, is_failure: bool
    ) -> tuple[str, bool]:
        """Record a tool execution and return (action_instruction, should_terminate).

        Returns:
            ("none" | "inject_warning_reminder" | "terminate_stuck_failures", should_terminate: bool)
        """
        if tool_name == self._last_tool and args_sig == self._last_args_sig:
            self._streak_length += 1
            if is_failure:
                self._consecutive_failures += 1
            else:
                self._consecutive_failures = 0
        else:
            self._last_tool = tool_name
            self._last_args_sig = args_sig
            self._streak_length = 1
            self._consecutive_failures = 1 if is_failure else 0

        # Check hard kill threshold
        if self._consecutive_failures >= self.kill_threshold:
            return ("terminate_stuck_failures", True)

        # Check warn threshold
        if self._streak_length == self.warn_threshold:
            return ("inject_warning_reminder", False)

        return ("none", False)

    def reset(self) -> None:
        """Reset streak counters."""
        self._last_tool = ""
        self._last_args_sig = ""
        self._streak_length = 0
        self._consecutive_failures = 0
