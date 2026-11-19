"""Depth-bounded producer-consumer prefetcher for plugin staging workloads."""

from __future__ import annotations

from collections.abc import Callable
import queue
import threading
from typing import Any


class BoundedArtifactPrefetcher:
    """Lazy single-worker producer-consumer prefetcher bounded by ``queue.Queue(maxsize=max_depth)``."""

    def __init__(self, loader: Callable[[str], Any], *, max_depth: int = 2) -> None:
        if max_depth <= 0:
            raise ValueError("max_depth must be positive")
        self._loader = loader
        self._requests: queue.Queue[str] = queue.Queue(maxsize=max_depth)
        self._results: queue.Queue[tuple[str, Any, BaseException | None]] = queue.Queue(maxsize=max_depth)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None

    @property
    def worker_alive(self) -> bool:
        return bool(self._worker is not None and self._worker.is_alive())

    def start(self) -> None:
        """Lazily spawn the background prefetch daemon thread."""
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("Prefetcher is closed")
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(
                    target=self._run,
                    name="plugin-artifact-prefetcher",
                    daemon=True,
                )
                self._worker.start()

    def submit(self, key: str, *, timeout: float | None = None) -> None:
        """Enqueue a prefetch key, blocking up to ``timeout`` when queue is at capacity."""
        self.start()
        self._requests.put(key, timeout=timeout)

    def next_result(self, *, timeout: float | None = None) -> tuple[str, Any]:
        """Dequeue the next completed prefetch result or re-raise loader errors."""
        key, val, exc = self._results.get(timeout=timeout)
        if exc is not None:
            raise exc
        return key, val

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                key = self._requests.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                payload: tuple[str, Any, BaseException | None] = (key, self._loader(key), None)
            except BaseException as exc:
                payload = (key, None, exc)
            while not self._stop.is_set():
                try:
                    self._results.put(payload, timeout=0.05)
                    break
                except queue.Full:
                    continue

    def close(self, *, timeout: float = 2.0) -> None:
        """Signal shutdown and join the worker thread."""
        self._stop.set()
        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=timeout)

    def __enter__(self) -> BoundedArtifactPrefetcher:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
