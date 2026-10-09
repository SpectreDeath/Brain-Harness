"""Conflict detection and evidence-based resolution for MemGraphRAG facts."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from .models import ConflictGroupModel

if TYPE_CHECKING:
    from .memory import ThreeLayerMemory


def detect_conflicts_for_memory(mem: ThreeLayerMemory) -> list[ConflictGroupModel]:
    """Detect facts with identical (head, relation) that assert contradictory tails."""
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for f in mem.fact_layer:
        key = (f.content[0].lower().strip(), f.content[1].lower().strip())
        grouped[key].append(f.idx)

    conflicts: list[ConflictGroupModel] = []
    for _key, fact_ids in grouped.items():
        if len(fact_ids) < 2:
            continue

        tails = [mem.fact_layer[idx].content[2].strip() for idx in fact_ids]
        unique_tails = list(set(tails))
        if len(unique_tails) > 1:
            sample_fact = mem.fact_layer[fact_ids[0]]
            all_p_indices: list[int] = []
            for idx in fact_ids:
                all_p_indices.extend(mem.fact_layer[idx].passage_indices)

            conflicts.append(
                ConflictGroupModel(
                    group_id=f"conflict_{len(conflicts) + 1}",
                    head=sample_fact.content[0],
                    relation=sample_fact.content[1],
                    conflicting_tails=unique_tails,
                    fact_indices=fact_ids,
                    supporting_passage_indices=sorted(list(set(all_p_indices))),
                    resolution_status="pending",
                )
            )

    return conflicts


def resolve_conflicts_for_memory(
    mem: ThreeLayerMemory, conflicts: list[ConflictGroupModel]
) -> int:
    """Resolve conflicts by selecting the fact with highest supporting passage evidence frequency."""
    resolved = 0
    for cg in conflicts:
        best_fact_idx = -1
        best_freq = -1

        for f_idx in cg.fact_indices:
            fact = mem.fact_layer[f_idx]
            freq = len(fact.passage_indices)
            if freq > best_freq:
                best_freq = freq
                best_fact_idx = f_idx

        if best_fact_idx != -1:
            winning_fact = mem.fact_layer[best_fact_idx]
            cg.resolved_tail = winning_fact.content[2]
            cg.resolution_status = "resolved"
            resolved += 1

    return resolved
