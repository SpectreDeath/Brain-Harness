"""Unified Plugin Synthesis Engine — authoritative seam for plugin and skill generation.

Consolidates:
    - Archetype-based scaffolding (ArchetypeRegistry)
    - Dynamic in-memory / prompt-driven synthesis (DynamicPluginBuilder)
    - Standard template scaffolding (PluginScaffoldEngine)
    - High-precision agent skill authoring (SkillScaffoldEngine)
    - Automated diagnostic validation and remediation
"""

from __future__ import annotations

import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.creator.archetypes import ArchetypeRegistry
from harness.creator.dynamic import DynamicPluginBuilder, DynamicPythonPlugin
from harness.creator.scaffold import (
    PluginScaffoldEngine,
    ScaffoldOptions,
    ScaffoldResult,
)
from harness.creator.skills import (
    SkillOptions,
    SkillResult,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import (
    PluginValidator,
    ValidationReport,
)
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode

logger = structlog.get_logger()


class SynthesisMode(str, Enum):
    """Synthesis generation modality."""

    ARCHETYPE = "archetype"
    DYNAMIC = "dynamic"
    SCAFFOLD = "scaffold"
    SKILL = "skill"


class SynthesisRequest(BaseModel):
    """Unified specification request for synthesizing plugins or skills."""

    name: str = Field(..., description="Plugin or skill name identifier")
    mode: SynthesisMode = Field(default=SynthesisMode.ARCHETYPE, description="Synthesis modality")
    target_dir: str | None = Field(default=None, description="Optional target directory path")
    description: str = Field(default="", description="Plugin or skill description")
    language: str = Field(default="python", description="Target programming language")
    preset: str = Field(default="general", description="Archetype or preset name")
    tools: list[str] = Field(default_factory=lambda: ["execute"], description="Tool names to generate")
    dependencies: list[str] = Field(default_factory=list, description="Third-party package dependencies")
    author: str = Field(default="Harness Developer", description="Author attribution string")
    category: str = Field(default="general", description="Domain classification category")
    isolation: str = Field(default="subprocess", description="Subprocess or inprocess isolation")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")
    code: str = Field(default="", description="Raw python code for dynamic in-memory plugins")
    triggers: list[str] = Field(default_factory=list, description="Trigger phrases for skill scaffolding")
    auto_validate: bool = Field(default=True, description="Whether to execute validation after synthesis")
    remediate: bool = Field(default=False, description="Whether to auto-repair validation defects")


class SynthesisResult(BaseModel):
    """Standardized output returned from the PluginSynthesisEngine."""

    status: str = Field(default="ok", description="ok or error")
    mode: SynthesisMode = Field(..., description="Synthesis modality used")
    name: str = Field(..., description="Generated plugin or skill name")
    path: str = Field(..., description="Target output directory path")
    generated_files: list[str] = Field(default_factory=list, description="List of generated file paths")
    validation_report: dict[str, Any] | None = Field(default=None, description="Validation report dict")
    error_message: str | None = Field(default=None, description="Error reason if failed")


@runtime_checkable
class CreatorService(Protocol):
    """Protocol for the authoritative Harness Plugin and Skill Creator service."""

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesize a new plugin or skill based on the unified request specification."""
        ...

    async def validate(
        self,
        path: str | Path,
        *,
        dry_run: bool = False,
        remediate: bool = False,
    ) -> ValidationReport:
        """Validate a plugin or skill directory."""
        ...

    def list_archetypes(self) -> list[dict[str, str]]:
        """List all registered archetype templates."""
        ...


CREATOR_SERVICE_KEY: ServiceKey[CreatorService] = ServiceKey("service.creator")


class PluginSynthesisEngine(CreatorService):
    """Authoritative execution engine for unified plugin and skill synthesis."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._scaffold_engine = PluginScaffoldEngine(templates_dir=templates_dir)

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesize a new plugin or skill based on the unified request specification."""
        clean_name = request.name.strip().lower().replace("_", "-")

        try:
            if request.mode == SynthesisMode.SKILL:
                return await self._synthesize_skill(request, clean_name)
            elif request.mode == SynthesisMode.DYNAMIC:
                return await self._synthesize_dynamic(request, clean_name)
            else:
                return await self._synthesize_scaffold(request, clean_name)
        except Exception as e:
            logger.error("Synthesis failed", name=request.name, mode=request.mode.value, error=str(e))
            return SynthesisResult(
                status="error",
                mode=request.mode,
                name=clean_name,
                path=request.target_dir or "",
                error_message=str(e),
            )

    async def _synthesize_skill(self, request: SynthesisRequest, clean_name: str) -> SynthesisResult:
        """Scaffold an agent skill with SKILL.md and CARD.md specifications."""
        out_dir = Path(request.target_dir) if request.target_dir else Path(".agents") / "skills" / clean_name
        opts = SkillOptions(
            name=clean_name,
            description=request.description,
            category=request.category,
            triggers=request.triggers,
            auto_validate=request.auto_validate,
        )
        res: SkillResult = SkillScaffoldEngine.scaffold(out_dir, options=opts)

        val_report_dict = None
        if request.auto_validate:
            val_report = SkillValidator.validate(out_dir)
            val_report_dict = val_report.to_dict()

        return SynthesisResult(
            status="ok",
            mode=SynthesisMode.SKILL,
            name=clean_name,
            path=str(res.path),
            generated_files=[str(f) for f in res.generated_files],
            validation_report=val_report_dict,
        )

    async def _synthesize_dynamic(self, request: SynthesisRequest, clean_name: str) -> SynthesisResult:
        """Create a dynamic in-memory plugin and optionally export to disk."""
        out_dir = Path(request.target_dir) if request.target_dir else Path("plugins") / clean_name
        code_body = request.code.strip() if request.code else "def execute() -> str:\n    return 'ok'\n"
        dyn_plugin = DynamicPluginBuilder.from_code(clean_name, code_body)

        scaffold_res = dyn_plugin.export_project(out_dir)

        val_report_dict = None
        if request.auto_validate:
            val_report = await PluginValidator.validate(out_dir)
            val_report_dict = val_report.to_dict()

        return SynthesisResult(
            status="ok",
            mode=SynthesisMode.DYNAMIC,
            name=clean_name,
            path=str(scaffold_res.path),
            generated_files=[str(f) for f in scaffold_res.generated_files],
            validation_report=val_report_dict,
        )

    async def _synthesize_scaffold(self, request: SynthesisRequest, clean_name: str) -> SynthesisResult:
        """Scaffold a plugin project directory from an archetype or standard template."""
        out_dir = Path(request.target_dir) if request.target_dir else Path("plugins") / clean_name

        iso_mode = IsolationMode.SUBPROCESS
        try:
            iso_mode = IsolationMode(request.isolation.lower())
        except ValueError:
            pass

        options = ScaffoldOptions(
            name=clean_name,
            description=request.description,
            language=request.language.lower(),
            preset=request.preset.lower(),
            tools=request.tools,
            dependencies=request.dependencies,
            author=request.author,
            category=request.category,
            isolation=iso_mode,
            tags=request.tags,
            auto_validate=request.auto_validate,
        )

        scaffold_res: ScaffoldResult = self._scaffold_engine.scaffold(out_dir, options=options)

        val_report_dict = None
        if request.auto_validate:
            val_report = await PluginValidator.validate(out_dir)
            if not val_report.valid and request.remediate:
                val_report = await PluginValidator.remediate(out_dir)
            val_report_dict = val_report.to_dict()

        return SynthesisResult(
            status="ok",
            mode=request.mode,
            name=clean_name,
            path=str(scaffold_res.path),
            generated_files=[str(f) for f in scaffold_res.generated_files],
            validation_report=val_report_dict,
        )

    async def validate(
        self,
        path: str | Path,
        *,
        dry_run: bool = False,
        remediate: bool = False,
    ) -> ValidationReport:
        """Validate a plugin or skill directory."""
        target = Path(path).resolve()
        if (target / "SKILL.md").exists():
            return SkillValidator.validate(target)
        if remediate:
            return await PluginValidator.remediate(target)
        return await PluginValidator.validate(target, dry_run=dry_run)

    def list_archetypes(self) -> list[dict[str, str]]:
        """List all available archetype templates."""
        return ArchetypeRegistry.list_archetypes()


class CreatorPlugin(HarnessPlugin):
    """In-process Harness plugin providing CreatorService."""

    name = "builtin.creator"
    version = "1.0.0"
    description = "Authoritative unified plugin and skill synthesis and validation engine"
    trusted = True

    def __init__(self) -> None:
        self._engine = PluginSynthesisEngine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CREATOR_SERVICE_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CREATOR_SERVICE_KEY, self._engine)

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass
