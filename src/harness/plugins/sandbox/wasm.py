"""WebAssembly in-process execution via wasmtime engine with WASI linking."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from harness.plugins.sandbox.base import SandboxExecutor

logger = structlog.get_logger()


class WasmSandboxExecutor(SandboxExecutor):
    """Execute pure leaf plugin logic inside an in-process WebAssembly sandbox via wasmtime."""

    def __init__(
        self,
        wasm_path: Path,
        *,
        memory_limit_bytes: int = 64 * 1024 * 1024,
        timeout_ticks: int = 1000,
    ) -> None:
        self._wasm_path = Path(wasm_path).resolve()
        self._memory_limit_bytes = memory_limit_bytes
        self._timeout_ticks = timeout_ticks
        self._running = False
        self._engine: Any = None
        self._module: Any = None

    @classmethod
    def is_available(cls) -> bool:
        """Check whether wasmtime runtime is installed and importable."""
        try:
            import wasmtime  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "wasm"

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def wasm_path(self) -> Path:
        return self._wasm_path

    async def start(self) -> None:
        """Compile and cache the WebAssembly module."""
        if not self.is_available():
            raise RuntimeError(
                "WasmSandboxExecutor requires 'wasmtime'. Please install it with 'pip install wasmtime'."
            )
        import wasmtime

        cfg = wasmtime.Config()
        cfg.epoch_interruption = True
        self._engine = wasmtime.Engine(cfg)
        self._module = wasmtime.Module.from_file(self._engine, str(self._wasm_path))
        self._running = True
        logger.info("WASM sandbox started", path=str(self._wasm_path))

    async def stop(self) -> None:
        """Clean up WASM engine state."""
        self._running = False
        self._module = None
        self._engine = None
        logger.info("WASM sandbox stopped", path=str(self._wasm_path))

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a method on the WASM module using JSON-RPC."""
        if not self._running or self._engine is None or self._module is None:
            return {"status": "error", "error": "WASM executor not running"}

        import json
        import tempfile
        import wasmtime

        req = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        }
        req_bytes = json.dumps(req).encode("utf-8")

        def _run_sync() -> dict[str, Any]:
            linker = wasmtime.Linker(self._engine)
            linker.define_wasi()

            wasi_cfg = wasmtime.WasiConfig()

            with (
                tempfile.NamedTemporaryFile("wb+", delete=False) as in_f,
                tempfile.NamedTemporaryFile("rb+", delete=False) as out_f,
                tempfile.NamedTemporaryFile("rb+", delete=False) as err_f,
            ):
                in_path = Path(in_f.name)
                out_path = Path(out_f.name)
                err_path = Path(err_f.name)

                try:
                    in_f.write(req_bytes)
                    in_f.flush()
                    in_f.seek(0)

                    wasi_cfg.stdin_file = str(in_path)
                    wasi_cfg.stdout_file = str(out_path)
                    wasi_cfg.stderr_file = str(err_path)

                    store = wasmtime.Store(self._engine)
                    store.set_wasi(wasi_cfg)
                    store.set_epoch_deadline(self._timeout_ticks)

                    instance = linker.instantiate(store, self._module)

                    # Try calling method directly or default WASI entry point _start
                    func = instance.exports(store).get(method)
                    if func is None:
                        func = instance.exports(store).get("_start")
                    if func is None:
                        func = instance.exports(store).get("main")

                    if func is None:
                        return {
                            "status": "error",
                            "error": f"Method or entrypoint not found in WASM exports: {method}",
                        }

                    func(store)

                    out_f.seek(0)
                    resp_bytes = out_f.read()
                    if not resp_bytes:
                        err_f.seek(0)
                        err_msg = err_f.read().decode("utf-8", errors="replace")
                        return {"status": "error", "error": err_msg or "Empty WASM output"}

                    resp = json.loads(resp_bytes.decode("utf-8"))
                    if "error" in resp:
                        return {"status": "error", "error": resp["error"]}
                    return {"status": "ok", "result": resp.get("result")}
                finally:
                    in_f.close()
                    out_f.close()
                    err_f.close()
                    in_path.unlink(missing_ok=True)
                    out_path.unlink(missing_ok=True)
                    err_path.unlink(missing_ok=True)

        try:
            return await asyncio.wait_for(asyncio.to_thread(_run_sync), timeout=timeout)
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"WASM execution timed out after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


__all__ = ["WasmSandboxExecutor"]
