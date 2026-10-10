"""SQLite OKF v0.2 Knowledge Database helpers and stable signature hashing."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


def init_okf_db(db_path: str = "knowledge.db") -> sqlite3.Connection:
    """Initialize SQLite database with Mantis schema and OKF v0.2 concept tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            title TEXT NOT NULL,
            cwe TEXT NOT NULL,
            severity TEXT NOT NULL,
            signature TEXT NOT NULL,
            status TEXT NOT NULL,
            details_json TEXT NOT NULL,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS okf_concepts (
            concept_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (concept_id, run_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def compute_stable_signature(filepath: str, cwe: str, target_symbol: str = "") -> str:
    """Compute deterministic stable hash signature for vulnerability identity."""
    norm_fp = Path(filepath).as_posix().lower()
    norm_cwe = cwe.strip().upper()
    norm_sym = target_symbol.strip().lower()
    raw = f"{norm_fp}::{norm_cwe}::{norm_sym}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
