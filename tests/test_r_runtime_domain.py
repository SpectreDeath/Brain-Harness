"""Contract tests for R Runtime Domain Engine & Slotted Frozen Models."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure skill scripts directory is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "r-language-server-toolkit" / "scripts"

if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from r_runtime_engine import (
    RDiagnosticItem,
    RLanguageServerConfig,
    RPlotEvent,
    RRuntimeDomainEngine,
    RSessionInspection,
)


@pytest.mark.unit
class TestRRuntimeDomainModels:
    """Validate immutability and contracts of R runtime domain models per Rule 12 & Rule 43."""

    def test_diagnostic_item_immutability(self) -> None:
        """Verify RDiagnosticItem is frozen and prevents attribute mutation."""
        diag = RDiagnosticItem(
            file_path="model.R",
            line=5,
            column=12,
            severity="Error",
            message="Unexpected token",
            code="parse_error",
        )
        assert diag.file_path == "model.R"
        assert diag.line == 5
        assert diag.column == 12
        assert diag.severity == "Error"

        # Rule 43: direct attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            diag.line = 10  # type: ignore

    def test_session_inspection_immutability(self) -> None:
        """Verify RSessionInspection is frozen and enforces valid state."""
        session = RSessionInspection(
            pid=4242,
            working_dir="/workspace/project",
            loaded_packages=("base", "utils", "stats"),
            global_symbols=("x", "y"),
            active_device="jgd",
            is_clean=True,
        )
        assert session.pid == 4242
        assert session.working_dir == "/workspace/project"
        assert session.is_clean is True

        with pytest.raises((AttributeError, TypeError)):
            session.pid = 9999  # type: ignore

    def test_plot_event_immutability(self) -> None:
        """Verify RPlotEvent dimensions and frozen constraints."""
        plot = RPlotEvent(
            plot_index=3,
            width=800.0,
            height=600.0,
            format="json",
            payload_size=2048,
        )
        assert plot.plot_index == 3
        assert plot.width == 800.0
        assert plot.height == 600.0

        with pytest.raises((AttributeError, TypeError)):
            plot.format = "png"  # type: ignore

    def test_language_server_config_validation(self) -> None:
        """Verify RLanguageServerConfig validates safety boundaries."""
        cfg = RLanguageServerConfig(
            r_path="R.exe",
            debounce_ms=300,
            lint_on_change=True,
        )
        assert cfg.debounce_ms == 300

        # Fails on empty path
        with pytest.raises(ValueError):
            RLanguageServerConfig(r_path="", debounce_ms=300)

        # Fails on too low debounce
        with pytest.raises(ValueError):
            RLanguageServerConfig(r_path="R.exe", debounce_ms=10)

    def test_engine_operations(self) -> None:
        """Verify RRuntimeDomainEngine transformation methods."""
        session = RRuntimeDomainEngine.inspect_session(
            pid=1001,
            working_dir="/home/r_user",
            loaded_packages=["ggplot2", "dplyr"],
            global_symbols=["my_data", "clean_fn"],
        )
        assert session.pid == 1001
        assert "ggplot2" in session.loaded_packages
        assert session.is_clean is True

        # Test diagnostic parsing
        raw = [
            {"file_path": "test.R", "line": 1, "column": 5, "severity": "error", "message": "Syntax error"}
        ]
        parsed = RRuntimeDomainEngine.parse_diagnostics(raw)
        assert len(parsed) == 1
        assert parsed[0].severity == "Error"
        assert parsed[0].message == "Syntax error"

