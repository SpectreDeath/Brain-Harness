"""The per-domain experience library: what earlier tasks in a domain produced.

Distilled from google/harness2 `core.library` (the *harnessing-level recursion* store).

    <root>/<domain>/INDEX.md
    <root>/<domain>/harnesses/<task>/harness/<rel>   the full adopted tree -- never a summary
    <root>/<domain>/harnesses/<task>/EXPERIENCE.md   why it was picked + one supported lesson

Retrieval is by construction: a domain directory only ever holds same-domain entries. An entry
is stored only when it carries a *supported* lesson (cue + lesson + evidence), so the library
never fills with unattributed folklore; trees and rationales pass the verdict tripwire first.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.guards import assert_tree_clean
from harness.services.recursive_harnessing.models import SurfaceSpec, Tree

_LESSON_FIELDS = ("cue", "lesson", "evidence", "confidence")


def slug(task_id: str) -> str:
    return task_id.replace("/", "__").replace("\\", "__")


def domain_dir(domain: str) -> str:
    """One directory name for a domain, never a path."""
    return re.sub(r"\s*[/\\]\s*", "__", domain).strip() or "unknown"


def has_experience(experience: dict | None) -> bool:
    return isinstance(experience, dict) and all(
        isinstance(experience.get(k), str) and experience[k].strip() for k in ("cue", "lesson", "evidence")
    )


def _field(path: Path, name: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(f"- **{name}**:"):
            return line.split(":", 1)[1].strip()
    return ""


def _inventory(spec: SurfaceSpec, tree: Tree) -> str:
    """A one-line census of the components actually in a harness."""
    skills = len(S.skill_names(spec, tree))
    subs = len(S.subagent_names(spec, tree))
    scripts = sum(1 for r in tree if r.startswith(spec.scripts_dir + "/"))
    bits = [f"{n} {k}" for k, n in (("skills", skills), ("sub_agents", subs), ("scripts", scripts)) if n]
    return f"{', '.join(bits) or 'always-on edits only'}; {len(S.always_on_text(spec, tree)):,} always-on chars"


@dataclass(slots=True)
class ExperienceLibrary:
    """One (run, domain) library: read before each task, appended after."""

    root: Path
    domain: str
    surface: SurfaceSpec

    @property
    def dir(self) -> Path:
        return Path(self.root) / domain_dir(self.domain)

    @property
    def index(self) -> Path:
        return self.dir / "INDEX.md"

    def entry_dir(self, task_id: str) -> Path:
        return self.dir / "harnesses" / slug(task_id)

    def exists(self) -> bool:
        return self.index.is_file()

    def entries(self) -> list[str]:
        d = self.dir / "harnesses"
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.is_dir() else []

    def context_dir(self) -> Path | None:
        """The directory handed to an improver session, or None when this domain is empty."""
        return self.dir if self.exists() and any(self.dir.rglob("EXPERIENCE.md")) else None

    def tree_of(self, task_id: str) -> Tree:
        return S.read_tree(self.surface, self.entry_dir(task_id) / "harness")

    def forget(self, task_ids: Sequence[str]) -> None:
        """Drop entries for these tasks and rebuild INDEX.md; unknown tasks are ignored."""
        removed = False
        for tid in task_ids:
            d = self.entry_dir(tid)
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
                removed = True
        if removed:
            self.rebuild_index()

    def retain(self, task_ids: Sequence[str]) -> None:
        """Keep only entries preceding the current task in this stream (no future leakage)."""
        keep = {slug(t) for t in task_ids}
        self.forget([e for e in self.entries() if e not in keep])

    def add(
        self,
        task_id: str,
        harness: Tree,
        *,
        why: str = "",
        label: str = "",
        run_id: str = "",
        experience: dict | None = None,
    ) -> Path | None:
        """Store one adopted harness and why; None when it carries no supported lesson."""
        if not has_experience(experience):
            return None
        exp = experience or {}
        assert_tree_clean(harness)
        assert_tree_clean({"EXPERIENCE.md": str(exp) + why})
        d = self.entry_dir(task_id)
        shutil.rmtree(d / "harness", ignore_errors=True)
        S.write_tree(self.surface, harness, d / "harness")
        lines = [
            f"# {task_id}",
            "",
            f"- adopted: `{label}`" + (f"  (run `{run_id}`)" if run_id else ""),
            f"- components: {_inventory(self.surface, harness)}",
            "",
        ]
        if why.strip():
            lines += ["## Why this was chosen", why.strip(), ""]
        if exp.get("edits"):
            lines += ["## What each edit did", str(exp["edits"]).strip(), ""]
        lines += ["## Transferable lesson"]
        lines += [f"- **{f}**: {str(exp[f]).strip()}" for f in _LESSON_FIELDS if exp.get(f)] + [""]
        (d / "EXPERIENCE.md").write_text("\n".join(lines), encoding="utf-8")
        self.rebuild_index()
        return d

    def rebuild_index(self) -> Path:
        """Regenerate INDEX.md from what is on disk."""
        rows = [
            f"# Library -- {self.domain}",
            "",
            "Each entry is an earlier task in THIS domain whose harness was chosen, stored with "
            "its FULL component tree and why it was picked. Browse this index, then open the "
            "entries that look relevant to the matter in front of you.",
            "",
        ]
        names = self.entries()
        if not names:
            rows.append("_(empty -- this is the first task in this domain)_")
        for name in names:
            ed = self.dir / "harnesses" / name
            tree = S.read_tree(self.surface, ed / "harness")
            rows += [
                f"## `harnesses/{name}/`",
                f"- harness: `harnesses/{name}/harness/` -- {_inventory(self.surface, tree)}",
                f"- why:     `harnesses/{name}/EXPERIENCE.md`",
            ]
            if cue := _field(ed / "EXPERIENCE.md", "cue"):
                rows.append(f"- cue:     {cue}")
            rows.append("")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.index.write_text("\n".join(rows), encoding="utf-8")
        return self.index


def library_root(base: Path | str, *, benchmark: str, k: int, variant: str = "", tag: str = "") -> Path:
    """Per-run library root `<base>/<benchmark>/k<k>[-variant]`; an explicit `tag` shares one."""
    if tag:
        return Path(base) / benchmark / tag
    return Path(base) / benchmark / "-".join([f"k{int(k)}"] + ([variant] if variant else []))
