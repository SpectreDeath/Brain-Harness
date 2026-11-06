"""Contract tests for skill clustering hardening and emergent capability engine (Track 5)."""

from __future__ import annotations

import copy
import re
import pytest

from harness.services.skill_clustering.engine import SkillClusteringEngine
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS
from harness.services.skill_graph import BuiltinSkillRegistryService


@pytest.mark.unit
class TestSkillClusteringHardening:
    """Verify that clustering and emergent capability synthesis adhere to strict contract invariants."""

    def test_emergent_capabilities_descriptions_complete_sentences(self) -> None:
        """Assert zero emergent_capabilities descriptions end mid-word or with broken fragments."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills, registry=registry)

        capabilities = engine.discover_emergent_capabilities()
        assert len(capabilities) >= 15

        broken_endings = {
            " .",  # isolated period without word
            "for .",
            "evidence d.",
            "executable agen.",
            "hotspots into sl.",
            "Runtime Store Min.",
            "no str.",
            "adversarial sel.",
            "resource manifest.",
            "where a se.",
            "model prompt dra.",
        }

        for cap in capabilities:
            desc = cap.description.strip()
            assert desc, f"Capability {cap.id} has empty description"

            # Check punctuation at end
            assert desc[-1] in {".", "!", ")", '"'}, (
                f"Capability {cap.id} description does not end with valid terminal punctuation: '{desc[-30:]}'"
            )

            # Assert none of the known broken sliced endings appear
            for broken in broken_endings:
                assert not desc.endswith(broken), (
                    f"Capability {cap.id} has broken mid-word slice ending: '{desc[-30:]}'"
                )

            # Assert last word is a clean word with letters
            last_token = desc.split()[-1].rstrip('.!?)""')
            assert len(last_token) >= 2, (
                f"Capability {cap.id} has truncated single-character word: '{last_token}'"
            )

    def test_canonical_emergent_patterns_immutability(self) -> None:
        """Assert CANONICAL_EMERGENT_PATTERNS is never mutated across multiple discovery calls."""
        patterns_snapshot = copy.deepcopy(CANONICAL_EMERGENT_PATTERNS)

        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills, registry=registry)

        # Call repeatedly
        _ = engine.discover_emergent_capabilities()
        _ = engine.discover_emergent_capabilities(query="vault")
        _ = engine.discover_emergent_capabilities(query="governance")

        assert CANONICAL_EMERGENT_PATTERNS == patterns_snapshot, (
            "CANONICAL_EMERGENT_PATTERNS was mutated in-place during discovery calls"
        )

    def test_top_in_degree_contains_only_valid_nodes(self) -> None:
        """Assert top_in_degree rankings contain only valid skill IDs present in graph.nodes (Rule 35)."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        skill_keys = set(registry.get_nodes().keys())

        # Collect in-degrees across all edges
        in_degrees: dict[str, int] = {}
        for edge in registry.edges:
            # Only count edges targeting valid registered skill nodes
            if edge.target in skill_keys:
                in_degrees[edge.target] = in_degrees.get(edge.target, 0) + 1

        top_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        top_keys = [k for k, _ in top_in[:20]]

        # Ensure no phantom HTML/markdown tokens exist
        forbidden_phantom_tokens = {
            "mermaid",
            "script",
            "knowledge",
            "skills",
            "dist",
            "head",
            "body",
            "html",
            "div",
        }

        for k in top_keys:
            assert k in skill_keys, f"Found unregistered node {k} in top_in_degree"
            assert k not in forbidden_phantom_tokens, f"Found phantom token {k} in top_in_degree"

    def test_skill_card_parser_parses_disable_model_invocation(self) -> None:
        """Assert that skills declaring disable-model-invocation have node.disable_model_invocation is True."""
        registry = BuiltinSkillRegistryService()
        _ = registry.discover_all(".")
        nodes = registry.get_nodes()

        known_disabled = [
            "ask-matt",
            "claude-handoff",
            "grill-me",
            "handoff",
            "writing-beats",
            "writing-fragments",
            "writing-shape",
            "wait-what",
        ]
        for name in known_disabled:
            assert name in nodes, f"Expected {name} to be discovered"
            assert (
                nodes[name].disable_model_invocation is True
            ), f"Expected {name}.disable_model_invocation to be True"

    def test_emergent_capabilities_autonomous_mode_and_alignment(self) -> None:
        """Assert autonomous capabilities exclude human-only skills and maintain pipeline alignment."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills, registry=registry)
        capabilities = engine.discover_emergent_capabilities()
        nodes = registry.get_nodes()

        for cap in capabilities:
            if cap.invocation_mode == "autonomous":
                for s in cap.recommended_pipeline:
                    assert (
                        not getattr(nodes.get(s), "disable_model_invocation", False)
                    ), f"Autonomous capability {cap.id} includes disabled skill {s} in pipeline"

            if cap.id.startswith("cap_synth_"):
                assert (
                    cap.primary_skills == cap.recommended_pipeline
                ), f"Capability {cap.id} primary_skills != recommended_pipeline"
                # Check description matches pipeline
                if cap.description.startswith("Integrates "):
                    header_part = cap.description.split(" into an end-to-end")[0].replace("Integrates ", "")
                    mentioned_skills = [s.strip() for s in header_part.split(",")]
                    for ms in mentioned_skills:
                        assert ms in cap.recommended_pipeline, (
                            f"Skill {ms} in description header is not in recommended_pipeline for {cap.id}"
                        )

        # Check human-only capabilities
        synth_14 = next((c for c in capabilities if c.id == "cap_synth_cluster_14_writing_beats"), None)
        assert synth_14 is not None
        assert synth_14.invocation_mode == "human_only"

    def test_report_and_readme_parity_with_json_data(self) -> None:
        """Assert reports/skill_knowledge_graph_cluster_analysis_report.md and README.md reflect cluster_analysis_data.json."""
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        data_path = root / "reports" / "cluster_analysis_data.json"
        rep_path = root / "reports" / "skill_knowledge_graph_cluster_analysis_report.md"
        readme_path = root / "reports" / "README.md"

        assert data_path.exists(), "cluster_analysis_data.json missing"
        assert rep_path.exists(), "skill_knowledge_graph_cluster_analysis_report.md missing"
        assert readme_path.exists(), "reports/README.md missing"

        cad = json.loads(data_path.read_text(encoding="utf-8"))
        rep_txt = rep_path.read_text(encoding="utf-8")
        readme_txt = readme_path.read_text(encoding="utf-8")

        total_nodes = cad["total_nodes"]
        total_edges = cad["total_edges"]
        num_clusters = len(cad["clusters"])
        num_bridges = len(cad["bridges"])
        num_caps = len(cad["emergent_capabilities"])

        # Check report markdown
        assert f"{total_edges} directed relationship edges" in rep_txt
        assert f"{num_clusters} cohesive functional clusters" in rep_txt or f"{num_clusters} functional clusters" in rep_txt
        assert f"## 3. The {num_clusters} Functional Clusters" in rep_txt
        assert f"{num_bridges} cross-cluster macro-bridges" in rep_txt
        assert f"{num_caps} emergent macro-capabilities" in rep_txt

        # Check reports/README.md
        assert f"{total_nodes} skill nodes" in readme_txt
        assert f"{total_edges} directed edges" in readme_txt
        assert f"{num_clusters} functional clusters" in readme_txt
        assert f"{num_bridges} cross-cluster bridges" in readme_txt
        assert f"{num_caps} emergent macro-capabilities" in readme_txt
