"""Authoritative ArchetypeRegistry for plugin scaffolding presets."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from harness.creator.archetypes.agentic_workflow import AgenticWorkflowArchetype
from harness.creator.archetypes.api_wrapper import ApiWrapperArchetype
from harness.creator.archetypes.base import PluginArchetype
from harness.creator.archetypes.container import ContainerArchetype
from harness.creator.archetypes.general import GeneralArchetype, ToolArchetype
from harness.creator.archetypes.mcp_bridge import McpBridgeArchetype
from harness.creator.archetypes.service import ServiceArchetype


class ArchetypeRegistry:
    """Authoritative registry for plugin scaffolding archetypes."""

    _archetypes: dict[str, PluginArchetype] = {}
    _aliases: dict[str, str] = {
        "workflow": "agentic_workflow",
        "agent": "agentic_workflow",
        "agentic": "agentic_workflow",
        "docker": "container",
        "containerized": "container",
        "api": "api_wrapper",
    }

    @classmethod
    @contextmanager
    def snapshot(cls) -> Iterator[None]:
        """Context manager preserving registry state for test isolation."""
        saved = dict(cls._archetypes)
        try:
            yield
        finally:
            cls._archetypes = saved

    @classmethod
    def register(cls, archetype: PluginArchetype | type[PluginArchetype]) -> None:
        """Register a new plugin archetype strategy."""
        instance = archetype() if isinstance(archetype, type) else archetype
        cls._archetypes[instance.name.lower()] = instance

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister an archetype preset by name. Returns True if removed."""
        clean_name = (name or "").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        if resolved in cls._archetypes:
            del cls._archetypes[resolved]
            return True
        return False

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if an archetype preset is registered."""
        clean_name = (name or "").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        return resolved in cls._archetypes

    @classmethod
    def get(cls, name: str) -> PluginArchetype:
        """Retrieve an archetype by preset name, falling back to GeneralArchetype."""
        clean_name = (name or "general").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        return cls._archetypes.get(resolved, cls._archetypes.get("general", GeneralArchetype()))

    @classmethod
    def list_archetypes(cls) -> list[dict[str, str]]:
        """List all registered archetypes and their descriptions."""
        return [
            {"name": arch.name, "description": arch.description}
            for arch in cls._archetypes.values()
        ]

    @classmethod
    def reset(cls) -> None:
        """Reset the registry to built-in default archetypes."""
        cls._archetypes.clear()
        cls.register(GeneralArchetype())
        cls.register(ToolArchetype())
        cls.register(ApiWrapperArchetype())
        cls.register(ServiceArchetype())
        cls.register(McpBridgeArchetype())
        cls.register(AgenticWorkflowArchetype())
        cls.register(ContainerArchetype())


# Initialize built-in archetypes
ArchetypeRegistry.reset()

__all__ = [
    "ArchetypeRegistry",
]
