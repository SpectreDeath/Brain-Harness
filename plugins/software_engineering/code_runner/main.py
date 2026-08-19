"""Sandboxed Python code runner and REPL plugin for Brain Harness."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def python_exec(code: str, timeout: float = 10.0) -> dict[str, Any]:
    """Execute a block of Python code in an isolated subprocess."""
    try:
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "status": "ok",
            "success": res.returncode == 0,
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": f"Execution timed out after {timeout} seconds.",
            "timed_out": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def python_eval(expression: str, timeout: float = 5.0) -> dict[str, Any]:
    """Evaluate a single Python expression and capture the output."""
    wrapper = f"import reprlib; res = ({expression}); print(repr(res))"
    res = python_exec(wrapper, timeout=timeout)
    if res.get("status") != "ok":
        return res

    if not res.get("success"):
        return {
            "status": "error",
            "error": res.get("stderr", "Evaluation failed").strip(),
        }

    return {
        "status": "ok",
        "expression": expression,
        "result": str(res.get("stdout", "")).strip(),
    }


def run_temp_script(
    script_content: str,
    args: list[str] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Write script to a temp file, execute it with arguments, and clean up."""
    temp_dir = tempfile.mkdtemp(prefix="harness_runner_")
    script_file = Path(temp_dir) / "runner_script.py"

    try:
        script_file.write_text(script_content, encoding="utf-8")
        cmd = [sys.executable, str(script_file)]
        if args:
            cmd.extend(args)

        res = subprocess.run(
            cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "status": "ok",
            "success": res.returncode == 0,
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": f"Script execution timed out after {timeout} seconds.",
            "timed_out": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        try:
            if script_file.exists():
                script_file.unlink()
            Path(temp_dir).rmdir()
        except Exception:
            pass
