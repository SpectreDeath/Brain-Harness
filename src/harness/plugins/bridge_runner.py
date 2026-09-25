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


async def _execute_func(func: Any, params: dict[str, Any]) -> Any:
    """Execute function supporting both synchronous and asynchronous implementations."""
    if inspect.iscoroutinefunction(func):
        return await func(**params)
    res = await asyncio.to_thread(func, **params)
    if inspect.isawaitable(res):
        return await res
    return res


async def async_main(module: Any) -> None:
    """Asynchronous JSON-RPC server loop over stdin/stdout with atomic locking."""
    stdout_lock = asyncio.Lock()

    async def handle_request(line_str: str) -> None:
        try:
            request = json.loads(line_str)
            method = request.get("method", "")
            params = request.get("params") or {}
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
                    result = await _execute_func(func, params)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                except Exception as e:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": str(e)}

            payload = json.dumps(response) + "\n"
            async with stdout_lock:
                sys.stdout.write(payload)
                sys.stdout.flush()
        except Exception as e:
            err_payload = (
                json.dumps({"jsonrpc": "2.0", "id": 0, "error": str(e)}) + "\n"
            )
            async with stdout_lock:
                sys.stdout.write(err_payload)
                sys.stdout.flush()

    tasks: set[asyncio.Task[Any]] = set()

    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            # EOF reached
            break
        line_str = line.strip()
        if not line_str:
            continue

        task = asyncio.create_task(handle_request(line_str))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


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

    import os
    if os.environ.get("HARNESS_NO_NETWORK") == "1":
        import socket

        def _blocked_connect(*args: Any, **kwargs: Any) -> None:
            raise PermissionError("Outbound network access disabled for sandboxed plugin")

        socket.socket.connect = _blocked_connect  # type: ignore[assignment]

    parser = argparse.ArgumentParser(description="Harness Sandboxed Plugin Runner")
    parser.add_argument("script_path", help="Path to plugin entrypoint script")
    args = parser.parse_args()

    from pathlib import Path

    runner_file = Path(__file__).resolve()
    if len(runner_file.parents) >= 3:
        src_dir = str(runner_file.parents[2])
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        workspace_root = str(runner_file.parents[3])
        if workspace_root not in sys.path:
            sys.path.insert(0, workspace_root)
    script_dir = str(Path(args.script_path).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Load the plugin module
    spec = importlib.util.spec_from_file_location("plugin", args.script_path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"Failed to load spec from {args.script_path}\n")
        sys.stderr.flush()
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    asyncio.run(async_main(module))


if __name__ == "__main__":
    main()
