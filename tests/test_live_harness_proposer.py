"""Unit & contract tests for LiveHarnessProposer, diff review trust boundary, and guards (Track 1.4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from harness.kernel.context import ServiceContext
from harness.services.harness_spawner import (
    HarnessSpawnerEngine,
    SpawnLifecycleState,
    SpawnSpec,
    build_tree_diff_review,
    compute_tree_sha256,
)
from harness.services.llm import LLM_SERVICE_KEY, LLMMessage, LLMResponse, LLMService
from harness.services.recursive_harnessing import (
    BRAIN_SURFACE,
    HarnessProposer,
    LiveHarnessProposer,
    ProposerError,
)


class _FakeLLMService(LLMService):
    """Deterministic fake LLMService for credential-free unit tests."""

    def __init__(self, reply_text: str) -> None:
        self.reply_text = reply_text
        self.calls: list[list[LLMMessage]] = []

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        self.calls.append(messages)
        return LLMResponse(content=self.reply_text, model="fake-model", usage={"total_tokens": 120})

    async def stream(self, messages: list[LLMMessage], **kwargs: Any):  # type: ignore[override]
        yield self.reply_text


@pytest.mark.unit
class TestLiveHarnessProposerAndDiffReview:
    """Verify live proposer protocol conformance, isolation guards, and diff-review digest gate."""

    def test_live_proposer_edits_harness_in_place_via_llm_service(self, tmp_path: Path) -> None:
        payload = json.dumps(
            {
                "notes": "Added domain verification skill trigger.",
                "files": {
                    "AGENTS.md": "# Child Harness\n\nAlways verify outputs using `verify_domain`.\n",
                    ".agents/skills/verify_domain/SKILL.md": (
                        "---\nname: verify_domain\n"
                        "description: Verify domain invariants and reconcile totals before reporting results. "
                        "Do not use for unrelated prose tasks.\n"
                        "---\nCheck every invariant.\n"
                    ),
                },
            }
        )
        ctx = ServiceContext()
        fake_llm = _FakeLLMService(f"```json\n{payload}\n```")
        ctx.provide(LLM_SERVICE_KEY, fake_llm)

        proposer = LiveHarnessProposer(context=ctx)
        assert isinstance(proposer, HarnessProposer)

        tree, reply = proposer.propose_tree_from_description(
            "Build a domain verification harness",
            tmp_path / "prop_work",
        )
        assert ".agents/skills/verify_domain/SKILL.md" in tree
        assert "<notes>Added domain verification skill trigger.</notes>" in reply.text
        assert len(fake_llm.calls) == 1

    def test_live_proposer_rejects_verdict_leaks_and_off_surface_paths(self, tmp_path: Path) -> None:
        ev_root = tmp_path / "ev"
        (ev_root / "harness").mkdir(parents=True)
        (ev_root / "grader_verdict.json").write_text('{"pass_rate": 0.5}', encoding="utf-8")

        proposer = LiveHarnessProposer(complete_fn=lambda _: '{"notes": "noop", "files": {}}')
        with pytest.raises(ProposerError, match="isolation"):
            proposer.propose("Fix task", ev_root, "lbl1")

        clean_root = tmp_path / "clean_ev"
        (clean_root / "harness").mkdir(parents=True)
        escape_proposer = LiveHarnessProposer(
            complete_fn=lambda _: '{"notes": "bad", "files": {"../outside.py": "print(1)"}}'
        )
        with pytest.raises(ProposerError):
            escape_proposer.propose("Fix task", clean_root, "lbl2")

        off_surface = LiveHarnessProposer(
            complete_fn=lambda _: '{"notes": "bad", "files": {"random_root.py": "print(1)"}}'
        )
        with pytest.raises(ProposerError, match="off-surface"):
            off_surface.propose("Fix task", clean_root, "lbl3")

    def test_diff_review_digest_gate_and_probe_failure_record_failed(self, tmp_path: Path) -> None:
        base_tree = {"AGENTS.md": "# Base\n\nInitial text.\n"}
        proposed_tree = {"AGENTS.md": "# Base\n\nUpdated with write-capable instructions.\n"}
        review = build_tree_diff_review(BRAIN_SURFACE, base_tree, proposed_tree)
        assert review.modified == ("AGENTS.md",)
        assert "--- a/AGENTS.md" in review.unified_diff
        assert "+++ b/AGENTS.md" in review.unified_diff
        assert review.tree_sha256 == compute_tree_sha256(proposed_tree)
        assert not review.approved

        engine = HarnessSpawnerEngine(state_file=tmp_path / "registry.json")

        # 1. write_permitted=True without approved digest fails fail-closed
        unapproved = engine.spawn(
            SpawnSpec(
                name="unapproved-writer",
                domain="ops",
                tree=proposed_tree,
                save_dir=tmp_path / "spawns",
                write_permitted=True,
                approved_tree_digest=None,
            )
        )
        assert unapproved.state == SpawnLifecycleState.FAILED
        assert not unapproved.trial.passed  # type: ignore[union-attr]
        assert "approved_tree_digest" in unapproved.error

        # 2. Mismatched / drifted digest fails admission
        drifted = engine.spawn(
            SpawnSpec(
                name="drifted-writer",
                domain="ops",
                tree=proposed_tree,
                save_dir=tmp_path / "spawns",
                write_permitted=True,
                approved_tree_digest="0" * 64,
            )
        )
        assert drifted.state == SpawnLifecycleState.FAILED
        assert "drift" in drifted.error.lower()

        # 3. Failing k=1 probe blocks spawn with FAILED recorded
        probe_fail = engine.spawn(
            SpawnSpec(
                name="probe-fail",
                domain="ops",
                tree=proposed_tree,
                save_dir=tmp_path / "spawns",
                write_permitted=True,
                approved_tree_digest=review.tree_sha256,
            ),
            probe_fn=lambda spec, ctx: False,
        )
        assert probe_fail.state == SpawnLifecycleState.FAILED
        assert "probe" in probe_fail.error.lower()

        # 4. Approved digest + passing probe succeeds
        approved = engine.spawn(
            SpawnSpec(
                name="approved-writer",
                domain="ops",
                tree=proposed_tree,
                save_dir=tmp_path / "spawns",
                write_permitted=True,
                approved_tree_digest=review.tree_sha256,
            ),
            probe_fn=lambda spec, ctx: True,
        )
        assert approved.state == SpawnLifecycleState.RUNNING
        assert approved.trial is not None and approved.trial.passed
        engine.retire_all()
