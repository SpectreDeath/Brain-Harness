"""Characterization test suite for the decomposed Skill Graph architecture.

Verifies:
1. Isolated submodule importability (models, protocols, guard, card_parser, indexer, routing, service).
2. Backward-compatible package re-exports from harness.services.skill_graph.
3. AST Guard, Indexer, Routing, and Registry service functionality.
"""

from __future__ import annotations

import ast
import pytest
from pathlib import Path

from harness.kernel.context import ServiceContext


def test_submodule_isolated_imports() -> None:
    """Verify each decomposed submodule can be imported in isolation."""
    from harness.services.skill_graph import models
    from harness.services.skill_graph import protocols
    from harness.services.skill_graph import guard
    from harness.services.skill_graph import card_parser
    from harness.services.skill_graph import indexer
    from harness.services.skill_graph import routing
    from harness.services.skill_graph import scanner
    from harness.services.skill_graph import topology
    from harness.services.skill_graph import intent
    from harness.services.skill_graph import guidance
    from harness.services.skill_graph import adapter
    from harness.services.skill_graph import plugin
    from harness.services.skill_graph import service

    assert hasattr(models, "SkillExecutionGuidance")
    assert hasattr(protocols, "SkillGraphService")
    assert hasattr(protocols, "SKILL_GRAPH_KEY")
    assert hasattr(guard, "AntiPatternGuard")
    assert hasattr(card_parser, "SkillCardParser")
    assert hasattr(indexer, "SkillCatalogIndexer")
    assert hasattr(routing, "find_shortest_path")
    assert hasattr(routing, "would_create_cycle")
    assert hasattr(scanner, "scan_skills_catalog")
    assert hasattr(scanner, "link_knowledge_vault_items")
    assert hasattr(topology, "compute_topology_report")
    assert hasattr(topology, "compute_prerequisite_closure")
    assert hasattr(topology, "compute_skill_chain")
    assert hasattr(topology, "evaluate_chain_feasibility")
    assert hasattr(intent, "route_skill_intent")
    assert hasattr(intent, "_trigram_overlap")
    assert hasattr(guidance, "compile_execution_guidance_plan")
    assert hasattr(guidance, "export_html_brief")
    assert hasattr(adapter, "SkillIntelligenceAdapter")
    assert hasattr(plugin, "SkillRegistryPlugin")
    assert hasattr(service, "BuiltinSkillRegistryService")
    assert hasattr(service, "resolve_skill_intelligence")


def test_package_re_exports() -> None:
    """Verify harness.services.skill_graph re-exports all public symbols."""
    import harness.services.skill_graph as sg

    expected_symbols = [
        "ActionGateResult",
        "AntiPatternGuard",
        "AntiPatternNode",
        "AntiPatternViolation",
        "CANONICAL_PIPELINE_PRECEDENCE",
        "EdgeType",
        "InvariantNode",
        "InvariantViolation",
        "SkillAntiPatternDefinition",
        "SkillCardDefinition",
        "SkillCardParser",
        "SkillCatalogIndexer",
        "SkillChainResult",
        "SkillEdge",
        "SkillExecutionGuidance",
        "SkillInvariantDefinition",
        "SkillNode",
        "SkillStageDefinition",
        "SkillTopologyReport",
        "StageNode",
        "SKILL_CLUSTERING_KEY",
        "SKILL_GRAPH_KEY",
        "SKILL_GRAPH_SERVICE_KEY",
        "SKILL_INTELLIGENCE_KEY",
        "SKILL_REGISTRY_KEY",
        "SkillGraphService",
        "SkillIntelligenceService",
        "SkillRegistryService",
        "BuiltinSkillGraphService",
        "BuiltinSkillRegistryService",
        "SkillIntelligenceAdapter",
        "SkillRegistryPlugin",
        "get_default_skill_graph",
        "get_default_skill_registry",
        "resolve_skill_intelligence",
        "CrossClusterBridge",
        "EmergentCapability",
        "SkillCluster",
        "SkillClusteringEngine",
        "SkillClusteringService",
        "SkillSelectionPlan",
        "find_shortest_path",
        "would_create_cycle",
    ]
    for sym in expected_symbols:
        assert hasattr(sg, sym), f"Missing symbol in harness.services.skill_graph: {sym}"


def test_anti_pattern_guard_ast_inspection() -> None:
    """Verify AntiPatternGuard inspects Python source without crashes."""
    from harness.services.skill_graph.guard import AntiPatternGuard

    violations = AntiPatternGuard.evaluate_action(
        action_name="run_command",
        action_input={"command": "val = input('Prompt: ')"},
        active_skills=["system_guard"],
    )
    assert len(violations) > 0
    assert any("input()" in v.symptom or "interactive" in v.rule.lower() or "input" in v.rule.lower() for v in violations)


def test_indexer_tokenization_and_weights() -> None:
    """Verify SkillCatalogIndexer computes BM25 token weights cleanly."""
    from harness.services.skill_graph.indexer import SkillCatalogIndexer
    from harness.services.skill_graph.models import SkillCardDefinition

    tokens = SkillCatalogIndexer.tokenize("A specialized skill for testing and AST evaluation.")
    assert "specialized" in tokens
    assert "testing" in tokens

    card = SkillCardDefinition(
        name="test-skill",
        description="A specialized skill for testing and AST evaluation.",
        triggers=["test", "ast"],
    )
    results = SkillCatalogIndexer.query("testing ast", skills={"test-skill": card})
    assert len(results) > 0
    assert results[0]["skill_name"] == "test-skill"
    assert results[0]["score"] > 0.0


