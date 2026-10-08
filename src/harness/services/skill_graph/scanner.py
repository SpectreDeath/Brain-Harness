"""Filesystem catalog scanning, directory parsing, and Knowledge Vault linking (Rule 52)."""

from __future__ import annotations

import collections
import json
import math
import os
from pathlib import Path
import re
from typing import Any

import structlog

from harness.services.skill_graph.card_parser import SkillCardParser
from harness.services.skill_graph.models import (
    CANONICAL_PIPELINE_PRECEDENCE,
    EdgeType,
    SkillCardDefinition,
    SkillEdge,
)
from harness.services.skill_graph.routing import _would_create_cycle

logger = structlog.get_logger()


def scan_skills_catalog(
    root_dir: str,
) -> tuple[
    dict[str, SkillCardDefinition],
    set[str],
    dict[str, set[str]],
    dict[str, set[str]],
    list[SkillEdge],
    dict[str, float],
]:
    """Scan workspace directories with bounded depth and return discovered graph artifacts (Rule 52)."""
    p = Path(root_dir).resolve()
    paths_to_scan = [
        p / ".agents" / "skills",
        p / "skills",
        p / "plugins",
    ]

    discovered: dict[str, SkillCardDefinition] = {}
    categories: set[str] = set()
    adjacency: dict[str, set[str]] = collections.defaultdict(set)

    ignored_parts = {
        ".venv",
        "venv",
        "venvs",
        ".git",
        "node_modules",
        "site-packages",
        "__pycache__",
        "target",
        "dist",
        ".gemini",
    }

    for scan_dir in paths_to_scan:
        if not scan_dir.exists():
            continue
        scan_dir_path = Path(scan_dir).resolve()
        for root_dirpath, dirnames, filenames in os.walk(str(scan_dir_path)):
            rel_parts = Path(root_dirpath).relative_to(scan_dir_path).parts
            if len(rel_parts) >= 8:
                dirnames.clear()
                continue

            dirnames[:] = [
                d
                for d in dirnames
                if d.lower() not in ignored_parts and not d.startswith(".")
            ]

            if "SKILL.md" in filenames:
                skill_file = Path(root_dirpath) / "SKILL.md"
                try:
                    card = SkillCardParser.parse_directory(skill_file.parent)
                    if card and card.name not in discovered:
                        discovered[card.name] = card
                        categories.add(card.category)
                        for dep in card.dependencies:
                            clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                            if clean_dep != card.name:
                                adjacency[card.name].add(clean_dep)
                except Exception as e:
                    logger.debug(
                        "Failed parsing skill directory",
                        path=str(skill_file.parent),
                        error=str(e),
                    )
                    continue

    synthetic_adj: dict[str, set[str]] = collections.defaultdict(set)
    for s1, s2 in CANONICAL_PIPELINE_PRECEDENCE:
        if s1 in discovered and s2 in discovered:
            synthetic_adj[s1].add(s2)
            adjacency[s1].add(s2)

    edges: list[SkillEdge] = []
    edge_keys: set[tuple[str, str, EdgeType]] = set()

    def _add_local_edge(source: str, target: str, relation: EdgeType, weight: float = 1.0) -> None:
        key = (source, target, relation)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append(SkillEdge(source=source, target=target, relation=relation, weight=weight))

    for card in discovered.values():
        _add_local_edge(card.name, f"cat:{card.category}", EdgeType.BELONGS_TO)
        for ap in card.anti_patterns:
            _add_local_edge(
                card.name,
                f"antipattern:{ap.name.lower().replace(' ', '-')}",
                EdgeType.MITIGATES,
            )
        for dep in card.dependencies:
            clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
            if clean_dep != card.name:
                _add_local_edge(card.name, clean_dep, EdgeType.REQUIRES)

    for s1, s2 in CANONICAL_PIPELINE_PRECEDENCE:
        if s1 in discovered and s2 in discovered:
            _add_local_edge(s1, s2, EdgeType.PRECEDES)

    producer_map: dict[str, set[str]] = collections.defaultdict(set)
    consumer_map: dict[str, set[str]] = collections.defaultdict(set)
    for card in discovered.values():
        for stage in card.stages:
            if stage.primary_artifact:
                producer_map[stage.primary_artifact].add(card.name)
            for artifact in stage.consumes or []:
                consumer_map[artifact].add(card.name)

    for artifact, producers in producer_map.items():
        for consumer_skill in consumer_map.get(artifact, set()):
            for producer_skill in producers:
                if producer_skill == consumer_skill:
                    continue
                if not _would_create_cycle(adjacency, producer_skill, consumer_skill):
                    _add_local_edge(producer_skill, consumer_skill, EdgeType.FEEDS)
                    adjacency[producer_skill].add(consumer_skill)
                else:
                    logger.debug(
                        "Skipping FEEDS edge %s -> %s: would create directed cycle",
                        producer_skill,
                        consumer_skill,
                    )

    corpus_df: dict[str, int] = collections.Counter()
    for skill in discovered.values():
        tokens = set(re.findall(r"\w+", f"{skill.target} {skill.category}".lower()))
        corpus_df.update(tokens)
    n_docs = max(1, len(discovered))
    idf_table = {
        t: math.log((n_docs + 1) / (df + 1)) for t, df in corpus_df.items()
    }

    return discovered, categories, adjacency, synthetic_adj, edges, idf_table


def link_knowledge_vault_items(
    skills_cache: dict[str, SkillCardDefinition],
    vault_dir: Path | str = ".harness/knowledge",
) -> int:
    """Scan dual-file on-disk knowledge vault and link matching KIs to registered skills."""
    v_path = Path(vault_dir).resolve()
    if not v_path.exists() or not v_path.is_dir():
        return 0

    linked_count = 0
    for ki_dir in v_path.iterdir():
        if not ki_dir.is_dir():
            continue
        meta_path = ki_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ki_id = meta.get("id", ki_dir.name)
            raw_tags = meta.get("tags") or []
            tags = [
                t.lower().replace("_", "-") for t in raw_tags if isinstance(t, str)
            ]
            title = (meta.get("title") or "").lower()

            for skill_name, skill in skills_cache.items():
                s_tokens = set(skill_name.split("-"))
                matched = False

                if (
                    skill_name in tags
                    or skill_name in ki_id.lower()
                    or skill_name.replace("-", "_") in ki_id.lower()
                    or any(tok in tags for tok in s_tokens if len(tok) > 3)
                    or any(tok in title for tok in s_tokens if len(tok) > 3)
                ):
                    matched = True

                if matched and ki_id not in skill.knowledge_items:
                    skill.knowledge_items.append(ki_id)
                    linked_count += 1
        except Exception as e:
            logger.debug(
                "Failed processing knowledge vault item",
                path=str(ki_dir),
                error=str(e),
            )
            continue

    return linked_count


__all__ = [
    "link_knowledge_vault_items",
    "scan_skills_catalog",
]
