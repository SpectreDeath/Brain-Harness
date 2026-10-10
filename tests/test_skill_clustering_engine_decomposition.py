"""Contract test suite for decomposed harness.services.skill_clustering.engine package.

Verifies:
1. Subpackage exports, module layout, and strict Rule 11 line count bounds (< 200 lines).
2. Tokenization and keyword filtering.
3. Affinity matrix calculation with degree damping.
4. Community detection and SkillCluster construction.
5. Emergent capability discovery and synthesis.
6. Cross-cluster bridge detection.
7. Intent scoring and candidate selection.
8. Topological execution planning and verifier injection.
9. Single-seam resolver factory per Rule 58.
"""

from __future__ import annotations

import pathlib
from typing import Any
import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_clustering.engine import (
    SkillClusteringEngine,
    cluster_skills,
    compute_affinity_matrix,
    detect_cross_cluster_bridges,
    discover_emergent_capabilities,
    resolve_skill_clustering_engine,
    score_skills_for_task,
    select_skills_for_task,
    tokenize,
)
from harness.services.skill_clustering.engine.affinity import compute_affinity_matrix as raw_affinity_fn
from harness.services.skill_clustering.engine.bridges import detect_cross_cluster_bridges as raw_bridges_fn
from harness.services.skill_clustering.engine.clusterer import cluster_skills as raw_cluster_fn
from harness.services.skill_clustering.engine.emergent import (
    discover_emergent_capabilities as raw_discover_fn,
    synthesize_cluster_capabilities,
)
from harness.services.skill_clustering.engine.planner import select_skills_for_task as raw_planner_fn
from harness.services.skill_clustering.engine.resolvers import resolve_skill_clustering_engine as raw_resolver_fn
from harness.services.skill_clustering.engine.scoring import (
    resolve_candidates_and_prereqs,
    score_skills_for_task as raw_scoring_fn,
)
from harness.services.skill_clustering.engine.tokens import tokenize as raw_tokenize_fn
from harness.services.skill_clustering.models import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)


class MockSkillNode:
    """Mock skill node for clustering and planning verification."""

    def __init__(
        self,
        name: str,
        category: str = "general",
        description: str = "",
        target: str = "",
        triggers: list[str] | None = None,
        dependencies: list[str] | None = None,
        references: list[str] | None = None,
        anti_patterns: list[Any] | None = None,
        invariants: list[Any] | None = None,
        stages: list[Any] | None = None,
    ) -> None:
        self.name = name
        self.category = category
        self.description = description
        self.target = target
        self.triggers = triggers or []
        self.dependencies = dependencies or []
        self.references = references or []
        self.anti_patterns = anti_patterns or []
        self.invariants = invariants or []
        self.stages = stages or []


@pytest.fixture
def sample_skills_fixture() -> dict[str, MockSkillNode]:
    """Provide a coherent sample skill graph for domain testing."""
    return {
        "deepen-architecture": MockSkillNode(
            "deepen-architecture",
            category="architecture",
            description="Run iterative architecture deepening loop and eliminate shallow modules.",
            target="Clean architecture seams and deep modules",
            triggers=["deepen architecture", "modularize"],
            dependencies=["adversarial-agent-verifier"],
        ),
        "adversarial-agent-verifier": MockSkillNode(
            "adversarial-agent-verifier",
            category="architecture",
            description="Execute rigorous runtime verification, inspect-before-edit protocols.",
            target="Strict invariant verification and regression test contracts",
            triggers=["verify", "test contracts", "adversarial review"],
        ),
        "codebase-context-architect": MockSkillNode(
            "codebase-context-architect",
            category="context",
            description="Govern multi-layer codebase context files and eliminate context rot.",
            target="Three-layer context boundaries and synchronized manifests",
            triggers=["context govern", "agents.md", "claude.md"],
            dependencies=["deepen-architecture"],
        ),
        "context-anti-rot-sync": MockSkillNode(
            "context-anti-rot-sync",
            category="context",
            description="Audit, prune, and synchronize context instructions.",
            target="Single-source instructions and Rule 11 bounds",
            triggers=["anti-rot", "context sync"],
            dependencies=["codebase-context-architect"],
        ),
    }


def test_engine_subpackage_line_bounds() -> None:
    """Assert all submodules in engine subpackage are strictly < 200 lines (Rule 11)."""
    engine_dir = pathlib.Path(__file__).parent.parent / "src" / "harness" / "services" / "skill_clustering" / "engine"
    assert engine_dir.is_dir(), f"Engine directory missing: {engine_dir}"

    py_files = list(engine_dir.glob("*.py"))
    assert len(py_files) >= 9, f"Expected at least 9 submodules, found {len(py_files)}"

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines < 200, f"Module {py_file.name} has {lines} lines, exceeding 200 line bound (Rule 11)"


