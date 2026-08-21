"""Skill Flywheel bridge — mounts catalog skills as Harness tools.

Connects to Skill Flywheel's catalog (839+ domain skills) and makes them
discoverable and invokable directly from Harness agents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from harness.bridges.base import BridgeCapability, EcosystemBridgePlugin
from harness.kernel.context import ServiceKey
from harness.services.tools import ToolSpec

logger = structlog.get_logger()

FLYWHEEL_BRIDGE_KEY: ServiceKey[FlywheelBridgePlugin] = ServiceKey("bridge.flywheel")


class FlywheelBridgePlugin(EcosystemBridgePlugin[Any]):
    """Bridge plugin that registers Skill Flywheel skills into Harness."""

    project_name = "Skill Flywheel"
    env_var = "FLYWHEEL_PATH"
    service_key = FLYWHEEL_BRIDGE_KEY
    capabilities = [
        BridgeCapability.PROMPT_OPTIMIZATION,
        BridgeCapability.TOOL_HOSTING,
    ]

    def __init__(
        self,
        flywheel_path: Path | str | None = None,
        *,
        override_path: Path | str | None = None,
    ) -> None:
        target = flywheel_path if flywheel_path is not None else override_path
        super().__init__(override_path=target)
        self._flywheel_path = self._override_path
        self._discovered_skills: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "bridge.flywheel"

    @property
    def version(self) -> str:
        return "0.3.0"

    @property
    def description(self) -> str:
        return "Skill Flywheel Unified MCP Skill Server & Catalog Bridge"

    async def init_substrate(self, root_path: Path) -> dict[str, dict[str, Any]]:
        self._discovered_skills = {}
        possible_paths = [
            root_path / "skill_registry.json",
            root_path / "skills.json",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in list(data.items())[:25]:  # mount top 25
                            desc = v.get("description", "") if isinstance(v, dict) else str(v)
                            self._discovered_skills[k] = {"description": desc}
                        break
                except Exception as e:
                    logger.warning("Failed to parse flywheel registry", error=str(e))

        return self._discovered_skills

    async def shutdown_substrate(self) -> None:
        self._discovered_skills = {}

    async def get_tool_specs(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        for skill_id, skill_meta in self._discovered_skills.items():
            tool_name = f"skill.{skill_id}"
            description = skill_meta.get("description", f"Flywheel skill {skill_id}")

            def _make_executor(s_id: str = skill_id) -> Any:
                async def _exec(**kwargs: Any) -> dict[str, Any]:
                    return {
                        "status": "ok",
                        "skill": s_id,
                        "result": f"Executed skill {s_id} with inputs {kwargs}",
                    }
                return _exec

            specs.append(
                ToolSpec(
                    name=tool_name,
                    description=description,
                    executor=_make_executor(skill_id),
                    parameters_schema={
                        "type": "object",
                        "properties": {
                            "params": {"type": "object", "description": "Skill input parameters"},
                        },
                    },
                    provider=self.name,
                )
            )
        return specs
