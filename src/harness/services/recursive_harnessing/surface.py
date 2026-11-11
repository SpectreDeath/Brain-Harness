"""The editable harness surface: read, validate, repair, write and diff component trees.

Distilled from google-research/harness2 `core.tree`. Everything that differs between agent frameworks
is data on `SurfaceSpec`; the logic exists once. The edit contract is *omitted-is-inherited*:
a proposal emits only what it changes. Validation collects **every** problem into one
`ValueError` written as actionable prose, because that message is fed back verbatim as the
proposer's retry feedback.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from harness.services.recursive_harnessing.models import SurfaceSpec, Tree
from harness.services.recursive_harnessing.surface_tree import (
    diff_summary,
    diversity,
    read_tree,
    write_tree,
)

__all__ = [
    "always_on_text",
    "autotrigger",
    "diff_summary",
    "diversity",
    "is_allowed",
    "normalize_rel",
    "read_tree",
    "skill_names",
    "subagent_names",
    "validate",
    "write_tree",
]

_NAME = r"[a-z0-9][a-z0-9_\-]*"


@lru_cache(maxsize=16)
def _rx(spec: SurfaceSpec) -> dict[str, re.Pattern[str]]:
    sd, ad, cd = (re.escape(x) for x in (spec.skill_dir, spec.subagent_dir, spec.scripts_dir))
    return {
        "skill": re.compile(rf"{sd}/({_NAME})/SKILL\.md"),
        "skill_script": re.compile(rf"{sd}/{_NAME}/scripts/[A-Za-z0-9_.\-]+"),
        "subagent": re.compile(rf"{ad}/({_NAME})/AGENT\.md"),
        "script": re.compile(rf"{cd}/[a-z0-9_][a-z0-9_]*\.py"),
        "script_ref": re.compile(rf"(?:python3?\s+)((?:{sd}/[\w\-]+/)?{cd}/[\w.\-]+\.py)"),
    }


def normalize_rel(rel: str) -> str:
    """Normalise a relative path, rejecting escapes before it is joined to a directory."""
    r = str(rel).strip().replace("\\", "/")
    if r.startswith("/") or ".." in r.split("/"):
        raise ValueError(f"path escapes the harness: {rel!r}")
    while r.startswith("./"):
        r = r[2:]
    return r.strip("/")


def is_allowed(spec: SurfaceSpec, rel: str) -> bool:
    """Whether this path is on the editable surface. A predicate: it never raises."""
    try:
        rel = normalize_rel(rel)
    except ValueError:
        return False
    if rel in spec.always_on:
        return True
    return any(rx.fullmatch(rel) for k, rx in _rx(spec).items() if k != "script_ref")


def skill_names(spec: SurfaceSpec, tree: Tree) -> list[str]:
    rx = _rx(spec)["skill"]
    return sorted({m.group(1) for rel in tree if (m := rx.fullmatch(rel))})


def subagent_names(spec: SurfaceSpec, tree: Tree) -> list[str]:
    rx = _rx(spec)["subagent"]
    return sorted({m.group(1) for rel in tree if (m := rx.fullmatch(rel))})


def always_on_text(spec: SurfaceSpec, tree: Tree) -> str:
    return "\n\n".join(tree.get(a, "") for a in spec.always_on)


def _frontmatter(text: str) -> str:
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    return m.group(1) if m else text[:600]


def _description(text: str) -> str | None:
    m = re.search(r"^description:\s*(\S.*)$", _frontmatter(text), re.M)
    return m.group(1).strip() if m else None


def autotrigger(spec: SurfaceSpec, tree: Tree) -> list[str]:
    """Give every skill a trigger line in always-on text; return the names repaired.

    A line that would push the body over the cap is skipped instead of truncating anything.
    """
    fixed: list[str] = []
    for name in skill_names(spec, tree):
        if name in always_on_text(spec, tree):
            continue
        desc = (
            _description(tree.get(f"{spec.skill_dir}/{name}/SKILL.md", "")) or f"the {name} workflow applies"
        ).rstrip(".")
        line = spec.trigger_line.format(name=name, desc=desc)
        if len(always_on_text(spec, tree)) + len(line) + 2 > spec.always_on_max:
            continue
        cur = tree.get(spec.always_on[0], "")
        tree[spec.always_on[0]] = (cur.rstrip() + "\n" + line) if cur.strip() else line
        fixed.append(name)
    return fixed


def _check_skills(spec: SurfaceSpec, tree: Tree, body: str, errs: list[str]) -> list[str]:
    skills = skill_names(spec, tree)
    for name in skills:
        rel = f"{spec.skill_dir}/{name}/SKILL.md"
        text = tree[rel]
        desc = _description(text)
        if desc is None:
            errs.append(f"{rel} needs a `description:` in its frontmatter, or the skill is dropped SILENTLY at load")
        elif spec.description_bounds:
            lo, hi = spec.description_bounds
            if not lo <= len(desc) <= hi:
                errs.append(f"{rel} description is {len(desc)} chars; the catalog budget requires {lo}-{hi}")
            if "do not use" not in desc.lower():
                errs.append(f"{rel} description must state a negative boundary ('Do not use for ...')")
        m_name = re.search(r"^name:\s*(\S+)\s*$", _frontmatter(text), re.M)
        if not (m_name and m_name.group(1) == name):
            errs.append(
                f"{rel} needs frontmatter `name: {name}` matching its directory (a "
                f"mismatch is dropped SILENTLY at load)"
            )
        if spec.require_always_on_triggers and name not in body:
            errs.append(
                f"skill '{name}' is never named in the always-on text, so the agent will "
                f"not know to invoke it -- add a line such as: "
                f"{spec.trigger_line.format(name=name, desc='<trigger>')}"
            )
    return skills


def _check_scripts(spec: SurfaceSpec, tree: Tree, errs: list[str]) -> None:
    r = _rx(spec)
    have = {rel for rel in tree if r["script"].fullmatch(rel) or r["skill_script"].fullmatch(rel)}
    for rel, src in tree.items():
        if r["script"].fullmatch(rel):
            try:
                compile(src, rel, "exec")
            except (SyntaxError, ValueError) as exc:
                where = f" (line {exc.lineno})" if isinstance(exc, SyntaxError) else ""
                errs.append(f"{rel} does not compile: {type(exc).__name__}: {exc}{where}"[:200])
        if not (r["skill"].fullmatch(rel) or rel in spec.always_on):
            continue
        m_skill = r["skill"].fullmatch(rel)
        for ref in r["script_ref"].findall(src):
            if ref.rsplit("/", 1)[-1] in spec.reserved_scripts or ref in have:
                continue
            if m_skill and ref.startswith(f"{spec.scripts_dir}/"):
                if f"{spec.skill_dir}/{m_skill.group(1)}/{ref}" in have:
                    continue
            errs.append(f"{rel} invokes `{ref}` but that file is not in the harness")


def validate(spec: SurfaceSpec, tree: Tree) -> dict:
    """Raise ValueError listing every problem; return a census of the validated tree."""
    errs: list[str] = []
    body = always_on_text(spec, tree)
    if len(body) > spec.always_on_max:
        errs.append(
            f"always-on content is {len(body)} chars, over the {spec.always_on_max} cap; "
            f"it is paid for on every run, so cut before you add"
        )
    if not body.strip():
        errs.append(f"{spec.always_on[0]} is empty -- a harness with no always-on text does not exist")
    skills = _check_skills(spec, tree, body, errs)
    subs = subagent_names(spec, tree)
    if subs and not spec.allow_subagents:
        errs.append(f"sub_agents are not available on this deployment: {subs}")
    _check_scripts(spec, tree, errs)
    if errs:
        raise ValueError(" | ".join(errs))
    return {
        "always_on_chars": len(body),
        "n_files": len(tree),
        "skills": len(skills),
        "sub_agents": len(subs),
        "scripts": sum(1 for r in tree if _rx(spec)["script"].fullmatch(r)),
    }
