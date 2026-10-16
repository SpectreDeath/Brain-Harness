#!/usr/bin/env python3
"""Plugin Seam & Mirror Auditor CLI Engine.

Comprehensive tool for auditing IoC DAG topology, fuzzing entrypoints with adversarial
parameter vectors, verifying documentation-code AST mirroring, and auto-synchronizing
documentation and manifests across any target directory.

Adheres to Rule 12 (Slotted Dataclasses), Rule 14 (Pipe Disposal), Rule 23 (Windows UTF-8 Streams),
Rule 33 (JSON Null Fallback), Rule 44 (Zero-Fork Bounds), and Rule 57 (Qualified Imports).
"""

from __future__ import annotations

import argparse
import ast
import asyncio
from dataclasses import dataclass, field
import inspect
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Sequence

# Rule 23 & Rule 50: Enforce UTF-8 standard stream codecs on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# -----------------------------------------------------------------------------
# Domain Models (Rule 12: Slotted Dataclass Architecture)
# -----------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class PluginTarget:
    """Discovered plugin target directory and metadata."""
    name: str
    path: Path
    manifest_path: Path | None
    main_py_path: Path | None
    readme_path: Path | None
    quickstart_path: Path | None
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DagAuditResult:
    """Result of IoC dependency graph analysis."""
    total_plugins: int = 0
    total_services_provided: int = 0
    cycles_detected: list[list[str]] = field(default_factory=list)
    dangling_requirements: list[dict[str, Any]] = field(default_factory=list)
    valid: bool = True


@dataclass(slots=True)
class FuzzFinding:
    """Finding surfaced during adversarial parameter fuzzing."""
    plugin: str
    entrypoint: str
    vector: str
    status: str  # safe | handled_error | unhandled_error | timeout
    error: str | None = None
    duration: float = 0.0


@dataclass(slots=True)
class MirrorFinding:
    """Discrepancy surfaced during documentation-code mirroring audit."""
    plugin: str
    category: str  # missing_doc | missing_entrypoint | param_drift | syntax_error
    description: str
    entrypoint: str | None = None
    target_file: str | None = None


# -----------------------------------------------------------------------------
# Target Discovery Engine
# -----------------------------------------------------------------------------

def discover_plugin_targets(target_path: Path) -> list[PluginTarget]:
    """Discover plugin targets in an arbitrary directory (single plugin or recursive)."""
    target_path = target_path.resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_path}")

    # Case 1: Target directory is directly a plugin
    if (target_path / "plugin.json").exists() or (target_path / "manifest.json").exists() or (target_path / "main.py").exists():
        targets = [target_path]
    else:
        # Case 2: Scan subdirectories recursively up to depth 4
        targets = []
        skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "target", "dist", ".gemini"}
        for root, dirs, files in os.walk(target_path):
            # Prune noise directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            current_p = Path(root)
            depth = len(current_p.relative_to(target_path).parts)
            if depth > 4:
                dirs.clear()
                continue
            if (current_p / "plugin.json").exists() or (current_p / "manifest.json").exists():
                targets.append(current_p)
                dirs.clear()  # Don't recurse into subdirectories of an identified plugin

    discovered: list[PluginTarget] = []
    for p_dir in targets:
        m_file = p_dir / "plugin.json"
        if not m_file.exists():
            m_file = p_dir / "manifest.json"
            if not m_file.exists():
                m_file = None

        manifest_data: dict[str, Any] = {}
        if m_file and m_file.exists():
            try:
                manifest_data = json.loads(m_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        name = manifest_data.get("name") or p_dir.name
        # Rule 33: JSON Null-Field Fallback Invariant
        provides = manifest_data.get("provides") or []
        requires = manifest_data.get("requires") or []
        raw_eps = manifest_data.get("entrypoints") or []
        entrypoints = [ep["name"] if isinstance(ep, dict) else str(ep) for ep in raw_eps]

        main_py = p_dir / "main.py"
        readme = p_dir / "README.md"
        quickstart = p_dir / "QUICKSTART.md"

        discovered.append(PluginTarget(
            name=name,
            path=p_dir,
            manifest_path=m_file,
            main_py_path=main_py if main_py.exists() else None,
            readme_path=readme if readme.exists() else None,
            quickstart_path=quickstart if quickstart.exists() else None,
            provides=provides,
            requires=requires,
            entrypoints=entrypoints,
        ))

    return discovered


# -----------------------------------------------------------------------------
# Phase 1: IoC Dependency DAG Auditor
# -----------------------------------------------------------------------------

def audit_dag(targets: list[PluginTarget]) -> DagAuditResult:
    """Analyze IoC service dependencies, detecting cycles and dangling requirements."""
    provided_map: dict[str, str] = {}
    graph: dict[str, list[str]] = {}

    for t in targets:
        graph[t.name] = []
        for prov in t.provides:
            provided_map[prov] = t.name

    dangling: list[dict[str, Any]] = []
    for t in targets:
        for req in t.requires:
            if req in provided_map:
                provider = provided_map[req]
                if provider != t.name:
                    graph[t.name].append(provider)
            else:
                dangling.append({"consumer": t.name, "missing_key": req})

    # Cycle Detection using Tarjan / DFS
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]):
        visited[node] = 1
        path.append(node)
        for neighbor in graph.get(node, []):
            if visited.get(neighbor) == 1:
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])
            elif visited.get(neighbor, 0) == 0:
                dfs(neighbor, path)
        path.pop()
        visited[node] = 2

    for node in graph:
        if visited.get(node, 0) == 0:
            dfs(node, [])

    return DagAuditResult(
        total_plugins=len(targets),
        total_services_provided=len(provided_map),
        cycles_detected=cycles,
        dangling_requirements=dangling,
        valid=len(cycles) == 0 and len(dangling) == 0,
    )


