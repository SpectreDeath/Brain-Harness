"""AST-based extraction of callable functions, parameters, and requirements."""

from __future__ import annotations

import ast
from pathlib import Path

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)


def extract_function_params(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterSpec]:
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
    num_defaults = len(args.defaults)
    num_args = len(args.args)

    for i, arg in enumerate(args.args):
        if arg.arg == "self":
            continue

        param_type = "any"
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                param_type = type_map.get(arg.annotation.id, arg.annotation.id)
            elif isinstance(arg.annotation, ast.Constant):
                val_str = str(arg.annotation.value)
                param_type = type_map.get(val_str, val_str)
            elif isinstance(arg.annotation, ast.Subscript) and isinstance(arg.annotation.value, ast.Name):
                container = arg.annotation.value.id
                param_type = type_map.get(container, container)

        has_default = i >= (num_args - num_defaults)
        params.append(
            ParameterSpec(
                name=arg.arg,
                type=param_type,
                required=not has_default,
            )
        )

    return params


def extract_python_entrypoints(repo_dir: Path) -> list[EntrypointSpec]:
    """Parse Python files via AST to find public callable functions."""
    entrypoints: list[EntrypointSpec] = []
    py_files = list(repo_dir.glob("*.py"))
    src_dir = repo_dir / "src"
    if src_dir.exists():
        py_files.extend(src_dir.rglob("*.py"))

    for py_file in py_files[:20]:
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    params = extract_function_params(node)
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


def read_requirements(repo_dir: Path) -> list[str]:
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


def guess_entrypoint(repo_dir: Path) -> str:
    """Guess the main entrypoint file."""
    candidates = ["main.py", "__main__.py", "plugin.py", "app.py", "server.py", "cli.py"]
    for name in candidates:
        if (repo_dir / name).exists():
            return name

    py_files = sorted(repo_dir.glob("*.py"))
    if py_files:
        return py_files[0].name
    return ""


def try_python_ast(repo_dir: Path) -> PluginManifest | None:
    """Fall back to AST parsing of Python files."""
    entrypoints = extract_python_entrypoints(repo_dir)
    if not entrypoints:
        return None

    deps = read_requirements(repo_dir)
    ep = guess_entrypoint(repo_dir)

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
