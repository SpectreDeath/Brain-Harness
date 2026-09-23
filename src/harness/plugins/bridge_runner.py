"""Subprocess JSON-RPC bridge runner for sandboxed plugins.

Staged entrypoint runner executing plugin modules in isolated subprocesses.
Eliminates inline -c strings (Rule 29) and enforces UTF-8 stream encoding (Rule 23).
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import inspect
import json
import sys
from typing import Any


def _execute_func(func: Any, params: dict[str, Any]) -> Any:
    """Execute function supporting both synchronous and asynchronous implementations."""
    if inspect.iscoroutinefunction(func):
        return asyncio.run(func(**params))
    res = func(**params)
    if inspect.isawaitable(res):
        return asyncio.run(res)
    return res


def main() -> None:
    # Ensure UTF-8 standard stream codecs across operating systems (Rule 23)
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Harness Sandboxed Plugin Runner")
    parser.add_argument("script_path", help="Path to plugin entrypoint script")
    args = parser.parse_args()

    # Load the plugin module
    spec = importlib.util.spec_from_file_location("plugin", args.script_path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"Failed to load spec from {args.script_path}\n")
        sys.stderr.flush()
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # JSON-RPC loop over stdin
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            request = json.loads(line_str)
            method = request.get("method", "")
            params = request.get("params", {})
            req_id = request.get("id", 0)

            func = getattr(module, method, None)
            if func is None:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": f"Method not found: {method}",
                }
            else:
                try:
                    result = _execute_func(func, params)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                except Exception as e:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": str(e)}

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(
                json.dumps({"jsonrpc": "2.0", "id": 0, "error": str(e)}) + "\n"
            )
            sys.stdout.flush()


if __name__ == "__main__":
    main()
