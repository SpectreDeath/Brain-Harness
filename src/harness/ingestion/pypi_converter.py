"""PyPI package to Harness Plugin Converter.

Fetches metadata from the PyPI JSON API and synthesizes an isolated Venv-sandboxed
harness plugin with package dependencies and auto-generated entrypoint wrappers.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any

import httpx
import structlog

from harness.plugins.manifest import EntrypointSpec, IsolationMode, ParameterSpec, PluginManifest

logger = structlog.get_logger()


class PyPIConverter:
    """Converts PyPI packages into isolated, dependency-managed harness plugins."""

    def __init__(self, output_base_dir: Path | None = None) -> None:
        self.output_base_dir = output_base_dir or (Path.home() / ".harness" / "plugins")

    def _sanitize_name(self, name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower().strip())
        if not clean or clean[0].isdigit():
            clean = f"pkg_{clean}"
        return clean

    async def fetch_metadata(self, package_name: str) -> dict[str, Any]:
        """Fetch package metadata from PyPI JSON API."""
        clean_name = package_name.replace("pypi:", "").strip()
        url = f"https://pypi.org/pypi/{clean_name}/json"

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning("Could not fetch PyPI API metadata", package=clean_name, error=str(e))

        # Fallback offline metadata
        return {
            "info": {
                "name": clean_name,
                "version": "1.0.0",
                "summary": f"PyPI package plugin for {clean_name}",
                "author": "PyPI Package Author",
                "requires_dist": [],
            }
        }

    async def convert(
        self,
        package_spec: str,
        output_dir: Path | None = None,
    ) -> Path:
        """Convert PyPI package into a sandboxed Harness plugin.

        Args:
            package_spec: Package name or 'pypi:package_name'.
            output_dir: Directory where the plugin will be stored.

        Returns:
            Path to the synthesized plugin directory.
        """
        raw_name = package_spec.replace("pypi:", "").strip()
        meta = await self.fetch_metadata(raw_name)
        info = meta.get("info", {})

        pkg_name = info.get("name", raw_name)
        safe_name = self._sanitize_name(pkg_name)
        version = info.get("version", "1.0.0")
        summary = info.get("summary") or f"Automated Harness wrapper for PyPI package {pkg_name}"
        author = info.get("author", "PyPI")

        target_dir = output_dir or (self.output_base_dir / safe_name)
        target_dir.mkdir(parents=True, exist_ok=True)

        entrypoints = [
            EntrypointSpec(
                name="run_package_action",
                description=f"Execute an action or import using {pkg_name}",
                parameters=[
                    ParameterSpec(name="action", type="string", description="Action to perform", required=True),
                    ParameterSpec(name="params", type="object", description="Parameters dictionary", required=False),
                ],
                returns="dict",
            ),
            EntrypointSpec(
                name="inspect_module",
                description=f"Inspect exported attributes and functions of {pkg_name}",
                parameters=[],
                returns="dict",
            ),
        ]

        manifest = PluginManifest(
            name=safe_name,
            version=version,
            description=summary,
            author=author,
            language="python",
            entrypoint="main.py",
            provides=[f"tool.{safe_name}"],
            isolation=IsolationMode.VENV,
            category="pypi_package",
            entrypoints=entrypoints,
            dependencies=[pkg_name],
        )

        main_py_code = textwrap.dedent(f"""\
            \"\"\"PyPI plugin wrapper for {pkg_name}.\"\"\"
            from __future__ import annotations
            from typing import Any

            def run_package_action(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
                \"\"\"Execute an action using {pkg_name}.\"\"\"
                try:
                    import importlib
                    mod = importlib.import_module({pkg_name!r})
                    func = getattr(mod, action, None)
                    if callable(func):
                        result = func(**(params or {{}}))
                    else:
                        result = str(func) if func is not None else f"Module {pkg_name} loaded successfully"
                    return {{"status": "ok", "package": {pkg_name!r}, "action": action, "result": result}}
                except Exception as e:
                    return {{"status": "error", "package": {pkg_name!r}, "error": str(e)}}

            def inspect_module() -> dict[str, Any]:
                \"\"\"Inspect exported members of {pkg_name}.\"\"\"
                try:
                    import importlib
                    mod = importlib.import_module({pkg_name!r})
                    attrs = [a for a in dir(mod) if not a.startswith('_')]
                    return {{"status": "ok", "package": {pkg_name!r}, "version": getattr(mod, '__version__', 'unknown'), "exports": attrs[:30]}}
                except Exception as e:
                    return {{"status": "error", "package": {pkg_name!r}, "error": str(e)}}
        """)

        (target_dir / "plugin.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "main.py").write_text(main_py_code, encoding="utf-8")
        (target_dir / "QUICKSTART.md").write_text(manifest.format_quickstart(), encoding="utf-8")

        logger.info(
            "Synthesized PyPI plugin",
            package=pkg_name,
            target_dir=str(target_dir),
        )
        return target_dir
