"""SandboxExecutorFactory for strategy resolution and single-seam IoC dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.plugins.sandbox.base import SANDBOX_FACTORY_KEY, SandboxExecutor
from harness.plugins.sandbox.container import ContainerExecutor
from harness.plugins.sandbox.in_process import InProcessExecutor
from harness.plugins.sandbox.subprocess import SubprocessExecutor
from harness.plugins.sandbox.venv import VenvExecutor
from harness.plugins.sandbox.wasm import WasmSandboxExecutor

logger = structlog.get_logger()


class SandboxExecutorFactory:
    """Authoritative factory for constructing appropriate SandboxExecutor instances.

    Consolidates isolation strategy resolution, entrypoint discovery, and
    dependency-driven sandbox provisioning across the plugin and ingestion subsystems.
    """

    @classmethod
    def find_entrypoint(cls, manifest: Any, root: Path) -> Path | None:
        """Find the main Python entrypoint script in the plugin root."""
        root_path = Path(root)
        if getattr(manifest, "entrypoint", None):
            ep = root_path / str(manifest.entrypoint)
            if ep.exists():
                return ep

        candidates = ["main.py", "__main__.py", "plugin.py", "app.py"]
        for c in candidates:
            p = root_path / c
            if p.exists():
                return p

        py_files = sorted(root_path.glob("*.py"))
        return py_files[0] if py_files else None

    @classmethod
    def create(
        cls,
        manifest: Any,
        root: Path,
        *,
        force_isolation: Any = None,
    ) -> SandboxExecutor | None:
        """Construct the appropriate SandboxExecutor for a manifest and filesystem root.

        Args:
            manifest: PluginManifest instance.
            root: Root path of the plugin.
            force_isolation: Optional override for isolation mode.

        Returns:
            Configured SandboxExecutor or None if no valid strategy/entrypoint found.
        """
        import importlib.util

        from harness.plugins.manifest import IsolationMode

        root_path = Path(root).resolve()
        entrypoint = cls.find_entrypoint(manifest, root_path)
        isolation = (
            force_isolation
            if force_isolation is not None
            else getattr(manifest, "isolation", IsolationMode.SUBPROCESS)
        )
        trusted = getattr(manifest, "trusted", False)
        deps = getattr(manifest, "dependencies", []) or []
        name = getattr(manifest, "name", root_path.name)
        container_cfg = getattr(manifest, "container", None)

        if isolation == IsolationMode.IN_PROCESS:
            if trusted and entrypoint and entrypoint.exists():
                try:
                    module_name = f"sandboxed_inproc_{name.replace('.', '_')}"
                    spec = importlib.util.spec_from_file_location(
                        module_name, entrypoint
                    )
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        return InProcessExecutor(mod)
                except Exception as e:
                    logger.warning(
                        "Failed in-process plugin import, falling back to subprocess",
                        plugin=name,
                        error=str(e),
                    )
            elif not trusted:
                logger.warning(
                    "Untrusted plugin requested in-process isolation; enforcing subprocess sandbox",
                    plugin=name,
                )

        if isolation == IsolationMode.DOCKER:
            runtime_bin = ContainerExecutor._detect_runtime()
            if runtime_bin:
                return ContainerExecutor(
                    plugin_dir=root_path,
                    entrypoint=entrypoint,
                    config=container_cfg,
                    runtime=runtime_bin,
                )
            logger.warning(
                "Container runtime (docker/podman) not available in PATH; falling back to SubprocessExecutor",
                plugin=name,
            )
            if entrypoint and entrypoint.exists():
                return SubprocessExecutor(entrypoint)
            return None

        if isolation == IsolationMode.VENV or len(deps) > 0:
            return VenvExecutor(
                plugin_dir=root_path,
                dependencies=deps,
            )

        mem_limit = 512.0
        if container_cfg and getattr(container_cfg, "memory_limit", None):
            try:
                raw_mem = str(container_cfg.memory_limit).lower()
                if raw_mem.endswith(("m", "mb")):
                    mem_limit = float(raw_mem.rstrip("mb"))
                elif raw_mem.endswith(("g", "gb")):
                    mem_limit = float(raw_mem.rstrip("gb")) * 1024
                else:
                    mem_limit = float(raw_mem)
            except Exception:
                pass

        if isolation == IsolationMode.WASM:
            wasm_entrypoint = getattr(manifest, "wasm_entrypoint", None)
            wasm_file: Path | None = None
            if wasm_entrypoint:
                candidate = root_path / str(wasm_entrypoint)
                if candidate.exists():
                    wasm_file = candidate
            if wasm_file is None:
                for cand in [root_path / "plugin.wasm", root_path / f"{name}.wasm"]:
                    if cand.exists():
                        wasm_file = cand
                        break

            if wasm_file and WasmSandboxExecutor.is_available():
                return WasmSandboxExecutor(wasm_file)

            if not WasmSandboxExecutor.is_available():
                logger.warning(
                    "Wasmtime runtime not available in environment; falling back to SubprocessExecutor",
                    plugin=name,
                )
            else:
                logger.warning(
                    "WASM binary not found; falling back to SubprocessExecutor",
                    plugin=name,
                    entrypoint=str(wasm_entrypoint),
                )
            if entrypoint and entrypoint.exists():
                return SubprocessExecutor(
                    entrypoint,
                    memory_limit_mb=mem_limit,
                    network_disabled=(not trusted),
                )
            return None

        if entrypoint and entrypoint.exists():
            return SubprocessExecutor(
                entrypoint,
                memory_limit_mb=mem_limit,
                network_disabled=(not trusted),
            )

        return None


def resolve_sandbox_executor_factory(context: Any) -> type[SandboxExecutorFactory]:
    """Resolve or provide SandboxExecutorFactory class through single-seam IoC (Rule 58)."""
    if hasattr(context, "optional") and callable(context.optional):
        existing = context.optional(SANDBOX_FACTORY_KEY)
        if existing is not None:
            return existing
    if hasattr(context, "provide") and callable(context.provide):
        context.provide(SANDBOX_FACTORY_KEY, SandboxExecutorFactory, provider="plugins.sandbox")
    return SandboxExecutorFactory


__all__ = [
    "SandboxExecutorFactory",
    "resolve_sandbox_executor_factory",
]
