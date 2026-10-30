"""Relational SQLite recursive CTE graph traversal engine (Stage 1 of Track 5)."""

from __future__ import annotations

import sqlite3
from typing import Any

from harness.services.storage.vault_graph_models import DerivedKnowledgeGraph


def init_ki_edges_table(conn: sqlite3.Connection) -> None:
    """Initialize indexed relational edge table for recursive graph queries."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ki_edges (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            target_kind TEXT NOT NULL DEFAULT 'ki',
            edge_type TEXT NOT NULL,
            derived INTEGER NOT NULL DEFAULT 0,
            confidence REAL NOT NULL DEFAULT 1.0,
            description TEXT DEFAULT '',
            PRIMARY KEY (source, target, edge_type)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ki_edges_source ON ki_edges(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ki_edges_target ON ki_edges(target)")
    conn.commit()


def sync_ki_edges(conn: sqlite3.Connection, graph: DerivedKnowledgeGraph) -> int:
    """Sync all asserted and derived edges from graph topology into SQLite ki_edges table."""
    init_ki_edges_table(conn)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ki_edges")

    rows = [
        (
            e.source,
            e.target,
            e.target_kind,
            e.type,
            1 if e.derived else 0,
            float(e.confidence),
            e.description or "",
        )
        for e in graph.edges
    ]
    cursor.executemany(
        """
        INSERT OR REPLACE INTO ki_edges (source, target, target_kind, edge_type, derived, confidence, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def find_path_sql(
    conn: sqlite3.Connection,
    from_id: str,
    to_id: str,
    max_depth: int = 6,
    exclude_derived: bool = False,
) -> dict[str, Any]:
    """Find cycle-safe shortest path between two nodes using SQLite WITH RECURSIVE CTE (Rule 55)."""
    init_ki_edges_table(conn)
    if from_id == to_id:
        return {"status": "found", "chain": [from_id], "length": 0, "hops": []}

    allow_derived = 0 if exclude_derived else 1
    query = """
    WITH RECURSIVE search_graph AS (
        SELECT 
            source, 
            target, 
            edge_type, 
            derived, 
            confidence, 
            1 AS hop_count, 
            '/' || source || '/' || target || '/' AS path_string
        FROM ki_edges
        WHERE source = ? AND (? = 1 OR derived = 0)

        UNION ALL

        SELECT 
            e.source, 
            e.target, 
            e.edge_type, 
            e.derived, 
            e.confidence, 
            sg.hop_count + 1,
            sg.path_string || e.target || '/'
        FROM ki_edges e
        JOIN search_graph sg ON sg.target = e.source
        WHERE instr(sg.path_string, '/' || e.target || '/') = 0
          AND sg.hop_count < ?
          AND (? = 1 OR e.derived = 0)
    )
    SELECT source, target, edge_type, derived, confidence, hop_count, path_string
    FROM search_graph
    WHERE target = ?
    ORDER BY hop_count ASC
    LIMIT 1;
    """
    cursor = conn.execute(query, (from_id, allow_derived, max_depth, allow_derived, to_id))
    row = cursor.fetchone()
    if not row:
        return {"status": "no_path", "chain": [], "length": 0, "hops": []}

    path_str = row[6]  # e.g. /ki-1/ki-2/ki-3/
    chain = [p for p in path_str.split("/") if p]
    return {
        "status": "found",
        "chain": chain,
        "length": row[5],
        "path_string": path_str,
    }


def get_transitive_dependents_sql(
    conn: sqlite3.Connection,
    target_id: str,
    max_depth: int = 6,
) -> list[dict[str, Any]]:
    """Retrieve all multi-hop inbound dependents using SQLite WITH RECURSIVE CTE."""
    init_ki_edges_table(conn)
    query = """
    WITH RECURSIVE dependents_tree AS (
        SELECT 
            source, 
            target, 
            edge_type, 
            derived, 
            confidence, 
            1 AS depth, 
            '/' || target || '/' || source || '/' AS path_string
        FROM ki_edges
        WHERE target = ?

        UNION ALL

        SELECT 
            e.source, 
            e.target, 
            e.edge_type, 
            e.derived, 
            e.confidence, 
            dt.depth + 1,
            dt.path_string || e.source || '/'
        FROM ki_edges e
        JOIN dependents_tree dt ON dt.source = e.target
        WHERE instr(dt.path_string, '/' || e.source || '/') = 0
          AND dt.depth < ?
    )
    SELECT DISTINCT source, target, edge_type, derived, confidence, depth
    FROM dependents_tree
    ORDER BY depth ASC;
    """
    cursor = conn.execute(query, (target_id, max_depth))
    return [
        {
            "source_ki": row[0],
            "target": row[1],
            "edge_type": row[2],
            "derived": bool(row[3]),
            "confidence": row[4],
            "depth": row[5],
        }
        for row in cursor.fetchall()
    ]

