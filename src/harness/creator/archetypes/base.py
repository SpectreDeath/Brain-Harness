"""Abstract PluginArchetype strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from harness.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldOptions


class PluginArchetype(ABC):
    """Abstract strategy for generating plugin manifests, source code, and tests."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique archetype preset identifier (e.g., 'general', 'tool', 'api_wrapper')."""

    @property
    def description(self) -> str:
        """Human-readable archetype description."""
        return f"Archetype preset for {self.name}"

    @abstractmethod
    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        """Generate a validated PluginManifest."""

    @abstractmethod
    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        """Generate entrypoint source code."""

    @abstractmethod
    def generate_test_code(self, options: ScaffoldOptions) -> str:
        """Generate unit test code."""

    @abstractmethod
    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        """Generate package/requirements configuration (filename, content)."""

    def generate_extra_files(self, options: ScaffoldOptions) -> dict[str, str]:
        """Generate optional auxiliary files (relative_path -> file_content)."""
        return {}


__all__ = [
    "PluginArchetype",
]
