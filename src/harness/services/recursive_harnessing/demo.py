"""A deterministic, credential-free demo of the whole loop (no model, real file I/O).

`DemoAdapter` simulates an agent whose output depends on the harness it runs under;
`ScriptedProposer` makes deterministic edits (INV adds a checklist skill, DOM adds a domain
skill, composers merge the pool). Together they exercise parallel and sequential recursion,
blind selection, the experience library and the budget identity end to end -- and they are the
test fixtures for the contract suite. Mirrors google/harness2 `harness2-demo`.
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.identity import inputs_fingerprint, is_complete, mark_complete
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import ProposalReply, SelectorChoice, SurfaceSpec, Tree
from harness.services.recursive_harnessing.recursion import roll, run_mode
from harness.services.recursive_harnessing.selection import blind_select, selection_pool, trivial_selection

DEMO_TASK = "demo/t1"
_SPEC = SurfaceSpec(name="demo", always_on=("AGENTS.md",), always_on_max=2000, skill_dir="skills")
_SKILLS = {
    "checklist": (
        "Before finishing, cross-check every total against its rows",
        "Totals cross-checked: 3 of 3 rows match.",
    ),
    "domain_notes": ("Define each financial term the reader must know", "Key terms defined: revenue, margin."),
}


class DemoAdapter:
    """A tiny file-backed task adapter whose deliverable improves with the harness skills."""

    leak_globs: tuple[str, ...] = ("answer_key*",)
    work = "Summarize the quarterly report for a finance reader, with verified totals."
    deliverable = "summary"

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.surface = _SPEC

    def task_prompt(self, task_id: str) -> str:
        return f"Task {task_id}: summarize the quarterly report and state the verified totals."

    def task_files(self, task_id: str) -> Path | None:
        return None

    def execute(self, task_id: str, harness_dir: Path | None, run_id: str) -> Path:
        rd = self.root / "runs" / run_id
        inputs = inputs_fingerprint(self.task_prompt(task_id), None)
        if is_complete(rd, harness_dir=harness_dir, inputs=inputs):
            return rd
        shutil.rmtree(rd, ignore_errors=True)
        rd.mkdir(parents=True)
        tree = S.read_tree(self.surface, harness_dir) if harness_dir else {}
        lines, steps = ["Quarterly summary: revenue up 4%."], ["[ACTION] read report", "[OBSERVATION] 3 rows"]
        for name, (_, line) in _SKILLS.items():
            if f"skills/{name}/SKILL.md" in tree:
                lines.append(line)
                steps.append(f"[ACTION] apply skill {name}")
        (rd / "deliverable.txt").write_text("\n".join(lines), encoding="utf-8")
        (rd / "trajectory.md").write_text("\n".join(steps + ["[ACTION] write deliverable"]), encoding="utf-8")
        mark_complete(rd, run_id=run_id, harness_dir=harness_dir, inputs=inputs)
        return rd

    def delivered(self, run_dir: Path) -> bool:
        f = Path(run_dir) / "deliverable.txt"
        return f.is_file() and bool(f.read_text(encoding="utf-8").strip())

    def trajectory(self, run_dir: Path) -> str:
        return (Path(run_dir) / "trajectory.md").read_text(encoding="utf-8")

    def deliverable_text(self, run_dir: Path) -> str:
        return (Path(run_dir) / "deliverable.txt").read_text(encoding="utf-8")

    def validate_tree(self, tree: Tree) -> None:
        return None


def _skill_md(name: str) -> str:
    return f"---\nname: {name}\ndescription: {_SKILLS[name][0]}\n---\nApply this on every summary.\n"


class ScriptedProposer:
    """Deterministic editor: INV -> checklist, DOM -> domain_notes, composers merge the pool."""

    def propose(self, mission: str, evidence_root: Path, label: str) -> ProposalReply:
        harness = Path(evidence_root) / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        stem = label.split(".")[0]
        if stem.startswith(("inv", "dom")):
            names = ["checklist" if stem.startswith("inv") else "domain_notes"]
            note = f"added {names[0]} skill (moment: base trajectory never cross-checked totals)"
        else:
            names = sorted({p.parent.name for p in (Path(evidence_root) / "pool").glob("*/harness/skills/*/SKILL.md")})
            note = f"merged skills from pool: {', '.join(names) or 'none'}"
        for name in names:
            target = harness / "skills" / name / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text(_skill_md(name), encoding="utf-8")
        return ProposalReply(text=f"<notes>{note}</notes>", workspace=harness, cost_usd=0.01)


class LongestSelector:
    """Deterministic blind selector: prefers the candidate artifact with the most content."""

    def choose(self, task_text: str, candidates: Mapping[str, str]) -> SelectorChoice:
        best = max(sorted(candidates), key=lambda c: len(candidates[c]))
        return SelectorChoice(anon_id=best, why="most complete artifact", cost_usd=0.0)


def run_demo(output: Path | str, k: int = 1, mode: str = "both") -> dict:
    """Run recursion + selection + library for each requested mode; return a JSON-able summary."""
    out = Path(output)
    adapter, proposer = DemoAdapter(out / "bench"), ScriptedProposer()
    base_tree: Tree = {"AGENTS.md": "Summarize the report. Verify the numbers."}
    summary: dict = {}
    for m in ("agg", "seq") if mode == "both" else (mode,):
        wd = out / m
        rid = lambda label, m=m: f"{m}-{label}"  # noqa: E731 - tiny closure over the mode token
        base = [roll(adapter, DEMO_TASK, f"base{i}", None, rid, wd) for i in range(1, k + 1)]
        res = run_mode(
            m, DEMO_TASK, k, base, adapter=adapter, proposer=proposer, work_dir=wd, run_id_of=rid, base_tree=base_tree
        )
        finals = selection_pool(m, k, res.rollouts, base)
        if k == 1:
            sel = trivial_selection(DEMO_TASK, k, m, finals, adapter=adapter, work_dir=wd)
        else:
            sel = blind_select(DEMO_TASK, k, m, finals, adapter=adapter, selector=LongestSelector(), work_dir=wd)
        lib = ExperienceLibrary(out / "library" / m, "demo/domain", adapter.surface)
        if sel.ok:
            lib.add(
                DEMO_TASK,
                res.trees[sel.chosen_label],
                why=sel.why,
                label=sel.chosen_label,
                run_id=sel.chosen_run_id,
                experience={
                    "cue": "summary needs numeric reconciliation",
                    "lesson": "add a checklist skill and a domain_notes skill, named in AGENTS.md",
                    "evidence": f"{sel.chosen_label} delivered reconciled lines the base rollout lacked",
                },
            )
        summary[m] = res.to_dict() | {"selection": asdict(sel), "library_entries": lib.entries()}
    return summary
