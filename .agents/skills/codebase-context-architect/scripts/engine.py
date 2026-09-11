# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""Core Engine and Domain Models for Codebase Context Architecture.

Provides deep-module abstractions for:
1. Slotted, frozen domain models for verification checks and reports (Rule 12).
2. Polyglot manifest script inspection (package.json, pyproject.toml, Makefile).
3. 3-tier zero-fork configuration resolution (Rule 44).
4. Authoritative CodebaseContextEngine facade for headless CLI and API callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Union

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore

try:
    import yaml
except ModuleNotFoundError:
    yaml = None  # type: ignore

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# --- Domain Models (Rule 12: Slotted & Frozen Dataclasses) ---

@dataclass(slots=True, frozen=True)
class TokenBudgetCheck:
    """Evaluation result for an always-loaded context file token budget."""

    file_path: str
    token_count: int
    token_ceiling: int
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "token_budget",
            "file": self.file_path,
            "tokens": self.token_count,
            "ceiling": self.token_ceiling,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class PathIntegrityCheck:
    """Evaluation result verifying that an inline backtick path exists on disk."""

    file_path: str
    target_path: str
    resolved_path: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "path_existence",
            "file": self.file_path,
            "target_path": self.target_path,
            "resolved_path": self.resolved_path,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class ScriptIntegrityCheck:
    """Evaluation result verifying that a mentioned command exists in project manifests."""

    file_path: str
    raw_command: str
    runner: str
    script_name: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "script_existence",
            "file": self.file_path,
            "script": self.raw_command,
            "runner": self.runner,
            "script_name": self.script_name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class SyncDriftCheck:
    """Evaluation result verifying that generated vendor files match canonical source."""

    target_file: str
    canonical_source: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "sync_drift",
            "file": self.target_file,
            "canonical_source": self.canonical_source,
            "passed": self.passed,
            "message": self.message,
        }


CheckResult = Union[TokenBudgetCheck, PathIntegrityCheck, ScriptIntegrityCheck, SyncDriftCheck]


@dataclass(slots=True, frozen=True)
class ContextLintReport:
    """Authoritative, immutable verification report for repository context files."""

    root_path: str
    passed: bool
    checks: tuple[CheckResult, ...] = field(default_factory=tuple)
    problems_count: int = 0
    checks_count: int = 0

    @property
    def problems(self) -> tuple[CheckResult, ...]:
        """Return only checks that failed."""
        return tuple(c for c in self.checks if not c.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root_path,
            "passed": self.passed,
            "problems_count": self.problems_count,
            "checks_count": self.checks_count,
            "problems": [p.to_dict() for p in self.problems],
            "all_checks": [c.to_dict() for c in self.checks],
        }


@dataclass(slots=True, frozen=True)
class SyncResult:
    """Result of synchronizing multi-format context files from canonical source."""

    root_path: str
    in_sync: bool
    actions: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root_path,
            "in_sync": self.in_sync,
            "actions": list(self.actions),
        }


# --- Polyglot Manifest Inspector ---

class ManifestScriptInspector:
    """Extracts declared executable scripts and CLI tools across polyglot project manifests."""

    KNOWN_PYTHON_TOOLS = {"pytest", "python", "ruff", "mypy", "harness", "uv", "pip", "tox", "black", "isort"}

    @classmethod
    def extract_available_scripts(cls, root: Path) -> set[str]:
        """Extract all valid script names and CLI commands from repo manifests."""
        scripts: set[str] = set()

        # 1. package.json (Node.js)
        pkg_file = root / "package.json"
        if pkg_file.exists():
            try:
                data = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
                npm_scripts = data.get("scripts") or {}
                scripts.update(npm_scripts.keys())
                scripts.update({"test", "start", "build"})  # standard npm defaults
            except Exception:
                pass

        # 2. pyproject.toml (Python)
        pyproj_file = root / "pyproject.toml"
        if pyproj_file.exists():
            scripts.update(cls.KNOWN_PYTHON_TOOLS)
            if tomllib is not None:
                try:
                    data = tomllib.loads(pyproj_file.read_text(encoding="utf-8", errors="ignore"))
                    # [project.scripts]
                    proj_scripts = (data.get("project") or {}).get("scripts") or {}
                    scripts.update(proj_scripts.keys())
                    # [tool.poetry.scripts]
                    poetry_scripts = ((data.get("tool") or {}).get("poetry") or {}).get("scripts") or {}
                    scripts.update(poetry_scripts.keys())
                except Exception:
                    pass

        # 3. Makefile
        make_file = root / "Makefile"
        if make_file.exists():
            try:
                content = make_file.read_text(encoding="utf-8", errors="ignore")
                targets = re.findall(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE)
                scripts.update(targets)
            except Exception:
                pass

        return scripts


