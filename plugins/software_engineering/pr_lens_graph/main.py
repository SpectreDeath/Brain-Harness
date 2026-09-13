"""PR Lens Graph Plugin entrypoint for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.pr_lens import (
    PR_LENS_GRAPH_SERVICE_KEY,
    PrLensAnalysisData,
    PrLensCommentData,
    PrLensDiffData,
    PrLensGraphService,
    PrLensRenderData,
    PrLensValidationData,
)

try:
    from plugins.software_engineering.pr_lens_graph.service import (
        PrLensGraphServiceImpl,
    )
except ImportError:
    from service import PrLensGraphServiceImpl  # type: ignore

logger = structlog.get_logger(__name__)


class PrLensGraphPlugin(HarnessPlugin, PrLensGraphService):
    """Brain Harness Plugin providing PR Lens graph validation, rendering, diffing, and commenting."""

    name = "plugin.pr_lens_graph"
    version = "1.0.0"
    description = "PR Lens standalone animated SVG architecture diagrams, graph validation, and diff visualization"
    trusted = False

    def __init__(self) -> None:
        super().__init__()
        self._impl = PrLensGraphServiceImpl()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PR_LENS_GRAPH_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(PR_LENS_GRAPH_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # PrLensGraphService Protocol Delegation
    # -------------------------------------------------------------------------

    def validate(self, graph_doc: dict[str, Any]) -> PrLensValidationData:
        return self._impl.validate(graph_doc)

    def render(
        self,
        graph_doc: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> PrLensRenderData:
        return self._impl.render(graph_doc, config)

    def diff(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        repo_path: str | None = None,
    ) -> PrLensDiffData:
        return self._impl.diff(base_ref, head_ref, repo_path)

    def analyze(
        self,
        diff_text: str,
        overlay_map: dict[str, Any] | None = None,
    ) -> PrLensAnalysisData:
        return self._impl.analyze(diff_text, overlay_map)

    def comment(
        self,
        analysis: dict[str, Any],
        svg_content: str,
    ) -> PrLensCommentData:
        return self._impl.comment(analysis, svg_content)


# Export module-level singleton per Rule 45
plugin = PrLensGraphPlugin()


# Top-level entrypoint functions declared in plugin.json
def pr_lens_validate(graph_doc: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    res = plugin.validate(graph_doc)
    return res.model_dump()


def pr_lens_render(
    graph_doc: dict[str, Any], config: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    res = plugin.render(graph_doc, config)
    return res.model_dump()


def pr_lens_diff(
    base_ref: str = "HEAD~1",
    head_ref: str = "HEAD",
    repo_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    res = plugin.diff(base_ref=base_ref, head_ref=head_ref, repo_path=repo_path)
    return res.model_dump()


def pr_lens_analyze(
    diff_text: str, overlay_map: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    res = plugin.analyze(diff_text=diff_text, overlay_map=overlay_map)
    return res.model_dump()


def pr_lens_comment(
    analysis: dict[str, Any], svg_content: str, **kwargs: Any
) -> dict[str, Any]:
    res = plugin.comment(analysis=analysis, svg_content=svg_content)
    return res.model_dump()
