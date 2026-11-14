"""Command safety guards and environment scrubbing helpers for Repository Dock."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .models import DockBoundaries


_CATASTROPHIC_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+-[rR]f\s+(?:/|/\*|~|\$HOME)", "Filesystem root deletion"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\s+", "Filesystem format"),
    (r"\bdd\s+if=.*of=/dev/[sh]d", "Direct disk overwrite"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb DoS"),
    (r"\b(?:curl|wget|fetch)\b.*\|\s*(?:bash|sh|zsh|python|perl|powershell)", "Unchecked remote script execution"),
    (r"\bgit\s+push\s+.*--force\b", "Prohibited git push --force"),
    (r"\bgit\s+push\s+.*-f\b", "Prohibited git push -f"),
    (r"\bgit\s+reset\s+--hard\b", "Prohibited git reset --hard"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "Prohibited git clean -f"),
    (r"\bshutdown\b", "System shutdown"),
    (r"\breboot\b", "System reboot"),
]


_CREDENTIAL_ACCESS_PATTERNS: list[tuple[str, str]] = [
    (r"\b(?:cat|type|more|less|head|tail)\s+.*\.env\b", "Attempted .env file read"),
    (r"\b(?:cat|type)\s+.*\.git-credentials\b", "Attempted .git-credentials read"),
    (r"\bprintenv\b", "Attempted environment variable dump"),
    (r"\b(?:get-childitem|gci)\s+env:\b", "Attempted PowerShell env dump"),
]


def check_command_safety(
    command: str,
    boundaries: DockBoundaries,
) -> tuple[bool, str]:
    """Check command string against catastrophic patterns, credentials, and boundaries."""
    clean_cmd = command.strip()
    if not clean_cmd:
        return True, ""

    # 1. Catastrophic patterns
    for pat, desc in _CATASTROPHIC_PATTERNS:
        if re.search(pat, clean_cmd, re.IGNORECASE):
            return False, f"Triggered catastrophic security rule: {desc}"

    # 2. Credential access patterns
    for pat, desc in _CREDENTIAL_ACCESS_PATTERNS:
        if re.search(pat, clean_cmd, re.IGNORECASE):
            return False, f"Prohibited credential inspection: {desc}"

    # 3. Manifest operation boundaries
    for op in boundaries.operations:
        op_clean = op.strip()
        if op_clean and op_clean.lower() in clean_cmd.lower():
            return False, f"Command matches prohibited boundary operation: '{op_clean}'"

    # 4. Manifest path boundaries
    for bp in boundaries.paths:
        bp_clean = bp.strip().replace("\\", "/").rstrip("/")
        if not bp_clean:
            continue
        # Check if boundary path token appears in command
        cmd_normalized = clean_cmd.replace("\\", "/")
        if re.search(rf"(?:^|[\s\"'/]){re.escape(bp_clean)}(?:$|[\s\"'/])", cmd_normalized, re.IGNORECASE):
            return False, f"Command references prohibited boundary path: '{bp_clean}'"

    return True, ""


def _build_scrubbed_env(repo_path: Path) -> dict[str, str]:
    """Prepare credential-scrubbed subprocess environment with repo PYTHONPATH/venv (Rules 15, 23, 50)."""
    env = dict(os.environ)
    for k in list(env.keys()):
        ku = k.upper()
        if "TOKEN" in ku or "SECRET" in ku or "PASSWORD" in ku or ("KEY" in ku and "PATH" not in ku):
            env.pop(k, None)
    env["PYTHONIOENCODING"] = "utf-8"

    repo_pp = f"{repo_path / 'src'}{os.pathsep}{repo_path}"
    if "PYTHONPATH" in env and env["PYTHONPATH"]:
        env["PYTHONPATH"] = f"{repo_pp}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = repo_pp

    venv_bin = repo_path / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    if venv_bin.is_dir():
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"
    return env


__all__ = ["_CATASTROPHIC_PATTERNS", "_CREDENTIAL_ACCESS_PATTERNS", "check_command_safety", "_build_scrubbed_env"]
