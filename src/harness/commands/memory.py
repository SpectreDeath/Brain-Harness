"""Memory command group — working-memory decay, Ebbinghaus retention, and 5-store routing."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import click

from plugins.memory_and_epistemics.memory_decay_engine.tools import (
    export_memory_session,
    import_memory_session,
    memory_query_working_set,
    memory_recall,
    memory_register,
    memory_step,
    rank_working_set,
    simulate_session_benchmark,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@click.group("memory")
def memory_group() -> None:
    """Manage working-memory decay, Ebbinghaus retention, and 5-store routing."""


@memory_group.command("register")
@click.option("--key", "-k", required=True, help="Unique memory key")
@click.option("--content", "-c", required=True, help="Memory content text")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option(
    "--channel",
    default="memory",
    type=click.Choice(["memory", "instruction", "evidence", "tool_output", "foundational"]),
    help="Semantic memory channel",
)
@click.option("--stability", default=5.0, type=float, help="Initial Ebbinghaus stability S")
@click.option("--foundational", is_flag=True, help="Mark item as foundational (exempt from eviction)")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_register_cmd(
    key: str,
    content: str,
    session: str,
    channel: str,
    stability: float,
    foundational: bool,
    as_json: bool,
) -> None:
    """Register a new memory item into the Ebbinghaus memory session."""
    res = memory_register(
        key=key,
        content=content,
        session_id=session,
        stability=stability,
        is_foundational=foundational,
        channel=channel,
    )
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return
    if res.get("status") == "ok":
        it = res.get("item") or {}
        click.secho(
            f"[OK] Registered memory '{key}' (Channel: {it.get('channel')}, Stability: {it.get('stability')}) in '{session}'",
            fg="green",
        )
    else:
        click.secho(f"[ERROR] Failed to register memory: {res.get('error')}", fg="red", err=True)
        sys.exit(1)


@memory_group.command("recall")
@click.argument("key")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_recall_cmd(key: str, session: str, as_json: bool) -> None:
    """Recall an active memory item, reinforcing stability non-linearly."""
    res = memory_recall(key=key, session_id=session)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return
    if res.get("status") == "ok":
        it = res.get("item") or {}
        click.secho(
            f"[OK] Recalled '{key}' (New Stability: {it.get('stability'):.2f}, Recalls: {it.get('recall_count')})",
            fg="green",
        )
        click.echo(f"     Content: {it.get('content')}")
    else:
        click.secho(f"[NOT FOUND] {res.get('message') or res.get('error')}", fg="yellow")
        sys.exit(1)


@memory_group.command("step")
@click.option("--turns", "-t", default=1, type=int, help="Number of turns to advance")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_step_cmd(turns: int, session: str, as_json: bool) -> None:
    """Advance session time by N turns, applying channel decay and soft-evicting expired items."""
    last_res = {}
    for _ in range(max(1, turns)):
        last_res = memory_step(session_id=session)

    if as_json:
        click.echo(json.dumps(last_res, indent=2))
        return
    if last_res.get("status") == "ok":
        click.secho(f"\nAdvanced session '{session}' to Turn {last_res.get('current_turn')}", fg="cyan", bold=True)
        click.echo(f"  Evicted Items Count : {last_res.get('evicted_count')}")
        click.echo(f"  Evicted Keys        : {', '.join(last_res.get('evicted_keys') or []) or 'none'}")
        click.echo(f"  Active Working Set  : {last_res.get('active_working_set_count')}")
    else:
        click.secho(f"[ERROR] Step failed: {last_res.get('error')}", fg="red", err=True)
        sys.exit(1)


@memory_group.command("working-set")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--include-evicted", is_flag=True, help="Include soft-evicted items in inspection")
@click.option("--ranked", is_flag=True, help="Sort by multi-criteria composite score")
@click.option("--limit", "-l", default=None, type=int, help="Max items to return")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_working_set_cmd(
    session: str,
    include_evicted: bool,
    ranked: bool,
    limit: int | None,
    as_json: bool,
) -> None:
    """Query items residing in the active working-memory set."""
    if ranked and not include_evicted:
        res = rank_working_set(session_id=session, limit=limit)
    else:
        res = memory_query_working_set(session_id=session, include_evicted=include_evicted)
        if limit and res.get("items"):
            res["items"] = res["items"][:limit]

    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"\nWorking Memory Set: '{session}' (Turn {res.get('current_turn', 0)})", fg="cyan", bold=True)
    click.echo("━" * 65)
    items = res.get("items", [])
    click.echo(f"  Total Retrievable Items: {len(items)}")
    for it in items:
        ev_flag = " [EVICTED]" if it.get("evicted") else ""
        fd_flag = " [FOUNDATIONAL]" if it.get("is_foundational") else ""
        ret_val = it.get("retention", it.get("composite_score", 0.0))
        click.echo(
            f"  • {it.get('key'):20} (Channel: {it.get('channel'):12} Retention: {ret_val:.2f}){fd_flag}{ev_flag}"
        )


@memory_group.command("benchmark")
@click.option("--turns", "-t", default=30, type=int, help="Number of turns to simulate")
@click.option("--items", "-i", "total_items", default=25, type=int, help="Total memories to inject")
@click.option("--seed", default=42, type=int, help="Simulation RNG seed")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_benchmark_cmd(turns: int, total_items: int, seed: int, as_json: bool) -> None:
    """Run comparative simulation comparing Ebbinghaus decay vs recency baseline."""
    res = simulate_session_benchmark(num_turns=turns, total_memories=total_items, seed=seed)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return
    sim = res.get("simulation") or {}
    click.secho(f"\nEbbinghaus Memory Decay Simulation Benchmark", fg="cyan", bold=True)
    click.echo("━" * 65)
    click.echo(f"  Turns Simulated   : {turns}")
    click.echo(f"  Total Injected    : {total_items}")
    click.echo(f"  Ebbinghaus Active : {sim.get('ebbinghaus_active_count')}")
    click.echo(f"  Recency Active    : {sim.get('recency_active_count')}")
    click.echo(f"  Overlap Ratio     : {sim.get('overlap_ratio', 0.0):.2%}")


@memory_group.command("snapshot")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--export", "export_path", default=None, type=click.Path(), help="File path to export snapshot JSON")
@click.option("--import", "import_path", default=None, type=click.Path(exists=True), help="File path to import snapshot JSON")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_snapshot_cmd(session: str, export_path: str | None, import_path: str | None, as_json: bool) -> None:
    """Export or restore an Ebbinghaus working-memory session snapshot."""
    if import_path:
        data = json.loads(Path(import_path).read_text(encoding="utf-8"))
        res = import_memory_session(session_id=session, snapshot=data)
        if as_json:
            click.echo(json.dumps(res, indent=2))
            return
        if res.get("status") == "ok":
            click.secho(f"[OK] Restored memory session '{session}' from {import_path}", fg="green")
        else:
            click.secho(f"[ERROR] Import failed: {res.get('error')}", fg="red", err=True)
            sys.exit(1)
    elif export_path:
        res = export_memory_session(session_id=session)
        if res.get("status") == "ok":
            Path(export_path).write_text(json.dumps(res.get("snapshot", {}), indent=2), encoding="utf-8")
            if as_json:
                click.echo(json.dumps(res, indent=2))
            else:
                click.secho(f"[OK] Exported memory session '{session}' to {export_path}", fg="green")
        else:
            click.secho(f"[ERROR] Export failed: {res.get('error')}", fg="red", err=True)
            sys.exit(1)
    else:
        res = export_memory_session(session_id=session)
        click.echo(json.dumps(res, indent=2))


# --- Track 5: Architectural Consolidations (5-Store Router & Status) ---
MEMORY_STORES = {
    "okf_memory": {
        "title": "OKF Git-Native Concept Store",
        "paradigm": "Normative Git concept bundle (OKF v0.2)",
        "scope": "Pre-edit file governance, path boundaries, actor trust",
        "cli": "harness okf",
        "service_key": "service.okf_memory",
    },
    "memgraphrag": {
        "title": "MemGraphRAG Passage Conflict Store",
        "paradigm": "Unstructured passage GraphRAG",
        "scope": "Entity-relation triples and semantic contradiction detection",
        "cli": "harness doc / harness knowledge",
        "service_key": "service.memgraphrag",
    },
    "graphiti_memory": {
        "title": "Graphiti Episodic Temporal Graph",
        "paradigm": "Bi-temporal episodic interaction graph",
        "scope": "Episodic user conversations, timeline changes, fact invalidation",
        "cli": "harness trajectory / harness session",
        "service_key": "service.graphiti_memory",
    },
    "memory_decay_engine": {
        "title": "Ebbinghaus Working-Memory Decay",
        "paradigm": "Channel-weighted Ebbinghaus decay",
        "scope": "In-flight step retention, soft eviction, stability reinforcement",
        "cli": "harness memory",
        "service_key": "service.memory_decay",
    },
    "knowledge_vault": {
        "title": "Epistemic Knowledge Vault",
        "paradigm": "Canonical dual-file Knowledge Items (Rule 40)",
        "scope": "Verified facts, Isnad chains, empirical heuristics",
        "cli": "harness knowledge",
        "service_key": "service.knowledge_vault",
    },
}


@memory_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_status_cmd(as_json: bool) -> None:
    """Inspect status and paradigms across all 5 partitioned memory stores."""
    report = {
        "status": "ok",
        "stores_count": len(MEMORY_STORES),
        "stores": MEMORY_STORES,
    }
    if as_json:
        click.echo(json.dumps(report, indent=2))
        return

    click.secho("\nHarness 5-Store Memory Architecture Status", fg="cyan", bold=True)
    click.echo("━" * 70)
    for sid, info in MEMORY_STORES.items():
        click.secho(f"  • {info['title']} (`{sid}`)", fg="yellow", bold=True)
        click.echo(f"    Paradigm : {info['paradigm']}")
        click.echo(f"    Scope    : {info['scope']}")
        click.echo(f"    CLI Seam : {info['cli']} (Key: {info['service_key']})")


@memory_group.command("route")
@click.argument("question")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def memory_route_cmd(question: str, as_json: bool) -> None:
    """Route a developer or agent memory inquiry to the authoritative store."""
    q_lower = question.lower()
    recommended_store = "knowledge_vault"
    reason = "General epistemic knowledge or fact lookup."
    example_cmd = "harness knowledge query"

    if any(k in q_lower for k in ["rule", "govern", "scope", "concept", "normative", "edit boundary", "path"]):
        recommended_store = "okf_memory"
        reason = "Path-based normative governance rules or concept constraints."
        example_cmd = "harness okf scope <path>"
    elif any(k in q_lower for k in ["decay", "working set", "evict", "retention", "ebbinghaus", "turn", "stability"]):
        recommended_store = "memory_decay_engine"
        reason = "In-flight conversational working memory retention and decay."
        example_cmd = "harness memory working-set"
    elif any(k in q_lower for k in ["episode", "time", "timeline", "temporal", "invalidat", "superseded fact", "user session"]):
        recommended_store = "graphiti_memory"
        reason = "Bi-temporal episodic interaction history and historical fact evolution."
        example_cmd = "harness session get <session-id>"
    elif any(k in q_lower for k in ["conflict", "passage", "graphrag", "triple", "contradict", "unstructured"]):
        recommended_store = "memgraphrag"
        reason = "Unstructured passage entity extraction and contradiction detection."
        example_cmd = "harness knowledge contradictions"
    else:
        recommended_store = "knowledge_vault"
        reason = "Verified epistemic knowledge items and Isnad provenance chains."
        example_cmd = f"harness knowledge joint-query \"{question}\""

    store_info = MEMORY_STORES[recommended_store]
    result = {
        "status": "ok",
        "question": question,
        "recommended_store": recommended_store,
        "store_title": store_info["title"],
        "reason": reason,
        "recommended_cli": example_cmd,
        "paradigm": store_info["paradigm"],
    }

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    click.secho(f"\nMemory Route Recommendation: '{question}'", fg="cyan", bold=True)
    click.echo("━" * 65)
    click.secho(f"  Target Store    : {store_info['title']} ({recommended_store})", fg="green", bold=True)
    click.echo(f"  Reason          : {reason}")
    click.echo(f"  Store Paradigm  : {store_info['paradigm']}")
    click.echo(f"  Suggested CLI   : {example_cmd}")


__all__ = ["memory_group"]

