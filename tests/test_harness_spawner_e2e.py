"""End-to-end acceptance tests for full spawn lifecycle and 4 use cases (Track 4.1 & 4.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.services.dock import DefaultDockService
from harness.services.harness_spawner import (
    EXPERIENCE_LIBRARY_KEY,
    HarnessSpawnerEngine,
    SpawnLifecycleState,
    SpawnSpec,
    build_tree_diff_review,
)
from harness.services.recursive_harnessing import (
    BRAIN_SURFACE,
    LiveHarnessProposer,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary


@pytest.mark.unit
class TestHarnessSpawnerEndToEndAcceptance:
    """Exercise full description -> spawn -> run -> retire -> adopt loop and all 4 use cases."""

    def test_full_loop_from_one_description(self, tmp_path: Path) -> None:
        """Track 4.1: Description -> LiveHarnessProposer -> diff review -> spawn -> task -> adopt -> retire."""
        description = "Audit markdown link hygiene across docs using a dedicated link_auditor skill."
        proposer_reply = json.dumps(
            {
                "notes": "Created narrow link-auditor child harness.",
                "files": {
                    "AGENTS.md": "# Link Auditor Harness\n\nUse `link_auditor` for relative markdown checks.\n",
                    ".agents/skills/link_auditor/SKILL.md": (
                        "---\nname: link_auditor\n"
                        "description: Check relative markdown links across docs and report broken targets. "
                        "Do not use for Python AST or code refactoring tasks.\n"
                        "---\nInspect every relative link.\n"
                    ),
                },
            }
        )
        proposer = LiveHarnessProposer(complete_fn=lambda _: proposer_reply)
        proposed_tree, _ = proposer.propose_tree_from_description(description, tmp_path / "propose_ws")

        review = build_tree_diff_review(BRAIN_SURFACE, {"AGENTS.md": ""}, proposed_tree)
        assert ".agents/skills/link_auditor/SKILL.md" in review.added

        engine = HarnessSpawnerEngine(state_file=tmp_path / "spawns" / "registry.json")
        rec = engine.spawn(
            SpawnSpec(
                name="link-auditor",
                domain="docs-audit",
                task="Verify markdown relative links",
                description=description,
                tree=proposed_tree,
                save_dir=tmp_path / "spawns",
                write_permitted=True,
                approved_tree_digest=review.tree_sha256,
            ),
            probe_fn=lambda spec, ctx: ".agents/skills/link_auditor/SKILL.md" in spec.tree,
        )
        assert rec.state == SpawnLifecycleState.RUNNING

        engine.record_usage(rec.spawn_id, tokens=450, rollouts=1)
        proposal = engine.propose_merge_back(
            rec.spawn_id,
            task_id="docs-check-1",
            cue="when validating workspace docs",
            lesson="strip fenced code blocks before regex link matching",
            evidence="0 false positives across 26 docs",
            proposal_kind="skill",
        )
        retired = engine.retire(rec.spawn_id)
        assert retired.state == SpawnLifecycleState.RETIRED
        assert engine.is_disposed(rec.spawn_id)

        parent_lib = tmp_path / "parent_lib"
        parent_kn = tmp_path / "parent_kn"
        adopted = engine.adopt_merge_proposal(
            proposal.proposal_id,
            parent_library_root=parent_lib,
            parent_knowledge_root=parent_kn,
            reviewer="operator",
        )
        assert adopted["status"] == "adopted"
        assert (parent_kn / proposal.ki_id / "metadata.json").is_file()
        assert len(ExperienceLibrary(parent_lib, "docs-audit", BRAIN_SURFACE).entries()) == 1

    def test_four_use_cases_pass_cleanly(self, tmp_path: Path) -> None:
        """Track 4.2: Swarm worker, domain harness (dock), sandbox experiment, and ingestion partition."""
        engine = HarnessSpawnerEngine(state_file=tmp_path / "registry.json")

        # 1. Swarm worker (task lifetime -> auto-retires upon completion)
        swarm_worker = engine.spawn(
            SpawnSpec(
                name="swarm-worker",
                domain="swarm-task",
                task="bounded verification slice",
                tree={"AGENTS.md": "# Swarm Worker\n\nRun slice check.\n"},
                save_dir=tmp_path / "spawns",
                lifetime="task",
            ),
            probe_fn=lambda s, c: True,
        )
        completed = engine.complete(swarm_worker.spawn_id, tokens_used=300)
        assert completed.state == SpawnLifecycleState.RETIRED
        assert engine.is_disposed(swarm_worker.spawn_id)

        # 2. Domain harness (narrow skill + materialized dock + dock run)
        dock = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks.json")
        domain_dir = tmp_path / "domain_dock"
        domain_tree = {
            "AGENTS.md": "# Domain Harness\n\nRun `sql_check` on queries.\n",
            ".agents/skills/sql_check/SKILL.md": (
                "---\nname: sql_check\n"
                "description: Audit recursive SQL CTEs for termination bounds before query execution. "
                "Do not use for NoSQL document stores or frontend CSS.\n"
                "---\nEnforce depth guard.\n"
            ),
        }
        domain_rec = engine.spawn(
            SpawnSpec(
                name="sql-domain",
                domain="sql",
                task="audit recursive queries",
                tree=domain_tree,
                save_dir=tmp_path / "spawns",
            ),
            materialize_dir=domain_dir,
            dock_service=dock,
            approve_dock=True,
        )
        assert domain_rec.dock_name == "sql-domain"
        dock_res = dock.run("sql-domain", "validate")
        assert dock_res.success and any("DOCK_HARNESS_OK" in s.stdout for s in dock_res.steps)

        # 3. Sandbox experiment (try it, adopt if trial passes)
        exp_rec = engine.spawn(
            SpawnSpec(
                name="sandbox-exp",
                domain="experiments",
                task="test prompt pruning pass",
                tree={"AGENTS.md": "# Experiment\n\nMeasure token savings.\n"},
                save_dir=tmp_path / "spawns",
            ),
            probe_fn=lambda s, c: True,
        )
        exp_prop = engine.propose_merge_back(
            exp_rec.spawn_id,
            task_id="prune-pass",
            cue="when context approaches cap",
            lesson="apply 3-pass deterministic pruning",
            evidence="18% token reduction in trial",
        )
        exp_adopt = engine.adopt_merge_proposal(
            exp_prop.proposal_id,
            parent_library_root=tmp_path / "parent_lib",
            parent_knowledge_root=tmp_path / "parent_kn",
        )
        assert exp_adopt["status"] == "adopted"

        # 4. Ingestion harness (one repo, own isolated partition, zero leak to parent)
        ing_rec = engine.spawn(
            SpawnSpec(
                name="repo-ingestor",
                domain="repo-acme-analytics",
                task="ingest single external repository into isolated partition",
                tree={"AGENTS.md": "# Ingestion Harness\n\nIngest acme-analytics.\n"},
                save_dir=tmp_path / "spawns",
            )
        )
        ing_ctx = engine.get_child_context(ing_rec.spawn_id)
        assert ing_ctx is not None
        ing_lib = ing_ctx.require(EXPERIENCE_LIBRARY_KEY)
        assert ing_rec.spawn_id in str(ing_lib.root)
        assert not (tmp_path / "parent_kn" / f"ki-spawn-{ing_rec.domain}-t1").exists()

        engine.retire_all()
