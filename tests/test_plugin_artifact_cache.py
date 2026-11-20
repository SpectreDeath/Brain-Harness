"""Contract tests for Phase 8 dual-capped LRU, bounded prefetch, and offset index."""

from __future__ import annotations

import asyncio
from pathlib import Path
import queue
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harness.plugins.artifact_cache import (
    ArtifactCacheEntry,
    ArtifactOffsetRecord,
    BoundedArtifactPrefetcher,
    OffsetManifestIndex,
    PluginArtifactCache,
    is_venv_healthy,
    venv_python_path,
)
from harness.plugins.sandbox.venv import VenvExecutor


def _make_fake_venv(venv_dir: Path, payload: bytes = b"python-bin") -> Path:
    py_path = venv_python_path(venv_dir)
    py_path.parent.mkdir(parents=True, exist_ok=True)
    py_path.write_bytes(payload)
    return py_path


@pytest.mark.unit
def test_cache_and_offset_dataclasses_frozen_and_validated(tmp_path: Path) -> None:
    """Rules 12 & 43: records validate inputs in __post_init__ and reject direct mutations."""
    entry = ArtifactCacheEntry(
        key="plugin_a",
        path=tmp_path / "a",
        size_bytes=128,
        created_at=10.0,
        ttl_seconds=30.0,
    )
    assert entry.is_expired(now=25.0) is False
    assert entry.is_expired(now=40.0) is True
    with pytest.raises((AttributeError, TypeError)):
        entry.size_bytes = 256  # type: ignore[misc]

    with pytest.raises(ValueError, match="empty"):
        ArtifactCacheEntry(key="  ", path=tmp_path, size_bytes=10, created_at=0.0)
    with pytest.raises(ValueError, match="non-negative"):
        ArtifactCacheEntry(key="k", path=tmp_path, size_bytes=-1, created_at=0.0)
    with pytest.raises(ValueError, match="positive"):
        ArtifactCacheEntry(key="k", path=tmp_path, size_bytes=1, created_at=0.0, ttl_seconds=0.0)

    rec = ArtifactOffsetRecord(artifact_id="mod_a", offset=0, size_bytes=64)
    with pytest.raises((AttributeError, TypeError)):
        rec.offset = 10  # type: ignore[misc]
    with pytest.raises(ValueError, match="empty"):
        ArtifactOffsetRecord(artifact_id="", offset=0, size_bytes=10)
    with pytest.raises(ValueError, match="non-negative"):
        ArtifactOffsetRecord(artifact_id="a", offset=-5, size_bytes=10)


@pytest.mark.unit
def test_dual_capped_lru_eviction_and_oversized_skip(tmp_path: Path) -> None:
    """Enforces max_entries + max_size_bytes with MRU promotion and clean skip for oversized items."""
    evicted: list[str] = []
    cache = PluginArtifactCache(
        max_entries=3,
        max_size_bytes=100,
        on_evict=lambda entry: evicted.append(entry.key),
    )

    assert cache.put("a", tmp_path / "a", 40) is True
    assert cache.put("b", tmp_path / "b", 40) is True
    # Promote "a" so "b" becomes LRU
    assert cache.get("a") is not None
    # Adding "c" (40B) exceeds 100B total -> must evict LRU ("b"), keeping "a" and "c"
    assert cache.put("c", tmp_path / "c", 40) is True
    assert cache.keys == ("a", "c")
    assert cache.total_bytes == 80
    assert evicted == ["b"]

    # Oversized single artifact (> 100B) skips cleanly without thrashing "a" or "c"
    assert cache.put("huge", tmp_path / "huge", 150) is False
    assert cache.skipped_oversized == 1
    assert cache.keys == ("a", "c")
    assert cache.total_bytes == 80

    # Adding 2 small items crosses max_entries=3 on the 4th total key -> evicts LRU ("a")
    assert cache.put("d", tmp_path / "d", 10) is True
    assert cache.keys == ("c", "d", "a") or cache.keys == ("a", "c", "d")
    assert cache.put("e", tmp_path / "e", 10) is True
    assert cache.entry_count <= 3
    assert cache.total_bytes <= 100
    assert "a" in evicted


