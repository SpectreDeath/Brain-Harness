"""Google ADK Web UI Bridge Plugin for Brain Harness."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)


import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

_DEFAULT_ADK_WEB = Path(r"D:\GitHub\cloned\Google\adk-web")


@runtime_checkable
class GoogleAdkWebBridgeService(Protocol):
    """Protocol for Google ADK Web UI bridge and graph export."""

    def web_status(self, project_dir: str = str(_DEFAULT_ADK_WEB), **kwargs: Any) -> dict[str, Any]:
        ...

    def export_graph(
        self,
        nodes: list[dict[str, Any]] | None = None,
        edges: list[dict[str, Any]] | None = None,
        format: str = "a2ui",
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...

    def start_dev_server(self, port: int = 4200, poll_interval: int = 1000, **kwargs: Any) -> dict[str, Any]:
        ...


GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY = ServiceKey[GoogleAdkWebBridgeService]("service.google_adk_web_bridge")


class GoogleAdkWebBridgeServiceImpl:
    """Service implementation for inspecting ADK Web and exporting visual node graphs."""

    def web_status(self, project_dir: str = str(_DEFAULT_ADK_WEB), **kwargs: Any) -> dict[str, Any]:
        if not project_dir and "task" in kwargs:
            project_dir = str(_DEFAULT_ADK_WEB)
        p = Path(project_dir)
        exists = p.exists()
        package_json = p / "package.json"
        angular_json = p / "angular.json"

        deps_count = 0
        scripts = {}
        if package_json.exists():
            try:
                pkg_data = json.loads(package_json.read_text(encoding="utf-8", errors="replace"))
                scripts = pkg_data.get("scripts", {})
                deps_count = len(pkg_data.get("dependencies", {}))
            except Exception as e:
                logger.debug("adk_web_pkg_read_error", error=str(e))

        return {
            "status": "success",
            "path": str(p),
            "exists": exists,
            "has_angular_config": angular_json.exists(),
            "dependencies_count": deps_count,
            "scripts": list(scripts.keys()),
            "framework": "Angular 19 + A2UI Core",
        }

    def export_graph(
        self,
        nodes: list[dict[str, Any]] | None = None,
        edges: list[dict[str, Any]] | None = None,
        format: str = "a2ui",
        **kwargs: Any,
    ) -> dict[str, Any]:
        nodes = nodes or [{"id": "root", "label": "Root Agent"}]
        edges = edges or []

        if format == "mermaid":
            lines = ["graph TD"]
            for n in nodes:
                nid = n.get("id", "node")
                label = n.get("label", nid)
                lines.append(f'    {nid}["{label}"]')
            for e in edges:
                lines.append(f"    {e.get('source')} --> {e.get('target')}")
            graph_output = "\n".join(lines)
        else:
            graph_output = {
                "version": "1.0",
                "kind": "a2ui_graph_view",
                "components": [
                    {
                        "id": n.get("id"),
                        "type": "AgentCard",
                        "properties": {
                            "name": n.get("label", n.get("id")),
                            "role": n.get("type", "worker"),
                            "state": n.get("status", "ready"),
                        }
                    }
                    for n in nodes
                ],
                "connections": edges,
            }

        return {
            "status": "success",
            "format": format,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "graph_data": graph_output,
        }

    def start_dev_server(self, port: int = 4200, poll_interval: int = 1000, **kwargs: Any) -> dict[str, Any]:
        cmd = f"npm run serve -- --port {port} --poll {poll_interval}"
        return {
            "status": "success",
            "command": cmd,
            "port": port,
            "poll_interval": poll_interval,
            "isolation": "subprocess",
            "launch_instructions": "Execute in subprocess sandbox with strict pipe cleanup in finally block (Rule 14).",
        }


_WEB_INSTANCE = GoogleAdkWebBridgeServiceImpl()


# Top-level entrypoints matching plugin.json
def adk_web_status(project_dir: str = str(_DEFAULT_ADK_WEB), **kwargs: Any) -> dict[str, Any]:
    return _WEB_INSTANCE.web_status(project_dir=project_dir, **kwargs)


def adk_web_export_graph(
    nodes: list[dict[str, Any]] | None = None,
    edges: list[dict[str, Any]] | None = None,
    format: str = "a2ui",
    **kwargs: Any,
) -> dict[str, Any]:
    return _WEB_INSTANCE.export_graph(nodes=nodes, edges=edges, format=format, **kwargs)


def adk_web_start_dev_server(port: int = 4200, poll_interval: int = 1000, **kwargs: Any) -> dict[str, Any]:
    return _WEB_INSTANCE.start_dev_server(port=port, poll_interval=poll_interval, **kwargs)


class GoogleAdkWebBridgePlugin(HarnessPlugin):
    """Brain Harness Plugin bridging Google ADK Web UI and telemetry graphs."""

    @property
    def name(self) -> str:
        return "plugin.google_adk_web_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google ADK Web UI bridge: Angular visualization status, execution DAG export (A2UI / ngx-vflow format), and dev server manager."

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY, _WEB_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)
    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()



plugin = GoogleAdkWebBridgePlugin()