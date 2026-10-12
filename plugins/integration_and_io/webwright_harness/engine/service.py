"""WebwrightHarnessEngine composite service class integrating sub-mixins."""

from __future__ import annotations

from pathlib import Path

from plugins.integration_and_io.webwright_harness.engine.browser import BrowserDaemonMixin
from plugins.integration_and_io.webwright_harness.engine.learning import SkillLearningMixin
from plugins.integration_and_io.webwright_harness.engine.models import BrowserDaemonState
from plugins.integration_and_io.webwright_harness.engine.reflection import ReflectionMixin
from plugins.integration_and_io.webwright_harness.engine.retrieval import SkillRetrievalMixin
from plugins.integration_and_io.webwright_harness.engine.routing import SkillRoutingMixin


class WebwrightHarnessEngine(
    SkillLearningMixin,
    SkillRetrievalMixin,
    SkillRoutingMixin,
    BrowserDaemonMixin,
    ReflectionMixin,
):
    """Production-grade Webwright engine for skill learning, routing, browser management, and evaluation."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._daemons: dict[int, BrowserDaemonState] = {}