def test_routing_dag_cycle_prevention() -> None:
    """Verify cycle prevention logic adheres to Rule 55."""
    from harness.services.skill_graph.routing import _would_create_cycle, find_shortest_path

    adj = {
        "A": {"B"},
        "B": {"C"},
        "C": set(),
    }
    # Adding C -> A would create cycle A -> B -> C -> A
    assert _would_create_cycle(adj, "C", "A") is True
    # Adding A -> C is a forward edge, no cycle
    assert _would_create_cycle(adj, "A", "C") is False

    path = find_shortest_path(adj, "A", "C")
    assert path == ["A", "B", "C"]

    no_path = find_shortest_path(adj, "C", "A")
    assert no_path is None


def test_resolve_skill_intelligence_fallback() -> None:
    """Verify resolve_skill_intelligence resolves cleanly with and without context."""
    from harness.services.skill_graph.service import resolve_skill_intelligence, BuiltinSkillRegistryService

    # Without context -> default registry singleton
    service = resolve_skill_intelligence()
    assert isinstance(service, BuiltinSkillRegistryService)

    # With empty context -> fallback to default
    ctx = ServiceContext()
    resolved = resolve_skill_intelligence(ctx)
    assert isinstance(resolved, BuiltinSkillRegistryService)


def test_intent_trigram_and_routing() -> None:
    """Verify trigram similarity and intent routing function cleanly."""
    from harness.services.skill_graph.intent import _trigram_overlap, route_skill_intent
    from harness.services.skill_graph.models import SkillCardDefinition, SkillChainResult

    # Trigram overlap
    score = _trigram_overlap("refactoring", "refactoring")
    assert score == 1.0
    score_diff = _trigram_overlap("apple", "banana")
    assert score_diff == 0.0

    # Route intent
    card = SkillCardDefinition(
        name="test-governor",
        description="Enforces strict codebase context governance rules.",
        category="governance",
        triggers=["govern", "context-audit"],
    )
    skills_cache = {"test-governor": card}
    idf_table = {"govern": 1.5, "context": 1.2}

    def dummy_chain(s1: str, s2: str, fallback_direct: bool = False) -> SkillChainResult:
        return SkillChainResult(status="no_path", start_skill=s1, target_skill=s2, chain=[], length=0)

    routed = route_skill_intent(
        "please run context-audit",
        skills_cache=skills_cache,
        idf_table=idf_table,
        chain_fn=dummy_chain,
    )
    assert routed["status"] == "ok"
    assert len(routed["matches"]) > 0
    assert routed["matches"][0]["skill_name"] == "test-governor"
    assert routed["recommended_chain"] == ["test-governor"]


def test_topology_bfs_chaining_and_reports() -> None:
    """Verify compute_skill_chain and topology reporting adhere to Rule 55."""
    from harness.services.skill_graph.topology import compute_skill_chain, compute_topology_report
    from harness.services.skill_graph.models import SkillCardDefinition, SkillEdge, EdgeType

    card_a = SkillCardDefinition(name="skill-a", description="A", category="core")
    card_b = SkillCardDefinition(name="skill-b", description="B", category="core")
    skills_cache = {"skill-a": card_a, "skill-b": card_b}

    def neighbors(node: str, include_synthetic: bool = False) -> set[str]:
        if node == "skill-a":
            return {"skill-b"}
        return set()

    # Reachable path
    res = compute_skill_chain("skill-a", "skill-b", skills_cache, neighbors)
    assert res.status == "ok"
    assert res.chain == ["skill-a", "skill-b"]

    # Unreachable path (Rule 55: no fake edges unless fallback_direct=True)
    res_no = compute_skill_chain("skill-b", "skill-a", skills_cache, neighbors, fallback_direct=False)
    assert res_no.status == "no_path"
    assert res_no.chain == []

    # Unreachable path with fallback_direct=True
    res_fallback = compute_skill_chain("skill-b", "skill-a", skills_cache, neighbors, fallback_direct=True)
    assert res_fallback.status == "ok"
    assert res_fallback.chain == ["skill-b", "skill-a"]

    # Topology report
    edge = SkillEdge(source="skill-a", target="skill-b", relation=EdgeType.PRECEDES)
    report = compute_topology_report(
        "skill-a",
        skills_cache=skills_cache,
        adj_out={"skill-a": [edge]},
        adj_in={"skill-b": [edge]},
    )
    assert report.skill.name == "skill-a"
    assert "skill-b" in report.downstream_handoffs


def test_adapter_delegation() -> None:
    """Verify SkillIntelligenceAdapter wraps registry cleanly."""
    from harness.services.skill_graph.adapter import SkillIntelligenceAdapter
    from harness.services.skill_graph.service import BuiltinSkillRegistryService

    reg = BuiltinSkillRegistryService()
    adapter = SkillIntelligenceAdapter(reg)

    # Calling discover_all through adapter
    skills = adapter.discover_all()
    assert isinstance(skills, list)
    # Check anti-pattern passthrough
    violations = adapter.check_anti_patterns("nonexistent", "dummy")
    assert violations == []
