"""Characterization and contract tests for deepened BrainBridgeService (Phase 2).

Validates:
1. DefaultBrainBridgeService operates completely in-process without plugin dependencies.
2. resolve_brain_bridge(ctx) single-seam factory resolves from IoC or falls back gracefully.
3. In-memory indexing, TF-IDF vector retrieval, format detection, and detach lifecycle.
4. Clean export of DefaultBrainBridgeService and resolve_brain_bridge from harness.services.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
    DefaultBrainBridgeService,
    detect_brain_format,
    is_git_url,
    resolve_brain_bridge,
)


def test_resolve_brain_bridge_without_context() -> None:
    """Verify resolve_brain_bridge returns DefaultBrainBridgeService when ctx is None."""
    svc = resolve_brain_bridge(None)
    assert isinstance(svc, DefaultBrainBridgeService)
    assert isinstance(svc, BrainBridgeService)


def test_resolve_brain_bridge_from_ioc_context() -> None:
    """Verify resolve_brain_bridge extracts registered service from ServiceContext."""
    ctx = ServiceContext()
    custom_service = DefaultBrainBridgeService()
    ctx.provide(BRAIN_BRIDGE_KEY, custom_service, provider="test")

    resolved = resolve_brain_bridge(ctx)
    assert resolved is custom_service


def test_detect_brain_format_and_git_url(tmp_path: Path) -> None:
    """Verify brain format detector and git url recognizer in core service."""
    assert is_git_url("https://github.com/example/repo.git") is True
    assert is_git_url("git@github.com:example/repo.git") is True
    assert is_git_url(str(tmp_path)) is False

    harness_dir = tmp_path / "harness_app"
    (harness_dir / ".harness").mkdir(parents=True)
    assert detect_brain_format(harness_dir) == "harness_instance"

    doc_dir = tmp_path / "docs_repo"
    doc_dir.mkdir()
    (doc_dir / "guide.md").write_text("# Guide", encoding="utf-8")
    assert detect_brain_format(doc_dir) == "raw_docs"


def test_default_brain_bridge_attach_query_detach_lifecycle(tmp_path: Path) -> None:
    """Verify complete in-memory lifecycle on DefaultBrainBridgeService."""
    repo = tmp_path / "sample_brain"
    repo.mkdir()
    (repo / "architecture.md").write_text(
        "# Micro-Kernel Architecture\nThe IoC container registers services via typed keys.\n"
        "Plugins provide typed services.\n",
        encoding="utf-8",
    )
    (repo / "main.py").write_text(
        "def run_kernel():\n    print('Kernel booting with event bus and services')\n",
        encoding="utf-8",
    )

    service = DefaultBrainBridgeService()

    # 1. Attach
    attach_res = service.attach(str(repo), alias="test_mount")
    assert isinstance(attach_res, BrainAttachResult)
    assert attach_res.status == "ok"
    assert attach_res.alias == "test_mount"
    assert attach_res.summary.get("total_chunks", 0) > 0

    # 2. List
    list_res = service.list_attached()
    assert isinstance(list_res, BrainListResult)
    assert list_res.attached_count == 1
    assert list_res.brains[0]["alias"] == "test_mount"

    # 3. Query
    query_res = service.query("IoC container services", brain_alias="test_mount")
    assert isinstance(query_res, BrainQueryResult)
    assert query_res.status == "ok"
    assert query_res.results_count > 0
    assert any("IoC" in r["snippet"] or "container" in r["snippet"] for r in query_res.results)

    # 4. Detach
    detach_res = service.detach("test_mount")
    assert isinstance(detach_res, BrainDetachResult)
    assert detach_res.status == "ok"
    assert detach_res.detached_alias == "test_mount"

    # Verify detach cleared mount
    list_after = service.list_attached()
    assert list_after.attached_count == 0


@pytest.mark.asyncio
async def test_async_bridge_methods(tmp_path: Path) -> None:
    """Verify asynchronous attach_async and query_async methods."""
    repo = tmp_path / "async_brain"
    repo.mkdir()
    (repo / "data.py").write_text("x = 42\n# Epistemic lineage and isnad chains\n", encoding="utf-8")

    service = DefaultBrainBridgeService()
    attach_res = await service.attach_async(str(repo), alias="async_mount")
    assert attach_res.status == "ok"

    query_res = await service.query_async("isnad chains", brain_alias="async_mount")
    assert query_res.status == "ok"
    assert query_res.results_count > 0
