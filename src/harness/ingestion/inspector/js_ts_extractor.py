"""JavaScript / TypeScript entrypoint and parameter extraction for universal ingestion."""

from __future__ import annotations

import json
import re
from pathlib import Path

from harness.ingestion.inspector.manifest_strategies import derive_plugin_name
from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

_TS_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "boolean": "boolean",
    "any": "any",
    "unknown": "any",
    "void": "null",
    "null": "null",
    "object": "object",
    "record": "object",
    "array": "array",
}


def _split_param_list(raw_params: str) -> list[str]:
    """Split comma-separated parameter list respecting nested brackets and generics."""
    tokens: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in raw_params:
        if ch in "<([{":
            depth += 1
            current.append(ch)
        elif ch in ">)]}":
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == "," and depth == 0:
            tokens.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current).strip())
    return [t for t in tokens if t]


def parse_js_ts_params(raw_params: str) -> list[ParameterSpec]:
    """Parse parameter list from JS/TS function signature into ParameterSpecs."""
    params: list[ParameterSpec] = []
    if not raw_params.strip():
        return params

    for raw in _split_param_list(raw_params):
        token = raw.strip()
        if not token or token.startswith("..."):
            continue
        has_default = "=" in token
        clean = token.split("=")[0].strip()
        is_optional = "?" in clean or has_default
        clean = clean.replace("?", "").strip()

        pname = clean
        ptype = "any"
        if ":" in clean:
            parts = clean.split(":", 1)
            pname = parts[0].strip()
            raw_t = parts[1].strip().lower()
            if "[]" in raw_t or "array" in raw_t:
                ptype = "array"
            else:
                base_t = re.sub(r"[<({].*$", "", raw_t).strip()
                ptype = _TS_TYPE_MAP.get(base_t, "any")

        if pname and pname != "this":
            params.append(
                ParameterSpec(
                    name=pname,
                    type=ptype,
                    required=not is_optional,
                )
            )
    return params


def extract_js_ts_entrypoints(repo_dir: Path) -> list[EntrypointSpec]:
    """Scan JavaScript / TypeScript source files to extract public exported functions."""
    entrypoints: list[EntrypointSpec] = []
    files: list[Path] = []

    for pattern in ("*.ts", "*.js", "*.mjs", "*.cjs"):
        files.extend(repo_dir.glob(pattern))
    src = repo_dir / "src"
    if src.exists():
        for pattern in ("**/*.ts", "**/*.js", "**/*.mjs"):
            files.extend(src.glob(pattern))

    seen_names: set[str] = set()
    fn_regex = re.compile(
        r"(?:/\*\*(?P<jsdoc>[\s\S]*?)\*/\s*)?export\s+(?:async\s+)?function\s+(?P<fn>[a-zA-Z0-9_$]+)\s*\((?P<params>[^)]*)\)"
    )
    arrow_regex = re.compile(
        r"(?:/\*\*(?P<jsdoc>[\s\S]*?)\*/\s*)?export\s+const\s+(?P<fn>[a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\((?P<params>[^)]*)\)"
    )

    for fpath in files[:25]:
        if fpath.name.endswith((".d.ts", ".test.ts", ".spec.ts", ".test.js", ".spec.js")):
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for regex in (fn_regex, arrow_regex):
            for match in regex.finditer(content):
                fn_name = match.group("fn")
                if fn_name in seen_names or fn_name.startswith("_"):
                    continue
                seen_names.add(fn_name)
                jsdoc = match.group("jsdoc") or ""
                doc = re.sub(r"^\s*\* ?", "", jsdoc, flags=re.MULTILINE).strip()[:200]
                params = parse_js_ts_params(match.group("params") or "")
                entrypoints.append(
                    EntrypointSpec(
                        name=fn_name,
                        description=doc or f"Exported {fpath.name} function {fn_name}",
                        parameters=params,
                    )
                )

    return entrypoints


def try_js_ts_inspection(repo_dir: Path) -> PluginManifest | None:
    """Synthesize or enrich a PluginManifest for a JavaScript/TypeScript repository."""
    pkg_json = repo_dir / "package.json"
    tsconfig = repo_dir / "tsconfig.json"
    is_ts = tsconfig.exists() or bool(list(repo_dir.glob("*.ts")) or list((repo_dir / "src").glob("*.ts") if (repo_dir / "src").exists() else []))

    pkg_data: dict = {}
    if pkg_json.exists():
        try:
            pkg_data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except Exception:
            pkg_data = {}

    entrypoints = extract_js_ts_entrypoints(repo_dir)
    if not pkg_data and not entrypoints and not is_ts:
        return None

    name = pkg_data.get("name") or derive_plugin_name(repo_dir)
    version = pkg_data.get("version", "0.1.0")
    desc = pkg_data.get("description", f"JavaScript/TypeScript plugin from {name}")

    ep = pkg_data.get("main") or pkg_data.get("module") or ("src/index.ts" if is_ts else "index.js")
    for cand in ("index.ts", "src/index.ts", "index.js", "src/index.js", "main.ts", "main.js"):
        if (repo_dir / cand).exists():
            ep = cand
            break

    deps = list((pkg_data.get("dependencies") or {}).keys())

    return PluginManifest(
        name=name.replace("@", "").replace("/", "__"),
        version=version,
        description=desc,
        language="typescript" if is_ts else "javascript",
        entrypoint=str(ep),
        entrypoints=entrypoints,
        dependencies=deps,
        isolation=IsolationMode.SUBPROCESS,
        metadata={
            "source_format": "package.json" if pkg_json.exists() else "js_ts_extraction",
            "typescript": is_ts,
        },
    )
