"""Plugin manifest schema — parsed from plugin.json or synthesized by inspection.

The manifest describes a plugin's identity, capabilities, dependencies,
and execution requirements. It can come from:
    1. An explicit ``plugin.json`` in the plugin directory
    2. Convention-based discovery (``mcp.json``, ``package.json``, etc.)
    3. Automatic synthesis by the RepoInspector
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class IsolationMode(str, Enum):
    """How the plugin should be executed relative to the harness process."""

    IN_PROCESS = "in_process"
    """Direct Python import — trusted plugins only."""

    SUBPROCESS = "subprocess"
    """JSON-RPC over stdin/stdout in a child process."""

    VENV = "venv"
    """Isolated virtualenv + subprocess execution."""

    DOCKER = "docker"
    """Docker container isolation (requires Docker)."""


class ParameterSpec(BaseModel):
    """A single parameter in a tool or function schema."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None


class EntrypointSpec(BaseModel):
    """Describes a callable entrypoint the plugin exposes."""

    name: str
    """Function or method name."""

    description: str = ""
    """What this entrypoint does."""

    parameters: list[ParameterSpec] = Field(default_factory=list)
    """Input parameters."""

    returns: str = "any"
    """Return type description."""


class ContainerConfig(BaseModel):
    """Configuration for container-isolated plugin execution."""

    image: str = "python:3.11-slim"
    """Docker / container image tag."""

    memory_limit: str = "256m"
    """Memory resource cap (e.g. 256m, 1g)."""

    cpu_limit: float = 1.0
    """CPU limit in cores."""

    network: str = "none"
    """Container network mode (none, bridge, host). Default is air-gapped none."""

    read_only_root: bool = True
    """Whether to enforce a read-only root filesystem."""

    environment: dict[str, str] = Field(default_factory=dict)
    """Environment variables passed into container."""


