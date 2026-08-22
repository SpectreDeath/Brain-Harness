"""Schema and type inference engine — deep AST and reflection for Python callables and docstrings.

Provides authoritative reflection from typed Python functions, methods, and classes
into ParameterSpec, EntrypointSpec, and PluginManifest definitions for Harness plugins.
"""

from __future__ import annotations

import inspect
import re
import types
import typing
from collections.abc import Callable
from typing import Any, get_args, get_origin

import structlog

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

logger = structlog.get_logger()


class SchemaInferrer:
    """Authoritative type, docstring, and manifest inferrer from Python callables."""

    # Map of Python primitive / standard types to JSON schema types
    PRIMITIVE_TYPE_MAP: dict[Any, str] = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
        set: "array",
        tuple: "array",
        bytes: "string",
        bytearray: "string",
    }

    NAME_TYPE_MAP: dict[str, str] = {
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "number": "number",
        "str": "string",
        "string": "string",
        "bool": "boolean",
        "boolean": "boolean",
        "list": "array",
        "array": "array",
        "dict": "object",
        "object": "object",
        "set": "array",
        "tuple": "array",
        "any": "string",
        "none": "null",
        "nonetype": "null",
    }

    @classmethod
    def python_type_to_schema_type(cls, annotation: Any) -> str:
        """Resolve any Python type annotation into a canonical JSON schema type string."""
        if annotation is inspect.Parameter.empty or annotation is None:
            return "string"

        # Check primitive type map directly
        if annotation in cls.PRIMITIVE_TYPE_MAP:
            return cls.PRIMITIVE_TYPE_MAP[annotation]

        origin = get_origin(annotation)
        args = get_args(annotation)

        # Handle Coroutine and Awaitable unwrapping
        import collections.abc
        if origin in (collections.abc.Coroutine, typing.Coroutine) and len(args) >= 3:
            return cls.python_type_to_schema_type(args[2])
        if origin in (collections.abc.Awaitable, typing.Awaitable) and len(args) >= 1:
            return cls.python_type_to_schema_type(args[0])

        # Handle Union and Optional (Union[T, None])
        if origin is typing.Union or (hasattr(types, "UnionType") and origin is types.UnionType):
            non_none_args = [a for a in args if a is not type(None)]
            if non_none_args:
                return cls.python_type_to_schema_type(non_none_args[0])
            return "string"

        # Handle List, Sequence, Iterable, Set, Tuple
        if origin in (list, set, tuple, typing.List, typing.Sequence, typing.Iterable, typing.Set, typing.Tuple):
            return "array"

        # Handle Dict, Mapping
        if origin in (dict, typing.Dict, typing.Mapping):
            return "object"

        # Handle BaseModel / Pydantic models
        try:
            from pydantic import BaseModel
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                return "object"
        except Exception:
            pass

        # Handle string annotations (e.g. from future annotations or forward refs)
        if isinstance(annotation, str):
            clean = annotation.strip().lower()
            if clean.startswith("coroutine[") and "," in clean:
                parts = clean[10:-1].split(",")
                return cls.python_type_to_schema_type(parts[-1].strip())
            if clean.startswith("awaitable["):
                inner = clean[10:-1].strip()
                return cls.python_type_to_schema_type(inner)
            if clean.startswith("list[") or clean.startswith("sequence[") or clean.startswith("set["):
                return "array"
            if clean.startswith("dict[") or clean.startswith("mapping["):
                return "object"
            if clean.startswith("optional["):
                inner = clean[9:-1].strip()
                return cls.python_type_to_schema_type(inner)
            if "|" in clean:
                first_part = clean.split("|")[0].strip()
                return cls.python_type_to_schema_type(first_part)
            return cls.NAME_TYPE_MAP.get(clean, "string")

        # Fallback to class name if available
        if hasattr(annotation, "__name__"):
            return cls.NAME_TYPE_MAP.get(annotation.__name__.lower(), "string")

        return "string"

    @classmethod
    def parse_docstring_param_descriptions(cls, docstring: str | None) -> tuple[str, dict[str, str]]:
        """Parse function docstring to extract main summary and parameter descriptions.

        Supports Google-style, Sphinx/reST-style, and standard descriptive docstrings.
        """
        if not docstring:
            return "", {}

        doc = docstring.strip()
        lines = doc.splitlines()
        summary = lines[0].strip() if lines else ""
        param_descriptions: dict[str, str] = {}

        # Sphinx-style: :param param_name: description
        sphinx_matches = re.findall(r":param\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)", doc)
        for p_name, p_desc in sphinx_matches:
            param_descriptions[p_name] = p_desc.strip()

        # Google-style: Args:\n  param_name (type): description or param_name: description
        in_args_section = False
        current_param = None
        current_desc: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.lower() in ("args:", "parameters:", "arguments:", "params:"):
                in_args_section = True
                continue
            if in_args_section:
                if stripped.lower() in ("returns:", "raises:", "yields:", "example:", "examples:", "note:"):
                    in_args_section = False
                    if current_param:
                        param_descriptions.setdefault(current_param, " ".join(current_desc))
                    current_param = None
                    current_desc = []
                    continue

                param_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)(?:\s*\([^)]*\))?\s*:\s*(.*)$", stripped)
                if param_match:
                    if current_param:
                        param_descriptions.setdefault(current_param, " ".join(current_desc))
                    current_param = param_match.group(1)
                    current_desc = [param_match.group(2).strip()] if param_match.group(2) else []
                elif current_param and stripped:
                    current_desc.append(stripped)

        if current_param:
            param_descriptions.setdefault(current_param, " ".join(current_desc))

        return summary, param_descriptions

    @classmethod
    def infer_parameters(cls, fn: Callable[..., Any]) -> list[ParameterSpec]:
        """Deeply inspect a Python callable to construct a list of ParameterSpec objects."""
        sig = inspect.signature(fn)
        _, param_docs = cls.parse_docstring_param_descriptions(inspect.getdoc(fn))
        parameters: list[ParameterSpec] = []

        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls", "kwargs", "args"):
                continue

            # Check if variadic *args or **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            type_str = cls.python_type_to_schema_type(param.annotation)
            is_required = param.default == inspect.Parameter.empty
            default_val = None if is_required else param.default

            # Clean default val if callable or complex
            if default_val is not None and not isinstance(default_val, (int, float, str, bool, list, dict, type(None))):
                default_val = str(default_val)

            desc = param_docs.get(p_name, f"Parameter '{p_name}'")

            parameters.append(
                ParameterSpec(
                    name=p_name,
                    type=type_str,
                    description=desc,
                    required=is_required,
                    default=default_val,
                )
            )

        return parameters

    @classmethod
    def infer_entrypoint_spec(cls, fn: Callable[..., Any], name: str | None = None) -> EntrypointSpec:
        """Infer an EntrypointSpec from a single callable."""
        fn_name = str(name or getattr(fn, "__name__", "execute"))
        doc = inspect.getdoc(fn) or ""
        summary, _ = cls.parse_docstring_param_descriptions(doc)
        desc = summary or f"Handler for {fn_name}"

        params = cls.infer_parameters(fn)

        # Return type
        sig = inspect.signature(fn)
        returns_type = "dict"
        if sig.return_annotation != inspect.Parameter.empty:
            returns_type = cls.python_type_to_schema_type(sig.return_annotation)

        return EntrypointSpec(
            name=fn_name,
            description=desc,
            parameters=params,
            returns=returns_type,
        )

    @classmethod
    def infer_manifest(
        cls,
        name: str,
        tools: dict[str, Callable[..., Any]] | list[Callable[..., Any]],
        *,
        version: str = "0.1.0",
        description: str = "",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        author: str = "Harness Developer",
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> PluginManifest:
        """Build a complete PluginManifest by reflecting over multiple callables."""
        tools_dict: dict[str, Callable[..., Any]] = {}
        if isinstance(tools, dict):
            tools_dict = tools
        elif isinstance(tools, list):
            tools_dict = {getattr(fn, "__name__", f"tool_{i}"): fn for i, fn in enumerate(tools)}

        entrypoints: list[EntrypointSpec] = [
            cls.infer_entrypoint_spec(fn, name=t_name) for t_name, fn in tools_dict.items()
        ]

        desc = description or f"Dynamically synthesized plugin: {name}"
        active_tags = list(tags or [])
        if preset not in active_tags:
            active_tags.append(preset)

        return PluginManifest(
            name=name,
            version=version,
            description=desc,
            language="python",
            entrypoint="main.py",
            isolation=isolation,
            author=author,
            category=category,
            tags=active_tags,
            provides=[f"tool.{name}"],
            entrypoints=entrypoints,
            dependencies=list(dependencies or []),
            metadata={"preset": preset, "dynamic_origin": True, "inferred_by": "SchemaInferrer"},
        )


__all__ = ["SchemaInferrer"]
