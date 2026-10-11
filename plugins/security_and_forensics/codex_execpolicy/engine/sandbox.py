"""Platform-native sandboxing requirement evaluation (Rule 5 & Rule 14)."""

from __future__ import annotations

import platform
import sys
from typing import Any

from plugins.security_and_forensics.codex_execpolicy.engine.ast_parser import _tokenize_command

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def check_sandbox_requirements(
    command: str,
    target_platform: str | None = None,
) -> dict[str, Any]:
    """Determine platform-native sandboxing requirements for a given command."""
    plat = (target_platform or platform.system()).lower()
    if "win" in plat:
        plat_name = "windows"
        sandbox_type = "windows_restricted_token"
    elif "darwin" in plat or "mac" in plat:
        plat_name = "macos"
        sandbox_type = "macos_seatbelt"
    else:
        plat_name = "linux"
        sandbox_type = "linux_landlock_bwrap"

    ast = _tokenize_command(command)
    binary = ast["binary"].lower()

    is_write_heavy = any(
        kw in command.lower()
        for kw in ["install", "build", "compile", "mkdir", "touch", "cp", "mv", "rm", "write"]
    )
    is_network_heavy = any(
        kw in command.lower()
        for kw in ["curl", "wget", "git clone", "git push", "npm install", "pip install", "fetch"]
    )

    recommended_reads = ["."]
    recommended_writes = ["."] if is_write_heavy else []

    requires_sandbox = True
    if binary in ("echo", "pwd", "whoami", "uname", "hostname"):
        requires_sandbox = False

    return {
        "status": "ok",
        "command": command,
        "target_platform": plat_name,
        "sandbox_type": sandbox_type,
        "requires_sandbox": requires_sandbox,
        "is_network_allowed": is_network_heavy,
        "recommended_read_paths": recommended_reads,
        "recommended_write_paths": recommended_writes,
        "security_recommendations": [
            f"Enforce {sandbox_type} isolation boundary on {plat_name}",
            "Block access to /etc, C:\\Windows\\System32, and user home root outside workspace",
        ],
    }


__all__ = [
    "check_sandbox_requirements",
]
