"""Google Mantis AST Content-Addressed Structural Index Plugin for Brain Harness."""

from __future__ import annotations

import ast
import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)


@runtime_checkable
class MantisStructuralIndexService(Protocol):
    """Protocol for AST content-addressed structural indexing and symbol lookup."""

    def build_structural_index(self, repo_path: str, db_path: str = "structural_index.db") -> dict[str, Any]:
        ...

    def query_symbol(self, symbol_name: str, db_path: str = "structural_index.db", query_type: str = "definition") -> dict[str, Any]:
        ...


MANTIS_STRUCTURAL_INDEX_KEY: ServiceKey[MantisStructuralIndexService] = ServiceKey("service.mantis_structural_index")


# -----------------------------------------------------------------------------
# SQLite Structural Index Database Engine
# -----------------------------------------------------------------------------

def init_index_db(db_path: str = "structural_index.db") -> sqlite3.Connection:
    """Initialize SQLite database with semantic-unit cache tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS semantic_units (
            id TEXT PRIMARY KEY,
            symbol_name TEXT NOT NULL,
            symbol_type TEXT NOT NULL,
            filepath TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            ast_hash TEXT NOT NULL,
            signature TEXT,
            docstring TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS symbol_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol_name TEXT NOT NULL,
            caller_filepath TEXT NOT NULL,
            line INTEGER NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sym_name ON semantic_units(symbol_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ref_sym ON symbol_references(symbol_name)")
    conn.commit()
    return conn


class MantisIndexEngine:
    """Content-addressed AST semantic indexer."""

    def build_structural_index(self, repo_path: str, db_path: str = "structural_index.db") -> dict[str, Any]:
        """Parse source files into content-addressed semantic units."""
        target = Path(repo_path)
        if not target.exists():
            return {"status": "error", "error": f"Path '{repo_path}' does not exist."}

        conn = init_index_db(db_path)
        cur = conn.cursor()

        indexed_units = 0
        indexed_refs = 0
        files_scanned = 0

        for root, _, files in os.walk(target):
            for file_name in files:
                if file_name.endswith(".py") and not file_name.startswith("."):
                    files_scanned += 1
                    fp = Path(root) / file_name
                    rel_path = fp.relative_to(target).as_posix()

                    try:
                        content = fp.read_text(encoding="utf-8", errors="replace")
                        tree = ast.parse(content)
                    except Exception:
                        continue

                    # Extract class and function definitions
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            symbol_name = node.name
                            symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"
                            start_line = node.lineno
                            end_line = getattr(node, "end_lineno", start_line)

                            # Content-addressed AST hash
                            raw_ast = ast.dump(node)
                            ast_hash = hashlib.sha256(raw_ast.encode("utf-8")).hexdigest()[:16]
                            unit_id = f"{rel_path}::{symbol_name}::{start_line}"

                            docstring = ast.get_docstring(node) or ""

                            # Signature representation
                            sig = ""
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                args = [a.arg for a in node.args.args]
                                sig = f"{symbol_name}({', '.join(args)})"
                            else:
                                sig = f"class {symbol_name}"

                            cur.execute("""
                                INSERT OR REPLACE INTO semantic_units
                                (id, symbol_name, symbol_type, filepath, start_line, end_line, ast_hash, signature, docstring)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (unit_id, symbol_name, symbol_type, rel_path, start_line, end_line, ast_hash, sig, docstring))
                            indexed_units += 1

                        # Extract call references
                        elif isinstance(node, ast.Call):
                            call_name = ""
                            if isinstance(node.func, ast.Name):
                                call_name = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                call_name = node.func.attr

                            if call_name:
                                cur.execute("""
                                    INSERT INTO symbol_references (symbol_name, caller_filepath, line)
                                    VALUES (?, ?, ?)
                                """, (call_name, rel_path, node.lineno))
                                indexed_refs += 1

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "repo_path": str(target),
            "db_path": db_path,
            "files_scanned": files_scanned,
            "indexed_semantic_units": indexed_units,
            "indexed_references": indexed_refs,
        }

    def query_symbol(self, symbol_name: str, db_path: str = "structural_index.db", query_type: str = "definition") -> dict[str, Any]:
        """Query definition or references for a given symbol from the SQLite index."""
        if not Path(db_path).exists():
            return {"status": "error", "error": f"Structural index database '{db_path}' not found."}

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        definitions: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []

        if query_type in ("definition", "all"):
            cur.execute("""
                SELECT symbol_name, symbol_type, filepath, start_line, end_line, ast_hash, signature, docstring
                FROM semantic_units
                WHERE symbol_name = ?
            """, (symbol_name,))
            for row in cur.fetchall():
                definitions.append({
                    "symbol_name": row[0],
                    "type": row[1],
                    "filepath": row[2],
                    "start_line": row[3],
                    "end_line": row[4],
                    "ast_hash": row[5],
                    "signature": row[6],
                    "docstring": row[7][:200] if row[7] else "",
                })

        if query_type in ("references", "all"):
            cur.execute("""
                SELECT caller_filepath, line
                FROM symbol_references
                WHERE symbol_name = ?
                LIMIT 50
            """, (symbol_name,))
            for row in cur.fetchall():
                references.append({
                    "caller_filepath": row[0],
                    "line": row[1],
                })

        conn.close()

        return {
            "status": "ok",
            "symbol_name": symbol_name,
            "query_type": query_type,
            "definitions_count": len(definitions),
            "references_count": len(references),
            "definitions": definitions,
            "references": references,
        }


_GLOBAL_INDEXER = MantisIndexEngine()


# -----------------------------------------------------------------------------
# Tool Entrypoints Matching plugin.json Specification
# -----------------------------------------------------------------------------

def mantis_build_structural_index(repo_path: str, db_path: str = "structural_index.db") -> dict[str, Any]:
    """Parse codebase AST into content-addressed semantic units and index into SQLite."""
    return _GLOBAL_INDEXER.build_structural_index(repo_path=repo_path, db_path=db_path)


def mantis_query_symbol(symbol_name: str, db_path: str = "structural_index.db", query_type: str = "definition") -> dict[str, Any]:
    """Query symbol definitions, references, and AST hashes from structural index."""
    return _GLOBAL_INDEXER.query_symbol(symbol_name=symbol_name, db_path=db_path, query_type=query_type)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------

class MantisStructuralIndexPlugin(HarnessPlugin, MantisStructuralIndexService):
    """Brain Harness Plugin providing AST structural indexing and semantic unit querying."""

    name = "plugin.mantis_structural_index"
    version = "1.0.0"
    description = "Google Mantis AST content-addressed semantic-unit indexing and SQLite symbol querying"
    trusted = True

    def __init__(self, engine: MantisIndexEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_INDEXER

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MANTIS_STRUCTURAL_INDEX_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MANTIS_STRUCTURAL_INDEX_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation
    # -------------------------------------------------------------------------

    def build_structural_index(self, repo_path: str, db_path: str = "structural_index.db") -> dict[str, Any]:
        return self._engine.build_structural_index(repo_path, db_path)

    def query_symbol(self, symbol_name: str, db_path: str = "structural_index.db", query_type: str = "definition") -> dict[str, Any]:
        return self._engine.query_symbol(symbol_name, db_path, query_type)