def test_engine_subpackage_exports() -> None:
    """Verify package public exports and types."""
    import harness.services.skill_clustering.engine as pkg

    assert hasattr(pkg, "SkillClusteringEngine")
    assert hasattr(pkg, "compute_affinity_matrix")
    assert hasattr(pkg, "cluster_skills")
    assert hasattr(pkg, "discover_emergent_capabilities")
    assert hasattr(pkg, "detect_cross_cluster_bridges")
    assert hasattr(pkg, "select_skills_for_task")
    assert hasattr(pkg, "resolve_skill_clustering_engine")
    assert hasattr(pkg, "tokenize")


def test_tokenization_and_filtering() -> None:
    """Verify tokenize correctly strips stopwords and extracts tokens."""
    text = "The user will deepen the architecture with strict verification across each module"
    tokens = raw_tokenize_fn(text)
    assert "deepen" in tokens
    assert "architecture" in tokens
    assert "strict" in tokens
    assert "verification" in tokens
    assert "module" in tokens
    # Stopwords filtered
    assert "the" not in tokens
    assert "user" not in tokens
    assert "with" not in tokens
    assert "across" not in tokens


def test_affinity_matrix_computation(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify affinity matrix computation with degree damping and structural alignment."""
    adj = raw_affinity_fn(sample_skills_fixture)
    assert isinstance(adj, dict)

    # deepen-architecture and adversarial-agent-verifier share architecture category and dependency
    assert "deepen-architecture" in adj
    assert "adversarial-agent-verifier" in adj["deepen-architecture"]
    weight = adj["deepen-architecture"]["adversarial-agent-verifier"]
    assert weight >= 1.6


def test_community_clustering(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify cluster_skills groups skills into coherent functional clusters."""
    adj = raw_affinity_fn(sample_skills_fixture)
    clusters = raw_cluster_fn(sample_skills_fixture, adj, min_cluster_size=2)

    assert len(clusters) >= 1
    for c in clusters:
        assert isinstance(c, SkillCluster)
        assert len(c.skills) >= 2
        assert c.central_hub_skill in c.skills
        assert 0.0 <= c.cohesion_score <= 1.0


def test_emergent_capabilities_discovery(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify emergent capability synthesis and search filtering."""
    adj = raw_affinity_fn(sample_skills_fixture)
    clusters = raw_cluster_fn(sample_skills_fixture, adj, min_cluster_size=2)
    caps = raw_discover_fn(sample_skills_fixture, clusters)

    assert isinstance(caps, list)
    for cap in caps:
        assert isinstance(cap, EmergentCapability)
        assert cap.title
        assert cap.id

    # Filtered search
    filtered = raw_discover_fn(sample_skills_fixture, clusters, query="architecture deepening")
    assert isinstance(filtered, list)


def test_cross_cluster_bridge_detection(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify detect_cross_cluster_bridges finds directed dependencies between clusters."""
    adj = raw_affinity_fn(sample_skills_fixture)
    clusters = raw_cluster_fn(sample_skills_fixture, adj, min_cluster_size=2)
    bridges = raw_bridges_fn(sample_skills_fixture, clusters)

    assert isinstance(bridges, list)
    for b in bridges:
        assert isinstance(b, CrossClusterBridge)
        assert b.source_cluster != b.target_cluster


def test_scoring_and_candidate_resolution(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify score_skills_for_task and resolve_candidates_and_prereqs."""
    task = "deepen architecture and verify seams"
    toks = raw_tokenize_fn(task)
    scores = raw_scoring_fn(sample_skills_fixture, None, task, toks)

    assert len(scores) > 0
    top_skill = scores[0][1]
    assert top_skill in ("deepen-architecture", "adversarial-agent-verifier")

    selected, prereqs, domain = resolve_candidates_and_prereqs(
        sample_skills_fixture, scores, None, max_skills=3
    )
    assert len(selected) > 0
    assert "deepen-architecture" in selected or "adversarial-agent-verifier" in selected


def test_planning_pipeline_and_verifier_injection(sample_skills_fixture: dict[str, MockSkillNode]) -> None:
    """Verify select_skills_for_task builds a DAG sorted plan with tail verifier."""
    plan = raw_planner_fn(
        sample_skills_fixture,
        None,
        task="deepen architecture and verify changes",
        max_skills=3,
        include_verifier=True,
    )

    assert isinstance(plan, SkillSelectionPlan)
    assert len(plan.execution_pipeline) > 0
    # Verifier injected at tail
    assert plan.execution_pipeline[-1] == "adversarial-agent-verifier"
    assert plan.recommended_verifier == "adversarial-agent-verifier"
    assert 0.0 < plan.confidence <= 1.0
    assert plan.rationale != ""


def test_single_seam_resolver_contract() -> None:
    """Verify resolve_skill_clustering_engine adheres to Rule 58 single seam."""
    ctx = ServiceContext()

    resolved_1 = resolve_skill_clustering_engine(ctx)
    assert isinstance(resolved_1, SkillClusteringEngine)

    # Resolution with existing engine instance
    resolved_2 = resolve_skill_clustering_engine(resolved_1)
    assert resolved_2 is resolved_1

    # Raw resolver function directly
    resolved_3 = raw_resolver_fn(None)
    assert isinstance(resolved_3, SkillClusteringEngine)
