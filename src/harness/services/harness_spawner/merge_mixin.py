"""HarnessSpawnerEngine mixin module: merge_mixin."""

from __future__ import annotations

import dataclasses
import uuid
from pathlib import Path
from typing import Any

from harness.services.recursive_harnessing import (
    guards,
    surface as surface_ops,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import (
    BRAIN_SURFACE,
    Tree,
)

from .models import (
    SpawnLifecycleState,
    SpawnMergeProposal,
)
from .helpers import (
    _slugify,
    _write_ki_dual_file,
)


class _SpawnerMergeMixin:
    """Mixin supplying merge mixin operations."""

    def propose_merge_back(
        self,
        spawn_id: str,
        *,
        task_id: str,
        cue: str,
        lesson: str,
        evidence: str,
        why: str = "",
        tree: Tree | None = None,
        ki_id: str = "",
    ) -> SpawnMergeProposal:
        """Stage a validated learning in the child's ExperienceLibrary & draft_kis partition."""
        rec = self._require_record(spawn_id)
        if rec.state == SpawnLifecycleState.FAILED:
            raise RuntimeError(f"Cannot propose merge-back from FAILED spawn '{spawn_id}'")

        handle = self._handles.get(spawn_id)
        surface = handle.surface if handle is not None else BRAIN_SURFACE
        candidate_tree: dict[str, str]
        if tree is not None:
            candidate_tree = dict(tree)
        elif handle is not None:
            candidate_tree = dict(handle.tree)
        else:
            candidate_tree = surface_ops.read_tree(surface, Path(rec.save_dir) / "harness")

        guards.assert_tree_clean(candidate_tree)
        surface_ops.validate(surface, candidate_tree)

        lib = self.get_child_library(spawn_id)
        assert lib is not None
        staged_path = lib.add(
            task_id,
            candidate_tree,
            why=why,
            label=rec.name,
            run_id=spawn_id,
            experience={"cue": cue, "lesson": lesson, "evidence": evidence},
        )
        if staged_path is None:
            raise ValueError("Failed to stage child ExperienceLibrary entry: unsupported lesson")

        resolved_ki_id = ki_id.strip() or f"ki-spawn-{_slugify(rec.domain)}-{_slugify(task_id)}"
        proposal_id = f"prop_{_slugify(task_id)}_{uuid.uuid4().hex[:8]}"
        proposal = SpawnMergeProposal(
            proposal_id=proposal_id,
            spawn_id=spawn_id,
            domain=rec.domain,
            task_id=task_id,
            tree=candidate_tree,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            ki_id=resolved_ki_id,
            status="pending",
        )

        draft_dir = Path(rec.save_dir) / "draft_kis" / resolved_ki_id
        _write_ki_dual_file(
            draft_dir,
            ki_id=resolved_ki_id,
            title=f"Spawn Learning: {rec.domain} ({task_id})",
            domain=rec.domain,
            spawn_id=spawn_id,
            task_id=task_id,
            proposal_id=proposal_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            status="draft",
        )

        self._proposals[proposal_id] = proposal
        self._save_state()
        return proposal

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
    ) -> dict[str, Any]:
        """Explicitly adopt a pending child proposal into parent ExperienceLibrary & Knowledge Vault."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"Unknown merge proposal: {proposal_id!r}")
        if proposal.status != "pending":
            raise ValueError(f"Proposal '{proposal_id}' is already {proposal.status!r} and cannot be re-adopted")

        rec = self._require_record(proposal.spawn_id)
        handle = self._handles.get(proposal.spawn_id)
        surface = handle.surface if handle is not None else BRAIN_SURFACE

        guards.assert_tree_clean(proposal.tree)
        surface_ops.validate(surface, proposal.tree)

        lib_root = Path(parent_library_root) if parent_library_root is not None else Path(".harness/experience")
        parent_lib = ExperienceLibrary(root=lib_root, domain=proposal.domain, surface=surface)
        lib_entry = parent_lib.add(
            proposal.task_id,
            dict(proposal.tree),
            why=proposal.why,
            label=rec.name,
            run_id=proposal.spawn_id,
            experience={
                "cue": proposal.cue,
                "lesson": proposal.lesson,
                "evidence": proposal.evidence,
            },
        )
        if lib_entry is None:
            raise ValueError(f"Parent library rejected proposal '{proposal_id}'")

        kn_root = Path(parent_knowledge_root) if parent_knowledge_root is not None else Path(".harness/knowledge")
        ki_dir = kn_root / proposal.ki_id
        _write_ki_dual_file(
            ki_dir,
            ki_id=proposal.ki_id,
            title=f"Spawn Learning: {proposal.domain} ({proposal.task_id})",
            domain=proposal.domain,
            spawn_id=proposal.spawn_id,
            task_id=proposal.task_id,
            proposal_id=proposal.proposal_id,
            cue=proposal.cue,
            lesson=proposal.lesson,
            evidence=proposal.evidence,
            why=proposal.why,
            status="adopted",
        )

        adopted = dataclasses.replace(proposal, status="adopted")
        self._proposals[proposal_id] = adopted
        self._save_state()
        return {
            "proposal_id": proposal_id,
            "status": "adopted",
            "domain": proposal.domain,
            "library_entry": str(lib_entry),
            "knowledge_dir": str(ki_dir),
            "ki_id": proposal.ki_id,
        }

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]:
        items = list(self._proposals.values())
        if status is not None:
            items = [p for p in items if p.status == status]
        return items


__all__ = ["_SpawnerMergeMixin"]
