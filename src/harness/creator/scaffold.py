"""Plugin scaffolding engine — unified code, manifest, and test generation.

Provides a deep, authoritative seam for creating structured, multi-language
plugin projects with manifest configuration, tool stubs, dependencies,
automated test harnesses, auxiliary file generation, and validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

if TYPE_CHECKING:
    from harness.creator.validator import ValidationReport

logger = structlog.get_logger()


@dataclass
class ScaffoldOptions:
    """Configuration options for scaffolding a new plugin project."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    language: str = "python"  # "python", "javascript", "typescript"
    isolation: IsolationMode = IsolationMode.SUBPROCESS
    tools: list[str] = field(default_factory=lambda: ["execute"])
    dependencies: list[str] = field(default_factory=list)
    include_tests: bool = True
    include_quickstart: bool = True
    author: str = "Harness Developer"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    preset: str = "general"  # "general", "tool", "service", "api_wrapper", "agentic_workflow", "container"
    entrypoints: list[EntrypointSpec] | None = None
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    extra_files: dict[str, str] = field(default_factory=dict)
    auto_validate: bool = False

    @classmethod
    def from_kwargs(
        cls,
        options: ScaffoldOptions | None = None,
        *,
        name: str | None = None,
        target_dir: Path | str | None = None,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        author: str = "Harness Developer",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        tags: list[str] | None = None,
        auto_validate: bool = False,
        **extra_kwargs: Any,
    ) -> ScaffoldOptions:
        """Construct or merge ScaffoldOptions from caller arguments."""
        if options is not None:
            return options

        resolved_name = name or (Path(target_dir).name if target_dir else "untitled")
        return cls(
            name=resolved_name,
            description=description,
            language=language,
            tools=tools or ["execute"],
            dependencies=dependencies or [],
            author=author,
            category=category,
            preset=preset,
            isolation=isolation,
            tags=tags or [],
            auto_validate=auto_validate,
            **extra_kwargs,
        )


@dataclass
class ScaffoldResult(os.PathLike[str]):
    """Structured result returned from plugin scaffolding."""

    path: Path
    manifest: PluginManifest
    generated_files: list[Path] = field(default_factory=list)
    validation_report: ValidationReport | None = None

    @property
    def files_count(self) -> int:
        return len(self.generated_files)

    def __fspath__(self) -> str:
        return str(self.path)

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f"ScaffoldResult(path={self.path!r}, files_count={self.files_count})"

    def __truediv__(self, other: str | Path) -> Path:
        return self.path / other

    def __rtruediv__(self, other: str | Path) -> Path:
        return Path(other) / self.path

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ScaffoldResult):
            return self.path == other.path
        if isinstance(other, (Path, str)):
            return self.path == Path(other)
        return False

    def exists(self) -> bool:
        return self.path.exists()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "manifest": self.manifest.model_dump(),
            "generated_files": [str(f) for f in self.generated_files],
            "files_count": self.files_count,
            "validation_report": self.validation_report.to_dict() if self.validation_report is not None else None,
        }