@pytest.mark.unit
def test_concurrent_cache_thread_safety(tmp_path: Path) -> None:
    """Concurrent multi-threaded put/get calls preserve dual bounds cleanly."""
    cache = PluginArtifactCache(max_entries=4, max_size_bytes=200)
    errors: list[BaseException] = []

    def worker(worker_id: int) -> None:
        try:
            for idx in range(40):
                key = f"k_{(worker_id + idx) % 8}"
                cache.put(key, tmp_path / key, 40)
                cache.get(f"k_{idx % 8}")
        except BaseException as exc:  # pragma: no cover - captured for assertion
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)

    assert not errors
    assert cache.entry_count <= 4
    assert cache.total_bytes <= 200
    assert cache.total_bytes >= 0


@pytest.mark.unit
def test_ttl_expiration_and_corrupt_venv_invalidation(tmp_path: Path) -> None:
    """Gap #4: expired TTL or missing/0-byte venv python triggers clean cache invalidation."""
    now = [100.0]
    evicted: list[str] = []
    cache = PluginArtifactCache(
        max_entries=4,
        max_size_bytes=1000,
        clock=lambda: now[0],
        on_evict=lambda e: evicted.append(e.key),
        health_check=lambda e: is_venv_healthy(e.path),
    )

    venv_ttl = tmp_path / "venv_ttl"
    _make_fake_venv(venv_ttl)
    assert is_venv_healthy(venv_ttl) is True
    cache.put("ttl_key", venv_ttl, 50, ttl_seconds=10.0)
    assert cache.get("ttl_key") is not None

    # Advance monotonic clock past TTL
    now[0] = 111.0
    assert cache.get("ttl_key") is None
    assert cache.total_bytes == 0
    assert evicted == ["ttl_key"]

    # Corrupt venv (0-byte python binary, then deleted binary) fails health check
    venv_bad = tmp_path / "venv_bad"
    py_bad = _make_fake_venv(venv_bad, b"valid")
    cache.put("bad_key", venv_bad, 60, ttl_seconds=100.0)
    assert cache.get("bad_key") is not None

    py_bad.write_bytes(b"")
    assert is_venv_healthy(venv_bad) is False
    assert cache.get("bad_key") is None
    assert evicted == ["ttl_key", "bad_key"]
    assert cache.total_bytes == 0


@pytest.mark.unit
def test_bounded_prefetcher_backpressure_and_errors() -> None:
    """BoundedArtifactPrefetcher uses lazy single worker and enforces bounded queue backpressure."""
    gate = threading.Event()
    started_first = threading.Event()

    def loader(key: str) -> str:
        started_first.set()
        gate.wait(timeout=5.0)
        if key == "boom":
            raise RuntimeError("broken artifact")
        return f"loaded:{key}"

    prefetcher = BoundedArtifactPrefetcher(loader, max_depth=2)
    assert prefetcher.worker_alive is False  # Lazy: no worker spawned at __init__

    with prefetcher:
        prefetcher.submit("item1")
        assert started_first.wait(timeout=2.0)
        assert prefetcher.worker_alive is True
        # With item1 blocked in loader and max_depth=2, requests queue holds 2 more
        prefetcher.submit("item2", timeout=0.5)
        prefetcher.submit("boom", timeout=0.5)
        with pytest.raises(queue.Full):
            prefetcher.submit("item4", timeout=0.05)

        gate.set()
        assert prefetcher.next_result(timeout=2.0) == ("item1", "loaded:item1")
        assert prefetcher.next_result(timeout=2.0) == ("item2", "loaded:item2")
        with pytest.raises(RuntimeError, match="broken artifact"):
            prefetcher.next_result(timeout=2.0)

    assert prefetcher.worker_alive is False


