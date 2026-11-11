"""Evidence tree data model and mission prompt pointer for recursive harnessing.

Distilled from google-research/harness2 `core.context`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from harness.services.recursive_harnessing.models import RunView

PoolItem = tuple[str, Path, RunView | None]


@dataclass(slots=True, frozen=True)
class EvidenceTree:
    """A built evidence tree, plus what actually landed in it."""

    root: Path
    rollouts: tuple[str, ...] = ()
    harness_files: int = 0
    library: bool = False
    pool: tuple[str, ...] = ()
    source_files: int = 0
    decisions: int = 0
    failed: tuple[str, ...] = field(default_factory=tuple)

    @property
    def layout(self) -> str:
        """The layout listing for the mission; it only mentions what exists."""
        rows = ["context/task.md                  the task as the agent received it"]
        if self.source_files:
            rows.append("context/source/                 task source materials")
        if self.decisions:
            rows.append("context/decisions/              earlier edits and composition decisions")
        if self.rollouts:
            names = ", ".join(f"{r}.md" for r in self.rollouts[:6])
            more = f" (+{len(self.rollouts) - 6} more)" if len(self.rollouts) > 6 else ""
            rows.append(f"context/rollouts/               FULL trajectories: {names}{more}")
            rows.append("context/deliverables/           the artifact each rollout produced")
        if self.harness_files:
            rows.append(f"context/harness/                the harness you are editing ({self.harness_files} files)")
        if self.pool:
            rows.append(
                f"context/pool/                   {len(self.pool)} candidates, each with its harness, diff and rollout"
            )
        if self.library:
            rows.append("context/library/                earlier tasks in this domain -- browse INDEX.md first")
        return "\n".join(rows)


def mission(tree: EvidenceTree, *, job: str) -> str:
    """The short pointer to the evidence on disk: the job, where evidence is, and 'open it'."""
    return "\n".join(
        [
            job.strip(),
            "",
            "# YOUR EVIDENCE",
            "",
            "It is on disk, in `context/`. Read it -- do not answer from this message alone.",
            "",
            tree.layout,
            "",
            "Every trajectory EVENT is present; an explicit renderer-truncation marker inside an "
            "observation is ours, not solver behaviour. Read `task.md` and the current harness first. "
            "Inventory every rollout or candidate and inspect each at least once. For a candidate, "
            "compare what changed from its editing baseline, what behaviour changed in its rollout, what "
            "improved and what regressed. Cite the specific trajectory moment behind every change; one "
            "you cannot trace to a moment is speculation.",
        ]
    )

