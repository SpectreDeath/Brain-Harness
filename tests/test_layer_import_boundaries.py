"""AST architectural boundary tests guarding UI and services import directionality."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "harness"


def _collect_forbidden_imports(
    subdir: str,
    forbidden_prefixes: tuple[str, ...],
    *,
    allowed_rel_paths: frozenset[str] = frozenset(),
) -> list[str]:
    base = _SRC_ROOT / subdir
    violations: list[str] = []
    for py_file in sorted(base.rglob("*.py")):
        rel = py_file.relative_to(base).as_posix()
        if rel in allowed_rel_paths:
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for mod in targets:
                if any(mod == prefix or mod.startswith(f"{prefix}.") for prefix in forbidden_prefixes):
                    violations.append(f"{subdir}/{rel}:{node.lineno} -> {mod}")
    return violations


@pytest.mark.unit
def test_ui_never_imports_commands() -> None:
    """UI routes and server modules must call services, never harness.commands."""
    violations = _collect_forbidden_imports("ui", ("harness.commands",))
    assert violations == [], f"Forbidden UI -> commands imports: {violations}"


@pytest.mark.unit
def test_services_never_imports_commands_or_creator() -> None:
    """Service layer must not depend upward on harness.commands or harness.creator."""
    cmd_violations = _collect_forbidden_imports("services", ("harness.commands",))
    assert cmd_violations == [], f"Forbidden services -> commands imports: {cmd_violations}"

    creator_violations = _collect_forbidden_imports("services", ("harness.creator",))
    assert creator_violations == [], f"Forbidden services -> creator imports: {creator_violations}"


@pytest.mark.unit
def test_creator_never_imports_commands() -> None:
    """Creator modules must not depend upward on harness.commands."""
    violations = _collect_forbidden_imports("creator", ("harness.commands",))
    assert violations == [], f"Forbidden creator -> commands imports: {violations}"


@pytest.mark.unit
def test_kernel_only_imports_events_and_plugins() -> None:
    """Kernel primitives must only import harness.kernel*, harness.events*, or harness.plugins*."""
    allowed_prefixes = ("harness.kernel", "harness.events", "harness.plugins")
    base = _SRC_ROOT / "kernel"
    violations: list[str] = []
    for py_file in sorted(base.rglob("*.py")):
        rel = py_file.relative_to(base).as_posix()
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for mod in targets:
                if mod.startswith("harness.") and not any(
                    mod == prefix or mod.startswith(f"{prefix}.") for prefix in allowed_prefixes
                ):
                    violations.append(f"kernel/{rel}:{node.lineno} -> {mod}")
    assert violations == [], f"Forbidden kernel cross-layer imports: {violations}"


@pytest.mark.unit
def test_kernel_runtime_compat_shim_emits_deprecation_and_preserves_identity() -> None:
    """Deprecated harness.kernel.runtime shim must warn and forward identical runtime symbols."""
    from harness.runtime import HarnessRuntime as RealHarnessRuntime

    with pytest.warns(DeprecationWarning, match="harness.runtime"):
        from harness.kernel.runtime import HarnessRuntime as ShimHarnessRuntime

    assert ShimHarnessRuntime is RealHarnessRuntime
