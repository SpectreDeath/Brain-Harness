"""Comprehensive unit and contract tests for skill_clustering package decomposition.

Verifies:
1. Isolated submodule imports (models, patterns, visualizer, engine, service, __init__).
2. Backward compatibility of all public symbols exported from harness.services.skill_clustering.
3. Standalone DefaultSkillClusteringService operations without requiring external registry.
4. Single-seam resolver resolve_skill_clustering with and without IoC context (Rule 58).
5. Model validation, topological planning, and Mermaid generation.
"""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_skill_clustering_submodule_isolated_imports() -> None:
    """Verify that each decomposed submodule can be imported independently."""
    from harness.services.skill_clustering.models import (
        CrossClusterBridge,
        EmergentCapability,
        SkillCluster,
        SkillSelectionPlan,
    )
    from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS
    from harness.services.skill_clustering.visualizer import generate_clustered_mermaid
    from harness.services.skill_clustering.engine import SkillClusteringEngine
    from harness.services.skill_clustering.service import (
        DefaultSkillClusteringService,
        SkillClusteringService,
    )

    assert EmergentCapability is not None
    assert SkillCluster is not None
    assert CrossClusterBridge is not None
    assert SkillSelectionPlan is not None
    assert len(CANONICAL_EMERGENT_PATTERNS) >= 10
    assert callable(generate_clustered_mermaid)
    assert SkillClusteringEngine is not None
    assert issubclass(DefaultSkillClusteringService, SkillClusteringService)


@pytest.mark.unit
def test_skill_clustering_backward_compatible_re_exports() -> None:
    """Verify harness.services.skill_clustering exports all canonical symbols seamlessly."""
    import harness.services.skill_clustering as sc

    expected_symbols = [
        "CrossClusterBridge",
        "DefaultSkillClusteringService",
        "EmergentCapability",
        "SKILL_CLUSTERING_KEY",
        "SkillCluster",
        "SkillClusteringEngine",
        "SkillClusteringService",
        "SkillSelectionPlan",
        "generate_clustered_mermaid",
        "resolve_skill_clustering",
    ]

    for sym in expected_symbols:
        assert hasattr(sc, sym), f"Missing symbol in facade: {sym}"


@pytest.mark.unit
def test_default_skill_clustering_service_standalone() -> None:
    """Verify DefaultSkillClusteringService operates standalone with mock or empty skills."""
    from harness.services.skill_clustering import (
        DefaultSkillClusteringService,
        SkillClusteringService,
    )

    service = DefaultSkillClusteringService()
    assert isinstance(service, SkillClusteringService)

    # Calling methods without crashing
    clusters = service.cluster_skills(min_cluster_size=2)
    assert isinstance(clusters, list)

    capabilities = service.discover_emergent_capabilities()
    assert isinstance(capabilities, list)

    bridges = service.get_cross_cluster_bridges()
    assert isinstance(bridges, list)

    plan = service.select_skills_for_task("Inspect codebase and modernize architecture", max_skills=3)
    assert plan is not None
    assert plan.task == "Inspect codebase and modernize architecture"


@pytest.mark.unit
def test_resolve_skill_clustering_without_context() -> None:
    """Verify resolve_skill_clustering defaults safely to DefaultSkillClusteringService (Rule 58)."""
    from harness.services.skill_clustering import (
        DefaultSkillClusteringService,
        SkillClusteringService,
        resolve_skill_clustering,
    )

    svc = resolve_skill_clustering(None)
    assert isinstance(svc, SkillClusteringService)
    assert isinstance(svc, DefaultSkillClusteringService)


@pytest.mark.unit
def test_resolve_skill_clustering_from_ioc_context() -> None:
    """Verify resolve_skill_clustering extracts registered service from IoC container (Rule 58)."""
    from harness.services.skill_clustering import (
        SKILL_CLUSTERING_KEY,
        DefaultSkillClusteringService,
        resolve_skill_clustering,
    )

    ctx = ServiceContext()
    custom_svc = DefaultSkillClusteringService()
    ctx.provide(SKILL_CLUSTERING_KEY, custom_svc)

    resolved = resolve_skill_clustering(ctx)
    assert resolved is custom_svc


@pytest.mark.unit
def test_visualizer_mermaid_generation() -> None:
    """Verify generate_clustered_mermaid creates well-formed dark-mode Mermaid DAG."""
    from harness.services.skill_clustering.models import CrossClusterBridge, SkillCluster
    from harness.services.skill_clustering.visualizer import generate_clustered_mermaid

    # Test empty
    empty_mermaid = generate_clustered_mermaid([])
    assert "graph TD" in empty_mermaid
    assert "emptyRoot" in empty_mermaid

    # Test populated
    c1 = SkillCluster(
        cluster_id="cluster_01_repo",
        name="Repo Tools",
        domain="engineering",
        skills=["repo-reader", "repo-to-plugin-forge"],
        central_hub_skill="repo-reader",
        categories=["engineering"],
        internal_edge_count=1,
        cohesion_score=0.8,
    )
    b1 = CrossClusterBridge(
        source_cluster="cluster_01_repo",
        target_cluster="cluster_02_other",
        bridge_skills=[("repo-reader", "other-skill")],
        synergy_description="Connects repo tools to others",
    )
    mermaid = generate_clustered_mermaid([c1], [b1])
    assert "graph TD" in mermaid
    assert "cluster_01_repo" in mermaid
    assert "repo-reader" in mermaid