@pytest.mark.unit
def test_offset_manifest_index_rule48_byte_seeks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Rule 48: OffsetManifestIndex loads entries via exact binary seek/read byte ranges."""
    bundle = tmp_path / "plugins.bundle"
    idx = OffsetManifestIndex.build(
        bundle,
        {
            "alpha": {"name": "alpha", "version": "1.0.0"},
            "beta": b"binary-payload-beta",
            "gamma": "text-gamma",
        },
    )
    assert set(idx.records.keys()) == {"alpha", "beta", "gamma"}
    assert (tmp_path / "plugins.bundle.index.json").is_file()

    reloaded = OffsetManifestIndex.load(bundle)
    assert set(reloaded.records.keys()) == {"alpha", "beta", "gamma"}

    seeks: list[int] = []
    real_open = open

    class _SpyFile:
        def __init__(self, fh: object) -> None:
            self._fh = fh

        def __enter__(self) -> _SpyFile:
            return self

        def __exit__(self, *args: object) -> None:
            self._fh.close()  # type: ignore[attr-defined]

        def seek(self, offset: int) -> int:
            seeks.append(offset)
            return self._fh.seek(offset)  # type: ignore[attr-defined]

        def read(self, n: int = -1) -> bytes:
            return self._fh.read(n)  # type: ignore[attr-defined]

    def spy_open(path: Path, mode: str = "r", *args: object, **kwargs: object) -> object:
        fh = real_open(path, mode, *args, **kwargs)
        if Path(path) == bundle and "rb" in mode:
            return _SpyFile(fh)
        return fh

    monkeypatch.setattr("builtins.open", spy_open)
    assert reloaded.read_bytes("beta") == b"binary-payload-beta"
    assert seeks == [reloaded.records["beta"].offset]
    assert reloaded.read_json("alpha") == {"name": "alpha", "version": "1.0.0"}
    with pytest.raises(KeyError):
        reloaded.read_bytes("missing")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_venv_executor_lazy_cache_reuse_and_invalidation(tmp_path: Path) -> None:
    """Rule 7 + Gap #4: VenvExecutor stays lazy at __init__, caches healthy venvs, rebuilds corrupt/expired."""
    plugin_dir = tmp_path / "sample_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "main.py").write_text("def ping(): return 'ok'\n", encoding="utf-8")
    venv_dir = tmp_path / "venvs" / "sample_plugin"

    now = [10.0]
    cache = PluginArtifactCache(
        max_entries=2,
        max_size_bytes=1024 * 1024,
        clock=lambda: now[0],
        health_check=lambda e: is_venv_healthy(e.path),
    )

    executor = VenvExecutor(
        plugin_dir,
        venv_dir=venv_dir,
        dependencies=["pydantic"],
        artifact_cache=cache,
        ttl_seconds=30.0,
    )
    # Rule 7: __init__ performs zero eager provisioning
    assert not venv_dir.exists()
    assert cache.entry_count == 0

    setup_calls = 0

    async def fake_setup(self: VenvExecutor) -> None:
        nonlocal setup_calls
        setup_calls += 1
        _make_fake_venv(self._venv_dir, b"python-exe-bytes")
        self._setup_done = True

    mock_sub = MagicMock()
    mock_sub.start = AsyncMock()
    mock_sub.stop = AsyncMock()
    mock_sub.is_running = True

    with (
        patch.object(VenvExecutor, "_setup_venv", fake_setup),
        patch("harness.plugins.sandbox.venv.SubprocessExecutor", return_value=mock_sub),
    ):
        await executor.start()
        assert setup_calls == 1
        assert cache.entry_count == 1
        assert executor.cache_key in cache.keys

        # Simulate fresh executor instance sharing cache & venv_dir -> reuses cached healthy venv
        executor2 = VenvExecutor(
            plugin_dir,
            venv_dir=venv_dir,
            dependencies=["pydantic"],
            artifact_cache=cache,
            ttl_seconds=30.0,
        )
        await executor2.start()
        assert setup_calls == 1  # Reused without re-running _setup_venv

        # Corrupt venv python executable -> health check fails -> rebuilds
        venv_python_path(venv_dir).unlink()
        await executor2.start()
        assert setup_calls == 2

        # Expire TTL -> invalidates cached entry -> rebuilds
        now[0] = 50.0
        await executor2.start()
        assert setup_calls == 3

        await asyncio.sleep(0)


