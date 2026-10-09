"""Friction scorecard analysis and failure cluster aggregation."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .models import ConversationManifest, FailureCluster, FrictionScorecard
from .sqlite_reader import categorize_error, connect_ro, scan_corpus

logger = logging.getLogger("harness.services.conversation_trajectory_miner")


def compile_friction_scorecard(manifests: list[ConversationManifest]) -> FrictionScorecard:
    """Compile aggregate friction and step distribution scorecard."""
    total_steps = sum(m.step_count for m in manifests)
    total_errors = sum(m.errors_detected for m in manifests)
    total_bytes = sum(m.file_size_bytes for m in manifests)

    aggregate_types: dict[str, int] = {}
    for m in manifests:
        for stype, count in m.step_types.items():
            aggregate_types[stype] = aggregate_types.get(stype, 0) + count

    high_error_sessions = [
        asdict(m)
        for m in manifests
        if m.errors_detected > 0
    ]
    high_error_sessions.sort(key=lambda x: x["errors_detected"], reverse=True)

    # Collect failure clusters
    failure_clusters: list[FailureCluster] = []
    cluster_map: dict[str, list[tuple[str, str, str]]] = {}

    for m in manifests:
        if m.errors_detected == 0:
            continue
        conn: sqlite3.Connection | None = None
        try:
            conn = connect_ro(m.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT task_details, error_details FROM steps "
                "WHERE status IN (6, 7) OR (error_details IS NOT NULL AND length(error_details) > 0) "
                "LIMIT 20"
            )
            for task_det, err_det in cur.fetchall():
                task_str = str(task_det or "")
                err_str = str(err_det or "")
                cat = categorize_error(err_str, task_str)
                if cat not in cluster_map:
                    cluster_map[cat] = []
                cluster_map[cat].append((m.cid, task_str[:60], err_str[:120]))
        except Exception as e:
            logger.debug("Error extracting failure clusters from %s: %s", m.cid, e)
        finally:
            if conn is not None:
                conn.close()

    for cat, occurrences in cluster_map.items():
        sample_cids = tuple(dict.fromkeys(cid for cid, _, _ in occurrences))[:5]
        tool_names = tuple(dict.fromkeys(t for _, t, _ in occurrences if t))[:5]
        sample_msgs = tuple(dict.fromkeys(msg for _, _, msg in occurrences if msg))[:3]
        failure_clusters.append(
            FailureCluster(
                error_type=cat,
                count=len(occurrences),
                sample_cids=sample_cids,
                tool_names=tool_names,
                sample_messages=sample_msgs,
            )
        )

    failure_clusters.sort(key=lambda c: c.count, reverse=True)

    return FrictionScorecard(
        total_conversations=len(manifests),
        total_steps=total_steps,
        total_bytes_mb=round(total_bytes / (1024 * 1024), 2),
        total_errors=total_errors,
        error_rate=round(total_errors / max(total_steps, 1), 4),
        step_type_distribution=aggregate_types,
        high_friction_sessions=tuple(high_error_sessions[:10]),
        failure_clusters=tuple(failure_clusters[:10]),
    )


def mine_failure_clusters(corpus_dir: Path | str, max_dbs: int | None = None) -> list[FailureCluster]:
    """Analyze step execution errors across databases and cluster recurring failure modes."""
    manifests = scan_corpus(corpus_dir, max_dbs=max_dbs)
    scorecard = compile_friction_scorecard(manifests)
    return list(scorecard.failure_clusters)


__all__ = [
    "compile_friction_scorecard",
    "mine_failure_clusters",
]
