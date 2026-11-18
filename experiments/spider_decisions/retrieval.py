"""Phase 6.3: Shared graph-based KI retrieval helper over the Knowledge Vault OntologyModel."""

from __future__ import annotations

from typing import Any


def _candidate_module_ids(module_dotted: str) -> set[str]:
    sanitized = module_dotted.strip().replace(".", "_").replace("-", "_")
    return {sanitized, f"plugins_{sanitized}"}


def retrieve_kis(
    vault_model: Any,
    module_dotted: str,
    *,
    hops: int = 1,
) -> list[tuple[str, int, str]]:
    """Retrieve KIs connected to a Brain Harness module via references_code + 1-hop sibling edges."""
    targets = _candidate_module_ids(module_dotted)
    best: dict[str, tuple[int, str]] = {}

    # Hop 0: KIs with references_code pointing to the module identifier (or plugins_ variant)
    for asrt in vault_model.assertions.values():
        if asrt.relation.predicate != "references_code":
            continue
        if asrt.relation.object in targets:
            ki_id = str(asrt.relation.subject)
            best.setdefault(ki_id, (0, "references_code"))

    if hops >= 1 and best:
        hop0_ids = set(best.keys())
        for asrt in vault_model.assertions.values():
            pred = asrt.relation.predicate
            if pred not in ("related_to", "same_domain"):
                continue
            subj = str(asrt.relation.subject)
            obj = str(asrt.relation.object)
            if subj in hop0_ids and obj not in best:
                best[obj] = (1, pred)
            elif obj in hop0_ids and subj not in best:
                best[subj] = (1, pred)

    return sorted(
        [(ki_id, dist, pred) for ki_id, (dist, pred) in best.items()],
        key=lambda item: (item[1], item[0]),
    )
