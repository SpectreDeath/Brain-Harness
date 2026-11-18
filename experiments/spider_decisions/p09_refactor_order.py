"""Phase 9.1-9.4: Propose dependency-safe Brain Harness refactor order and cross-check KIs."""

from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import SNAPSHOTS, VAULT, bootstrap, project_entities, write_json, write_md  # noqa: E402

bootstrap()


def _bfs_reachable(adj: dict[str, set[str]], start: str) -> set[str]:
    visited: set[str] = set()
    q = deque(adj.get(start, ()))
    while q:
        cur = q.popleft()
        if cur == start or cur in visited:
            continue
        visited.add(cur)
        for nxt in adj.get(cur, ()):
            if nxt not in visited and nxt != start:
                q.append(nxt)
    return visited


def _tarjan_sccs(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in sorted(adj.get(v, ())):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            comp: list[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(sorted(comp))

    for n in sorted(nodes):
        if n not in indices:
            strongconnect(n)
    return sccs


def _load_ki_summary_tokens(ki_dir_name: str) -> tuple[str, str]:
    p = VAULT / ki_dir_name / "summary.md"
    if not p.is_file():
        return ("", "")
    txt = p.read_text(encoding="utf-8", errors="ignore")
    return (txt, txt.lower())


def main() -> int:
    from ontology_spider.api import load_model, validate_model

    model = load_model(SNAPSHOTS / "brain_harness_src.json")
    ents = project_entities(model)
    units = sorted(ents.keys())

    fwd: dict[str, set[str]] = {u: set() for u in units}
    rev: dict[str, set[str]] = {u: set() for u in units}
    for asrt in model.assertions.values():
        if asrt.relation.predicate != "depends_on_project":
            continue
        s, o = str(asrt.relation.subject), str(asrt.relation.object)
        if s in fwd and o in rev:
            fwd[s].add(o)
            rev[o].add(s)

    in_degree = {u: len(rev[u]) for u in units}
    out_degree = {u: len(fwd[u]) for u in units}
    blast_radius = {u: len(_bfs_reachable(rev, u)) for u in units}
    fwd_reach = {u: len(_bfs_reachable(fwd, u)) for u in units}

    # Spider validate_model cycles
    violations = validate_model(model)
    cycle_violations = [v for v in violations if v.get("check_type") == "cycle_violation"]
    spider_cycle_paths: list[str] = []
    unit_min_cycle_size: dict[str, int] = {}
    for cv in cycle_violations:
        details = cv.get("details") or {}
        cpath = str(details.get("cycle_path") or cv.get("message") or "")
        spider_cycle_paths.append(cpath)
        cnodes = [n for n in (details.get("cycle_nodes") or []) if n in ents]
        unique_nodes = set(cnodes)
        csize = len(unique_nodes)
        for u in unique_nodes:
            if u not in unit_min_cycle_size or csize < unit_min_cycle_size[u]:
                unit_min_cycle_size[u] = csize

    # Also detect full SCC cycles in Python for visibility
    tarjan_sccs = _tarjan_sccs(units, fwd)

    # Ordering rule (9.2):
    # (1) Units flagged in spider cycle_violations first, ordered by cycle_size (then -py_file_count)
    # (2) Remaining units ordered in reverse topological / leaf-dependent-first order
    #     (peeling lowest active in_degree from dependents -> foundations; tie-break -py_file_count)
    cycle_units = sorted(
        unit_min_cycle_size.keys(),
        key=lambda u: (
            unit_min_cycle_size[u],
            -int(ents[u].get("py_file_count") or 0),
            u,
        ),
    )

    remaining = set(units) - set(cycle_units)
    active_rev: dict[str, set[str]] = {u: (rev[u] & remaining) for u in remaining}
    non_cycle_order: list[str] = []
    while remaining:
        # Lowest active caller count (0-in-degree dependents first = lowest downstream breakage)
        picked = min(
            remaining,
            key=lambda u: (
                len(active_rev[u]),
                blast_radius[u],
                -int(ents[u].get("py_file_count") or 0),
                u,
            ),
        )
        non_cycle_order.append(picked)
        remaining.remove(picked)
        for dep in fwd[picked]:
            if dep in active_rev:
                active_rev[dep].discard(picked)

    full_order = cycle_units + non_cycle_order
    assert len(full_order) == len(units) and set(full_order) == set(units)

    # Step 9.3: Cross-check against ki-file-size-hotspots & ki-deepening-cycle-history
    hs_raw, hs_low = _load_ki_summary_tokens("ki-file-size-hotspots")
    dch_raw, dch_low = _load_ki_summary_tokens("ki-deepening-cycle-history")
    corp_raw, corp_low = _load_ki_summary_tokens("ki_20261014_70_cycle_deepening_corpus")

    # Map known hotspot filenames/phrases in those KIs to src/harness subpackages
    ki_unit_hints: dict[str, list[str]] = {
        "agent": ["archetypes.py", "swarm.py", "session.py", "agent session"],
        "commands": ["cli.py", "reflection.py", "commands/"],
        "creator": ["creator package"],
        "kernel": ["micro-kernel", "kernel"],
        "mcp": ["server.py"],
        "plugins": ["cellcog.py"],
        "services": ["compute_assessor.py", "tools.py", "validator.py", "services/compute/"],
    }

    top10_units = full_order[:10]
    ordered_rows: list[dict[str, Any]] = []
    cross_check_hits: list[dict[str, Any]] = []

    for rank, u in enumerate(full_order, start=1):
        py_cnt = int(ents[u].get("py_file_count") or 0)
        hints = ki_unit_hints.get(u, [u])
        in_hs = any(h in hs_low for h in hints)
        in_dch = any(h in dch_low for h in hints)
        in_corp = any(h in corp_low for h in hints)
        in_cycle = u in unit_min_cycle_size
        row = {
            "order": rank,
            "unit": u,
            "py_file_count": py_cnt,
            "in_spider_cycle": in_cycle,
            "spider_cycle_size": unit_min_cycle_size.get(u, 0),
            "hub_in_degree": in_degree[u],
            "out_degree": out_degree[u],
            "blast_radius_reverse_reachable": blast_radius[u],
            "forward_transitive_deps": fwd_reach[u],
            "in_top10": u in top10_units,
            "in_ki_file_size_hotspots": in_hs,
            "in_ki_deepening_cycle_history": in_dch,
            "in_ki_70_cycle_corpus": in_corp,
        }
        ordered_rows.append(row)
        if u in top10_units and (in_hs or in_dch):
            cross_check_hits.append(
                {
                    "unit": u,
                    "order": rank,
                    "in_ki_file_size_hotspots": in_hs,
                    "in_ki_deepening_cycle_history": in_dch,
                    "matched_signals": [h for h in hints if h in hs_low or h in dch_low],
                }
            )

    hubs_ranked = sorted(units, key=lambda u: (-in_degree[u], -blast_radius[u], u))
    payload = {
        "total_units": len(units),
        "total_depends_on_edges": sum(Counter({u: len(fwd[u]) for u in units}).values()),
        "spider_cycle_violations": spider_cycle_paths,
        "tarjan_scc_cycles": tarjan_sccs,
        "blast_radius_method": "Python reverse BFS (spider transitive queries follow forward depends_on_project edges only)",
        "dependency_hubs": [
            {"unit": u, "in_degree": in_degree[u], "blast_radius": blast_radius[u]} for u in hubs_ranked
        ],
        "refactor_order": ordered_rows,
        "ki_cross_check_top10": cross_check_hits,
    }
    json_path = write_json(9, "refactor_order", payload)

    md_lines = [
        "# Phase 9 — Brain Harness Dependency-Safe Refactor Order",
        "",
        f"Analyzed **{len(units)}** subpackages in `src/harness` (`{payload['total_depends_on_edges']}` `depends_on_project` edges).",
        "",
        "## Detected Cycles",
        f"- **Spider `validate_model` cycles ({len(spider_cycle_paths)}):** "
        + (", ".join(f"`{c}`" for c in spider_cycle_paths) or "none"),
        f"- **Full Tarjan strongly connected components (`size > 1`):** `{tarjan_sccs}`",
        "- **Note on blast radius:** `ontology_spider` `transitive` queries traverse forward `depends_on_project` edges; "
        "reverse reachability (**blast radius** = transitive dependents) was computed via reverse BFS in Python.",
        "",
        "## Proposed Refactor Order",
        "",
        "| Order | Unit | Py Files | Cycle? | Hub In-Deg | Blast Radius | Out-Deg | In `hotspots` KI? | In `deepening` KI? |",
        "|---:|---|---:|---|---:|---:|---:|---|---|",
    ]
    for r in ordered_rows:
        cyc_str = f"Yes (size {r['spider_cycle_size']})" if r["in_spider_cycle"] else "No"
        md_lines.append(
            f"| {r['order']} | `{r['unit']}` | {r['py_file_count']} | {cyc_str} "
            f"| {r['hub_in_degree']} | {r['blast_radius_reverse_reachable']} | {r['out_degree']} "
            f"| {r['in_ki_file_size_hotspots']} | {r['in_ki_deepening_cycle_history']} |"
        )

    md_lines.extend(
        [
            "",
            "## Cross-Check Against Historical KIs (Top-10)",
            "",
            "| Unit | Order | `ki-file-size-hotspots` | `ki-deepening-cycle-history` | Matched Signals |",
            "|---|---:|---|---|---|",
        ]
    )
    for hit in cross_check_hits:
        md_lines.append(
            f"| `{hit['unit']}` | {hit['order']} | {hit['in_ki_file_size_hotspots']} "
            f"| {hit['in_ki_deepening_cycle_history']} | {', '.join(hit['matched_signals'])} |"
        )
    md_lines.append("")
    md_path = write_md(9, "summary", "\n".join(md_lines))

    print(f"Ordered {len(units)} units: {[r['unit'] for r in ordered_rows]}")
    print(f"Spider cycles: {spider_cycle_paths}")
    print(f"Tarjan SCCs: {tarjan_sccs}")
    print(f"Cross-check top-10 overlap: {len(cross_check_hits)} units")
    print(f"JSON: {json_path}")
    print(f"Summary: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
