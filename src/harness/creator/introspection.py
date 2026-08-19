"""Runtime Introspector — live system diagnostics, dependency graphing, and sandbox monitoring.

Provides authoritative runtime inspection capabilities for running Harness systems:
    - Service and plugin state reporting
    - Bi-directional dependency graph rendering (Mermaid syntax)
    - Sandbox process and isolation tracking
    - Plugin catalog correlation and documentation cards
"""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.tools import ToolRegistry

logger = structlog.get_logger()


class RuntimeIntrospector:
    """Provides live diagnostic introspection of a running Harness system."""

    def __init__(
        self,
        context: ServiceContext,
        lifecycle: PluginLifecycle,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.context = context
        self.lifecycle = lifecycle
        self.tool_registry = tool_registry

    def get_status_report(self) -> dict[str, Any]:
        """Generate a complete diagnostic snapshot."""
        services = self.context.list_services()
        plugins = self.lifecycle.summary()
        tools = self.tool_registry.list_tools() if self.tool_registry else []

        tools_by_provider: dict[str, list[str]] = {}
        for t in tools:
            prov = t.provider or "core"
            tools_by_provider.setdefault(prov, []).append(t.name)

        return {
            "plugins_count": len(plugins),
            "plugins": plugins,
            "services_count": len(services),
            "services": services,
            "tools_count": len(tools),
            "tools": [t.name for t in tools],
            "tools_by_provider": tools_by_provider,
        }

    def generate_mermaid_graph(self, include_tools: bool = False) -> str:
        """Generate a Mermaid diagram representing the active bi-directional dependency graph.

        Args:
            include_tools: If True, renders individual tool nodes attached to provider plugins.
        """
        lines = ["graph TD"]
        rendered_services: set[str] = set()
        rendered_edges: set[str] = set()

        # Nodes for plugins
        for p_name, state in self.lifecycle.summary().items():
            safe_p = p_name.replace(".", "_").replace("-", "_")
            lines.append(f'  P_{safe_p}["Plugin: {p_name} ({state})"]')

        # Register active services from context
        for s_name, provider in self.context.list_services().items():
            safe_s = s_name.replace(".", "_").replace("-", "_")
            rendered_services.add(s_name)
            lines.append(f'  S_{safe_s}["Service: {s_name}"]')
            if provider:
                safe_provider = provider.replace(".", "_").replace("-", "_")
                edge = f"P_{safe_provider} -->|provides| S_{safe_s}"
                if edge not in rendered_edges:
                    rendered_edges.add(edge)
                    lines.append(f"  {edge}")

        # Add provides and requires from plugin instances
        for p_name, entry in self.lifecycle.plugins.items():
            safe_p = p_name.replace(".", "_").replace("-", "_")

            # Declared provides
            for prov_key in getattr(entry.plugin, "provides", []):
                prov_name = prov_key.name if hasattr(prov_key, "name") else str(prov_key)
                safe_prov = prov_name.replace(".", "_").replace("-", "_")
                if prov_name not in rendered_services:
                    rendered_services.add(prov_name)
                    lines.append(f'  S_{safe_prov}["Service: {prov_name}"]')
                edge = f"P_{safe_p} -->|provides| S_{safe_prov}"
                if edge not in rendered_edges:
                    rendered_edges.add(edge)
                    lines.append(f"  {edge}")

            # Declared requires
            for req_key in getattr(entry.plugin, "requires", []):
                req_name = req_key.name if hasattr(req_key, "name") else str(req_key)
                safe_req = req_name.replace(".", "_").replace("-", "_")
                if req_name not in rendered_services:
                    rendered_services.add(req_name)
                    lines.append(f'  S_{safe_req}["Service: {req_name} (MISSING)"]')
                edge = f"P_{safe_p} -.->|requires| S_{safe_req}"
                if edge not in rendered_edges:
                    rendered_edges.add(edge)
                    lines.append(f"  {edge}")

        # Optional tool nodes
        if include_tools and self.tool_registry:
            for tool in self.tool_registry.list_tools():
                safe_t = tool.name.replace(".", "_").replace("-", "_")
                st = "✓" if tool.enabled else "✗"
                lines.append(f'  T_{safe_t}["Tool: {tool.name} [{st}]"]')
                if tool.provider:
                    safe_prov = tool.provider.replace(".", "_").replace("-", "_")
                    t_edge = f"P_{safe_prov} -.->|exposes| T_{safe_t}"
                    if t_edge not in rendered_edges:
                        rendered_edges.add(t_edge)
                        lines.append(f"  {t_edge}")

        return "\n".join(lines)

    def get_sandboxes_report(self) -> list[dict[str, Any]]:
        """Inspect and return runtime sandbox state for all registered plugins."""
        sandboxes: list[dict[str, Any]] = []
        for name, entry in self.lifecycle.plugins.items():
            plugin = entry.plugin
            is_sandboxed = hasattr(plugin, "sandbox") or "Sandboxed" in plugin.__class__.__name__
            executor = getattr(plugin, "_executor", None) or getattr(plugin, "sandbox", None)

            executor_name = "in_process"
            is_running = False
            pid = None

            if executor is not None:
                executor_name = getattr(executor, "name", executor.__class__.__name__)
                is_running = getattr(executor, "is_running", False)
                transport = getattr(executor, "_transport", None)
                if transport is not None:
                    pid = getattr(transport, "pid", None)

            sandboxes.append({
                "plugin": name,
                "state": entry.state.value,
                "is_sandboxed": is_sandboxed,
                "executor": executor_name,
                "is_running": is_running,
                "pid": pid,
                "trusted": getattr(plugin, "trusted", False),
            })
        return sandboxes

    def get_catalog_report(self, loader: Any | None = None) -> list[dict[str, Any]]:
        """Return enriched plugin catalog correlated with active lifecycle states."""
        if loader is None:
            from harness.commands.plugins import list_plugins

            catalog = list_plugins()
        else:
            catalog = loader.list_catalog()

        active_summary = self.lifecycle.summary()
        enriched = []
        for item in catalog:
            p_name = item.get("name", "")
            state = active_summary.get(p_name, "unloaded")
            enriched.append({
                **item,
                "state": state,
            })
        return enriched

    def get_plugin_guide_report(self, name: str, loader: Any | None = None) -> dict[str, Any]:
        """Return structured guide and card documentation for a plugin."""
        guide_res = None
        if loader is not None:
            guide_res = loader.get_guide(name)
        else:
            from harness.commands.plugins import get_plugin_guide

            guide_res = get_plugin_guide(name)

        if guide_res:
            manifest, guide = guide_res
            return {
                "status": "ok",
                "name": manifest.name,
                "version": manifest.version,
                "category": manifest.category,
                "description": manifest.description,
                "card": manifest.format_card(),
                "guide": guide,
                "entrypoints": [
                    {
                        "name": ep.name,
                        "description": ep.description,
                        "parameters": [p.model_dump() for p in ep.parameters],
                    }
                    for ep in manifest.entrypoints
                ],
            }

        # Fallback: check if tracked in lifecycle
        entry = self.lifecycle.plugins.get(name)
        if entry:
            manifest = getattr(entry.plugin, "manifest", None)
            if manifest:
                return {
                    "status": "ok",
                    "name": manifest.name,
                    "version": manifest.version,
                    "category": manifest.category,
                    "description": manifest.description,
                    "card": manifest.format_card(),
                    "guide": manifest.format_quickstart(),
                    "entrypoints": [
                        {"name": ep.name, "description": ep.description}
                        for ep in manifest.entrypoints
                    ],
                }
            desc = getattr(entry.plugin, "description", f"Plugin {name}")
            return {
                "status": "ok",
                "name": name,
                "version": getattr(entry.plugin, "version", "0.1.0"),
                "category": "core",
                "description": desc,
                "card": f"Plugin: {name}\nStatus: {entry.state.value}\nDescription: {desc}",
                "guide": f"# {name}\n\n{desc}\n\n## State\nCurrently **{entry.state.value}**.",
                "entrypoints": [],
            }
        return {"status": "error", "error": f"Plugin '{name}' not found"}
