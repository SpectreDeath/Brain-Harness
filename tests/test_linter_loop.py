"""Unit tests for ArchLinterService per-file syntax validation and self-repair loop."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.services.arch_linter import (
    ARCH_LINTER_KEY,
    DefaultArchLinterService,
    FileDiagnostic,
    FileLintResult,
)


@pytest.mark.unit
def test_arch_linter_service_key() -> None:
    """Verify ServiceKey registration."""
    assert ARCH_LINTER_KEY.name == "service.arch_linter"


@pytest.mark.unit
def test_lint_file_clean_python() -> None:
    """Test linting valid Python code."""
    svc = DefaultArchLinterService()
    valid_py = "def add(a: int, b: int) -> int:\n    return a + b\n"
    res = svc.lint_file("test.py", content=valid_py)
    assert res.status == "ok"
    assert res.is_clean is True
    assert res.error_count == 0


@pytest.mark.unit
def test_lint_file_syntax_error_python() -> None:
    """Test linting Python with missing colon / syntax error."""
    svc = DefaultArchLinterService()
    invalid_py = "def broken(a, b\n    return a + b\n"
    res = svc.lint_file("broken.py", content=invalid_py)
    assert res.status == "error"
    assert res.is_clean is False
    assert res.error_count >= 1
    assert "SyntaxError" in res.formatted_summary


@pytest.mark.unit
def test_lint_file_json_error() -> None:
    """Test linting malformed JSON."""
    svc = DefaultArchLinterService()
    invalid_json = '{"name": "test", "unclosed": }'
    res = svc.lint_file("config.json", content=invalid_json)
    assert res.status == "error"
    assert res.is_clean is False
    assert "JSONDecodeError" in res.formatted_summary


@pytest.mark.unit
def test_lint_file_bracket_balance_error() -> None:
    """Test bracket balancing diagnostic."""
    svc = DefaultArchLinterService()
    unbalanced = "const fn = (x) => { console.log(x); // missing brace"
    res = svc.lint_file("app.ts", content=unbalanced)
    assert res.status == "error"
    assert res.is_clean is False
    assert "Unclosed opening delimiter" in res.formatted_summary