# -----------------------------------------------------------------------------
# Phase 2: Adversarial Parameter Fuzzing Engine
# -----------------------------------------------------------------------------

async def run_with_timeout(coro_or_fn: Any, timeout: float) -> Any:
    """Execute callable or coroutine with strict async timeout."""
    if inspect.iscoroutinefunction(coro_or_fn):
        return await asyncio.wait_for(coro_or_fn(), timeout=timeout)
    elif inspect.iscoroutine(coro_or_fn):
        return await asyncio.wait_for(coro_or_fn, timeout=timeout)
    else:
        # Run synchronous callable in default thread executor to bound execution
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(loop.run_in_executor(None, coro_or_fn), timeout=timeout)


async def fuzz_target(target: PluginTarget, timeout: float = 5.0) -> list[FuzzFinding]:
    """Fuzz all callable entrypoints of a plugin against 4 adversarial parameter matrices."""
    if not target.main_py_path or not target.main_py_path.exists():
        return []

    # Import plugin module
    p_dir = target.path
    if str(p_dir) not in sys.path:
        sys.path.insert(0, str(p_dir))

    module_name = f"_fuzz_target_{target.name.replace('.', '_').replace('-', '_')}"
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, target.main_py_path)
    if not spec or not spec.loader:
        return []

    try:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
    except Exception as e:
        return [FuzzFinding(
            plugin=target.name,
            entrypoint="<module_load>",
            vector="import",
            status="unhandled_error",
            error=f"Failed to import main.py: {e}",
        )]

    findings: list[FuzzFinding] = []

    # Identify callable entrypoints
    entrypoints = set(target.entrypoints)
    for attr in dir(mod):
        if not attr.startswith("_") and callable(getattr(mod, attr)):
            entrypoints.add(attr)

    # 4 Test Vector Matrices
    vectors = {
        "empty": lambda: {},
        "null_none": lambda params: {p: None for p in params},
        "type_confusion": lambda params: {p: 42 for p in params},
        "boundary_injection": lambda params: {p: "../../etc/passwd\x00\n🔥" for p in params},
    }

    for ep in entrypoints:
        fn = getattr(mod, ep, None)
        if not fn or not callable(fn) or inspect.isclass(fn):
            continue

        try:
            sig = inspect.signature(fn)
            param_names = [p.name for p in sig.parameters.values() if p.name not in ("self", "cls")]
        except Exception:
            param_names = []

        for v_name, gen in vectors.items():
            start_t = time.time()
            kwargs = gen() if v_name == "empty" else gen(param_names)

            def make_call():
                try:
                    res = fn(**kwargs)
                    if inspect.iscoroutine(res):
                        return res
                    return res
                except TypeError:
                    # In case kwargs format doesn't match varargs, try positional
                    return fn(*list(kwargs.values()))

            try:
                res = await run_with_timeout(make_call, timeout=timeout)
                duration = time.time() - start_t
                if isinstance(res, dict) and res.get("status") == "error":
                    status = "handled_error"
                else:
                    status = "safe"
                findings.append(FuzzFinding(
                    plugin=target.name,
                    entrypoint=ep,
                    vector=v_name,
                    status=status,
                    duration=round(duration, 3),
                ))
            except asyncio.TimeoutError:
                findings.append(FuzzFinding(
                    plugin=target.name,
                    entrypoint=ep,
                    vector=v_name,
                    status="timeout",
                    error=f"Exceeded {timeout}s timeout limit",
                    duration=timeout,
                ))
            except Exception as exc:
                duration = time.time() - start_t
                error_str = f"{type(exc).__name__}: {exc}"
                # Classify expected validation exceptions vs unhandled runtime errors
                if isinstance(exc, (ValueError, KeyError, TypeError, FileNotFoundError, PermissionError)):
                    status = "handled_error"
                else:
                    status = "unhandled_error"
                findings.append(FuzzFinding(
                    plugin=target.name,
                    entrypoint=ep,
                    vector=v_name,
                    status=status,
                    error=error_str,
                    duration=round(duration, 3),
                ))

    return findings


