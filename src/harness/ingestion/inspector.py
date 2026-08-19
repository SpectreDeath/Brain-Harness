"""Repo inspector — analyzes downloaded repositories and synthesizes manifests.

The inspector examines a repository to determine:
    1. What it provides (functions, tools, services)
    2. What it depends on (packages, runtimes)
    3. How it should be executed (language, entrypoint)
    4. What isolation it needs (subprocess, venv, docker)

Discovery strategies (in priority order):
    1. Explicit ``plugin.json`` → use as-is
    2. Claude/Agent skills bundle
    3. ``mcp.json`` / ``tool.json`` → convert to PluginManifest
    4. ``pyproject.toml`` / ``setup.py`` → extract Python project metadata
    5. ``package.json`` → extract Node.js project metadata
    6. AST-based extraction → parse Python files for callable functions
"""

from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path

import structlog

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

logger = structlog.get_logger()


class InspectionError(Exception):
    """Raised when repository inspection fails."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Inspection failed for {path}: {reason}")


class RepoInspector:
    """Inspects repository directories and synthesizes PluginManifests."""

    def inspect(self, repo_dir: Path) -> PluginManifest:
        """Inspect a repository directory and return a synthesized PluginManifest.

        Tries discovery strategies in priority order until one succeeds.
        """
        if not repo_dir.exists() or not repo_dir.is_dir():
            raise InspectionError(str(repo_dir), "Directory does not exist")

        manifest: PluginManifest | None = None

        # Strategy 1: Explicit Harness plugin.json
        manifest = self._try_plugin_json(repo_dir)
        if manifest:
            logger.info("Found plugin.json manifest", plugin=manifest.name)

        # Strategy 2: Claude plugin / Agent skills bundle (.claude-plugin/plugin.json or skills/**/SKILL.md)
        if manifest is None:
            manifest = self._try_skills_bundle(repo_dir)
            if manifest:
                logger.info("Synthesized manifest from skills bundle", plugin=manifest.name, skills=len(manifest.entrypoints))

        # Strategy 3: MCP / tool.json
        if manifest is None:
            manifest = self._try_mcp_json(repo_dir)
            if manifest:
                logger.info("Found mcp.json manifest", plugin=manifest.name)

        # Strategy 4: pyproject.toml
        if manifest is None:
            manifest = self._try_pyproject(repo_dir)
            if manifest:
                logger.info("Synthesized manifest from pyproject.toml", plugin=manifest.name)

        # Strategy 5: package.json
        if manifest is None:
            manifest = self._try_package_json(repo_dir)
            if manifest:
                logger.info("Synthesized manifest from package.json", plugin=manifest.name)

        # Strategy 6: requirements.txt + AST extraction
        if manifest is None:
            manifest = self._try_python_ast(repo_dir)
            if manifest:
                logger.info("Synthesized manifest via AST extraction", plugin=manifest.name)

        # Fallback: create a minimal manifest from the directory name
        if manifest is None:
            logger.warning(
                "No metadata found, creating minimal manifest",
                directory=str(repo_dir),
            )
            manifest = PluginManifest.minimal(
                name=repo_dir.name,
                entrypoint=self._guess_entrypoint(repo_dir),
            )

        # Post-Inspection Standardization: Quick Start Guide & Metadata
        quickstart_path = repo_dir / "QUICKSTART.md"
        if quickstart_path.exists() and not manifest.usage_guide:
            try:
                manifest.usage_guide = quickstart_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        if not manifest.usage_guide:
            manifest.usage_guide = manifest.format_quickstart()

        if not quickstart_path.exists():
            try:
                quickstart_path.write_text(manifest.usage_guide, encoding="utf-8")
            except Exception as e:
                logger.warning("Could not write QUICKSTART.md", error=str(e))

        return manifest

    # --- Discovery strategies ---

    def _try_plugin_json(self, repo_dir: Path) -> PluginManifest | None:
        """Check for an explicit plugin.json."""
        path = repo_dir / "plugin.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                # If this is a Claude plugin format with "skills" key, let skills_bundle handle it
                if "skills" in data and "entrypoints" not in data and "provides" not in data:
                    return None
                return PluginManifest.from_file(path)
            except Exception as e:
                logger.warning("Invalid plugin.json", error=str(e))
        return None

    def _try_skills_bundle(self, repo_dir: Path) -> PluginManifest | None:
        """Check for a Claude plugin or Agent skills bundle repository."""
        claude_plugin = repo_dir / ".claude-plugin" / "plugin.json"
        agents_plugin = repo_dir / ".agents" / "plugin.json"
        root_plugin = repo_dir / "plugin.json"
        skills_dir = repo_dir / "skills"

        has_skills = skills_dir.exists() and any(skills_dir.rglob("SKILL.md"))
        has_plugin_spec = claude_plugin.exists() or agents_plugin.exists() or (
            root_plugin.exists() and "skills" in root_plugin.read_text(encoding="utf-8", errors="ignore")
        )

        if not (has_plugin_spec or has_skills):
            return None

        # Extract package info
        data = {}
        for target_json in (claude_plugin, agents_plugin, root_plugin):
            if target_json.exists():
                try:
                    data = json.loads(target_json.read_text(encoding="utf-8", errors="ignore"))
                    if "name" in data:
                        break
                except Exception:
                    pass

        name = data.get("name", repo_dir.name)
        version = data.get("version", "1.0.0")
        description = data.get("description", f"Agent skills plugin bundle from {name}")

        # Scan for SKILL.md files
        entrypoints: list[EntrypointSpec] = []
        skill_files = sorted(repo_dir.rglob("SKILL.md"))

        for sfile in skill_files:
            try:
                raw = sfile.read_text(encoding="utf-8", errors="ignore")
                sname, sdesc = self._parse_skill_frontmatter(raw)
                if not sname:
                    sname = sfile.parent.name
                if not sdesc:
                    sdesc = f"Execute {sname} skill"

                entrypoints.append(
                    EntrypointSpec(
                        name=sname,
                        description=sdesc[:300],
                        parameters=[
                            ParameterSpec(
                                name="task",
                                type="string",
                                description=f"Task description or input context for {sname}",
                                required=False,
                            ),
                            ParameterSpec(
                                name="context",
                                type="string",
                                description="Additional project context or file contents",
                                required=False,
                            ),
                        ],
                    )
                )
            except Exception:
                continue

        if not entrypoints:
            return None

        # Write runner entrypoint script
        entrypoint_file = repo_dir / "skills_entrypoint.py"
        entrypoint_code = textwrap.dedent('''\
            """Auto-generated entrypoint runner for Agent Skills Bundle."""
            from __future__ import annotations

            from pathlib import Path
            from typing import Any

            ROOT = Path(__file__).parent

            def _get_skill(skill_name: str, task: str = "", context: str = "", **kwargs: Any) -> dict[str, Any]:
                clean_name = skill_name.replace("_", "-")
                for p in ROOT.glob(f"skills/**/{clean_name}/SKILL.md"):
                    if p.exists():
                        return {
                            "status": "ok",
                            "skill": clean_name,
                            "instructions": p.read_text(encoding="utf-8", errors="ignore"),
                            "task": task,
                            "context": context,
                        }
                for p in ROOT.glob("skills/**/SKILL.md"):
                    try:
                        txt = p.read_text(encoding="utf-8", errors="ignore")
                        if f"name: {clean_name}" in txt:
                            return {
                                "status": "ok",
                                "skill": clean_name,
                                "instructions": txt,
                                "task": task,
                                "context": context,
                            }
                    except Exception:
                        continue
                return {"status": "error", "error": f"Skill '{clean_name}' not found in bundle."}

            def __getattr__(name: str) -> Any:
                def _skill_caller(task: str = "", context: str = "", **kwargs: Any) -> dict[str, Any]:
                    return _get_skill(name, task=task, context=context, **kwargs)
                return _skill_caller
        ''')
        try:
            entrypoint_file.write_text(entrypoint_code, encoding="utf-8")
        except Exception as e:
            logger.warning("Could not write skills_entrypoint.py", error=str(e))

        return PluginManifest(
            name=name,
            version=version,
            description=description,
            language="python",
            entrypoint="skills_entrypoint.py",
            entrypoints=entrypoints,
            isolation=IsolationMode.SUBPROCESS,
            metadata={"source_format": "agent_skills_bundle", "skills_count": len(entrypoints)},
        )

    def _parse_skill_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract name and description from YAML frontmatter in SKILL.md."""
        name = ""
        desc = ""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].splitlines():
                    line_s = line.strip()
                    if line_s.startswith("name:"):
                        name = line_s[5:].strip().strip("\"'")
                    elif line_s.startswith("description:"):
                        desc = line_s[12:].strip().strip("\"'")
        return name, desc

    def _try_mcp_json(self, repo_dir: Path) -> PluginManifest | None:
        """Check for mcp.json or tool.json."""
        for filename in ("mcp.json", "tool.json"):
            path = repo_dir / filename
            if path.exists():
                try:
                    return self._convert_mcp_json(path, repo_dir)
                except Exception as e:
                    logger.warning(f"Invalid {filename}", error=str(e))
        return None

    def _convert_mcp_json(self, path: Path, repo_dir: Path) -> PluginManifest:
        """Convert an MCP/tool JSON spec to a PluginManifest."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Extract tools as entrypoints
        entrypoints: list[EntrypointSpec] = []
        tools = data.get("tools", [])
        for tool in tools:
            params: list[ParameterSpec] = []
            schema = tool.get("inputSchema", {}).get("properties", {})
            required = tool.get("inputSchema", {}).get("required", [])
            for pname, pspec in schema.items():
                params.append(
                    ParameterSpec(
                        name=pname,
                        type=pspec.get("type", "string"),
                        description=pspec.get("description", ""),
                        required=pname in required,
                    )
                )
            entrypoints.append(
                EntrypointSpec(
                    name=tool.get("name", "unknown"),
                    description=tool.get("description", ""),
                    parameters=params,
                )
            )

        return PluginManifest(
            name=data.get("name", repo_dir.name),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            entrypoints=entrypoints,
            isolation=IsolationMode.SUBPROCESS,
            metadata={"source_format": path.name},
        )

    def _try_pyproject(self, repo_dir: Path) -> PluginManifest | None:
        """Check for pyproject.toml."""
        path = repo_dir / "pyproject.toml"
        if path.exists():
            try:
                manifest = PluginManifest.from_pyproject(path)
                # Enrich with AST-extracted entrypoints
                entrypoints = self._extract_python_entrypoints(repo_dir)
                if entrypoints:
                    manifest = manifest.model_copy(
                        update={"entrypoints": entrypoints}
                    )
                # Find the actual entrypoint
                ep = self._guess_entrypoint(repo_dir)
                if ep:
                    manifest = manifest.model_copy(update={"entrypoint": ep})
                return manifest
            except Exception as e:
                logger.warning("Invalid pyproject.toml", error=str(e))
        return None

    def _try_package_json(self, repo_dir: Path) -> PluginManifest | None:
        """Check for package.json."""
        path = repo_dir / "package.json"
        if path.exists():
            try:
                return PluginManifest.from_package_json(path)
            except Exception as e:
                logger.warning("Invalid package.json", error=str(e))
        return None

    def _try_python_ast(self, repo_dir: Path) -> PluginManifest | None:
        """Fall back to AST parsing of Python files."""
        entrypoints = self._extract_python_entrypoints(repo_dir)
        if not entrypoints:
            return None

        # Look for dependencies
        deps = self._read_requirements(repo_dir)
        ep = self._guess_entrypoint(repo_dir)

        return PluginManifest(
            name=repo_dir.name,
            version="0.0.0",
            description=f"Auto-discovered plugin from {repo_dir.name}",
            language="python",
            entrypoint=ep,
            entrypoints=entrypoints,
            dependencies=deps,
            isolation=IsolationMode.VENV if deps else IsolationMode.SUBPROCESS,
            metadata={"source_format": "ast_extraction"},
        )

    # --- Helpers ---

    def _extract_python_entrypoints(self, repo_dir: Path) -> list[EntrypointSpec]:
        """Parse Python files via AST to find public callable functions."""
        entrypoints: list[EntrypointSpec] = []

        py_files = list(repo_dir.glob("*.py"))
        # Also check src/ directory
        src_dir = repo_dir / "src"
        if src_dir.exists():
            py_files.extend(src_dir.rglob("*.py"))

        for py_file in py_files[:20]:  # Limit to prevent huge repos from blocking
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private functions
                        if node.name.startswith("_"):
                            continue

                        params = self._extract_function_params(node)
                        docstring = ast.get_docstring(node) or ""

                        entrypoints.append(
                            EntrypointSpec(
                                name=node.name,
                                description=docstring[:200],
                                parameters=params,
                            )
                        )
            except (SyntaxError, UnicodeDecodeError):
                continue

        return entrypoints

    def _extract_function_params(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterSpec]:
        """Extract parameter specs from a function's AST node."""
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "dict": "object",
            "list": "array",
            "Any": "any",
            "None": "null",
        }

        params: list[ParameterSpec] = []
        args = func_node.args

        # Count defaults to determine which args have defaults
        num_defaults = len(args.defaults)
        num_args = len(args.args)

        for i, arg in enumerate(args.args):
            if arg.arg == "self":
                continue

            # Determine type from annotation
            param_type = "any"
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = type_map.get(arg.annotation.id, arg.annotation.id)
                elif isinstance(arg.annotation, ast.Constant):
                    val_str = str(arg.annotation.value)
                    param_type = type_map.get(val_str, val_str)
                elif isinstance(arg.annotation, ast.Subscript):
                    if isinstance(arg.annotation.value, ast.Name):
                        container = arg.annotation.value.id
                        param_type = type_map.get(container, container)

            # Determine if required (no default)
            has_default = i >= (num_args - num_defaults)

            params.append(
                ParameterSpec(
                    name=arg.arg,
                    type=param_type,
                    required=not has_default,
                )
            )

        return params

    def _read_requirements(self, repo_dir: Path) -> list[str]:
        """Read dependencies from requirements.txt."""
        req_path = repo_dir / "requirements.txt"
        if not req_path.exists():
            return []

        deps: list[str] = []
        try:
            for line in req_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    deps.append(line)
        except Exception:
            pass
        return deps

    def _guess_entrypoint(self, repo_dir: Path) -> str:
        """Guess the main entrypoint file."""
        candidates = [
            "main.py",
            "__main__.py",
            "plugin.py",
            "app.py",
            "server.py",
            "cli.py",
        ]
        for name in candidates:
            if (repo_dir / name).exists():
                return name

        # Find the first .py file
        py_files = sorted(repo_dir.glob("*.py"))
        if py_files:
            return py_files[0].name

        return ""
