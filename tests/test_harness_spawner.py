"""Contract and unit tests for child harness spawning (Step 1 Option A, Rules 12, 17, 19, 40, 43)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    DefaultAgentExecutionGraphService,
    ThreadSpawnStatus,
)
from harness.services.harness_spawner import (
    EXPERIENCE_LIBRARY_KEY,
    HARD_MAX_SPAWN_DEPTH,
    SPAWN_DEPTH_KEY,
    HarnessSpawnerEngine,
    SpawnBudgetSpec,
    SpawnedHarnessRecord,
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnSpec,
    SpawnTrialResult,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

PARENT_GREETING_KEY: ServiceKey[str] = ServiceKey("test.parent.greeting")
SECRET_REALM_KEY: ServiceKey[str] = ServiceKey("test.isolated.secret")


def _valid_tree(note: str = "Focus on domain research.") -> dict[str, str]:
    return {"AGENTS.md": f"# Child Harness\n\n{note}\n"}


@pytest.mark.unit
class TestHarnessSpawnerModelsAndIsolation:
    """Verify frozen/slotted invariants, inheritance, and realm isolation."""

    def test_slotted_and_frozen_immutability(self, tmp_path: Path) -> None:
        """Rules 12, 43: direct attribute mutation on frozen records must fail."""
        budget = SpawnBudgetSpec(max_tokens=8000, k=1, max_rollouts=4, max_sessions=3)
        spec = SpawnSpec(
            name="child-a",
            domain="research",
            tree=_valid_tree(),
            budget=budget,
            save_dir=tmp_path,
        )
        trial = SpawnTrialResult(passed=True, fingerprint="abc123", census={"always_on_chars": 30})
        proposal = SpawnMergeProposal(
            proposal_id="prop_1",
            spawn_id="spawn_1",
            domain="research",
            task_id="t1",
            tree=_valid_tree(),
            cue="when auditing",
            lesson="check invariants first",
            evidence="unit test trace",
        )
        record = SpawnedHarnessRecord(
            spawn_id="spawn_1",
            name="child-a",
            domain="research",
            task="audit",
            state=SpawnLifecycleState.RUNNING,
            depth=1,
            max_spawn_depth=1,
            parent_spawn_id=None,
            parent_session_id=None,
            session_id="sess_1",
            node_id="harness:spawn_1",
            fingerprint="abc123",
            save_dir=str(tmp_path),
            tokens_used=0,
            rollouts_used=0,
            sessions_used=1,
            budget=budget,
            lifetime="persistent",
            trial=trial,
        )

        with pytest.raises((AttributeError, TypeError)):
            budget.max_tokens = 1  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            spec.domain = "other"  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            trial.passed = False  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            proposal.status = "adopted"  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            record.tokens_used = 99  # type: ignore[misc]

    def test_child_context_inherits_parent_and_isolates_realms(self, tmp_path: Path) -> None:
        """Child inherits parent services while isolating ExperienceLibrary & declared keys."""
        parent_ctx = ServiceContext()
        parent_lib = ExperienceLibrary(root=tmp_path / "parent_lib", domain="prime", surface=BRAIN_SURFACE)
        parent_ctx.provide(PARENT_GREETING_KEY, "hello-from-prime")
        parent_ctx.provide(EXPERIENCE_LIBRARY_KEY, parent_lib)
        parent_ctx.provide(SECRET_REALM_KEY, "top-secret-parent-value")

        engine = HarnessSpawnerEngine(parent_context=parent_ctx)
        rec = engine.spawn(
            SpawnSpec(
                name="worker",
                domain="code-audit",
                task="verify isolation",
                tree=_valid_tree(),
                isolated_keys=("service.experience_library", "test.isolated.secret"),
                save_dir=tmp_path / "spawns",
            )
        )
        assert rec.state == SpawnLifecycleState.RUNNING

        child_ctx = engine.get_child_context(rec.spawn_id)
        assert child_ctx is not None

        # Non-isolated parent registration is inherited
        assert child_ctx.require(PARENT_GREETING_KEY) == "hello-from-prime"
        assert child_ctx.require(SPAWN_DEPTH_KEY) == 1

        # Isolated secret key is hidden from child without touching parent
        assert parent_ctx.require(SECRET_REALM_KEY) == "top-secret-parent-value"
        assert child_ctx.optional(SECRET_REALM_KEY) is None

        # Child ExperienceLibrary points to isolated partition while parent library stays untouched
        child_lib = child_ctx.require(EXPERIENCE_LIBRARY_KEY)
        assert child_lib is not parent_lib
        assert str(tmp_path / "spawns" / rec.spawn_id / "library") in str(child_lib.root)
        assert parent_ctx.require(EXPERIENCE_LIBRARY_KEY) is parent_lib

        engine.retire_all()


@pytest.mark.unit
class TestHarnessSpawnerGatesAndBudgets:
    """Verify recursion depth caps, admission probe gate, dual budgets, and disposal cascade."""

    def test_recursion_depth_enforcement_and_hard_cap(self, tmp_path: Path) -> None:
        """Default cap=1 blocks grandchildren; explicit max=2 permits depth=2; >3 always rejected."""
        with pytest.raises(ValueError, match="max_spawn_depth=4"):
            SpawnSpec(
                name="too-deep",
                domain="d",
                tree=_valid_tree(),
                max_spawn_depth=HARD_MAX_SPAWN_DEPTH + 1,
                save_dir=tmp_path,
            )

        engine = HarnessSpawnerEngine()
        # Default cap=1: depth=0 -> child depth=1 succeeds
        child = engine.spawn(
            SpawnSpec(name="c1", domain="research", tree=_valid_tree(), save_dir=tmp_path / "s1")
        )
        assert child.depth == 1
        assert child.state == SpawnLifecycleState.RUNNING

        # Attempting grandchild under cap=1 fails with ValueError
        with pytest.raises(ValueError, match="exceeds max_spawn_depth=1"):
            engine.spawn(
                SpawnSpec(
                    name="gc1",
                    domain="research",
                    tree=_valid_tree(),
                    parent_spawn_id=child.spawn_id,
                    save_dir=tmp_path / "s1",
                )
            )

        # Explicit max_spawn_depth=2 permits grandchild at depth=2, blocks depth=3
        parent2 = engine.spawn(
            SpawnSpec(
                name="c2",
                domain="research",
                tree=_valid_tree(),
                max_spawn_depth=2,
                save_dir=tmp_path / "s2",
            )
        )
        grandchild = engine.spawn(
            SpawnSpec(
                name="gc2",
                domain="research",
                tree=_valid_tree(),
                parent_spawn_id=parent2.spawn_id,
                max_spawn_depth=2,
                save_dir=tmp_path / "s2",
            )
        )
        assert grandchild.depth == 2
        assert grandchild.state == SpawnLifecycleState.RUNNING

        with pytest.raises(ValueError, match="exceeds max_spawn_depth=2"):
            engine.spawn(
                SpawnSpec(
                    name="ggc2",
                    domain="research",
                    tree=_valid_tree(),
                    parent_spawn_id=grandchild.spawn_id,
                    max_spawn_depth=3,
                    save_dir=tmp_path / "s2",
                )
            )
        engine.retire_all()

    def test_admission_gate_blocks_invalid_tree_and_failed_probe(self, tmp_path: Path) -> None:
        """Invalid surface tree, leaked verdict markers, or failing k=1 probe stay FAILED."""
        graph = DefaultAgentExecutionGraphService()
        engine = HarnessSpawnerEngine(graph_store=graph)

        # 1. Empty AGENTS.md fails surface validation
        bad_surface = engine.spawn(
            SpawnSpec(name="empty", domain="audit", tree={}, save_dir=tmp_path / "bad1")
        )
        assert bad_surface.state == SpawnLifecycleState.FAILED
        assert bad_surface.trial is not None and bad_surface.trial.passed is False
        assert engine.is_disposed(bad_surface.spawn_id) is True

        # 2. Failed k=1 probe fails admission
        bad_probe = engine.spawn(
            SpawnSpec(name="probe-fail", domain="audit", tree=_valid_tree(), save_dir=tmp_path / "bad2"),
            probe_fn=lambda _spec, _ctx: False,
        )
        assert bad_probe.state == SpawnLifecycleState.FAILED
        assert "probe trial returned False" in bad_probe.error
        assert engine.is_disposed(bad_probe.spawn_id) is True
        assert graph.export_graph().nodes[bad_probe.node_id].status == "failed"

        # 3. Grader verdict marker leak fails clean-tree tripwire
        bad_leak = engine.spawn(
            SpawnSpec(
                name="leak",
                domain="audit",
                tree={"AGENTS.md": 'do not cheat "test_pass_rate": 1.0'},
                save_dir=tmp_path / "bad3",
            )
        )
        assert bad_leak.state == SpawnLifecycleState.FAILED
        assert engine.is_disposed(bad_leak.spawn_id) is True

    def test_dual_budget_exhaustion_fails_closed(self, tmp_path: Path) -> None:
        """Exceeding max_tokens, max_rollouts, or max_sessions fails closed and disposes child."""
        graph = DefaultAgentExecutionGraphService()
        engine = HarnessSpawnerEngine(graph_store=graph)

        rec_tok = engine.spawn(
            SpawnSpec(
                name="tok",
                domain="d",
                tree=_valid_tree(),
                budget=SpawnBudgetSpec(max_tokens=500, k=1, max_rollouts=4, max_sessions=3),
                save_dir=tmp_path / "b1",
            )
        )
        updated = engine.record_usage(rec_tok.spawn_id, tokens=300, rollouts=1)
        assert updated.tokens_used == 300
        assert updated.rollouts_used == 1

        with pytest.raises(RuntimeError, match="Token budget exceeded"):
            engine.record_usage(rec_tok.spawn_id, tokens=250)

        failed_rec = engine.get_spawn(rec_tok.spawn_id)
        assert failed_rec is not None
        assert failed_rec.state == SpawnLifecycleState.FAILED
        assert engine.is_disposed(rec_tok.spawn_id) is True
        assert graph.export_graph().nodes[rec_tok.node_id].status == "failed"

        rec_roll = engine.spawn(
            SpawnSpec(
                name="roll",
                domain="d",
                tree=_valid_tree(),
                budget=SpawnBudgetSpec(max_tokens=5000, k=1, max_rollouts=2, max_sessions=2),
                save_dir=tmp_path / "b2",
            )
        )
        with pytest.raises(RuntimeError, match="Rollout budget exceeded"):
            engine.record_usage(rec_roll.spawn_id, rollouts=3)
        assert engine.get_spawn(rec_roll.spawn_id).state == SpawnLifecycleState.FAILED  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_parent_dispose_cascades_to_live_children_and_task_auto_retire(
        self, tmp_path: Path
    ) -> None:
        """Disposing parent ServiceContext automatically retires all live child contexts."""
        graph = DefaultAgentExecutionGraphService()
        parent_ctx = ServiceContext()
        parent_ctx.provide(AGENT_GRAPH_STORE_KEY, graph)
        engine = HarnessSpawnerEngine(parent_context=parent_ctx)

        c_persistent = engine.spawn(
            SpawnSpec(
                name="persist",
                domain="d1",
                tree=_valid_tree("one"),
                lifetime="persistent",
                save_dir=tmp_path / "cascade",
            )
        )
        c_task = engine.spawn(
            SpawnSpec(
                name="oneshot",
                domain="d2",
                tree=_valid_tree("two"),
                lifetime="task",
                save_dir=tmp_path / "cascade",
            )
        )

        # Completing a task-scoped harness auto-retires it cleanly
        completed_task = engine.complete(c_task.spawn_id, tokens_used=120)
        assert completed_task.state == SpawnLifecycleState.RETIRED
        assert engine.is_disposed(c_task.spawn_id) is True

        child_persist_ctx = engine.get_child_context(c_persistent.spawn_id)
        assert child_persist_ctx is not None
        assert len(child_persist_ctx._dispose_stack) > 0

        # Parent disposal must cascade via effect hook and empty child _dispose_stack
        await parent_ctx.dispose()
        rec_after = engine.get_spawn(c_persistent.spawn_id)
        assert rec_after is not None
        assert rec_after.state == SpawnLifecycleState.RETIRED
        assert engine.is_disposed(c_persistent.spawn_id) is True
        assert len(child_persist_ctx._dispose_stack) == 0

        export = graph.export_graph()
        assert any(e.status in (ThreadSpawnStatus.CLOSED, ThreadSpawnStatus.COMPLETED) for e in export.edges)


@pytest.mark.unit
class TestReviewedMergeBackAndCli:
    """Verify reviewed merge-back isolation, dual-file KI promotion, and Click CLI."""

    def test_reviewed_merge_back_stages_then_adopts(self, tmp_path: Path) -> None:
        """propose_merge_back isolates to child; adopt_merge_proposal promotes to parent."""
        spawns_dir = tmp_path / "spawns"
        parent_lib_root = tmp_path / "parent_lib"
        parent_kn_root = tmp_path / "parent_knowledge"

        engine = HarnessSpawnerEngine(state_file=spawns_dir / "registry.json")
        rec = engine.spawn(
            SpawnSpec(
                name="learner",
                domain="sql-audit",
                task="learn index hints",
                tree=_valid_tree("Always verify index selectivity."),
                save_dir=spawns_dir,
            )
        )

        proposal = engine.propose_merge_back(
            rec.spawn_id,
            task_id="task-01",
            cue="When full table scan exceeds 1M rows",
            lesson="Add covering composite index on filter + sort keys",
            evidence="Benchmarked 18x speedup in child trial",
            why="Prevents full table sorts in analytical queries",
            ki_id="ki-spawn-sql-audit-task-01",
        )
        assert proposal.status == "pending"

        # Child partition has library entry and draft KI; parent stores remain untouched
        assert (spawns_dir / rec.spawn_id / "library" / "sql-audit" / "INDEX.md").is_file()
        assert (spawns_dir / rec.spawn_id / "draft_kis" / proposal.ki_id / "metadata.json").is_file()
        assert (spawns_dir / rec.spawn_id / "draft_kis" / proposal.ki_id / "summary.md").is_file()
        assert not (parent_lib_root / "sql-audit").exists()
        assert not (parent_kn_root / proposal.ki_id).exists()

        # Explicit adoption promotes both ExperienceLibrary entry and dual-file KI
        adopted = engine.adopt_merge_proposal(
            proposal.proposal_id,
            parent_library_root=parent_lib_root,
            parent_knowledge_root=parent_kn_root,
        )
        assert adopted["status"] == "adopted"
        assert (parent_lib_root / "sql-audit" / "INDEX.md").is_file()
        ki_meta = parent_kn_root / proposal.ki_id / "metadata.json"
        ki_md = parent_kn_root / proposal.ki_id / "summary.md"
        assert ki_meta.is_file() and ki_md.is_file()
        meta_json = json.loads(ki_meta.read_text(encoding="utf-8"))
        assert meta_json["status"] == "adopted"
        assert meta_json["id"] == proposal.ki_id

        # Second adoption of already-adopted proposal raises ValueError
        with pytest.raises(ValueError, match="already 'adopted'"):
            engine.adopt_merge_proposal(
                proposal.proposal_id,
                parent_library_root=parent_lib_root,
                parent_knowledge_root=parent_kn_root,
            )
        engine.retire_all()

    def test_harness_spawn_cli_workflow(self, tmp_path: Path) -> None:
        """Exercise `harness spawn run | list | propose | adopt | retire` end to end."""
        runner = CliRunner()
        save_dir = tmp_path / "cli_spawns"
        lib_dir = tmp_path / "cli_lib"
        kn_dir = tmp_path / "cli_kn"

        # 1. spawn run
        res_run = runner.invoke(
            main,
            [
                "spawn",
                "run",
                "--name",
                "cli-worker",
                "--domain",
                "diagnostics",
                "--task",
                "inspect logs",
                "--save-dir",
                str(save_dir),
            ],
        )
        assert res_run.exit_code == 0, res_run.output
        run_data: dict[str, Any] = json.loads(res_run.output)
        spawn_id = run_data["spawn_id"]
        assert run_data["state"] == "RUNNING"
        assert run_data["depth"] == 1

        # 2. spawn list
        res_list = runner.invoke(main, ["spawn", "list", "--save-dir", str(save_dir)])
        assert res_list.exit_code == 0, res_list.output
        list_data = json.loads(res_list.output)
        assert list_data["count"] == 1
        assert list_data["spawns"][0]["spawn_id"] == spawn_id

        # 3. spawn propose
        res_prop = runner.invoke(
            main,
            [
                "spawn",
                "propose",
                spawn_id,
                "--task-id",
                "t-cli-1",
                "--cue",
                "when log rotation fails",
                "--lesson",
                "flush ring buffer before archive",
                "--evidence",
                "verified across 3 restarts",
                "--save-dir",
                str(save_dir),
            ],
        )
        assert res_prop.exit_code == 0, res_prop.output
        prop_data = json.loads(res_prop.output)
        proposal_id = prop_data["proposal_id"]

        # 4. spawn adopt
        res_adopt = runner.invoke(
            main,
            [
                "spawn",
                "adopt",
                proposal_id,
                "--save-dir",
                str(save_dir),
                "--library-root",
                str(lib_dir),
                "--knowledge-root",
                str(kn_dir),
            ],
        )
        assert res_adopt.exit_code == 0, res_adopt.output
        adopt_data = json.loads(res_adopt.output)
        assert adopt_data["status"] == "adopted"
        assert (kn_dir / prop_data["ki_id"] / "metadata.json").is_file()

        # 5. spawn retire
        res_retire = runner.invoke(
            main, ["spawn", "retire", spawn_id, "--save-dir", str(save_dir)]
        )
        assert res_retire.exit_code == 0, res_retire.output
        retire_data = json.loads(res_retire.output)
        assert retire_data["state"] == "RETIRED"