# --- 3-Tier Zero-Fork Configuration Resolver (Rule 44) ---

class ConfigResolver:
    """Resolves layered configuration: Project Override -> Skill Default -> Hardcoded Fallback."""

    DEFAULT_BUDGETS = {
        "AGENTS.md": 800,
        "CLAUDE.md": 300,
        ".github/copilot-instructions.md": 900,
        "src/AGENTS.md": 400,
    }
    CHARS_PER_TOKEN = 4

    @classmethod
    def resolve_config(cls, root: Path, skill_dir: Path | None = None) -> dict[str, Any]:
        config: dict[str, Any] = {
            "chars_per_token": cls.CHARS_PER_TOKEN,
            "budgets": dict(cls.DEFAULT_BUDGETS),
        }

        # 1. Skill Default config
        if skill_dir is None:
            skill_dir = root / ".agents" / "skills" / "codebase-context-architect"
        default_file = skill_dir / "config.default.yaml"
        if default_file.exists() and yaml is not None:
            try:
                parsed = yaml.safe_load(default_file.read_text(encoding="utf-8")) or {}
                if "chars_per_token" in parsed:
                    config["chars_per_token"] = parsed["chars_per_token"]
                if "budgets" in parsed and "always_loaded_files" in parsed["budgets"]:
                    for item in parsed["budgets"]["always_loaded_files"]:
                        p = item.get("path")
                        b = item.get("budget_tokens")
                        if p and b:
                            config["budgets"][p] = int(b)
            except Exception:
                pass

        # 2. Project Override config (.agents/skills.config.yaml)
        override_file = root / ".agents" / "skills.config.yaml"
        if override_file.exists() and yaml is not None:
            try:
                overrides = yaml.safe_load(override_file.read_text(encoding="utf-8")) or {}
                skill_overrides = overrides.get("codebase-context-architect") or {}
                if "chars_per_token" in skill_overrides:
                    config["chars_per_token"] = skill_overrides["chars_per_token"]
                if "budgets" in skill_overrides:
                    config["budgets"].update(skill_overrides["budgets"])
            except Exception:
                pass

        return config


# --- Semantic Path Classifier (Rule 12: Slotted & Frozen) ---

@dataclass(slots=True, frozen=True)
class SemanticPathClassifier:
    """Classifies inline backtick spans to distinguish real repository paths from MIME types and archetypes."""

    MIME_TYPE_RE = re.compile(
        r"^(?:text|application|image|audio|video|multipart|font|model)/[a-zA-Z0-9.+_-]+$"
    )
    ARCHETYPE_FILENAMES = frozenset({
        "CARD.md",
        "SKILL.md",
        "metadata.json",
        "summary.md",
        "config.default.yaml",
        "config.yaml",
        "CONTEXT.md",
        "colors.toml",
    })

    @classmethod
    def is_mime_type(cls, span: str) -> bool:
        """Check if span matches RFC media/MIME type syntax."""
        return bool(cls.MIME_TYPE_RE.match(span))

    @classmethod
    def is_archetype_template(cls, span: str) -> bool:
        """Check if span is a standalone architectural archetype template name without directory path."""
        return "/" not in span and "\\" not in span and span in cls.ARCHETYPE_FILENAMES


# --- Codebase Context Deep Engine ---

