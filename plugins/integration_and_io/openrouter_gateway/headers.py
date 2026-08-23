"""Header construction and metadata attribution for OpenRouter Gateway.

Ported and extended from Kilo Code's packages/kilo-gateway/src/headers.ts.
Provides fine-grained request attribution, task tracing, and tester suppression.
"""

from __future__ import annotations

import os
import time
from typing import Any

# Header Constants
HEADER_ORGANIZATION_ID = "X-KiloCode-OrganizationId"
HEADER_TASK_ID = "X-KiloCode-TaskId"
HEADER_PARENT_TASK_ID = "X-KiloCode-Parent-TaskId"
HEADER_PROJECT_ID = "X-KiloCode-ProjectId"
HEADER_TESTER = "X-KiloCode-Tester"
HEADER_EDITOR_NAME = "X-KiloCode-EditorName"
HEADER_MACHINE_ID = "X-KiloCode-MachineId"
HEADER_FEATURE = "X-KiloCode-Feature"

USER_AGENT_BASE = "BrainHarness-KiloGateway/1.0"
DEFAULT_EDITOR_NAME = "Brain Harness"
TESTER_SUPPRESS_VALUE = "SUPPRESS"

ENV_EDITOR_NAME = "KILOCODE_EDITOR_NAME"
ENV_VERSION = "KILOCODE_VERSION"
ENV_FEATURE = "KILOCODE_FEATURE"


def get_user_agent() -> str:
    """Return configured or default User-Agent string."""
    version = os.getenv(ENV_VERSION)
    if version:
        return f"{USER_AGENT_BASE}/{version}"
    return USER_AGENT_BASE


def get_editor_name_header() -> str:
    """Return editor name identifier."""
    custom = os.getenv(ENV_EDITOR_NAME)
    if custom:
        return custom
    version = os.getenv(ENV_VERSION)
    if version:
        return f"{DEFAULT_EDITOR_NAME} {version}"
    return DEFAULT_EDITOR_NAME


def get_feature_header() -> str | None:
    """Return active feature tag from environment if set."""
    return os.getenv(ENV_FEATURE) or None


def build_kilo_headers(
    task_id: str | None = None,
    parent_task_id: str | None = None,
    project_id: str | None = None,
    organization_id: str | None = None,
    feature: str | None = None,
    tester_warnings_disabled_until: float | None = None,
    machine_id: str | None = None,
    custom_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Construct standard attribution headers for OpenRouter / Kilo Gateway requests."""
    resolved_feature = feature or get_feature_header()
    headers: dict[str, str] = {
        "User-Agent": get_user_agent(),
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/SpectreDeath/Brain-Harness",
        "X-Title": "Brain Harness Agent System",
        HEADER_EDITOR_NAME: get_editor_name_header(),
    }

    if resolved_feature:
        headers[HEADER_FEATURE] = resolved_feature

    if task_id:
        headers[HEADER_TASK_ID] = task_id

    if parent_task_id:
        headers[HEADER_PARENT_TASK_ID] = parent_task_id

    if organization_id:
        headers[HEADER_ORGANIZATION_ID] = organization_id
        if project_id:
            headers[HEADER_PROJECT_ID] = project_id
    elif project_id:
        headers[HEADER_PROJECT_ID] = project_id

    if tester_warnings_disabled_until and tester_warnings_disabled_until > time.time():
        headers[HEADER_TESTER] = TESTER_SUPPRESS_VALUE

    if machine_id:
        headers[HEADER_MACHINE_ID] = machine_id

    if custom_headers:
        headers.update(custom_headers)

    return headers
