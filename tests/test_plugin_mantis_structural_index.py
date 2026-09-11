"""Tests for Google Mantis Structural Index Plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.software_engineering.mantis_structural_index.main import (
    MANTIS_STRUCTURAL_INDEX_KEY,
    MantisStructuralIndexPlugin,
    MantisStructuralIndexService,
    mantis_build_structural_index,
    mantis_query_symbol,
)


@pytest.mark.unit
class TestMantisStructuralIndexPlugin:
    """Unit test suite for Mantis AST structural indexer."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey into ServiceContext."""
        ctx = ServiceContext()
        plugin = MantisStructuralIndexPlugin()

        assert plugin.name == "plugin.mantis_structural_index"
        assert MANTIS_STRUCTURAL_INDEX_KEY in plugin.provides

        await plugin.on_load(ctx)
        svc = ctx.require(MANTIS_STRUCTURAL_INDEX_KEY)
        assert isinstance(svc, MantisStructuralIndexService)

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    def test_build_and_query_structural_index(self, tmp_path: Path) -> None:
        """Verify AST parsing extracts semantic units and queries return definitions and callers."""
        repo_dir = tmp_path / "sample_repo"
        repo_dir.mkdir()

        (repo_dir / "service.py").write_text('''
class PaymentGateway:
    """Handles financial transactions."""
    def process_payment(self, amount):
        return True

def execute_charge(user, amount):
    gw = PaymentGateway()
    return gw.process_payment(amount)
''', encoding="utf-8")

        db_file = tmp_path / "test_structural_index.db"

        # 1. Build Index
        build_res = mantis_build_structural_index(
            repo_path=str(repo_dir),
            db_path=str(db_file)
        )
        assert build_res["status"] == "ok"
        assert build_res["files_scanned"] == 1
        assert build_res["indexed_semantic_units"] >= 3  # PaymentGateway, process_payment, execute_charge

        # 2. Query Definition
        query_def = mantis_query_symbol(
            symbol_name="process_payment",
            db_path=str(db_file),
            query_type="definition"
        )
        assert query_def["status"] == "ok"
        assert query_def["definitions_count"] >= 1
        assert query_def["definitions"][0]["symbol_name"] == "process_payment"
        assert query_def["definitions"][0]["ast_hash"] != ""

        # 3. Query Callers / References
        query_ref = mantis_query_symbol(
            symbol_name="process_payment",
            db_path=str(db_file),
            query_type="references"
        )
        assert query_ref["status"] == "ok"
        assert query_ref["references_count"] >= 1