class CodebaseContextEngine:
    """Authoritative deep module engine for codebase context verification and synchronization."""

    PATH_LIKE_RE = re.compile(
        r"^(?:[\w.-]+/)+[\w.-]+(?:\.\w+)?$|"
        r"^\.?\.?/[\w.-]+|"
        r"^[\w.-]+\.(?:md|js|mjs|ts|py|json|ya?ml|sh|rs|go|txt|toml)$"
    )

    BANNER_TEMPLATE = "<!-- Generated from {source} by `python scripts/sync_context.py`. Edit {source} instead. -->"

    DEFAULT_CLAUDE_EXTRAS = """## Claude Code specific

- Use plan mode for architectural modifications or changes touching more than three files.
- Execute atomic fixes directly without ceremony.
- Delegate codebase exploration to subagents so findings return summarized rather than consuming context.
"""

    def __init__(self, root: Path | str, config: dict[str, Any] | None = None) -> None:
        self.root = Path(root).resolve()
        self.config = config or ConfigResolver.resolve_config(self.root)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token volume from raw text using configured chars_per_token heuristic."""
        cpt = self.config.get("chars_per_token", 4)
        return math.ceil(len(text) / cpt) if text else 0

    def strip_fenced_blocks(self, text: str) -> str:
        """Strip markdown code fences so illustrative snippet examples are not evaluated as real paths."""
        return re.sub(r"```[\s\S]*?```", "", text)

    def extract_inline_spans(self, text: str) -> list[str]:
        """Extract backtick code spans from prose text."""
        prose = self.strip_fenced_blocks(text)
        return [m.group(1).strip() for m in re.finditer(r"`([^`\n]+)`", prose)]

    def looks_like_path(self, span: str) -> bool:
        """Determine whether an inline backtick span resembles a repository filesystem path."""
        if span.startswith(("-", "npm ", "node ", "python ", "pytest ", "git ", "ruff ", "cargo ", "make ")):
            return False
        if " " in span or span in {"const", "var", "let", "return", "true", "false", "null", "undefined"}:
            return False
        if SemanticPathClassifier.is_mime_type(span):
            return False
        if SemanticPathClassifier.is_archetype_template(span):
            return False
        return bool(self.PATH_LIKE_RE.match(span))

    def lint(self) -> ContextLintReport:
        """Execute complete 4-check context verification suite."""
        checks: list[CheckResult] = []
        budgets: dict[str, int] = self.config.get("budgets") or ConfigResolver.DEFAULT_BUDGETS

        # 1. Token budget checks
        for rel_path, ceiling in budgets.items():
            target = self.root / rel_path
            if not target.exists():
                continue
            text = target.read_text(encoding="utf-8", errors="ignore")
            tok_count = self.estimate_tokens(text)
            passed = tok_count <= ceiling
            msg = f"{rel_path}: {tok_count}/{ceiling} tokens" + (" (EXCEEDED)" if not passed else " (OK)")
            checks.append(
                TokenBudgetCheck(
                    file_path=rel_path,
                    token_count=tok_count,
                    token_ceiling=ceiling,
                    passed=passed,
                    message=msg,
                )
            )

        # 2. Path & Script checks across markdown context files
        available_scripts = ManifestScriptInspector.extract_available_scripts(self.root)
        md_files = [self.root / "AGENTS.md", self.root / "CLAUDE.md"]
        if (self.root / ".github").exists():
            md_files.extend((self.root / ".github").glob("*.md"))
        if (self.root / "src").exists():
            md_files.extend((self.root / "src").glob("**/*.md"))
        if (self.root / "docs").exists():
            md_files.extend((self.root / "docs").glob("**/*.md"))

        for mf in md_files:
            if not mf.exists():
                continue
            rel_file = str(mf.relative_to(self.root)).replace("\\", "/")
            text = mf.read_text(encoding="utf-8", errors="ignore")
            spans = self.extract_inline_spans(text)

            for span in spans:
                # Path check
                if self.looks_like_path(span):
                    target_root = self.root / span
                    target_rel = mf.parent / span
                    if not target_root.exists() and not target_rel.exists():
                        checks.append(
                            PathIntegrityCheck(
                                file_path=rel_file,
                                target_path=span,
                                resolved_path=str(target_root),
                                passed=False,
                                message=f"{rel_file} points at non-existent path: `{span}`",
                            )
                        )

                # Script check
                npm_m = re.match(r"^npm run ([\w:-]+)$", span) or re.match(r"^npm (test|start|build)$", span)
                if npm_m:
                    s_name = npm_m.group(1)
                    if available_scripts and s_name not in available_scripts:
                        checks.append(
                            ScriptIntegrityCheck(
                                file_path=rel_file,
                                raw_command=span,
                                runner="npm",
                                script_name=s_name,
                                passed=False,
                                message=f"{rel_file} mentions script not in package.json: `{span}`",
                            )
                        )

        # 3. Sync drift checks
        canonical = self.root / "AGENTS.md"
        if canonical.exists():
            claude_file = self.root / "CLAUDE.md"
            if claude_file.exists():
                content = claude_file.read_text(encoding="utf-8", errors="ignore")
                if "Generated from AGENTS.md" in content:
                    if "@AGENTS.md" not in content and "@./AGENTS.md" not in content:
                        checks.append(
                            SyncDriftCheck(
                                target_file="CLAUDE.md",
                                canonical_source="AGENTS.md",
                                passed=False,
                                message="CLAUDE.md missing @AGENTS.md pointer import reference",
                            )
                        )

            copilot_file = self.root / ".github" / "copilot-instructions.md"
            if copilot_file.exists():
                content = copilot_file.read_text(encoding="utf-8", errors="ignore")
                if "Generated from AGENTS.md" in content:
                    source_content = canonical.read_text(encoding="utf-8", errors="ignore")
                    sample = source_content.strip()[:80]
                    if sample and sample not in content:
                        checks.append(
                            SyncDriftCheck(
                                target_file=".github/copilot-instructions.md",
                                canonical_source="AGENTS.md",
                                passed=False,
                                message=".github/copilot-instructions.md is out of sync with AGENTS.md",
                            )
                        )

        problems = [c for c in checks if not c.passed]
        return ContextLintReport(
            root_path=str(self.root),
            passed=len(problems) == 0,
            checks=tuple(checks),
            problems_count=len(problems),
            checks_count=len(checks),
        )

    def render_claude_md(self, source_name: str = "AGENTS.md") -> str:
        """Render CLAUDE.md using pointer syntax to minimize token overhead."""
        banner = self.BANNER_TEMPLATE.format(source=source_name)
        return f"{banner}\n\n@{source_name}\n\n{self.DEFAULT_CLAUDE_EXTRAS.strip()}\n"

    def render_copilot_md(self, source_name: str, source_content: str) -> str:
        """Render .github/copilot-instructions.md inlining the canonical source."""
        banner = self.BANNER_TEMPLATE.format(source=source_name)
        return f"{banner}\n\n{source_content.strip()}\n"

    def sync(self, source_rel: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
        """Synchronize downstream context files against canonical source."""
        source_file = self.root / source_rel
        if not source_file.exists():
            return SyncResult(root_path=str(self.root), in_sync=False, actions=(f"Canonical source missing: {source_file}",))

        source_content = source_file.read_text(encoding="utf-8", errors="ignore")
        actions: list[str] = []
        has_drift = False

        targets = [
            ("CLAUDE.md", self.render_claude_md(source_rel)),
            (".github/copilot-instructions.md", self.render_copilot_md(source_rel, source_content)),
        ]

        for rel_path, expected_content in targets:
            target_file = self.root / rel_path
            exists = target_file.exists()
            current_content = target_file.read_text(encoding="utf-8", errors="ignore") if exists else ""

            if current_content != expected_content:
                has_drift = True
                if dry_run:
                    actions.append(f"[DRIFT] {rel_path} differs from generated canonical source.")
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(expected_content, encoding="utf-8")
                    actions.append(f"[UPDATED] Synchronized {rel_path} from {source_rel}")
            else:
                if not dry_run:
                    actions.append(f"[OK] {rel_path} already in sync.")

        return SyncResult(
            root_path=str(self.root),
            in_sync=not has_drift,
            actions=tuple(actions),
        )


__all__ = [
    "CheckResult",
    "CodebaseContextEngine",
    "ConfigResolver",
    "ContextLintReport",
    "ManifestScriptInspector",
    "PathIntegrityCheck",
    "ScriptIntegrityCheck",
    "SemanticPathClassifier",
    "SyncDriftCheck",
    "SyncResult",
    "TokenBudgetCheck",
]
