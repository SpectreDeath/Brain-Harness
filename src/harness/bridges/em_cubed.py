"""Em-Cubed bridge — adapts Em-Cubed neuro-symbolic surfaces into Harness plugins and tools.

Enables Harness to leverage Em-Cubed's 11+ execution surfaces (Prolog, Z3, Datalog,
Hy, SQLite, Python, QuickJS, etc.) with timeout protection and shared substrate.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import structlog

from harness.bridges.base import BridgeCapability, EcosystemBridgePlugin
from harness.kernel.context import ServiceKey
from harness.services.tools import ToolSpec

logger = structlog.get_logger()

# Service key for Em-Cubed coprocessor / surface engine
EM_CUBED_BRIDGE_KEY: ServiceKey[EmCubedPlugin] = ServiceKey("bridge.em_cubed")


class EmCubedPlugin(EcosystemBridgePlugin[Any]):
    """Bridge plugin that discovers and mounts Em-Cubed surfaces as tools."""

    project_name = "em-cubed"
    env_var = "EM_CUBED_PATH"
    service_key = EM_CUBED_BRIDGE_KEY
    capabilities = [
        BridgeCapability.CODE_EXECUTION,
        BridgeCapability.TOOL_HOSTING,
        BridgeCapability.VECTOR_INDEX,
    ]

    def __init__(
        self,
        em_cubed_path: Path | str | None = None,
        *,
        override_path: Path | str | None = None,
    ) -> None:
        target = em_cubed_path if em_cubed_path is not None else override_path
        super().__init__(override_path=target)
        self._em_cubed_path = self._override_path
        self._plugin_manager: Any = None
        self._available_surfaces: list[str] = []

    @property
    def name(self) -> str:
        return "bridge.em_cubed"

    @property
    def version(self) -> str:
        return "0.8.0"

    @property
    def description(self) -> str:
        return "Em-Cubed Polyglot AI Skill Engine & Neuro-Symbolic OS bridge"

    @property
    def available_surfaces(self) -> list[str]:
        """List of detected and available Em-Cubed surface names."""
        return list(self._available_surfaces)

    async def init_substrate(self, root_path: Path) -> Any:
        src_path = root_path / "src"
        if src_path.exists() and str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        elif str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))

        try:
            from em_cubed.plugin_manager import PluginManager

            self._plugin_manager = PluginManager()
            self._available_surfaces = self._plugin_manager.get_available_surfaces()
            logger.info("Em-Cubed PluginManager initialized successfully")
            return self._plugin_manager
        except ImportError as e:
            logger.warning(
                "Em-Cubed package not importable. Surface bridge will operate in stub mode.",
                error=str(e),
            )
            self._plugin_manager = None
            self._available_surfaces = []
            return None

    async def shutdown_substrate(self) -> None:
        if self._plugin_manager:
            try:
                self._plugin_manager.shutdown_all()
            except Exception as e:
                logger.warning("Em-Cubed shutdown error", error=str(e))
            self._plugin_manager = None
        self._available_surfaces = []

    async def get_tool_specs(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        for surface_name in self._available_surfaces:
            tool_name = f"surface.{surface_name}"
            description = f"Execute code on the Em-Cubed '{surface_name}' neuro-symbolic surface."
            executor = self._make_surface_executor(surface_name)

            specs.append(
                ToolSpec(
                    name=tool_name,
                    description=description,
                    executor=executor,
                    parameters_schema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": f"Source code to execute on {surface_name}",
                            },
                            "context": {
                                "type": "object",
                                "description": "Optional variable context dictionary",
                            },
                        },
                        "required": ["code"],
                    },
                    provider=self.name,
                )
            )
        return specs

    async def execute_surface(
        self,
        surface_name: str,
        code: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Direct programmatic execution on a named surface."""
        if not self._plugin_manager:
            return {"status": "error", "message": "Em-Cubed is not initialized"}

        surface = self._plugin_manager.get(surface_name)
        if not surface:
            return {
                "status": "error",
                "message": f"Surface '{surface_name}' is not available or failed to load",
            }

        try:
            res = await surface.execute_with_timeout(code, context)
            return cast(dict[str, Any], res)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _make_surface_executor(self, surface_name: str) -> Any:
        """Create an async callable tool executor for a given surface."""

        async def _executor(code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return await self.execute_surface(surface_name, code, context)

        return _executor
