"""Unit and contract tests for graph-driven harness blueprint recommender (Track 1.2 & 1.3)."""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any

from click.testing import CliRunner
import pytest

from harness.cli import main
from harness.services.harness_spawner import (
    HARD_MAX_BLUEPRINT_SKILLS,
    HarnessBlueprint,
    SeededKI,
    build_blueprint_tree,
    recommend_harness_blueprints,
)
from harness.services.harness_spawner import blueprints as blueprints_mod
from harness.services.harness_spawner._blueprint_catalog import CANONICAL_SPECS
from harness.services.recursive_harnessing import guards, surface as surface_ops
from harness.services.recursive_harnessing.models import BRAIN_SURFACE
from plugins.agent_orchestration.harness_spawner.main import plugin as spawner_plugin


@pytest.mark.unit
class TestHarnessSpawnerBlueprints:
    """Verify deterministic graph ranking, UNVERIFIED KI exclusion, caps, and CLI parity."""

    def test_deterministic_ranking_and_skill_caps(self) -> None:
        first = recommend_harness_blueprints(max_skills=5)
        second = recommend_harness_blueprints(max_skills=5)
        assert [b.name for b in first] == [b.name for b in second]
        assert [b.score for b in first] == [b.score for b in second]
        assert [b.skills for b in first] == [b.skills for b in second]
        assert len(first) == len(CANONICAL_SPECS)

        for bp in first:
            assert 1 <= len(bp.skills) <= 5
            assert len(bp.skills) <= HARD_MAX_BLUEPRINT_SKILLS
            assert bp.icm_form in {"pipeline", "record_library", "knowledge_bundle", "context_map", "system_map"}
            assert all(k.isnad_status == "VERIFIED" for k in bp.seeded_kis)

    def test_unverified_kis_excluded_and_flagged(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(
            blueprints_mod,
            "cluster_skills_cmd",
            lambda **_: {
                "status": "ok",
                "total_clusters": 1,
                "clusters": [
                    {
                        "cluster_id": "cluster_12_brain_artifact_miner",
                        "cohesion_score": 0.5,
                        "skills": ["brain-artifact-miner", "conversation-trajectory-miner"],
                    }
                ],
            },
        )
        monkeypatch.setattr(
            blueprints_mod,
            "get_cross_cluster_bridges_cmd",
            lambda **_: {
                "status": "ok",
                "total_bridges": 1,
                "bridges": [
                    {
                        "source_cluster": "cluster_12_brain_artifact_miner",
                        "target_cluster": "cluster_04_external_repo_bridge_forge",
                        "bridge_skills": [("brain-artifact-miner", "repo-triad-forge")],
                    }
                ],
            },
        )

        def _fake_jq(topic: str, **_: Any) -> dict[str, Any]:
            return {
                "knowledge_items": [
                    {
                        "ki_id": "ki-ver-1",
                        "title": "Verified Graph Finding",
                        "domain": "knowledge_distillation",
                        "status": "ACTIVE",
                        "isnad_status": "VERIFIED",
                    },
                    {
                        "ki_id": "ki-unver-2",
                        "title": "Unverified Draft",
                        "domain": "knowledge_distillation",
                        "status": "ACTIVE",
                        "isnad_status": "UNVERIFIED",
                    },
                    {
                        "ki_id": "ki-unk-3",
                        "title": "Missing Lineage",
                        "domain": "knowledge_distillation",
                        "status": "ACTIVE",
                        "isnad_status": "UNKNOWN",
                    },
                ]
            }

        monkeypatch.setattr(blueprints_mod, "query_knowledge_and_skills", _fake_jq)

        bps = recommend_harness_blueprints(root_path=tmp_path, name="harness-repo-distiller")
        assert len(bps) == 1
        bp = bps[0]
        assert [k.ki_id for k in bp.seeded_kis] == ["ki-ver-1"]
        assert bp.excluded_unverified_kis == ("ki-unk-3", "ki-unver-2")

    def test_blueprint_invariants_and_frozen_immutability(self) -> None:
        with pytest.raises(ValueError, match="max_skills"):
            recommend_harness_blueprints(max_skills=7)

        with pytest.raises(ValueError, match="Only VERIFIED KIs"):
            HarnessBlueprint(
                name="bad-ki",
                domain="security",
                title="Bad KI Harness",
                mission="Should reject unverified KI.",
                icm_form="record_library",
                skills=("icm-workspace-architect",),
                graph_source="test",
                cohesion_score=0.5,
                bridge_count=1,
                score=10.0,
                seeded_kis=(SeededKI("ki-bad", "Bad", "security", "UNVERIFIED"),),
                excluded_unverified_kis=(),
                use_cases=("Run test",),
                out_of_scope=("No out-of-scope",),
            )

        with pytest.raises(ValueError, match="Blueprint skills count"):
            HarnessBlueprint(
                name="too-many-skills",
                domain="security",
                title="Oversized Harness",
                mission="Should reject >6 skills.",
                icm_form="pipeline",
                skills=tuple(f"skill-{i}" for i in range(7)),
                graph_source="test",
                cohesion_score=0.5,
                bridge_count=1,
                score=10.0,
                seeded_kis=(),
                excluded_unverified_kis=(),
                use_cases=("Run test",),
                out_of_scope=("Out",),
            )

        bp = recommend_harness_blueprints(name="harness-repo-distiller")[0]
        # Rule 43: verify frozen immutability via direct attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            bp.score = 999.0  # type: ignore[misc]

    def test_blueprint_tree_and_cli_blueprints_command(self) -> None:
        runner = CliRunner()
        res_all = runner.invoke(main, ["spawn", "blueprints", "--json", "--max-skills", "5"])
        assert res_all.exit_code == 0, res_all.output
        payload = json.loads(res_all.output)
        assert payload["count"] == len(CANONICAL_SPECS)
        names = [item["name"] for item in payload["blueprints"]]
        assert "harness-repo-distiller" in names
        assert "harness-security-forensics" in names
        assert "harness-reverse-engineering" in names
        assert "harness-ontology-spider" in names
        assert "harness-knowledge-graph" in names
        assert "harness-memory-graph" in names
        assert "harness-data-lakehouse" in names
        assert "harness-agent-reliability" in names
        assert "harness-swarm-orchestrator" in names
        assert "harness-docs-architect" in names
        assert "harness-cloud-k8s" in names
        assert "harness-geospatial-gis" in names
        assert "harness-skill-factory" in names
        assert "harness-repo-plugin-forge" in names
        assert "harness-literature-media-forge" in names
        assert "harness-kernel-plugin-dev" in names
        assert "harness-self-evolution" in names
        assert "harness-mind-artifact-miner" in names
        assert "harness-runtime-governor" in names

        res_one = runner.invoke(main, ["spawn", "blueprints", "--name", "harness-repo-distiller", "--json"])
        assert res_one.exit_code == 0, res_one.output
        one_payload = json.loads(res_one.output)
        assert one_payload["count"] == 1
        assert one_payload["blueprints"][0]["icm_form"] == "knowledge_bundle"

        bp = spawner_plugin.recommend_blueprints(name="harness-repo-distiller")[0]
        tree = build_blueprint_tree(bp)
        assert len(tree["AGENTS.md"].splitlines()) < 60
        census = surface_ops.validate(BRAIN_SURFACE, tree)
        assert census["skills"] == len(bp.skills)

        res_rev = runner.invoke(main, ["spawn", "review", "--blueprint", "harness-repo-distiller", "--json"])
        assert res_rev.exit_code == 0, res_rev.output
        rev_data = json.loads(res_rev.output)
        assert rev_data["tree_sha256"]

    def test_seeded_kis_rank_by_domain_relevance_and_skip_signature_dumps(self) -> None:
        sec_bp = recommend_harness_blueprints(name="harness-security-forensics")[0]
        sec_ids = [k.ki_id for k in sec_bp.seeded_kis]
        assert "ki_20260908_mantis_01" in sec_ids
        assert not any(kid.startswith("ki-rea-sig-") for kid in sec_ids)

        econ_bp = recommend_harness_blueprints(name="harness-context-economizer")[0]
        assert "ki_20261028_headroom_context_optimization" in [k.ki_id for k in econ_bp.seeded_kis]

        arch_bp = recommend_harness_blueprints(name="harness-arch-modernizer")[0]
        assert "ki_20260908_earthengine_01" not in [k.ki_id for k in arch_bp.seeded_kis]

    def test_blueprint_collection_is_invariant_to_iterdir_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        vault_resolved = Path(".harness/knowledge").resolve()
        orig_iterdir = Path.iterdir

        def _run_with_order(mode: str) -> list[tuple[str, float, tuple[str, ...], list[str]]]:
            def _fake_iterdir(self: Path) -> Any:
                items = list(orig_iterdir(self))
                if self.resolve() == vault_resolved:
                    if mode == "reversed":
                        items.reverse()
                    elif mode == "shuffled":
                        random.Random(17).shuffle(items)
                    else:
                        items.sort()
                return iter(items)

            with monkeypatch.context() as mp:
                mp.setattr(Path, "iterdir", _fake_iterdir)
                bps = recommend_harness_blueprints(max_skills=5)
            return [(b.name, b.score, b.skills, [k.ki_id for k in b.seeded_kis]) for b in bps]

        baseline = _run_with_order("sorted")
        assert _run_with_order("reversed") == baseline
        assert _run_with_order("shuffled") == baseline

    def test_wave2_blueprints_seed_verified_kis_and_pass_surface_and_guards(self) -> None:
        expected = {
            "harness-reverse-engineering": ("pipeline", 4),
            "harness-ontology-spider": ("system_map", 6),
            "harness-knowledge-graph": ("knowledge_bundle", 6),
            "harness-memory-graph": ("context_map", 6),
        }
        for name, (expected_form, min_kis) in expected.items():
            bps = recommend_harness_blueprints(name=name, max_skills=5)
            assert len(bps) == 1
            bp = bps[0]
            assert bp.icm_form == expected_form
            assert len(bp.skills) == 5
            assert len(bp.seeded_kis) >= min_kis
            ki_ids = [k.ki_id for k in bp.seeded_kis]
            assert not any(kid.startswith("ki-rea-sig-") for kid in ki_ids)
            assert all(k.isnad_status == "VERIFIED" for k in bp.seeded_kis)
            tree = build_blueprint_tree(bp)
            guards.assert_tree_clean(tree)
            census = surface_ops.validate(BRAIN_SURFACE, tree)
            assert census["skills"] == 5

        sec_wiki = recommend_harness_blueprints(name="harness-ontology-spider")[0]
        sec_wiki_ids = [k.ki_id for k in sec_wiki.seeded_kis]
        assert any(kid.startswith("ki-trustgraph-") for kid in sec_wiki_ids)
        assert "ki_ontological_engineering_gruber_criteria" in sec_wiki_ids

        re_bp = recommend_harness_blueprints(name="harness-reverse-engineering")[0]
        assert "ki-rea-reconstruction-obligations" in [k.ki_id for k in re_bp.seeded_kis]

    def test_wave3_blueprints_seed_verified_kis_and_pass_surface_and_guards(self) -> None:
        expected = {
            "harness-data-lakehouse": ("pipeline", 5, 4),
            "harness-agent-reliability": ("pipeline", 5, 4),
            "harness-swarm-orchestrator": ("context_map", 5, 4),
            "harness-docs-architect": ("system_map", 5, 4),
            "harness-cloud-k8s": ("record_library", 3, 4),
            "harness-geospatial-gis": ("system_map", 4, 4),
            "harness-skill-factory": ("pipeline", 4, 4),
        }
        assert len(CANONICAL_SPECS) == 21
        for name, (expected_form, expected_skills, min_kis) in expected.items():
            bps = recommend_harness_blueprints(name=name, max_skills=5)
            assert len(bps) == 1
            bp = bps[0]
            assert bp.icm_form == expected_form
            assert len(bp.skills) == expected_skills
            assert len(bp.seeded_kis) >= min_kis
            ki_ids = [k.ki_id for k in bp.seeded_kis]
            assert not any(kid.startswith("ki-rea-sig-") for kid in ki_ids)
            assert all(k.isnad_status == "VERIFIED" for k in bp.seeded_kis)
            tree = build_blueprint_tree(bp)
            guards.assert_tree_clean(tree)
            census = surface_ops.validate(BRAIN_SURFACE, tree)
            assert census["skills"] == expected_skills

    def test_wave4_blueprints_seed_verified_kis_and_pass_surface_and_guards(self) -> None:
        expected = {
            "harness-repo-plugin-forge": ("pipeline", 5, 6),
            "harness-literature-media-forge": ("knowledge_bundle", 5, 6),
            "harness-kernel-plugin-dev": ("system_map", 5, 6),
            "harness-self-evolution": ("pipeline", 5, 6),
            "harness-mind-artifact-miner": ("record_library", 5, 6),
            "harness-runtime-governor": ("context_map", 5, 6),
        }
        for name, (expected_form, expected_skills, min_kis) in expected.items():
            bps = recommend_harness_blueprints(name=name, max_skills=5)
            assert len(bps) == 1
            bp = bps[0]
            assert bp.icm_form == expected_form
            assert len(bp.skills) == expected_skills
            assert len(bp.seeded_kis) >= min_kis
            ki_ids = [k.ki_id for k in bp.seeded_kis]
            assert not any(kid.startswith("ki-rea-sig-") for kid in ki_ids)
            assert all(k.isnad_status == "VERIFIED" for k in bp.seeded_kis)
            tree = build_blueprint_tree(bp)
            guards.assert_tree_clean(tree)
            census = surface_ops.validate(BRAIN_SURFACE, tree)
            assert census["skills"] == expected_skills
