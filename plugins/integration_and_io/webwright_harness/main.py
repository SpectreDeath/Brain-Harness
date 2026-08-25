"""Webwright Harness Plugin Entrypoint & Service Implementation."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.webwright_harness import (
    WEBWRIGHT_HARNESS_KEY,
    WebwrightBrowserStatus,
    WebwrightHarnessService,
    WebwrightImageQAResult,
    WebwrightLearnResult,
    WebwrightRetrieveCandidate,
    WebwrightRetrieveResult,
    WebwrightRouteResult,
    WebwrightSelfReflectionResult,
)

from .engine import WebwrightHarnessEngine

logger = structlog.get_logger(__name__)

_GLOBAL_ENGINE = WebwrightHarnessEngine()


def _get_engine() -> WebwrightHarnessEngine:
    return _GLOBAL_ENGINE


# -----------------------------------------------------------------------------
# Tool Handlers (Standalone Functions for Tool Registry)
# -----------------------------------------------------------------------------

def webwright_skill_learn(
    trajectory_dirs: list[str],
    template: str,
    library_dir: str = "skills",
) -> dict[str, Any]:
    """Synthesize reusable Python web automation skill scripts from agent trajectory runs and execution traces."""
    engine = _get_engine()
    return engine.learn_skill(trajectory_dirs=trajectory_dirs, template=template, library_dir=library_dir)


def webwright_skill_retrieve(
    task: str,
    k: int = 3,
    library_dir: str = "skills",
) -> dict[str, Any]:
    """Semantically match and rank relevant candidate skills from the skill library for a target task."""
    engine = _get_engine()
    return engine.retrieve_skills(task=task, k=k, library_dir=library_dir)


def webwright_skill_route_and_execute(
    task: str,
    start_url: str,
    library_dir: str = "skills",
    timeout_s: int = 120,
) -> dict[str, Any]:
    """Route a task to direct skill execution (with slot filling) or fallback to agent solving."""
    engine = _get_engine()
    return engine.route_and_execute(task=task, start_url=start_url, library_dir=library_dir, timeout_s=timeout_s)


def webwright_browser_session_manage(
    action: str,
    port: int = 9222,
    headless: bool = True,
) -> dict[str, Any]:
    """Manage persistent local Chromium browser daemons with DevTools remote debugging endpoints."""
    engine = _get_engine()
    return engine.manage_browser_session(action=action, port=port, headless=headless)


def webwright_image_qa(
    image_path: str,
    question: str,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """Perform high-detail multimodal visual question answering on web screenshots and DOM captures."""
    engine = _get_engine()
    return engine.image_qa(image_path=image_path, question=question, model=model)


def webwright_self_reflection(
    task: str,
    screenshots_dir: str,
    action_history: list[str],
) -> dict[str, Any]:
    """Critique and verify task success over screenshot sequences and chronological action histories."""
    engine = _get_engine()
    return engine.self_reflect(task=task, screenshots_dir=screenshots_dir, action_history=action_history)


# -----------------------------------------------------------------------------
# Plugin Class
# -----------------------------------------------------------------------------

class WebwrightHarnessPlugin(HarnessPlugin, WebwrightHarnessService):
    """Harness Plugin providing Webwright skill learning, browser daemon, and verification services."""

    name = "plugin.webwright_harness"
    version = "1.0.0"
    description = "SWE-style browser agent harness with trajectory skill learning, semantic retrieval, and browser lifecycle"
    trusted = True

    def __init__(self) -> None:
        self._engine = _get_engine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [WEBWRIGHT_HARNESS_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(WEBWRIGHT_HARNESS_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # WebwrightHarnessService Protocol Implementation
    # -------------------------------------------------------------------------

    async def learn_skill(
        self,
        trajectory_dirs: list[str],
        template: str,
        library_dir: str = "skills",
    ) -> WebwrightLearnResult:
        res = self._engine.learn_skill(trajectory_dirs=trajectory_dirs, template=template, library_dir=library_dir)
        return WebwrightLearnResult(**res)

    async def retrieve_skills(
        self,
        task: str,
        k: int = 3,
        library_dir: str = "skills",
    ) -> WebwrightRetrieveResult:
        res = self._engine.retrieve_skills(task=task, k=k, library_dir=library_dir)
        candidates = [WebwrightRetrieveCandidate(**c) for c in res["candidates"]]
        return WebwrightRetrieveResult(
            status=res["status"],
            task=res["task"],
            candidates=candidates,
            error=res["error"],
        )

    async def route_and_execute(
        self,
        task: str,
        start_url: str,
        library_dir: str = "skills",
        timeout_s: int = 120,
    ) -> WebwrightRouteResult:
        res = self._engine.route_and_execute(
            task=task, start_url=start_url, library_dir=library_dir, timeout_s=timeout_s
        )
        return WebwrightRouteResult(**res)

    async def manage_browser_session(
        self,
        action: str,
        port: int = 9222,
        headless: bool = True,
    ) -> WebwrightBrowserStatus:
        res = self._engine.manage_browser_session(action=action, port=port, headless=headless)
        return WebwrightBrowserStatus(**res)

    async def image_qa(
        self,
        image_path: str,
        question: str,
        model: str = "gpt-4o",
    ) -> WebwrightImageQAResult:
        res = self._engine.image_qa(image_path=image_path, question=question, model=model)
        return WebwrightImageQAResult(**res)

    async def self_reflect(
        self,
        task: str,
        screenshots_dir: str,
        action_history: list[str],
    ) -> WebwrightSelfReflectionResult:
        res = self._engine.self_reflect(
            task=task, screenshots_dir=screenshots_dir, action_history=action_history
        )
        return WebwrightSelfReflectionResult(**res)