# -----------------------------------------------------------------------------
# Phase 3: Documentation-Code AST Mirror Auditor
# -----------------------------------------------------------------------------

def extract_ast_functions(file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract functions and parameter signatures from Python source via AST."""
    if not file_path.exists():
        return {}
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return {}

    module_funcs: dict[str, dict[str, Any]] = {}
    plugin_funcs: dict[str, dict[str, Any]] = {}
    other_funcs: dict[str, dict[str, Any]] = {}

    def extract_fn(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
        args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
        args.extend([a.arg for a in node.args.kwonlyargs])
        doc = ast.get_docstring(node) or "Executes the operation."
        return {
            "name": node.name,
            "args": args,
            "doc": doc.strip().splitlines()[0] if doc else "Executes operation.",
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            module_funcs[node.name] = extract_fn(node)
        elif isinstance(node, ast.ClassDef):
            is_plugin = "Plugin" in node.name
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn_data = extract_fn(item)
                    if is_plugin:
                        plugin_funcs[item.name] = fn_data
                    else:
                        other_funcs[item.name] = fn_data

    # Precedence: module-level > plugin methods > other methods
    return {**other_funcs, **plugin_funcs, **module_funcs}


def parse_readme_tools_table(readme_path: Path) -> dict[str, list[str]]:
    """Parse tool names and parameter signatures from README.md tables."""
    if not readme_path.exists():
        return {}
    content = readme_path.read_text(encoding="utf-8", errors="ignore")
    tools: dict[str, list[str]] = {}

    table_rows = re.findall(r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|\s*`?\(([^)]*)\)`?\s*\|", content)
    for name, params_str in table_rows:
        clean_params = [p.strip().split("=")[0].split(":")[0].strip() for p in params_str.split(",") if p.strip()]
        tools[name] = clean_params

    return tools


def check_markdown_codeblocks(md_path: Path) -> list[dict[str, Any]]:
    """Check Python codeblocks inside markdown for syntax validity."""
    if not md_path.exists():
        return []
    content = md_path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.findall(r"```(?:python|py)\s*\n(.*?)```", content, re.DOTALL)
    errors = []
    for idx, b in enumerate(blocks, 1):
        try:
            ast.parse(b)
        except SyntaxError as se:
            errors.append({"block_index": idx, "error": str(se), "snippet": b[:100]})
    return errors


def audit_mirror(target: PluginTarget) -> list[MirrorFinding]:
    """Audit a plugin for documentation-code discrepancies."""
    findings: list[MirrorFinding] = []

    # 1. Missing README check
    if not target.readme_path or not target.readme_path.exists():
        findings.append(MirrorFinding(
            plugin=target.name,
            category="missing_doc",
            description="README.md does not exist for plugin",
            target_file="README.md",
        ))
        return findings

    code_funcs = extract_ast_functions(target.main_py_path) if target.main_py_path else {}
    readme_tools = parse_readme_tools_table(target.readme_path)

    # 2. Check code block syntax in docs
    code_errors = check_markdown_codeblocks(target.readme_path)
    if target.quickstart_path and target.quickstart_path.exists():
        code_errors.extend(check_markdown_codeblocks(target.quickstart_path))
    for err in code_errors:
        findings.append(MirrorFinding(
            plugin=target.name,
            category="syntax_error",
            description=f"Python codeblock #{err['block_index']} syntax error: {err['error']}",
            target_file="README.md",
        ))

    # 3. Check every manifest entrypoint
    for ep in target.entrypoints:
        if ep not in readme_tools:
            findings.append(MirrorFinding(
                plugin=target.name,
                category="missing_entrypoint",
                description=f"Tool `{ep}` is declared in manifest but missing from README.md tools table",
                entrypoint=ep,
                target_file="README.md",
            ))
        else:
            code_fn = code_funcs.get(ep)
            if code_fn:
                doc_params = readme_tools[ep]
                code_params = code_fn["args"]
                if doc_params != code_params:
                    findings.append(MirrorFinding(
                        plugin=target.name,
                        category="param_drift",
                        description=f"Tool `{ep}` parameters in README ({doc_params}) drift from code AST ({code_params})",
                        entrypoint=ep,
                        target_file="README.md",
                    ))

    return findings


# -----------------------------------------------------------------------------
# Phase 4: Auto-Fix & Synchronization Engine
# -----------------------------------------------------------------------------

def auto_fix_target(target: PluginTarget) -> dict[str, Any]:
    """Auto-synchronize README.md, manifest entrypoints, and tools table with code."""
    actions: list[str] = []
    main_py = target.main_py_path
    if not main_py or not main_py.exists():
        return {"actions": actions}

    ast_funcs = extract_ast_functions(main_py)
    manifest_file = target.manifest_path

    # 1. Update Manifest if entrypoints are missing
    manifest_data: dict[str, Any] = {}
    if manifest_file and manifest_file.exists():
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    current_eps = target.entrypoints
    if not current_eps and ast_funcs:
        discovered_eps = []
        for fname, finfo in ast_funcs.items():
            if not fname.startswith(("_", "on_", "provides", "requires")) and fname not in ("name", "version", "description", "trusted", "enable", "disable", "main", "run"):
                discovered_eps.append({
                    "name": fname,
                    "description": finfo["doc"],
                    "parameters": [{"name": a, "type": "string", "required": False} for a in finfo["args"]],
                })
        if discovered_eps and manifest_file:
            manifest_data["entrypoints"] = discovered_eps
            manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            actions.append(f"Updated {manifest_file.name} with {len(discovered_eps)} discovered entrypoints")
            current_eps = [ep["name"] for ep in discovered_eps]

    # 2. Format Tools Table
    table_lines = [
        "## Tools & Entrypoints",
        "",
        "| Entrypoint | Parameters | Description |",
        "|---|---|---|",
    ]
    for ep in current_eps:
        fn_info = ast_funcs.get(ep) or ast_funcs.get(ep.replace("-", "_"))
        args = fn_info["args"] if fn_info else []
        params_str = f"({', '.join(args)})"
        doc = (fn_info["doc"] if fn_info else "Executes operation.").replace("|", "\\|").replace("\n", " ").strip()
        table_lines.append(f"| `{ep}` | `{params_str}` | {doc} |")
    table_md = "\n".join(table_lines)

    # 3. Scaffold README if missing
    readme_file = target.path / "README.md"
    if not readme_file.exists():
        rel_path = target.path.as_posix()
        desc = manifest_data.get("description", "Harness plugin providing specialized capabilities.")
        scaffold_content = f"""# {target.name} (v{manifest_data.get('version', '1.0.0')})

{desc}

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `{rel_path}` |
| Isolation Mode | `{manifest_data.get('isolation', 'in_process')}` |
| Services Provided | {", ".join(f"`{k}`" for k in target.provides) if target.provides else "None"} |
| Dependencies Required | {", ".join(f"`{k}`" for k in target.requires) if target.requires else "None"} |

---

{table_md}

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from {target.path.name}.main import plugin

context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork configuration (Rule 44).
"""
        readme_file.write_text(scaffold_content, encoding="utf-8")
        actions.append(f"Scaffolded Diátaxis README.md for {target.name}")
    else:
        # 4. Synchronize existing README tools table
        content = readme_file.read_text(encoding="utf-8")
        if "## Tools & Entrypoints" in content:
            pattern = r"## Tools & Entrypoints\s*\n\s*\|[^\n]+\|\s*\n\s*\|[^\n]+\|\s*\n(?:\|[^\n]+\|\s*\n?)*"
            match = re.search(pattern, content)
            if match:
                new_content = content[:match.start()] + table_md + "\n" + content[match.end():]
            else:
                new_content = re.sub(r"## Tools & Entrypoints.*?(?=\n## |\Z)", table_md + "\n\n", content, flags=re.DOTALL)
        else:
            if "## Key Modules" in content:
                new_content = content.replace("## Key Modules", table_md + "\n\n---\n\n## Key Modules")
            else:
                new_content = content + "\n\n---\n\n" + table_md + "\n"

        if new_content != content:
            readme_file.write_text(new_content, encoding="utf-8")
            actions.append(f"Synchronized ## Tools & Entrypoints in {readme_file.name}")

    return {"actions": actions}


# -----------------------------------------------------------------------------
# CLI Entrypoint & Multi-Command Dispatcher
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="plugin_auditor",
        description="Comprehensive plugin IoC DAG topology, adversarial fuzzing, and documentation mirror auditor.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. DAG Command
    dag_p = subparsers.add_parser("dag", help="Audit IoC dependency DAG for cycles and missing requirements.")
    dag_p.add_argument("--target-dir", default=".", help="Target directory (default: current directory)")
    dag_p.add_argument("--output", help="Optional JSON output file path")

    # 2. Fuzz Command
    fuzz_p = subparsers.add_parser("fuzz", help="Run adversarial 4-matrix parameter fuzzing on entrypoints.")
    fuzz_p.add_argument("--target-dir", default=".", help="Target directory (default: current directory)")
    fuzz_p.add_argument("--timeout", type=float, default=5.0, help="Per-vector execution timeout (default: 5.0s)")
    fuzz_p.add_argument("--output", help="Optional JSON output file path")

    # 3. Mirror Command
    mirror_p = subparsers.add_parser("mirror", help="Audit documentation-code AST mirroring across entrypoints.")
    mirror_p.add_argument("--target-dir", default=".", help="Target directory (default: current directory)")
    mirror_p.add_argument("--output", help="Optional JSON output file path")

    # 4. Sync Command (Auto-Fix)
    sync_p = subparsers.add_parser("sync", help="Auto-synchronize README tables and scaffold missing docs.")
    sync_p.add_argument("--target-dir", default=".", help="Target directory (default: current directory)")

    # 5. All Command
    all_p = subparsers.add_parser("all", help="Execute complete 5-phase audit and auto-fix pipeline.")
    all_p.add_argument("--target-dir", default=".", help="Target directory (default: current directory)")
    all_p.add_argument("--auto-fix", action="store_true", default=True, help="Automatically fix discovered doc/manifest drift (default: True)")
    all_p.add_argument("--timeout", type=float, default=5.0, help="Per-vector execution timeout (default: 5.0s)")
    all_p.add_argument("--output", help="Optional JSON audit report output file path")

    args = parser.parse_args()
    target_path = Path(args.target_dir)

    print(f"Scanning target directory: {target_path.resolve()}...")
    targets = discover_plugin_targets(target_path)
    print(f"Discovered {len(targets)} plugin target(s).\n")

    if not targets:
        print("No plugins discovered in target directory.")
        sys.exit(0)

    # Command Execution
    if args.command == "dag":
        res = audit_dag(targets)
        print(f"=== IoC DEPENDENCY DAG AUDIT ===")
        print(f"Total Plugins:          {res.total_plugins}")
        print(f"Total Services:         {res.total_services_provided}")
        print(f"Cycles Detected:        {len(res.cycles_detected)}")
        print(f"Dangling Requirements:  {len(res.dangling_requirements)}")
        if res.cycles_detected:
            for c in res.cycles_detected:
                print(f"  CYCLE: {' -> '.join(c)}")
        if res.dangling_requirements:
            for d in res.dangling_requirements:
                print(f"  DANGLING: Plugin '{d['consumer']}' requires unprovided '{d['missing_key']}'")
        if args.output:
            Path(args.output).write_text(json.dumps({
                "valid": res.valid,
                "cycles": res.cycles_detected,
                "dangling": res.dangling_requirements,
            }, indent=2), encoding="utf-8")
        sys.exit(0 if res.valid else 1)

    elif args.command == "fuzz":
        print(f"=== ADVERSARIAL PARAMETER FUZZING (Timeout: {args.timeout}s) ===")
        findings: list[FuzzFinding] = []
        for t in targets:
            f_list = asyncio.run(fuzz_target(t, timeout=args.timeout))
            findings.extend(f_list)
        
        safe = sum(1 for f in findings if f.status == "safe")
        handled = sum(1 for f in findings if f.status == "handled_error")
        unhandled = sum(1 for f in findings if f.status == "unhandled_error")
        timeouts = sum(1 for f in findings if f.status == "timeout")

        print(f"Total Vectors Executed: {len(findings)}")
        print(f"Safe Invocations:       {safe}")
        print(f"Handled Exceptions:     {handled}")
        print(f"Unhandled Exceptions:   {unhandled}")
        print(f"Timeouts / Deadlocks:   {timeouts}")

        if args.output:
            Path(args.output).write_text(json.dumps([
                {"plugin": f.plugin, "entrypoint": f.entrypoint, "vector": f.vector, "status": f.status, "error": f.error}
                for f in findings
            ], indent=2), encoding="utf-8")
        sys.exit(0 if timeouts == 0 and unhandled == 0 else 1)

    elif args.command == "mirror":
        print("=== DOCUMENTATION-CODE AST MIRROR AUDIT ===")
        all_findings: list[MirrorFinding] = []
        for t in targets:
            f_list = audit_mirror(t)
            all_findings.extend(f_list)

        print(f"Total Discrepancies Found: {len(all_findings)}")
        for f in all_findings:
            print(f"  [{f.category.upper()}] {f.plugin}: {f.description}")

        if args.output:
            Path(args.output).write_text(json.dumps([
                {"plugin": f.plugin, "category": f.category, "description": f.description, "entrypoint": f.entrypoint}
                for f in all_findings
            ], indent=2), encoding="utf-8")
        sys.exit(0 if not all_findings else 1)

    elif args.command == "sync":
        print("=== AUTO-FIX & DOCUMENTATION SYNCHRONIZATION ===")
        total_actions = 0
        for t in targets:
            res = auto_fix_target(t)
            for act in res["actions"]:
                print(f"  [FIX] {act}")
                total_actions += 1
        print(f"\nAuto-fix complete: {total_actions} action(s) applied.")
        sys.exit(0)

    elif args.command == "all":
        print("=== FULL 5-PHASE AUDIT & AUTO-FIX CAMPAIGN ===")
        dag_res = audit_dag(targets)
        print(f"1. DAG Check:     {'PASS' if dag_res.valid else 'FAIL'} (Cycles: {len(dag_res.cycles_detected)}, Dangling: {len(dag_res.dangling_requirements)})")

        mirror_findings: list[MirrorFinding] = []
        for t in targets:
            mirror_findings.extend(audit_mirror(t))
        print(f"2. Mirror Check:  {len(mirror_findings)} discrepancy(ies) detected")

        if args.auto_fix and mirror_findings:
            print("\nApplying Auto-Fix Remediation...")
            fixed_count = 0
            for t in targets:
                f_res = auto_fix_target(t)
                for a in f_res["actions"]:
                    print(f"  [AUTO-FIX] {a}")
                    fixed_count += 1
            print(f"Auto-fix remediation applied {fixed_count} modification(s).")
            # Re-audit mirror
            mirror_findings = []
            for t in targets:
                mirror_findings.extend(audit_mirror(t))
            print(f"Post-fix Mirror Check: {len(mirror_findings)} discrepancy(ies) remaining.")

        print(f"\n3. Adversarial Fuzzing (Timeout: {args.timeout}s)...")
        fuzz_findings: list[FuzzFinding] = []
        for t in targets:
            fuzz_findings.extend(asyncio.run(fuzz_target(t, timeout=args.timeout)))

        safe = sum(1 for f in fuzz_findings if f.status == "safe")
        timeouts = sum(1 for f in fuzz_findings if f.status == "timeout")
        unhandled = sum(1 for f in fuzz_findings if f.status == "unhandled_error")
        print(f"Fuzzing Complete: {len(fuzz_findings)} vectors (Safe: {safe}, Timeouts: {timeouts}, Unhandled: {unhandled})")

        report_data = {
            "target_dir": str(target_path.resolve()),
            "total_plugins": len(targets),
            "dag_valid": dag_res.valid,
            "mirror_discrepancies": len(mirror_findings),
            "fuzz_safe": safe,
            "fuzz_timeouts": timeouts,
            "fuzz_unhandled": unhandled,
        }
        if args.output:
            Path(args.output).write_text(json.dumps(report_data, indent=2), encoding="utf-8")
            print(f"\nAudit report saved to: {args.output}")

        sys.exit(0 if dag_res.valid and timeouts == 0 and not mirror_findings else 1)


if __name__ == "__main__":
    main()
