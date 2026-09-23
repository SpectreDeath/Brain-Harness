"""Hugging Face Doc Builder service protocol, typed models, and authoritative engine.

Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
Rule 49: Authoritative in-memory domain engine for micro-kernel IoC elevation.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import importlib.machinery
import inspect
import os
import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)

# Rule 23: UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Slotted & Frozen Dataclass Domain Models (Rule 12)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class AutodocParameter:
    """Immutable parameter definition extracted from AST / type hints."""

    name: str
    type_annotation: str = "Any"
    default_value: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("AutodocParameter.name cannot be empty")


@dataclass(slots=True, frozen=True)
class AutodocSignature:
    """Immutable structured signature and docstring payload."""

    object_path: str
    signature_str: str
    parameters: tuple[AutodocParameter, ...] = field(default_factory=tuple)
    return_type: str = "None"
    docstring: str = ""
    docstring_format: str = "markdown"
    code_examples: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.object_path or not self.object_path.strip():
            raise ValueError("AutodocSignature.object_path cannot be empty")


@dataclass(slots=True, frozen=True)
class LinkDiagnostic:
    """Diagnostic entry for a single link or anchor check."""

    source_file: str
    target_link: str
    anchor: str | None = None
    is_valid: bool = True
    line_number: int = 1
    error_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.source_file or not self.source_file.strip():
            raise ValueError("LinkDiagnostic.source_file cannot be empty")
        if not self.target_link or not self.target_link.strip():
            raise ValueError("LinkDiagnostic.target_link cannot be empty")


@dataclass(slots=True, frozen=True)
class TocDiagnostic:
    """Diagnostic entry for table-of-contents integrity checks."""

    entry: str
    file_path: str | None = None
    is_valid: bool = True
    error_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.entry or not self.entry.strip():
            raise ValueError("TocDiagnostic.entry cannot be empty")


@dataclass(slots=True, frozen=True)
class LinkValidationReport:
    """Aggregated link and table-of-contents validation report."""

    scanned_files_count: int = 0
    total_links_checked: int = 0
    broken_links: tuple[LinkDiagnostic, ...] = field(default_factory=tuple)
    toc_diagnostics: tuple[TocDiagnostic, ...] = field(default_factory=tuple)
    orphaned_files: tuple[str, ...] = field(default_factory=tuple)
    valid: bool = True


@dataclass(slots=True, frozen=True)
class DocFormatConvertResult:
    """Result of converting a document into MDX format with Svelte tags."""

    source_path: str
    target_format: str = "mdx"
    converted_content: str = ""
    svelte_components_injected: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source_path or not self.source_path.strip():
            raise ValueError("DocFormatConvertResult.source_path cannot be empty")


@dataclass(slots=True, frozen=True)
class DocLintResult:
    """Result of styling / linting code examples in documentation."""

    file_path: str
    issues_count: int = 0
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    formatted_content: str | None = None

    def __post_init__(self) -> None:
        if not self.file_path or not self.file_path.strip():
            raise ValueError("DocLintResult.file_path cannot be empty")


@dataclass(slots=True, frozen=True)
class DocChunk:
    """Heading-anchored documentation chunk for search / embeddings."""

    chunk_id: str
    title: str
    heading_level: int
    content: str
    tokens_estimate: int = 0
    breadcrumb: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("DocChunk.chunk_id cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("DocChunk.title cannot be empty")


# Backward compatibility aliases for existing callers
AutodocSignatureData = AutodocSignature
LinkDiagnosticData = LinkDiagnostic
LinkValidationReportData = LinkValidationReport
DocFormatConvertData = DocFormatConvertResult
DocLintResultData = DocLintResult
DocChunkData = DocChunk


# ---------------------------------------------------------------------------
# PEP 302/451 Zero-Dependency Mock Virtualization
# ---------------------------------------------------------------------------


class _DynamicProxyMeta(type):
    """Metaclass allowing arbitrary class attribute resolution and subclassing."""

    def __getattr__(cls, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        new_cls = _DynamicProxyMeta(name, (_DynamicProxyClass,), {})
        setattr(cls, name, new_cls)
        return new_cls

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__call__(*args, **kwargs)
        return instance


class _DynamicProxyClass(metaclass=_DynamicProxyMeta):
    """Dynamic class that can be called, instantiated, and accessed recursively."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        val = _DynamicProxyClass()
        setattr(self, name, val)
        return val

    @classmethod
    def __subclasscheck__(cls, subclass: Any) -> bool:
        return True

    @classmethod
    def __instancecheck__(cls, instance: Any) -> bool:
        return True


