"""Fine-grained rule checkers for repository invariants."""

from __future__ import annotations

import re
from typing import Any

from harness.services.skill_graph.models import (
    AntiPatternViolation,
    InvariantViolation,
)


def check_rule15_credentials(
    combined_text: str, skill_name: str = "system_guard"
) -> list[AntiPatternViolation]:
    """Rule 15: Check for plaintext access tokens in proposed action parameters."""
    violations: list[AntiPatternViolation] = []
    if re.search(r"(?:ghp_[A-Za-z0-9_]{10,}|github_pat_[A-Za-z0-9_]{10,})", combined_text):
        violations.append(
            AntiPatternViolation(
                skill_name=skill_name,
                anti_pattern="Rule 15: Credential Exposure in Action Parameters",
                symptom="Plaintext access token detected in proposed action parameters",
                remedy="Pass authenticated credentials via isolated runner script with in-memory log redaction",
                matched_phrase="[REDACTED_TOKEN_DETECTED]",
            )
        )
    return violations


def check_rule30_powershell_glob(
    action_name: str,
    action_input: dict[str, Any],
    combined_text: str,
    skill_name: str = "system_guard",
) -> list[AntiPatternViolation]:
    """Rule 30: Check for unexpanded wildcard globs in PowerShell commands."""
    violations: list[AntiPatternViolation] = []
    if action_name in ("run_command", "bash", "execute_command"):
        cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
        if re.search(r"pytest\s+[^\s]*\*", cmd_val):
            violations.append(
                AntiPatternViolation(
                    skill_name=skill_name,
                    anti_pattern="Rule 30: PowerShell Glob Non-Expansion in pytest",
                    symptom="Glob wildcard '*' in pytest target path will not be expanded by PowerShell",
                    remedy='Use pytest -k "<pattern>" keyword filtering or explicit file lists instead of glob paths',
                    matched_phrase="pytest * glob",
                )
            )
    return violations


def check_inv_artifact_metadata(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], text_lower: str, skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 31: Artifact metadata restricted to artifact directory."""
    if (
        "artifact metadata" in inv_lower
        and ("restricted" in inv_lower or "only accepts" in inv_lower)
        and action_name in ("write_to_file", "write_file", "create_file")
        and ("artifactmetadata" in text_lower or any("artifactmetadata" in str(k).lower() for k in action_input))
    ):
        target = str(action_input.get("target_file") or action_input.get("TargetFile") or action_input.get("path") or action_input.get("file_path") or "").replace("\\", "/")
        if target and not ("brain" in target or ".gemini" in target or "artifact" in target):
            return InvariantViolation(
                skill_name=skill_name,
                rule=inv_rule,
                matched_phrase="ArtifactMetadata on workspace file",
                is_blocking=is_blocking,
                remedy="Omit ArtifactMetadata when writing files outside the artifact directory",
            )
    return None


def check_inv_scratch_execution(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], combined_text: str, skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 29: Scratch file execution over inline -c strings."""
    if (
        ("scratch file execution" in inv_lower or "inline -c" in inv_lower)
        and "never" in inv_lower
        and (action_name in ("run_command", "bash", "execute_command") or "command" in action_input or "CommandLine" in action_input)
    ):
        cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
        if "python -c" in cmd_val or 'python -c "' in cmd_val or "python -c '" in cmd_val:
            return InvariantViolation(
                skill_name=skill_name,
                rule=inv_rule,
                matched_phrase="python -c inline string",
                is_blocking=is_blocking,
                remedy="Write logic to a scratch script and execute via python <path>",
            )
    return None


def check_inv_powershell_glob(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], combined_text: str, skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 30: PowerShell glob non-expansion."""
    if (
        ("powershell glob" in inv_lower or "non-expansion" in inv_lower or "rule 30" in inv_lower)
        and (action_name in ("run_command", "bash", "execute_command") or "command" in action_input or "CommandLine" in action_input)
    ):
        cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
        if re.search(r"pytest\s+[^\s]*\*", cmd_val):
            return InvariantViolation(
                skill_name=skill_name,
                rule=inv_rule,
                matched_phrase="pytest glob path in PowerShell",
                is_blocking=is_blocking,
                remedy='Use pytest -k "<pattern>" keyword filtering or explicit file lists instead of glob paths',
            )
    return None


def check_inv_credentials(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], combined_text: str, skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 15: Secure credential injection & runner isolation."""
    if (
        ("credential" in inv_lower or "token" in inv_lower or "rule 15" in inv_lower or "runner isolation" in inv_lower)
        and (action_name in ("run_command", "bash", "execute_command") or "command" in action_input or "CommandLine" in action_input)
    ):
        cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
        if "git push" in cmd_val and ("ghp_" in cmd_val or "github_pat_" in cmd_val):
            return InvariantViolation(
                skill_name=skill_name,
                rule=inv_rule,
                matched_phrase="authenticated git push via shell expansion",
                is_blocking=is_blocking,
                remedy="Execute authenticated git push via isolated python runner script using standard input pipe",
            )
    return None


def check_inv_utf8_streams(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], combined_text: str, skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 23 & 50: Windows UTF-8 stream codec entrypoint."""
    if (
        ("utf-8" in inv_lower or "reconfigure" in inv_lower or "rule 23" in inv_lower or "rule 50" in inv_lower)
        and action_name in ("write_to_file", "write_file", "create_file")
    ):
        target = str(action_input.get("target_file") or action_input.get("TargetFile") or action_input.get("path") or action_input.get("file_path") or "").replace("\\", "/")
        code = str(action_input.get("CodeContent") or action_input.get("content") or action_input.get("code") or combined_text)
        if "scratch" in target and target.endswith(".py") and "sys.stdout.reconfigure" not in code:
            return InvariantViolation(
                skill_name=skill_name,
                rule=inv_rule,
                matched_phrase="Missing sys.stdout.reconfigure(encoding='utf-8') in scratch runner",
                is_blocking=is_blocking,
                remedy="Add sys.stdout.reconfigure(encoding='utf-8') at module entry to prevent cp1252 charmap crashes",
            )
    return None


def check_inv_knowledge_vault(
    inv_rule: str, inv_lower: str, action_name: str, action_input: dict[str, Any], skill_name: str, is_blocking: bool
) -> InvariantViolation | None:
    """Check Rule 40: Canonical Knowledge Vault dual-file directory format."""
    if (
        ("knowledge vault" in inv_lower or "dual-file" in inv_lower or "rule 40" in inv_lower)
        and action_name in ("write_to_file", "write_file", "create_file")
    ):
        target = str(action_input.get("target_file") or action_input.get("TargetFile") or action_input.get("path") or action_input.get("file_path") or "").replace("\\", "/")
        if ".harness/knowledge" in target or "harness/knowledge" in target:
            parts = target.split("knowledge/")[-1].strip("/").split("/")
            if len(parts) == 1 and parts[0].endswith(".json"):
                return InvariantViolation(
                    skill_name=skill_name,
                    rule=inv_rule,
                    matched_phrase="Flat JSON file in knowledge vault root",
                    is_blocking=is_blocking,
                    remedy="Persist items in directory structure: .harness/knowledge/<ki_id>/ (metadata.json + summary.md)",
                )
    return None
