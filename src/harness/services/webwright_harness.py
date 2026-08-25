"""Webwright Harness service protocol, typed result models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class WebwrightLearnResult(BaseModel):
    """Result of learning a skill from agent execution trajectories."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    skill_id: str | None = Field(default=None, description="Generated unique skill identifier")
    file_path: str | None = Field(default=None, description="Path where skill code was written")
    signature: dict[str, Any] = Field(default_factory=dict, description="Skill parameter signatures")
    output_schema: dict[str, Any] = Field(default_factory=dict, description="Inferred output JSON schema")
    error: str | None = Field(default=None, description="Error explanation if failed")


class WebwrightRetrieveCandidate(BaseModel):
    """A candidate skill matched by semantic search."""

    skill_id: str = Field(..., description="Skill identifier")
    score: float = Field(..., description="Relevance score (0.0 - 1.0)")
    reason: str = Field(default="", description="Relevance rationale")
    template: str = Field(default="", description="Skill prompt template")


class WebwrightRetrieveResult(BaseModel):
    """Result of retrieving relevant skills for a task."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    task: str = Field(..., description="Queried task prompt")
    candidates: list[WebwrightRetrieveCandidate] = Field(default_factory=list, description="Ranked matching skills")
    error: str | None = Field(default=None, description="Error explanation if failed")


class WebwrightRouteResult(BaseModel):
    """Result of routing a task to direct skill execution or agent fallback."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    decision: str = Field(..., description="Routing decision: run, adapt, or skip")
    skill_id: str | None = Field(default=None, description="Matched skill ID if applicable")
    filled_params: dict[str, Any] = Field(default_factory=dict, description="Extracted slot parameters")
    result: Any | None = Field(default=None, description="Output returned from executed skill")
    returncode: int = Field(default=0, description="Process returncode")
    error: str | None = Field(default=None, description="Error explanation if execution failed")


class WebwrightBrowserStatus(BaseModel):
    """Status of persistent local Chromium browser daemon."""

    status: str = Field(default="ok", description="Status indicator (ok, not_running, error)")
    pid: int | None = Field(default=None, description="Process ID of Chromium")
    cdp_url: str | None = Field(default=None, description="DevTools WebSocket endpoint URL")
    port: int = Field(default=9222, description="Debugging port")
    user_data_dir: str | None = Field(default=None, description="Path to profile data dir")
    error: str | None = Field(default=None, description="Error message if operation failed")


class WebwrightImageQAResult(BaseModel):
    """Result of multimodal vision question answering on a web screenshot."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    image_path: str = Field(..., description="Input image path")
    question: str = Field(..., description="Question evaluated")
    answer: str = Field(..., description="VLM answer")
    confidence: float = Field(default=1.0, description="Confidence score (0.0 - 1.0)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Model metadata")
    error: str | None = Field(default=None, description="Error explanation if failed")


class WebwrightSelfReflectionResult(BaseModel):
    """Result of evaluating task success across screenshot sequence and action history."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    verdict: str = Field(..., description="Verdict: success, failure, or partial")
    confidence: float = Field(default=1.0, description="Confidence assessment (0.0 - 1.0)")
    reason: str = Field(default="", description="Detailed rationale")
    critique: list[str] = Field(default_factory=list, description="Actionable observations & critique items")
    error: str | None = Field(default=None, description="Error explanation if failed")


@runtime_checkable
class WebwrightHarnessService(Protocol):
    """Protocol for Webwright web agent skill synthesis, browser lifecycle, and multimodal evaluation."""

    async def learn_skill(
        self,
        trajectory_dirs: list[str],
        template: str,
        library_dir: str = "skills",
    ) -> WebwrightLearnResult:
        """Synthesize reusable Python web automation skill scripts from trajectory runs."""
        ...

    async def retrieve_skills(
        self,
        task: str,
        k: int = 3,
        library_dir: str = "skills",
    ) -> WebwrightRetrieveResult:
        """Semantically match and rank relevant candidate skills from the skill library for a target task."""
        ...

    async def route_and_execute(
        self,
        task: str,
        start_url: str,
        library_dir: str = "skills",
        timeout_s: int = 120,
    ) -> WebwrightRouteResult:
        """Route a task to direct skill execution (with slot filling) or fallback to agent solving."""
        ...

    async def manage_browser_session(
        self,
        action: str,
        port: int = 9222,
        headless: bool = True,
    ) -> WebwrightBrowserStatus:
        """Manage persistent local Chromium browser daemons with DevTools remote debugging endpoints."""
        ...

    async def image_qa(
        self,
        image_path: str,
        question: str,
        model: str = "gpt-4o",
    ) -> WebwrightImageQAResult:
        """Perform multimodal visual question answering on web screenshots and DOM captures."""
        ...

    async def self_reflect(
        self,
        task: str,
        screenshots_dir: str,
        action_history: list[str],
    ) -> WebwrightSelfReflectionResult:
        """Critique and verify task success over execution screenshots and chronological action logs."""
        ...


WEBWRIGHT_HARNESS_KEY: ServiceKey[WebwrightHarnessService] = ServiceKey("service.webwright_harness")