class PluginScaffoldEngine:
    """Authoritative code generation and template engine for Harness plugins."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self.templates_dir = Path(templates_dir).resolve() if templates_dir else None

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        """Create a validated PluginManifest from scaffold options."""
        from harness.creator.archetypes import ArchetypeRegistry

        archetype = ArchetypeRegistry.get(options.preset)
        return archetype.generate_manifest(options)

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        """Generate entrypoint boilerplate source code with tool stubs."""
        # Check template override first
        if self.templates_dir:
            ext = ".py" if options.language == "python" else (".ts" if options.language == "typescript" else ".js")
            tmpl_file = self.templates_dir / f"entrypoint_{options.preset}{ext}"
            if tmpl_file.exists():
                return tmpl_file.read_text(encoding="utf-8")

        from harness.creator.archetypes import ArchetypeRegistry

        archetype = ArchetypeRegistry.get(options.preset)
        return archetype.generate_entrypoint_code(options)

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        """Generate test harness code for the scaffolded plugin."""
        from harness.creator.archetypes import ArchetypeRegistry

        archetype = ArchetypeRegistry.get(options.preset)
        return archetype.generate_test_code(options)

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        """Generate dependency configuration file (filename and content)."""
        from harness.creator.archetypes import ArchetypeRegistry

        archetype = ArchetypeRegistry.get(options.preset)
        return archetype.generate_project_config(options)

    def generate_extra_files(self, options: ScaffoldOptions) -> dict[str, str]:
        """Generate auxiliary archetype and user files (rel_path -> content)."""
        from harness.creator.archetypes import ArchetypeRegistry

        archetype = ArchetypeRegistry.get(options.preset)
        files = dict(archetype.generate_extra_files(options))
        files.update(options.extra_files)
        return files

    def _write_scaffold_files(
        self, target_dir: Path, opts: ScaffoldOptions
    ) -> tuple[PluginManifest, list[Path]]:
        """Internal synchronous file generation logic."""
        target_dir.mkdir(parents=True, exist_ok=True)
        generated_files: list[Path] = []

        # 1. Manifest
        manifest = self.generate_manifest(opts)
        manifest_path = target_dir / "plugin.json"
        manifest.to_file(manifest_path)
        generated_files.append(manifest_path)

        # 2. Entrypoint source code
        entrypoint_file = target_dir / manifest.entrypoint
        entrypoint_file.parent.mkdir(parents=True, exist_ok=True)
        entrypoint_file.write_text(self.generate_entrypoint_code(opts), encoding="utf-8")
        generated_files.append(entrypoint_file)

        # 3. Quickstart Documentation
        if opts.include_quickstart:
            quickstart_path = target_dir / "QUICKSTART.md"
            quickstart_path.write_text(manifest.format_quickstart(), encoding="utf-8")
            generated_files.append(quickstart_path)

        # 4. Dependency Configuration
        config_filename, config_content = self.generate_project_config(opts)
        config_path = target_dir / config_filename
        config_path.write_text(config_content, encoding="utf-8")
        generated_files.append(config_path)

        # 5. TypeScript Config (if ts)
        if opts.language == "typescript":
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2022",
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                }
            }
            ts_path = target_dir / "tsconfig.json"
            ts_path.write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")
            generated_files.append(ts_path)

        # 6. Unit Tests
        if opts.include_tests:
            tests_dir = target_dir / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            test_file = (
                tests_dir / "test_plugin.py"
                if opts.language == "python"
                else tests_dir / "plugin.test.js"
            )
            test_file.write_text(self.generate_test_code(opts), encoding="utf-8")
            generated_files.append(test_file)

        # 7. Auxiliary / Extra Archetype Files
        extra_files = self.generate_extra_files(opts)
        for rel_path, content in extra_files.items():
            dest = target_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            generated_files.append(dest)

        return manifest, generated_files

    def scaffold(
        self,
        target_dir: Path,
        options: ScaffoldOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        category: str = "general",
        preset: str = "general",
        auto_validate: bool = False,
        **extra_kwargs: Any,
    ) -> ScaffoldResult:
        """Scaffold a complete plugin directory with all boilerplate files synchronously."""
        opts = ScaffoldOptions.from_kwargs(
            options=options,
            name=name,
            target_dir=target_dir,
            description=description,
            language=language,
            tools=tools,
            dependencies=dependencies,
            category=category,
            preset=preset,
            auto_validate=auto_validate,
            **extra_kwargs,
        )

        manifest, generated_files = self._write_scaffold_files(target_dir, opts)

        validation_report = None
        if opts.auto_validate:
            from harness.creator.validator import PluginValidator
            try:
                validation_report = PluginValidator.validate_sync(target_dir, dry_run=False)
            except Exception as e:
                logger.warning("Scaffold auto-validation encountered issue", error=str(e))

        logger.info(
            "Scaffolded plugin project",
            path=str(target_dir),
            name=opts.name,
            language=opts.language,
            tools=opts.tools,
            preset=opts.preset,
            files_count=len(generated_files),
        )

        return ScaffoldResult(
            path=target_dir,
            manifest=manifest,
            generated_files=generated_files,
            validation_report=validation_report,
        )

    async def scaffold_async(
        self,
        target_dir: Path,
        options: ScaffoldOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        category: str = "general",
        preset: str = "general",
        auto_validate: bool = False,
        **extra_kwargs: Any,
    ) -> ScaffoldResult:
        """Scaffold a complete plugin directory asynchronously with native coroutine validation."""
        opts = ScaffoldOptions.from_kwargs(
            options=options,
            name=name,
            target_dir=target_dir,
            description=description,
            language=language,
            tools=tools,
            dependencies=dependencies,
            category=category,
            preset=preset,
            auto_validate=auto_validate,
            **extra_kwargs,
        )

        manifest, generated_files = self._write_scaffold_files(target_dir, opts)

        validation_report = None
        if opts.auto_validate:
            from harness.creator.validator import PluginValidator
            try:
                validation_report = await PluginValidator.validate(target_dir, dry_run=False)
            except Exception as e:
                logger.warning("Scaffold async auto-validation encountered issue", error=str(e))

        logger.info(
            "Scaffolded plugin project (async)",
            path=str(target_dir),
            name=opts.name,
            language=opts.language,
            tools=opts.tools,
            preset=opts.preset,
            files_count=len(generated_files),
        )

        return ScaffoldResult(
            path=target_dir,
            manifest=manifest,
            generated_files=generated_files,
            validation_report=validation_report,
        )


__all__ = [
    "PluginScaffoldEngine",
    "ScaffoldOptions",
    "ScaffoldResult",
]
