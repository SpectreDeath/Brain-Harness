"""Autodoc inspector extracting structured signature and parameter metadata."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Any

import structlog

from harness.services.doc_builder.ast_analyzer import DocAstStaticAnalyzer
from harness.services.doc_builder.models import (
    AutodocParameter,
    AutodocSignature,
)
from harness.services.doc_builder.virtualizer import virtualize_imports

logger = structlog.get_logger(__name__)


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
