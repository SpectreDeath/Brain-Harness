"""Node.js and renderer runtime detection utilities."""
from __future__ import annotations

import shutil
import subprocess


def check_node_available() -> tuple[bool, str]:
    """Check if node and npx are present on PATH.

    Returns:
        (available, description_or_version)
    """
    node_path = shutil.which("node")
    npx_path = shutil.which("npx")

    if not node_path or not npx_path:
        return False, "Node.js or npx not found on PATH"

    try:
        proc = subprocess.run(
            [node_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            version = proc.stdout.strip()
            return True, f"Node.js {version} detected ({node_path})"
        return False, f"node exited with code {proc.returncode}"
    except Exception as exc:
        return False, f"Failed to probe node version: {exc}"