@pytest.mark.unit
def test_bounded_prefetcher_submit_default_timeout_raises_full_without_hanging() -> None:
    """BoundedArtifactPrefetcher.submit defaults to finite timeout so queue-full raises instead of hanging."""
    import time

    gate = threading.Event()
    started = threading.Event()

    def slow_loader(key: str) -> str:
        started.set()
        gate.wait(timeout=2.0)
        return key

    prefetcher = BoundedArtifactPrefetcher(slow_loader, max_depth=1, default_submit_timeout=0.05)
    try:
        prefetcher.submit("first")
        assert started.wait(timeout=1.0)
        prefetcher.submit("queued")
        t0 = time.monotonic()
        with pytest.raises(queue.Full):
            prefetcher.submit("overflow")  # No explicit timeout= kwarg: must use finite default
        assert time.monotonic() - t0 < 1.0
    finally:
        gate.set()
        prefetcher.close(timeout=1.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_factory_wires_artifact_cache_and_sandboxed_plugin_prefetch_smoke(tmp_path: Path) -> None:
    """Factory wires shared artifact_cache into VenvExecutor and SandboxedPlugin prefetcher warms venv checks."""
    from harness.kernel.context import ServiceContext
    from harness.plugins.manifest import IsolationMode, PluginManifest
    from harness.plugins.sandbox.factory import SandboxExecutorFactory
    from harness.plugins.sandboxed import SandboxedPlugin

    plugin_root = tmp_path / "demo_venv_plugin"
    plugin_root.mkdir()
    (plugin_root / "main.py").write_text("def ping():\n    return 'pong'\n", encoding="utf-8")

    manifest = PluginManifest(name="demo.venv", isolation=IsolationMode.VENV, dependencies=["demo-pkg"])
    executor = SandboxExecutorFactory.create(manifest, plugin_root)
    assert isinstance(executor, VenvExecutor)
    default_cache = SandboxExecutorFactory.get_default_artifact_cache()
    assert executor._artifact_cache is default_cache

    venv_dir = tmp_path / "staged_venv"
    _make_fake_venv(venv_dir, b"python-exe-bytes")
    executor._venv_dir = venv_dir
    default_cache.put(executor.cache_key, venv_dir, 16)

    mock_sub = MagicMock()
    mock_sub.start = AsyncMock()
    mock_sub.stop = AsyncMock()
    mock_sub.is_running = True

    setup_mock = AsyncMock(side_effect=AssertionError("_setup_venv should not run on cache hit"))
    with (
        patch.object(VenvExecutor, "_setup_venv", setup_mock),
        patch("harness.plugins.sandbox.venv.SubprocessExecutor", return_value=mock_sub),
    ):
        await executor.start()
        setup_mock.assert_not_awaited()
        await executor.stop()

    ctx = ServiceContext()
    plug = SandboxedPlugin(manifest, plugin_root, executor=executor)
    prefetcher = SandboxExecutorFactory.get_default_prefetcher()
    try:
        await plug.on_load(ctx)
        key, status = prefetcher.next_result(timeout=2.0)
        assert key == executor.cache_key
        assert status["cached"] is True
        assert status["healthy"] is True
    finally:
        prefetcher.close(timeout=1.0)
