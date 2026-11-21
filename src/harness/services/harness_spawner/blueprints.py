"""Deterministic graph-to-blueprint recommender and L0 tree builder (Rules 12, 43, 49)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

from ._blueprint_catalog import CANONICAL_SPECS, VALID_ICM_FORMS

DEFAULT_MAX_BLUEPRINT_SKILLS = 5
HARD_MAX_BLUEPRINT_SKILLS = 6
PRIME_SKILL_BASELINE_FALLBACK = 114


def cluster_skills_cmd(*, min_cluster_size: int = 2, root_path: str | Path = ".") -> dict[str, Any]:
    """Read functional skill clusters from the skill graph service without command-layer imports."""
    from harness.services.skill_graph import get_default_skill_registry

    registry = get_default_skill_registry(root_dir=str(root_path))
    clusters = registry.cluster_skills(min_cluster_size=min_cluster_size)
    return {
        "status": "ok",
        "total_clusters": len(clusters),
        "clusters": [c.model_dump() for c in clusters],
    }


def get_cross_cluster_bridges_cmd(*, root_path: str | Path = ".") -> dict[str, Any]:
    """Read cross-cluster macro bridges from the skill graph service cleanly."""
    from harness.services.skill_graph import get_default_skill_registry

    registry = get_default_skill_registry(root_dir=str(root_path))
    bridges = registry.get_cross_cluster_bridges()
    return {
        "status": "ok",
        "total_bridges": len(bridges),
        "bridges": [b.model_dump() for b in bridges],
    }


def query_knowledge_and_skills(
    topic: str,
    *,
    vault_dir: str = ".harness/knowledge",
    root_path: str = ".",
    limit: int = 8,
) -> dict[str, Any]:
    """Lazy wrapper over dual-graph joint query preserving test patching seams."""
    from harness.services.skill_graph.joint_query import query_knowledge_and_skills as _impl

    return _impl(topic, vault_dir=vault_dir, root_path=root_path, limit=limit)


@dataclass(slots=True, frozen=True)
class SeededKI:
    """Verified Knowledge Item reference attached to a spawned domain harness blueprint."""

    ki_id: str
    title: str
    domain: str
    isnad_status: str
    status: str = "ACTIVE"

    def to_dict(self) -> dict[str, str]:
        return {
            "ki_id": self.ki_id,
            "title": self.title,
            "domain": self.domain,
            "isnad_status": self.isnad_status,
            "status": self.status,
        }


@dataclass(slots=True, frozen=True)
class HarnessBlueprint:
    """Scored, bounded domain harness specification derived from live graph topology."""

    name: str
    domain: str
    title: str
    mission: str
    icm_form: str
    skills: tuple[str, ...]
    graph_source: str
    cohesion_score: float
    bridge_count: int
    score: float
    seeded_kis: tuple[SeededKI, ...]
    excluded_unverified_kis: tuple[str, ...]
    use_cases: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    prime_skill_count: int = PRIME_SKILL_BASELINE_FALLBACK
    estimated_token_savings_pct: float = 0.0

    def __post_init__(self) -> None:
        if not 1 <= len(self.skills) <= HARD_MAX_BLUEPRINT_SKILLS:
            raise ValueError(
                f"Blueprint skills count must be in [1, {HARD_MAX_BLUEPRINT_SKILLS}], got {len(self.skills)}"
            )
        if self.icm_form not in VALID_ICM_FORMS:
            raise ValueError(f"Invalid ICM form {self.icm_form!r}")
        for ki in self.seeded_kis:
            if ki.isnad_status.upper() != "VERIFIED":
                raise ValueError(f"Only VERIFIED KIs may be seeded; got {ki.ki_id!r} ({ki.isnad_status})")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "title": self.title,
            "mission": self.mission,
            "icm_form": self.icm_form,
            "skills": list(self.skills),
            "skill_count": len(self.skills),
            "graph_source": self.graph_source,
            "cohesion_score": self.cohesion_score,
            "bridge_count": self.bridge_count,
            "score": self.score,
            "seeded_kis": [k.to_dict() for k in self.seeded_kis],
            "excluded_unverified_kis": list(self.excluded_unverified_kis),
            "use_cases": list(self.use_cases),
            "out_of_scope": list(self.out_of_scope),
            "prime_skill_count": self.prime_skill_count,
            "estimated_token_savings_pct": self.estimated_token_savings_pct,
        }


_GENERIC_DOMAIN_TOKENS = frozenset({"and", "general", "engineering", "software", "developer", "experience"})


def _domain_tokens(val: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", val.lower()) if len(t) >= 4 and t not in _GENERIC_DOMAIN_TOKENS}


def _collect_kis(
    keywords: tuple[str, ...], *, domain: str = "", vault_dir: str, root_path: str
) -> tuple[tuple[SeededKI, ...], tuple[str, ...]]:
    seen_verified: dict[str, SeededKI] = {}
    scores: dict[str, float] = {}
    matched_tags_or_titles: set[str] = set()
    excluded: set[str] = set()
    bp_tokens = _domain_tokens(domain)

    for kw in keywords:
        kw_low = kw.lower()
        res = query_knowledge_and_skills(kw, vault_dir=vault_dir, root_path=root_path, limit=8)
        for rank_idx, item in enumerate(res.get("knowledge_items") or []):
            ki_id = str(item.get("ki_id") or "").strip()
            if not ki_id or ki_id.startswith("ki-rea-sig-"):
                continue
            isnad_status = str(item.get("isnad_status") or "UNKNOWN").upper()
            if isnad_status != "VERIFIED":
                excluded.add(ki_id)
                continue
            title = str(item.get("title") or ki_id)
            ki_domain = str(item.get("domain") or "general")
            tags = [str(t).lower() for t in (item.get("tags") or [])]
            if ki_id not in seen_verified:
                seen_verified[ki_id] = SeededKI(
                    ki_id=ki_id,
                    title=title,
                    domain=ki_domain,
                    isnad_status=isnad_status,
                    status=str(item.get("status") or "ACTIVE").upper(),
                )
                scores[ki_id] = 3.0 if (bp_tokens & _domain_tokens(ki_domain)) else 0.0

            delta = 1.0 + max(0.0, (8 - rank_idx) * 0.1)
            if kw_low in title.lower():
                delta += 3.0
                matched_tags_or_titles.add(ki_id)
            if kw_low in ki_domain.lower() or any(kw_low in t for t in tags):
                delta += 2.0
                matched_tags_or_titles.add(ki_id)
            scores[ki_id] += delta

    for ki_id, ki in seen_verified.items():
        if ki_id not in matched_tags_or_titles and not (bp_tokens & _domain_tokens(ki.domain)):
            scores[ki_id] -= 2.0

    verified = tuple(sorted(seen_verified.values(), key=lambda k: (-scores[k.ki_id], k.ki_id))[:6])
    return verified, tuple(sorted(excluded))


def _count_bridges(cluster_id: str, skills: tuple[str, ...], bridges: list[dict[str, Any]]) -> int:
    skill_set = set(skills)
    count = 0
    for b in bridges:
        if b.get("source_cluster") == cluster_id or b.get("target_cluster") == cluster_id:
            count += 1
            continue
        pairs = b.get("bridge_skills") or []
        if any(str(s) in skill_set for pair in pairs for s in pair):
            count += 1
    return count


def recommend_harness_blueprints(
    *,
    root_path: Path | str = ".",
    vault_dir: Path | str = ".harness/knowledge",
    max_skills: int = DEFAULT_MAX_BLUEPRINT_SKILLS,
    limit: int = 8,
    name: str | None = None,
) -> list[HarnessBlueprint]:
    """Discover, filter, and deterministically rank domain harness blueprints from live graph data."""
    if not 1 <= max_skills <= HARD_MAX_BLUEPRINT_SKILLS:
        raise ValueError(f"max_skills must be in [1, {HARD_MAX_BLUEPRINT_SKILLS}], got {max_skills}")
    root = Path(root_path).resolve()
    vault = str((root / vault_dir).resolve() if not Path(vault_dir).is_absolute() else Path(vault_dir).resolve())
    skills_dir = root / ".agents" / "skills"
    disk_skills = (
        {d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()}
        if skills_dir.is_dir()
        else set()
    )
    prime_count = len(disk_skills) if disk_skills else PRIME_SKILL_BASELINE_FALLBACK

    clusters = list((cluster_skills_cmd(min_cluster_size=2, root_path=str(root)).get("clusters") or []))
    bridges = list((get_cross_cluster_bridges_cmd(root_path=str(root)).get("bridges") or []))
    clusters_by_id: dict[str, dict[str, Any]] = {str(c.get("cluster_id") or ""): c for c in clusters}

    specs = [s for s in CANONICAL_SPECS if name is None or s.name == name]
    candidates: list[HarnessBlueprint] = []
    for spec in specs:
        selected = [s for s in spec.skills if not disk_skills or s in disk_skills] or list(spec.skills)
        capped_skills = tuple(dict.fromkeys(selected))[:max_skills]
        cluster = clusters_by_id.get(spec.cluster_id)
        cohesion = round(float(cluster.get("cohesion_score") or 0.0), 4) if cluster else 0.0
        bridge_count = _count_bridges(spec.cluster_id, capped_skills, bridges)
        verified_kis, excluded_kis = _collect_kis(
            spec.query_keywords, domain=spec.domain, vault_dir=vault, root_path=str(root)
        )
        savings_pct = round(100.0 * (1.0 - len(capped_skills) / max(prime_count, 1)), 2)
        tier_bonus = 6.0 if spec.tier == 1 else 0.0
        score = round(
            cohesion * 30.0
            + min(bridge_count, 12) * 1.5
            + min(len(verified_kis), 6) * 3.0
            + savings_pct / 10.0
            + tier_bonus,
            4,
        )
        candidates.append(
            HarnessBlueprint(
                name=spec.name,
                domain=spec.domain,
                title=spec.title,
                mission=spec.mission,
                icm_form=spec.icm_form,
                skills=capped_skills,
                graph_source=f"{spec.cluster_id} (cohesion={cohesion:.2f}, bridges={bridge_count})",
                cohesion_score=cohesion,
                bridge_count=bridge_count,
                score=score,
                seeded_kis=verified_kis,
                excluded_unverified_kis=excluded_kis,
                use_cases=spec.use_cases,
                out_of_scope=spec.out_of_scope,
                prime_skill_count=prime_count,
                estimated_token_savings_pct=savings_pct,
            )
        )

    candidates.sort(key=lambda bp: (-bp.score, bp.name))
    if name is not None:
        return [bp for bp in candidates if bp.name == name][:limit]
    return candidates[:limit]


def build_blueprint_tree(blueprint: HarnessBlueprint, *, skills_root: Path | str = ".agents/skills") -> dict[str, str]:
    """Build a BRAIN_SURFACE-valid L0 tree (AGENTS.md < 60 lines + selected skills/scripts)."""
    skills_base = Path(skills_root).resolve()
    skill_links = "\n".join(
        f"- `{s}`: [.agents/skills/{s}/SKILL.md](.agents/skills/{s}/SKILL.md)" for s in blueprint.skills
    )
    agents_md = (
        f"# {blueprint.name}\n\n"
        f"{blueprint.title} (`domain={blueprint.domain}`, ICM form: `{blueprint.icm_form}`).\n\n"
        "## Routing Table\n"
        "- Overview & Quick Start: [README.md](README.md)\n"
        "- Operational Contracts: [CONTEXT.md](CONTEXT.md)\n"
        "- Worked Use Cases: [docs/USE_CASES.md](docs/USE_CASES.md)\n"
        "- Graph & KI Provenance: [docs/PROVENANCE.md](docs/PROVENANCE.md)\n"
        "- Operations Runbook: [docs/RUNBOOK.md](docs/RUNBOOK.md)\n"
        "- Factory Voice: [_shared/voice.md](_shared/voice.md)\n\n"
        f"## Included Skills ({len(blueprint.skills)})\n"
        f"{skill_links}\n\n"
        "## Domain Rules\n"
        "- Read `CONTEXT.md` before running any stage; stay within `<8,000` tokens per step.\n"
        "- Stage learnings via `harness spawn propose`; never auto-adopt or raw-merge into Prime.\n"
    )
    tree: dict[str, str] = {"AGENTS.md": agents_md}
    for skill in blueprint.skills:
        sdir = skills_base / skill
        skill_md = sdir / "SKILL.md"
        if not skill_md.is_file():
            raise FileNotFoundError(f"Missing SKILL.md for blueprint skill {skill!r}: {skill_md}")
        tree[f".agents/skills/{skill}/SKILL.md"] = skill_md.read_text(encoding="utf-8")
        scripts_dir = sdir / "scripts"
        if scripts_dir.is_dir():
            for sp in sorted(scripts_dir.iterdir()):
                rel = f".agents/skills/{skill}/scripts/{sp.name}"
                if sp.is_file() and surface_ops.is_allowed(BRAIN_SURFACE, rel):
                    tree[rel] = sp.read_text(encoding="utf-8")
    return tree


__all__ = [
    "DEFAULT_MAX_BLUEPRINT_SKILLS",
    "HARD_MAX_BLUEPRINT_SKILLS",
    "HarnessBlueprint",
    "PRIME_SKILL_BASELINE_FALLBACK",
    "SeededKI",
    "build_blueprint_tree",
    "recommend_harness_blueprints",
]