class MockModule(types.ModuleType):
    """Dynamic synthetic mock module allowing arbitrary attribute and subclass access."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__file__ = f"<mock {name}>"
        self.__path__: list[str] = []
        self.__loader__ = None
        self.__spec__ = None

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        cls = _DynamicProxyMeta(name, (_DynamicProxyClass,), {})
        setattr(self, name, cls)
        return cls


class ZeroDepMockFinder:
    """PEP 302/451 meta-path hook for synthesizing mock specs on uninstalled heavy packages."""

    def __init__(self, packages_to_mock: tuple[str, ...]) -> None:
        self.packages = set(packages_to_mock)

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        root_pkg = fullname.split(".")[0]
        if root_pkg in self.packages:
            spec = importlib.machinery.ModuleSpec(fullname, ZeroDepMockLoader(fullname))
            spec.submodule_search_locations = []
            return spec
        return None


class ZeroDepMockLoader:
    """Loader returning synthetic MockModule instances."""

    def __init__(self, fullname: str) -> None:
        self.fullname = fullname

    def create_module(self, spec: Any) -> Any:
        return MockModule(self.fullname)

    def exec_module(self, module: Any) -> None:
        pass


@contextlib.contextmanager
def virtualize_imports(
    packages: tuple[str, ...] = (
        "torch",
        "tensorflow",
        "jax",
        "flax",
        "transformers",
        "datasets",
        "accelerate",
    ),
):
    """Context manager to intercept and virtualize missing heavy dependencies."""
    finder = ZeroDepMockFinder(packages)
    sys.meta_path.insert(0, finder)
    orig_modules = set(sys.modules.keys())
    try:
        yield finder
    finally:
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        for mod_name in list(sys.modules.keys()):
            if mod_name not in orig_modules:
                root = mod_name.split(".")[0]
                if root in finder.packages:
                    sys.modules.pop(mod_name, None)


# ---------------------------------------------------------------------------
# Static AST Parser & Table of Contents Auditor
# ---------------------------------------------------------------------------


class DocAstStaticAnalyzer:
    """Pure static AST analyzer extracting docstrings and signatures without execution."""

    @staticmethod
    def parse_source(
        source_text: str, target_object: str | None = None
    ) -> list[AutodocSignature]:
        tree = ast.parse(source_text)
        signatures: list[AutodocSignature] = []

        def _format_arg(
            arg: ast.arg, default: ast.expr | None = None
        ) -> AutodocParameter:
            ann = ast.unparse(arg.annotation) if arg.annotation else "Any"
            def_val = ast.unparse(default) if default else None
            return AutodocParameter(
                name=arg.arg,
                type_annotation=ann,
                default_value=def_val,
                description=f"Parameter {arg.arg}",
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if target_object and node.name != target_object:
                    continue
                doc = ast.get_docstring(node) or ""
                # Find __init__ method if available
                init_params: list[AutodocParameter] = []
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name == "__init__":
                        args = sub.args
                        defaults = [None] * (
                            len(args.args) - len(args.defaults)
                        ) + list(args.defaults)
                        for a, d in zip(args.args, defaults):
                            if a.arg != "self":
                                init_params.append(_format_arg(a, d))
                sig_str = f"{node.name}({', '.join(p.name for p in init_params)})"
                signatures.append(
                    AutodocSignature(
                        object_path=node.name,
                        signature_str=sig_str,
                        parameters=tuple(init_params),
                        return_type=node.name,
                        docstring=doc,
                        docstring_format="markdown",
                    )
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if target_object and node.name != target_object:
                    continue
                # Skip private helpers if not targeted
                if node.name.startswith("_") and not target_object:
                    continue
                doc = ast.get_docstring(node) or ""
                args = node.args
                defaults = [None] * (len(args.args) - len(args.defaults)) + list(
                    args.defaults
                )
                params: list[AutodocParameter] = []
                for a, d in zip(args.args, defaults):
                    if a.arg not in ("self", "cls"):
                        params.append(_format_arg(a, d))
                ret_ann = ast.unparse(node.returns) if node.returns else "None"
                sig_str = (
                    f"{node.name}({', '.join(p.name for p in params)}) -> {ret_ann}"
                )
                signatures.append(
                    AutodocSignature(
                        object_path=node.name,
                        signature_str=sig_str,
                        parameters=tuple(params),
                        return_type=ret_ann,
                        docstring=doc,
                        docstring_format="markdown",
                    )
                )

        return signatures


class TocIntegrityAuditor:
    """Audits _toctree.yml / _toctree.yaml against documentation files."""

    @staticmethod
    def audit_toc(docs_path: Path) -> tuple[tuple[TocDiagnostic, ...], tuple[str, ...]]:
        toc_files = [
            docs_path / "_toctree.yml",
            docs_path / "_toctree.yaml",
            docs_path / "_toctree.json",
        ]
        target_toc = next((f for f in toc_files if f.exists()), None)
        if not target_toc:
            return (), ()

        diagnostics: list[TocDiagnostic] = []
        indexed_pages: set[str] = set()

        raw_text = target_toc.read_text(encoding="utf-8", errors="ignore")
        # Try YAML parsing or fallback regex extraction
        entries: list[str] = []
        try:
            import yaml

            parsed = yaml.safe_load(raw_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        if "local" in item:
                            entries.append(str(item["local"]))
                        elif "sections" in item and isinstance(item["sections"], list):
                            for sub in item["sections"]:
                                if isinstance(sub, dict) and "local" in sub:
                                    entries.append(str(sub["local"]))
                    elif isinstance(item, str):
                        entries.append(item)
        except Exception:
            # Fallback regex search for 'local: <path>' or simple entries
            for m in re.finditer(r"local:\s*([^\s#]+)", raw_text):
                entries.append(m.group(1).strip("'\""))

        for entry in entries:
            clean_entry = entry.strip().lstrip("/")
            possible_files = [
                docs_path / clean_entry,
                docs_path / f"{clean_entry}.md",
                docs_path / f"{clean_entry}.mdx",
                docs_path / clean_entry / "index.md",
            ]
            matched = next((p for p in possible_files if p.exists()), None)
            if matched:
                rel = str(matched.relative_to(docs_path)).replace("\\", "/")
                indexed_pages.add(rel)
                # also add extensionless
                indexed_pages.add(rel.rsplit(".", 1)[0])
                diagnostics.append(
                    TocDiagnostic(entry=entry, file_path=rel, is_valid=True)
                )
            else:
                diagnostics.append(
                    TocDiagnostic(
                        entry=entry,
                        file_path=None,
                        is_valid=False,
                        error_reason=f"TOC entry '{entry}' does not resolve to an existing file in {docs_path}",
                    )
                )

        # Detect orphaned markdown/mdx documentation files
        all_md_files = list(docs_path.rglob("*.md")) + list(docs_path.rglob("*.mdx"))
        orphans: list[str] = []
        for mf in all_md_files:
            rel = str(mf.relative_to(docs_path)).replace("\\", "/")
            base_rel = rel.rsplit(".", 1)[0]
            if (
                rel not in indexed_pages
                and base_rel not in indexed_pages
                and not rel.startswith("_")
            ):
                orphans.append(rel)

        return tuple(diagnostics), tuple(sorted(orphans))


# ---------------------------------------------------------------------------
# Authoritative In-Memory Domain Engine
# ---------------------------------------------------------------------------


class DocBuilderDomainEngine:
    """Authoritative in-memory domain engine for documentation compilation and verification."""

    @staticmethod
    def inspect_autodoc(
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        """Extract structured signature and parameters from a Python object or source file."""
        # 1. If explicit source_file provided, parse via static AST
        if source_file:
            p = Path(source_file)
            if p.exists():
                sigs = DocAstStaticAnalyzer.parse_source(
                    p.read_text(encoding="utf-8"), target_object=object_name
                )
                if sigs:
                    return sigs[0]

        # 2. Dynamic import with optional mock virtualization
        obj: Any = None
        try:
            if mock_heavy_deps:
                with virtualize_imports():
                    mod = importlib.import_module(package_name)
                    obj = getattr(mod, object_name)
            else:
                mod = importlib.import_module(package_name)
                obj = getattr(mod, object_name)
        except Exception as exc:
            logger.debug(
                "dynamic_import_fallback",
                package=package_name,
                object=object_name,
                error=str(exc),
            )
            # 3. Static AST fallback by finding module source if possible
            try:
                mod_spec = importlib.util.find_spec(package_name)
                if mod_spec and mod_spec.origin and Path(mod_spec.origin).exists():
                    sigs = DocAstStaticAnalyzer.parse_source(
                        Path(mod_spec.origin).read_text(
                            encoding="utf-8", errors="ignore"
                        ),
                        target_object=object_name,
                    )
                    if sigs:
                        return sigs[0]
            except Exception:
                pass

            # Safe static fallback signature
            return AutodocSignature(
                object_path=f"{package_name}.{object_name}",
                signature_str=f"{object_name}(*args, **kwargs)",
                parameters=(
                    AutodocParameter(
                        name="args",
                        type_annotation="tuple",
                        description="Positional arguments",
                    ),
                    AutodocParameter(
                        name="kwargs",
                        type_annotation="dict",
                        description="Keyword arguments",
                    ),
                ),
                return_type="Any",
                docstring=f"Documentation for {object_name} in {package_name}.",
                docstring_format="markdown",
                code_examples=(),
            )

        doc = inspect.getdoc(obj) or ""
        sig = None
        try:
            sig = inspect.signature(obj) if callable(obj) else None
        except Exception:
            sig = None
        sig_str = str(sig) if sig else "()"

        params: list[AutodocParameter] = []
        ret_type = "None"
        if sig:
            if sig.return_annotation is not inspect.Signature.empty:
                ret_type = str(sig.return_annotation)
            for p_name, param in sig.parameters.items():
                annotation = (
                    str(param.annotation)
                    if param.annotation is not inspect.Signature.empty
                    else "Any"
                )
                default = (
                    str(param.default)
                    if param.default is not inspect.Signature.empty
                    else None
                )
                params.append(
                    AutodocParameter(
                        name=p_name,
                        type_annotation=annotation,
                        default_value=default,
                        description=f"Parameter {p_name}",
                    )
                )

        return AutodocSignature(
            object_path=f"{package_name}.{object_name}",
            signature_str=f"{object_name}{sig_str}",
            parameters=tuple(params),
            return_type=ret_type,
            docstring=doc,
            docstring_format="markdown",
            code_examples=(),
        )

    @staticmethod
    def verify_links(
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        """Verify internal Markdown links, anchors, and TOC integrity across documentation."""
        target_path = Path(docs_dir)
        if not target_path.exists():
            return LinkValidationReport(
                scanned_files_count=0,
                total_links_checked=0,
                broken_links=(
                    LinkDiagnostic(
                        source_file=str(target_path),
                        target_link="",
                        is_valid=False,
                        error_reason=f"Docs directory does not exist: {target_path}",
                    ),
                ),
                valid=False,
            )

        md_files = list(target_path.rglob("*.md")) + list(target_path.rglob("*.mdx"))
        if not md_files and target_path.is_file():
            md_files = [target_path]

        # 1. Build anchor index across all files
        anchor_index: dict[str, set[str]] = {}
        file_rel_paths: set[str] = set()

        for mf in md_files:
            rel = str(
                mf.relative_to(
                    target_path if target_path.is_dir() else target_path.parent
                )
            ).replace("\\", "/")
            file_rel_paths.add(rel)
            base_rel = rel.rsplit(".", 1)[0]
            file_rel_paths.add(base_rel)

            text = mf.read_text(encoding="utf-8", errors="ignore")
            anchors: set[str] = set()
            for line in text.splitlines():
                if line.startswith("#"):
                    title = re.sub(r"^#+\s*", "", line).strip()
                    slug = (
                        re.sub(r"[^a-zA-Z0-9\-_ ]", "", title).lower().replace(" ", "-")
                    )
                    anchors.add(slug)
                for m in re.finditer(r'id=["\']([^"\']+)["\']', line):
                    anchors.add(m.group(1))
            anchor_index[rel] = anchors
            anchor_index[base_rel] = anchors

        # 2. Check links
        diagnostics: list[LinkDiagnostic] = []
        total_links = 0

        for mf in md_files:
            rel_src = str(
                mf.relative_to(
                    target_path if target_path.is_dir() else target_path.parent
                )
            ).replace("\\", "/")
            src_dir = str(Path(rel_src).parent).replace("\\", "/")
            text = mf.read_text(encoding="utf-8", errors="ignore")

            # Strip code fences before searching links
            clean_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

            for line_idx, line in enumerate(clean_text.splitlines(), start=1):
                for match in re.finditer(r"\[([^\]]*)\]\(([^\)]+)\)", line):
                    total_links += 1
                    target_link = match.group(2).strip()

                    # Skip external URLs
                    if target_link.startswith(
                        ("http://", "https://", "mailto:", "ftp:")
                    ):
                        continue

                    target_url, _, anchor = target_link.partition("#")
                    anchor = anchor.strip() if anchor else None

                    # Anchor-only link (#heading)
                    if not target_url:
                        if check_anchors and anchor:
                            current_anchors = anchor_index.get(rel_src, set())
                            if anchor not in current_anchors:
                                diagnostics.append(
                                    LinkDiagnostic(
                                        source_file=rel_src,
                                        target_link=target_link,
                                        anchor=anchor,
                                        is_valid=False,
                                        line_number=line_idx,
                                        error_reason=f"Anchor #{anchor} not found in {rel_src}",
                                    )
                                )
                        continue

                    # Resolve target path relative to source file
                    if target_url.startswith("/"):
                        resolved = target_url.lstrip("/")
                    else:
                        norm = os.path.normpath(
                            f"{src_dir}/{target_url}" if src_dir != "." else target_url
                        ).replace("\\", "/")
                        resolved = norm

                    resolved_clean = resolved.rstrip("/")
                    valid_file = (
                        resolved_clean in file_rel_paths
                        or f"{resolved_clean}.md" in file_rel_paths
                        or f"{resolved_clean}.mdx" in file_rel_paths
                        or f"{resolved_clean}/index.md" in file_rel_paths
                    )

                    if not valid_file:
                        diagnostics.append(
                            LinkDiagnostic(
                                source_file=rel_src,
                                target_link=target_link,
                                anchor=anchor,
                                is_valid=False,
                                line_number=line_idx,
                                error_reason=f"Target file path does not resolve: {target_url}",
                            )
                        )
                    elif check_anchors and anchor:
                        target_key = resolved_clean
                        if (
                            target_key not in anchor_index
                            and f"{resolved_clean}.md" in anchor_index
                        ):
                            target_key = f"{resolved_clean}.md"
                        target_anchors = anchor_index.get(target_key, set())
                        if target_anchors and anchor not in target_anchors:
                            diagnostics.append(
                                LinkDiagnostic(
                                    source_file=rel_src,
                                    target_link=target_link,
                                    anchor=anchor,
                                    is_valid=False,
                                    line_number=line_idx,
                                    error_reason=f"Anchor #{anchor} not found in target file {target_url}",
                                )
                            )

        # 3. Check Table of Contents integrity
        toc_diags: tuple[TocDiagnostic, ...] = ()
        orphans: tuple[str, ...] = ()
        if check_toc and target_path.is_dir():
            toc_diags, orphans = TocIntegrityAuditor.audit_toc(target_path)

        broken_toc_count = sum(1 for td in toc_diags if not td.is_valid)
        is_valid = len(diagnostics) == 0 and broken_toc_count == 0

        return LinkValidationReport(
            scanned_files_count=len(md_files),
            total_links_checked=total_links,
            broken_links=tuple(diagnostics),
            toc_diagnostics=toc_diags,
            orphaned_files=orphans,
            valid=is_valid,
        )

    @staticmethod
    def convert_format(
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        """Transpile Markdown, RST, or IPYNB into MDX with Svelte tags."""
        p = Path(source_path)
        content = (
            p.read_text(encoding="utf-8", errors="ignore")
            if p.exists()
            else str(source_path)
        )

        injected_components: list[str] = []

        # Convert Sphinx directives to Svelte components
        if ".. note::" in content or ".. warning::" in content or ".. tip::" in content:
            content = re.sub(
                r"\.\. note::\s*(.*?)(?=\n\S|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")
            content = re.sub(
                r"\.\. warning::\s*(.*?)(?=\n\S|\Z)",
                r"<Warning>\n\1\n</Warning>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Warning>")
            content = re.sub(
                r"\.\. tip::\s*(.*?)(?=\n\S|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")

        # Normalize markdown blockquotes: > [!NOTE] -> <Tip>
        if "> [!NOTE]" in content or "> [!TIP]" in content:
            content = re.sub(
                r"> \[!(?:NOTE|TIP)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")
        if "> [!WARNING]" in content or "> [!CAUTION]" in content:
            content = re.sub(
                r"> \[!(?:WARNING|CAUTION)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
                r"<Warning>\n\1\n</Warning>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Warning>")

        return DocFormatConvertResult(
            source_path=str(p),
            target_format=target_format,
            converted_content=content,
            svelte_components_injected=tuple(sorted(set(injected_components))),
        )

    @staticmethod
    def lint_style(
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        """Lint and format code examples inside docstrings or MDX files."""
        p = Path(file_path)
        content = (
            p.read_text(encoding="utf-8", errors="ignore")
            if p.exists()
            else str(file_path)
        )

        diagnostics: list[str] = []
        code_blocks = re.findall(r"```python(.*?)```", content, flags=re.DOTALL)
        for idx, block in enumerate(code_blocks, start=1):
            lines = block.strip().splitlines()
            if not lines:
                diagnostics.append(f"Block #{idx}: Empty python code block")
            for l_idx, line in enumerate(lines, start=1):
                if line.endswith((" ", "\t")):
                    diagnostics.append(
                        f"Block #{idx} Line {l_idx}: Trailing whitespace detected"
                    )

        formatted = content
        if fix:
            formatted = re.sub(
                r"```python(.*?)```",
                lambda m: (
                    "```python\n"
                    + "\n".join(l.rstrip() for l in m.group(1).strip().splitlines())
                    + "\n```"
                ),
                content,
                flags=re.DOTALL,
            )

        return DocLintResult(
            file_path=str(p),
            issues_count=len(diagnostics),
            diagnostics=tuple(diagnostics),
            formatted_content=formatted if fix else None,
        )

    @staticmethod
    def chunk_markdown(
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        """Hierarchically partition Markdown text by headings for search indexing."""
        lines = markdown_text.splitlines()
        chunks: list[DocChunk] = []

        current_heading = page_title
        current_level = 1
        current_lines: list[str] = []
        heading_stack: list[str] = [page_title]
        chunk_idx = 0

        def flush_chunk() -> None:
            nonlocal chunk_idx, current_lines
            if not current_lines:
                return
            body = "\n".join(current_lines).strip()
            if body:
                chunks.append(
                    DocChunk(
                        chunk_id=f"chunk_{chunk_idx}",
                        title=current_heading,
                        heading_level=current_level,
                        content=body,
                        tokens_estimate=max(1, len(body) // 4),
                        breadcrumb=tuple(heading_stack),
                    )
                )
                chunk_idx += 1
            current_lines = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if header_match:
                flush_chunk()
                level = len(header_match.group(1))
                h_text = header_match.group(2).strip()

                while len(heading_stack) >= level and len(heading_stack) > 1:
                    heading_stack.pop()
                heading_stack.append(h_text)

                current_heading = h_text
                current_level = level
            else:
                current_lines.append(line)

        flush_chunk()

        if not chunks:
            chunks.append(
                DocChunk(
                    chunk_id="chunk_0",
                    title=page_title,
                    heading_level=1,
                    content=markdown_text[:max_chunk_size],
                    tokens_estimate=max(1, len(markdown_text[:max_chunk_size]) // 4),
                    breadcrumb=(page_title,),
                )
            )

        return tuple(chunks)


# ---------------------------------------------------------------------------
# Typed Service Protocol & Micro-Kernel IoC Provider
# ---------------------------------------------------------------------------


@runtime_checkable
class HfDocBuilderProtocol(Protocol):
    """Protocol for Hugging Face doc-builder operations."""

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        """Extract structured signature, parameters, and docstrings from Python object."""
        ...

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        """Verify internal relative links, anchors, and table-of-contents integrity."""
        ...

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        """Convert Markdown, RST, or IPYNB to MDX with Svelte tags."""
        ...

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        """Lint and format code examples inside docstrings and MDX."""
        ...

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        """Hierarchically chunk markdown by headings for embedding indexation."""
        ...


class DefaultHfDocBuilderService(HfDocBuilderProtocol):
    """Authoritative in-process service implementation wrapping doc builder domain logic."""

    def __init__(self, engine: Any | None = None) -> None:
        self._engine = engine or DocBuilderDomainEngine

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        return self._engine.inspect_autodoc(
            package_name, object_name, mock_heavy_deps, source_file
        )

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        return self._engine.verify_links(docs_dir, check_anchors, check_toc)

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        return self._engine.convert_format(source_path, target_format)

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        return self._engine.lint_style(file_path, fix)

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        return self._engine.chunk_markdown(markdown_text, page_title, max_chunk_size)


# Backward compatibility class alias
HfDocBuilderService = DefaultHfDocBuilderService

DOC_BUILDER_SERVICE_KEY: ServiceKey[HfDocBuilderProtocol] = ServiceKey(
    "service.doc_builder"
)

__all__ = [
    "DOC_BUILDER_SERVICE_KEY",
    "AutodocParameter",
    "AutodocSignature",
    "AutodocSignatureData",
    "DefaultHfDocBuilderService",
    "DocAstStaticAnalyzer",
    "DocBuilderDomainEngine",
    "DocChunk",
    "DocChunkData",
    "DocFormatConvertData",
    "DocFormatConvertResult",
    "DocLintResult",
    "DocLintResultData",
    "HfDocBuilderProtocol",
    "HfDocBuilderService",
    "LinkDiagnostic",
    "LinkDiagnosticData",
    "LinkValidationReport",
    "LinkValidationReportData",
    "MockModule",
    "TocDiagnostic",
    "TocIntegrityAuditor",
    "ZeroDepMockFinder",
    "ZeroDepMockLoader",
    "virtualize_imports",
]
