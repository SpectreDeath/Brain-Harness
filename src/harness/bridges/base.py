"""Ecosystem bridge base — generic adapter for peer ecosystem repositories.

Unifies path resolution, lazy substrate binding, tool registration, and lifecycle
management across Em-Cubed, Memtext, Skill Flywheel, and other ecosystem peers.
"""

from __future__ import annotations

from enum import Enum
import inspect
from pathlib import Path
from typing import Any, Generic, TypeVar

import structlog

from harness.bridges.locator import EcosystemLocator
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.services.tools import TOOL_REGISTRY_KEY, ToolSpec

logger = structlog.get_logger()

TSubstrate = TypeVar("TSubstrate")


class BridgeCapability(str, Enum):
    """Capabilities exposed by peer ecosystem bridges."""

    VECTOR_INDEX = "vector_index"
    MEMORY_GRAPH = "memory_graph"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    CODE_EXECUTION = "code_execution"
    EPISTEMIC_AUDIT = "epistemic_audit"
    TOOL_HOSTING = "tool_hosting"
    REACTIVE_EVENT_STORE = "reactive_event_store"


class EcosystemBridgeCatalog:
    """Authoritative registry and discovery engine for ecosystem peer bridges."""

    _registry: dict[str, type[EcosystemBridgePlugin[Any]]] = {}

    @classmethod
    def register(cls, bridge_cls: type[EcosystemBridgePlugin[Any]]) -> None:
        """Register an ecosystem bridge plugin class."""
        project_name = getattr(bridge_cls, "project_name", None)
        if project_name:
            cls._registry[project_name] = bridge_cls
            env_var = getattr(bridge_cls, "env_var", None)
            if env_var:
                EcosystemLocator.ENV_VARS[project_name] = env_var

    @classmethod
    def list_bridges(cls) -> list[type[EcosystemBridgePlugin[Any]]]:
        """List all registered ecosystem bridge classes."""
        cls._ensure_builtins_registered()
        return list(cls._registry.values())

    @classmethod
    def get_bridge(cls, project_name: str) -> type[EcosystemBridgePlugin[Any]] | None:
        """Get bridge class by project name."""
        cls._ensure_builtins_registered()
        return cls._registry.get(project_name)

    @classmethod
    def find_bridges_by_capability(
        cls, capability: BridgeCapability | str
    ) -> list[type[EcosystemBridgePlugin[Any]]]:
        """Find bridge plugin classes that provide the specified capability."""
        cls._ensure_builtins_registered()
        cap_val = capability.value if isinstance(capability, BridgeCapability) else str(capability)
        matches = []
        for bridge_cls in cls._registry.values():
            caps = getattr(bridge_cls, "capabilities", [])
            cap_vals = [c.value if isinstance(c, BridgeCapability) else str(c) for c in caps]
            if cap_val in cap_vals:
                matches.append(bridge_cls)
        return matches

    @classmethod
    def get_capability_matrix(cls) -> dict[str, list[str]]:
        """Return a mapping of bridge names to their exposed capability lists."""
        cls._ensure_builtins_registered()
        matrix: dict[str, list[str]] = {}
        for name, bridge_cls in cls._registry.items():
            caps = getattr(bridge_cls, "capabilities", [])
            matrix[name] = [c.value if isinstance(c, BridgeCapability) else str(c) for c in caps]
        return matrix

    @classmethod
    def get_diagnostic_reports(cls) -> list[Any]:
        """Return structured diagnostic reports for all registered and discovered bridges."""
        cls._ensure_builtins_registered()
        return EcosystemLocator.inspect_all()

    @classmethod
    def status(cls) -> dict[str, dict[str, Any]]:
        """Return discovery status for all registered ecosystem bridges."""
        cls._ensure_builtins_registered()
        report: dict[str, dict[str, Any]] = {}
        for name, bridge_cls in cls._registry.items():
            env_var = getattr(bridge_cls, "env_var", "")
            path = EcosystemLocator.locate(name, env_var=env_var)
            caps = getattr(bridge_cls, "capabilities", [])
            report[name] = {
                "available": path is not None,
                "path": str(path) if path else None,
                "env_var": env_var,
                "service_key": getattr(bridge_cls, "service_key", None),
                "capabilities": [c.value if isinstance(c, BridgeCapability) else str(c) for c in caps],
                "status": "connected" if path is not None else "missing_substrate",
            }
        return report


    @classmethod
    def unregister(cls, project_name: str) -> None:
        """Unregister an ecosystem bridge plugin class."""
        cls._registry.pop(project_name, None)
        if project_name not in ("em-cubed", "Memtext", "Skill Flywheel", "Brain Harness"):
            EcosystemLocator.ENV_VARS.pop(project_name, None)

    @classmethod
    def discover_available_plugins(
        cls,
        override_paths: dict[str, Path | str] | None = None,
        *,
        include_unresolved: bool = True,
    ) -> list[HarnessPlugin]:
        """Instantiate bridge plugins for registered ecosystem repositories."""
        cls._ensure_builtins_registered()
        plugins: list[HarnessPlugin] = []
        overrides = override_paths or {}

        for name, bridge_cls in cls._registry.items():
            if inspect.isabstract(bridge_cls):
                continue
            explicit = overrides.get(name)
            env_var = getattr(bridge_cls, "env_var", "")
            path = EcosystemLocator.locate(name, explicit_path=explicit, env_var=env_var)

            if path is not None or include_unresolved:
                try:
                    plugin_instance = bridge_cls(override_path=path or explicit)
                    plugins.append(plugin_instance)
                except Exception as e:
                    logger.warning(
                        "Failed to instantiate bridge plugin",
                        bridge=name,
                        error=str(e),
                    )

        return plugins


    @classmethod
    def _ensure_builtins_registered(cls) -> None:
        """Lazily ensure standard built-in bridges are imported and registered."""
        if len(cls._registry) >= 3:
            return
        try:
            from harness.bridges.em_cubed import EmCubedPlugin  # noqa: F401
            from harness.bridges.flywheel import FlywheelBridgePlugin  # noqa: F401
            from harness.bridges.memtext import MemtextServicePlugin  # noqa: F401
        except ImportError:
            pass


