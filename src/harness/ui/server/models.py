"""Request and response DTO schemas for the UI dashboard API."""

from __future__ import annotations

from pydantic import BaseModel


class TaskRequest(BaseModel):
    task: str
    max_steps: int = 10


class PluginToggleRequest(BaseModel):
    name: str
    action: str  # "enable" or "disable"


class ToolToggleRequest(BaseModel):
    name: str
    enabled: bool | None = None


class PluginIngestRequest(BaseModel):
    source: str
    ref: str = "main"
    force: bool = False


class CreatorScaffoldRequest(BaseModel):
    name: str
    description: str = ""
    language: str = "python"
    tools: list[str] = ["execute"]
    dependencies: list[str] = []
    author: str = "Harness Developer"
    category: str = "general"
    preset: str = "general"
    isolation: str = "subprocess"
    target_dir: str | None = None
    auto_enable: bool = True


class CreatorValidateRequest(BaseModel):
    path: str
    dry_run: bool = False
    timeout: float = 15.0


class SwarmRunRequest(BaseModel):
    objective: str
    max_tokens: int = 100_000
    consensus_threshold: float = 0.66
    run_id: str | None = None


class SwarmSkillDispatchRequest(BaseModel):
    objective: str
    skills: list[str] | None = None
    max_tokens: int = 100_000
    include_verifier: bool = True
    consensus_threshold: float = 0.66
    run_id: str | None = None


__all__ = [
    "CreatorScaffoldRequest",
    "CreatorValidateRequest",
    "PluginIngestRequest",
    "PluginToggleRequest",
    "SwarmRunRequest",
    "SwarmSkillDispatchRequest",
    "TaskRequest",
    "ToolToggleRequest",
]
