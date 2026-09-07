"""The 60 Canonical Patterns Capability Profiler & Invariant Validator.

Distilled from Part II and Part III of 'The AI Agent Engineer\'s Guide' by Vahe Aslanyan.
Formulates a 1-page capability contract across the 8 Capabilities and enforces
architectural composition invariants (tool sprawl, mutation gating, corrigibility).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class PatternDefinition:
    """Canonical pattern definition from the 60-pattern catalog."""

    number: int
    name: str
    capability: str
    tagline: str


@dataclass(slots=True, frozen=True)
class CapabilityProfile:
    """Declared capability contract for a proposed agent architecture."""

    agent_name: str
    target_level: int
    declared_patterns: list[int]
    tools_count: int = 0
    has_external_mutations: bool = False
    estimated_session_steps: int = 1
    is_multi_agent: bool = False


@dataclass(slots=True, frozen=True)
class ProfileValidationFinding:
    """Diagnostic finding produced during capability profile inspection."""

    rule_name: str
    passed: bool
    severity: str  # "ERROR", "WARNING", "INFO"
    message: str


@dataclass(slots=True, frozen=True)
class ProfileValidationReport:
    """Consolidated validation report for a capability profile."""

    agent_name: str
    valid: bool
    findings: list[ProfileValidationFinding]
    capability_counts: dict[str, int]


class CapabilityProfiler:
    """Catalog and invariant validator for the 60 canonical agent patterns."""

    PATTERNS_CATALOG: dict[int, PatternDefinition] = {
        # 1. Perception (1-7)
        1: PatternDefinition(1, "Multimodal Grounding", "Perception", "Aligns linguistic references to visual/audio referents"),
        2: PatternDefinition(2, "Document Layout", "Perception", "Turns PDFs into typed region trees"),
        3: PatternDefinition(3, "Temporal Sensor-Fusion", "Perception", "Aligns asynchronous streams onto one timeline"),
        4: PatternDefinition(4, "Anomaly-Spotter", "Perception", "Surfaces deviations from expected patterns"),
        5: PatternDefinition(5, "Visual Question Decomposition", "Perception", "Breaks compound visual queries into sub-queries"),
        6: PatternDefinition(6, "Ambient Context", "Perception", "Passively integrates environmental signals"),
        7: PatternDefinition(7, "Schema-Inference", "Perception", "Discovers the structure of an unknown data source"),
        # 2. Reasoning (8-15)
        8: PatternDefinition(8, "Chain-of-Thought Auditor", "Reasoning", "Verifies each step in a reasoning trace"),
        9: PatternDefinition(9, "Counterfactual Reasoner", "Reasoning", "Runs 'what-if' branches against current state"),
        10: PatternDefinition(10, "Analogical Mapping", "Reasoning", "Finds structural parallels to prior cases"),
        11: PatternDefinition(11, "Constraint-Satisfaction", "Reasoning", "Narrows the feasible region with a real solver"),
        12: PatternDefinition(12, "Causal Graph Builder", "Reasoning", "Induces causal structure for intervention reasoning"),
        13: PatternDefinition(13, "Symbolic-Neural Bridge", "Reasoning", "Translates problems to formal expressions and back"),
        14: PatternDefinition(14, "Probabilistic Belief Updater", "Reasoning", "Maintains and revises posterior beliefs"),
        15: PatternDefinition(15, "Self-Consistency Voter", "Reasoning", "Runs N chains and aggregates by majority"),
        # 3. Planning (16-22)
        16: PatternDefinition(16, "Hierarchical Decomposer", "Planning", "Breaks goals into recursive subgoal trees"),
        17: PatternDefinition(17, "ReAct Loop", "Planning", "Interleaves reasoning and action with bounds"),
        18: PatternDefinition(18, "Tree-of-Thought Explorer", "Planning", "Branches and prunes a search tree of plans"),
        19: PatternDefinition(19, "Plan-Then-Execute", "Planning", "Plans upfront, executes under monitoring"),
        20: PatternDefinition(20, "Adaptive Replanner", "Planning", "Rebuilds the plan on detected deviation"),
        21: PatternDefinition(21, "Resource-Aware Scheduler", "Planning", "Plans under compute/time/budget constraints"),
        22: PatternDefinition(22, "Backward Goal-Regression", "Planning", "Plans from goal state backward"),
        # 4. Memory (23-29)
        23: PatternDefinition(23, "Episodic Buffer", "Memory", "Stores time-and-actor-indexed events"),
        24: PatternDefinition(24, "Semantic Memory Curator", "Memory", "Distills episodes into stable facts"),
        25: PatternDefinition(25, "Working-Memory Manager", "Memory", "Reshapes context per step"),
        26: PatternDefinition(26, "Forgetting-Policy", "Memory", "Prunes memory by relevance decay"),
        27: PatternDefinition(27, "Memory-of-Self", "Memory", "Maintains a self-model of capabilities"),
        28: PatternDefinition(28, "Vector-Store Curator", "Memory", "Maintains embedding store quality over time"),
        29: PatternDefinition(29, "Persistent Identity", "Memory", "Resolves identity across surfaces and sessions"),
        # 5. Tool Use (30-37)
        30: PatternDefinition(30, "Tool Selector", "Tool Use", "Picks from a large registry without prompt bloat"),
        31: PatternDefinition(31, "API-Schema Adapter", "Tool Use", "Derives tools from OpenAPI at runtime"),
        32: PatternDefinition(32, "Code-Execution Sandbox", "Tool Use", "Runs model code in isolation"),
        33: PatternDefinition(33, "Shell-Operator", "Tool Use", "Drives a shell with safety and rollback"),
        34: PatternDefinition(34, "Browser-Driver", "Tool Use", "Navigates web UIs via accessibility trees"),
        35: PatternDefinition(35, "DB Query Synthesizer", "Tool Use", "Translates intent to SQL with safety checks"),
        36: PatternDefinition(36, "File-System Curator", "Tool Use", "Maintains a directory as a living asset"),
        37: PatternDefinition(37, "Side-Effect Auditor", "Tool Use", "Records every side effect with rollback"),
        # 6. Coordination (38-45)
        38: PatternDefinition(38, "Router/Dispatcher", "Coordination", "Routes tasks to specialist agents"),
        39: PatternDefinition(39, "Debate Moderator", "Coordination", "Adversarial debate between reasoners"),
        40: PatternDefinition(40, "Consensus-Builder", "Coordination", "Aggregates heterogeneous outputs"),
        41: PatternDefinition(41, "Pipeline Orchestrator", "Coordination", "Sequences agents into producer-consumer chains"),
        42: PatternDefinition(42, "Human-in-the-Loop Liaison", "Coordination", "Structured human-in-the-loop integration"),
        43: PatternDefinition(43, "Negotiation", "Coordination", "Inter-principal bargaining with utility functions"),
        44: PatternDefinition(44, "Auctioneer", "Coordination", "Market mechanism for task allocation"),
        45: PatternDefinition(45, "Supervisor-Worker", "Coordination", "Manages a pool of identical workers"),
        # 7. Learning (46-52)
        46: PatternDefinition(46, "Feedback Loop", "Learning", "Accumulates user corrections"),
        47: PatternDefinition(47, "Reflection", "Learning", "Self-critique and revise before delivery"),
        48: PatternDefinition(48, "Skill-Library Builder", "Learning", "Saves successful procedures as reusable skills"),
        49: PatternDefinition(49, "Curriculum Designer", "Learning", "Sequences experience for accelerated growth"),
        50: PatternDefinition(50, "Few-Shot Prompt Tuner", "Learning", "Dynamic example selection per call"),
        51: PatternDefinition(51, "Distillation", "Learning", "Compresses teacher into student"),
        52: PatternDefinition(52, "Active Learner", "Learning", "Picks high-value cases for human labeling"),
        # 8. Alignment (53-60)
        53: PatternDefinition(53, "Constitution-Bound", "Alignment", "Per-action structural rule enforcement"),
        54: PatternDefinition(54, "Refusal Calibrator", "Alignment", "Measured refusal behavior"),
        55: PatternDefinition(55, "Provenance Tracker", "Alignment", "Citations on every load-bearing claim"),
        56: PatternDefinition(56, "Red-Team Auditor", "Alignment", "Continuous adversarial evaluation"),
        57: PatternDefinition(57, "Privacy-Preserving", "Alignment", "Minimization and de-identification at boundaries"),
        58: PatternDefinition(58, "Explainer", "Alignment", "Honest post-hoc decision rationales"),
        59: PatternDefinition(59, "Drift Detector", "Alignment", "Monitors input/output distribution shift"),
        60: PatternDefinition(60, "Off-Switch-Compatible", "Alignment", "Graceful human override at any point"),
    }

    @classmethod
    def validate_profile(cls, profile: CapabilityProfile, config: dict[str, Any] | None = None) -> ProfileValidationReport:
        """Assert architectural invariants on a proposed capability profile."""
        findings: list[ProfileValidationFinding] = []
        p_set = set(profile.declared_patterns)

        # Count patterns per capability
        cap_counts: dict[str, int] = {
            "Perception": 0, "Reasoning": 0, "Planning": 0, "Memory": 0,
            "Tool Use": 0, "Coordination": 0, "Learning": 0, "Alignment": 0
        }
        for p_num in profile.declared_patterns:
            pat = cls.PATTERNS_CATALOG.get(p_num)
            if pat:
                cap_counts[pat.capability] += 1

        # Invariant 1: Valid pattern IDs (1-60)
        invalid_ids = [p for p in profile.declared_patterns if p not in cls.PATTERNS_CATALOG]
        if invalid_ids:
            findings.append(ProfileValidationFinding(
                "ValidPatternNumbers", False, "ERROR", f"Invalid pattern numbers declared: {invalid_ids}"
            ))
        else:
            findings.append(ProfileValidationFinding(
                "ValidPatternNumbers", True, "INFO", f"All {len(profile.declared_patterns)} declared patterns recognized."
            ))

        # Invariant 2: Tool Sprawl without Selector (Rule: >15 tools requires Pattern 30)
        if profile.tools_count > 15 and 30 not in p_set:
            findings.append(ProfileValidationFinding(
                "ToolSprawlSelector", False, "ERROR",
                f"Agent declares {profile.tools_count} tools (>15) but lacks Pattern 30 (Tool Selector). Risk of prompt bloat."
            ))
        else:
            findings.append(ProfileValidationFinding("ToolSprawlSelector", True, "INFO", "Tool registry budget within safe limits."))

        # Invariant 3: Consequential Mutation Gating (Rule: Mutations require Pat 53 Constitution and Pat 37 Side-Effect Auditor)
        if profile.has_external_mutations:
            has_c = 53 in p_set
            has_a = 37 in p_set
            if not has_c or not has_a:
                findings.append(ProfileValidationFinding(
                    "ConsequentialMutationGuard", False, "ERROR",
                    "Agent performs external state mutations but lacks Pattern 53 (Constitution-Bound) "
                    "or Pattern 37 (Side-Effect Auditor) for transactional rollback."
                ))
            else:
                findings.append(ProfileValidationFinding("ConsequentialMutationGuard", True, "INFO", "Mutation gating verified with Constitution and Auditor."))

        # Invariant 4: Autonomy Corrigibility (Rule: Level 4 mandates Pattern 60 Off-Switch)
        if profile.target_level == 4:
            if 60 not in p_set:
                findings.append(ProfileValidationFinding(
                    "OffSwitchMandatory", False, "ERROR",
                    "Level 4 Full Agent strictly mandates Pattern 60 (Off-Switch-Compatible) for operator override."
                ))
            else:
                findings.append(ProfileValidationFinding("OffSwitchMandatory", True, "INFO", "Pattern 60 (Off-Switch) confirmed for Level 4 autonomy."))

        # Invariant 5: Long Horizon Memory Management (Rule: Steps > 15 requires Pat 25 Working-Memory Manager)
        if profile.estimated_session_steps > 15 and 25 not in p_set:
            findings.append(ProfileValidationFinding(
                "WorkingMemoryCompaction", False, "WARNING",
                f"Session estimated at {profile.estimated_session_steps} steps (>15) but lacks Pattern 25 (Working-Memory Manager). Risk of context exhaustion."
            ))

        # Invariant 6: Multi-Agent Skepticism (Rule: Multi-agent coordination requires at least one coordination pattern)
        if profile.is_multi_agent and cap_counts["Coordination"] == 0:
            findings.append(ProfileValidationFinding(
                "CoordinationPatternPresent", False, "ERROR",
                "Agent declared as multi-agent swarm but declares zero Coordination patterns (38-45)."
            ))

        is_valid = not any(f.severity == "ERROR" and not f.passed for f in findings)

        return ProfileValidationReport(
            agent_name=profile.agent_name,
            valid=is_valid,
            findings=findings,
            capability_counts=cap_counts,
        )