class PluginManifest(BaseModel):
    """Complete manifest describing a harness plugin.

    This is the canonical metadata format. It can be:
    - Read from a ``plugin.json`` file
    - Synthesized by the RepoInspector from other conventions
    - Written by the user manually

    Example ``plugin.json``::

        {
            "name": "my-tool",
            "version": "1.0.0",
            "description": "A tool that does things",
            "language": "python",
            "entrypoint": "main.py",
            "provides": ["tool.my-tool"],
            "requires": ["llm.provider"],
            "isolation": "subprocess",
            "entrypoints": [
                {
                    "name": "run",
                    "description": "Execute the tool",
                    "parameters": [
                        {"name": "input", "type": "string", "required": true}
                    ]
                }
            ]
        }
    """

    name: str
    """Unique plugin name."""

    version: str = "0.0.0"
    """Plugin version (semver)."""

    description: str = ""
    """Human-readable description."""

    language: str = "python"
    """Primary implementation language."""

    entrypoint: str = ""
    """Path to the main module or script, relative to plugin root."""

    provides: list[str] = Field(default_factory=list)
    """Service key names this plugin provides."""

    requires: list[str] = Field(default_factory=list)
    """Service key names this plugin depends on."""

    isolation: IsolationMode = IsolationMode.SUBPROCESS
    """Default isolation mode for this plugin."""

    trusted: bool = False
    """Whether the plugin is trusted to run in-process."""

    author: str = ""
    """Plugin author or organization."""

    category: str = "general"
    """Domain category (e.g., engineering, bridge, core, developer_tools)."""

    tags: list[str] = Field(default_factory=list)
    """Searchable classification tags."""

    usage_guide: str = ""
    """Quick start and agent usage guide in markdown."""

    entrypoints: list[EntrypointSpec] = Field(default_factory=list)
    """Callable entrypoints the plugin exposes."""

    dependencies: list[str] = Field(default_factory=list)
    """Package dependencies (pip-installable)."""

    container: ContainerConfig | None = None
    """Optional container execution configuration for Docker isolation."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    """Arbitrary key-value metadata."""

    source_url: str | None = None
    """URL the plugin was fetched from (for GitHub-sourced plugins)."""

    source_commit: str | None = None
    """Git commit SHA the plugin was fetched at."""

    def format_card(self, width: int = 50) -> str:
        """Generate a standardized ASCII Plugin Summary Card."""
        sep = "=" * width
        lines = [
            sep,
            "PLUGIN SUMMARY CARD".center(width).rstrip(),
            sep,
            f"Plugin Name:        {self.name}",
            f"Version:            {self.version}",
            f"Category:           {self.category}",
        ]
        if self.author:
            lines.append(f"Author:             {self.author}")
        if self.description:
            lines.append(f"Description:        {self.description}")
        lines.extend([
            f"Language:           {self.language}",
            f"Isolation Mode:     {self.isolation.value}",
            f"Entrypoint Script:  {self.entrypoint or '(auto-detect)'}",
            f"Total Skills/Tools: {len(self.entrypoints)}",
        ])
        if self.provides:
            lines.append(f"Provides:           {', '.join(self.provides)}")
        if self.requires:
            lines.append(f"Requires:           {', '.join(self.requires)}")
        if self.tags:
            lines.append(f"Tags:               {', '.join(self.tags)}")
        lines.append(sep)
        return "\n".join(lines)

    def format_quickstart(self) -> str:
        """Generate a structured Markdown Quick Start Guide for users and agents."""
        if self.usage_guide.strip():
            return self.usage_guide.strip()

        lines = [
            f"# Quick Start Guide: `{self.name}` (v{self.version})",
            "",
            f"> {self.description}" if self.description else "",
            "",
            "## 🎯 When to Use",
            f"Use this plugin when you need capabilities related to `{self.category}`.",
        ]
        if self.entrypoints:
            lines.append("\nCommon trigger intents:")
            for ep in self.entrypoints[:8]:
                desc = f": {ep.description}" if ep.description else ""
                lines.append(f"- **`{ep.name}`**{desc}")
        lines.extend([
            "",
            "## 🛠️ How to Use (Agent & User)",
            "### Python / Runtime Tool Call:",
            "```python",
        ])
        if self.entrypoints:
            sample_ep = self.entrypoints[0]
            param_dict = {p.name: f"<{p.name}>" for p in sample_ep.parameters}
            lines.append(f"result = await runtime.tools.invoke('{self.name}.{sample_ep.name}', {param_dict})")
        else:
            lines.append(f"# Load plugin into runtime\nawait runtime.lifecycle.enable('{self.name}')")
        lines.extend([
            "```",
            "",
            "### CLI Quick Action:",
            "```powershell",
            f"harness tool list --provider {self.name}",
            f"harness plugin enable {self.name}",
            "```",
            "",
            "## ⚡ Available Entrypoints & Skills",
        ])
        for ep in self.entrypoints:
            params_str = ", ".join(f"{p.name}: {p.type}" for p in ep.parameters)
            lines.append(f"- **`{ep.name}({params_str})`**")
            if ep.description:
                lines.append(f"  {ep.description}")
        return "\n".join(lines)

    @classmethod
    def from_file(cls, path: Path) -> PluginManifest:
        """Load a manifest from a JSON file.

        Args:
            path: Path to the manifest file (e.g., ``plugin.json``).

        Returns:
            Parsed PluginManifest.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def to_file(self, path: Path) -> None:
        """Write the manifest to a JSON file.

        Args:
            path: Destination file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_package_json(cls, path: Path) -> PluginManifest:
        """Synthesize a manifest from a Node.js package.json.

        Args:
            path: Path to ``package.json``.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            name=data.get("name", path.parent.name),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            language="javascript",
            entrypoint=data.get("main", "index.js"),
            isolation=IsolationMode.SUBPROCESS,
            metadata={"source_format": "package.json"},
        )

    @classmethod
    def from_pyproject(cls, path: Path) -> PluginManifest:
        """Synthesize a manifest from a Python pyproject.toml.

        Args:
            path: Path to ``pyproject.toml``.
        """
        try:
            import tomllib  # type: ignore[import-not-found]
        except ImportError:
            import tomli as tomllib  # type: ignore[import-not-found,no-redef]

        with open(path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        deps = project.get("dependencies", [])

        return cls(
            name=project.get("name", path.parent.name),
            version=project.get("version", "0.0.0"),
            description=project.get("description", ""),
            language="python",
            dependencies=deps,
            isolation=IsolationMode.VENV,
            metadata={"source_format": "pyproject.toml"},
        )

    @classmethod
    def minimal(cls, name: str, entrypoint: str = "") -> PluginManifest:
        """Create a minimal manifest for quick plugin registration."""
        return cls(name=name, entrypoint=entrypoint)