class EcosystemBridgePlugin(ToolMountMixin, HarnessPlugin, Generic[TSubstrate]):
    """Generic base class for ecosystem integration bridges."""

    project_name: str
    env_var: str
    service_key: ServiceKey[Any]
    capabilities: list[BridgeCapability] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "project_name") and cls.project_name:
            EcosystemBridgeCatalog.register(cls)

    def __init__(self, override_path: Path | str | None = None) -> None:
        self._override_path = Path(override_path) if override_path else None
        self._substrate: TSubstrate | None = None
        self._ctx: ServiceContext | None = None

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [self.service_key]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def health_check(self) -> dict[str, Any]:
        """Perform health and connectivity check of the substrate."""
        root = self.resolve_root()
        sub = await self.get_substrate()
        return {
            "name": self.name,
            "project_name": self.project_name,
            "available": root is not None and root.exists(),
            "substrate_loaded": sub is not None,
            "root_path": str(root) if root else None,
            "capabilities": [c.value if isinstance(c, BridgeCapability) else str(c) for c in self.capabilities],
            "status": "healthy" if (root is not None and sub is not None) else "fallback",
        }

    @property
    def substrate(self) -> TSubstrate | None:
        """The underlying active peer library / engine instance."""
        return self._substrate

    def resolve_root(self) -> Path | None:
        """Resolve the peer repository root path via override or EcosystemLocator."""
        if self._override_path and self._override_path.exists():
            return self._override_path
        return EcosystemLocator.locate(
            self.project_name,
            explicit_path=self._override_path,
            env_var=self.env_var,
        )

    async def get_substrate(self) -> TSubstrate | None:
        """Get or lazily initialize the substrate instance."""
        if self._substrate is not None:
            return self._substrate

        root = self.resolve_root()
        if root:
            try:
                res = self.init_substrate(root)
                if inspect.isawaitable(res):
                    self._substrate = await res
                else:
                    self._substrate = res
            except Exception as e:
                logger.warning(
                    "Substrate initialization encountered warning",
                    bridge=self.name,
                    error=str(e),
                )

        if self._substrate is None:
            try:
                res = self.init_fallback_substrate()
                if inspect.isawaitable(res):
                    self._substrate = await res
                else:
                    self._substrate = res
            except Exception as e:
                logger.warning(
                    "Fallback substrate initialization failed",
                    bridge=self.name,
                    error=str(e),
                )

        return self._substrate

    def provide_instance(self) -> Any:
        """Return the service instance to register into ServiceContext.
        
        Subclasses may override to return self._substrate or self.
        """
        return self

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self.setup_tool_mount(ctx, self.name)
        await self.get_substrate()
        ctx.provide(self.service_key, self.provide_instance(), provider=self.name)
        logger.info("Ecosystem bridge loaded", bridge=self.name)


    async def on_enable(self) -> None:
        await self.get_substrate()
        specs = await self._resolve_tool_specs()
        if specs:
            await self.mount_tools(specs)

        else:
            # Check if subclass provided a 0-arg mount_tools override
            try:
                sig = inspect.signature(self.mount_tools)
                if len(sig.parameters) == 0:
                    res = self.mount_tools()  # type: ignore[call-arg]
                    if inspect.isawaitable(res):
                        await res
            except TypeError:
                pass

        root = self.resolve_root()
        logger.info(
            "Ecosystem bridge enabled",
            bridge=self.name,
            resolved_path=str(root) if root else "fallback",
        )


    async def on_disable(self) -> None:
        await self.unmount_tools()
        logger.info("Ecosystem bridge disabled", bridge=self.name)

    async def on_unload(self) -> None:
        await self.shutdown_substrate()
        self._substrate = None
        self.teardown_tool_mount()
        self._ctx = None
        logger.info("Ecosystem bridge unloaded", bridge=self.name)

    async def init_substrate(self, root_path: Path) -> TSubstrate | None:
        """Subclasses override this to initialize their specific substrate engine."""
        return None

    async def init_fallback_substrate(self) -> TSubstrate | None:
        """Subclasses override this to provide a fallback substrate when peer repo is absent."""
        return None

    async def shutdown_substrate(self) -> None:
        """Subclasses override this to clean up substrate resources on unload."""
        pass

    async def get_tool_specs(self) -> list[ToolSpec]:
        """Subclasses override this to return declarative tool specs to mount."""
        return []

    async def _resolve_tool_specs(self) -> list[ToolSpec]:
        res = self.get_tool_specs()
        if inspect.isawaitable(res):
            return await res  # type: ignore[no-any-return]
        return res  # type: ignore[return-value]

    async def mount_tools(self, specs: list[ToolSpec] | None = None) -> None:
        """Mount tools into the registry."""
        if specs is not None:
            await super().mount_tools(specs)
