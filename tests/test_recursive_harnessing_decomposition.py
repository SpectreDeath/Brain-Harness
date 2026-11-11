"""Contract tests for recursive harnessing service decomposition and line limits."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.services.recursive_harnessing import (
    BRAIN_SURFACE,
    EVIDENCE_ISOLATION_SERVICE_KEY,
    RECURSIVE_REFINER_SERVICE_KEY,
    BudgetError,
    BudgetLedger,
    EvidenceLeakError,
    ExperienceLibrary,
    ModeResult,
    RunView,
    Selection,
    SurfaceSpec,
    Tree,
    assert_no_leak_paths,
    assert_no_verdicts,
    assign_ids,
    blind_select,
    expected_rollouts,
    expected_sessions,
    fingerprint_dir,
    fingerprint_tree,
    resolve_evidence_isolation,
    resolve_recursive_refiner,
    run_mode,
    run_parallel,
    run_sequential,
    selection_pool,
    trivial_selection,
)


@pytest.mark.unit
class TestRecursiveHarnessingDecomposition:
    """Rigorous decomposition and architectural boundary enforcement."""

    def test_all_submodules_under_200_lines(self) -> None:
        """Convention: Every module in src/harness/services/recursive_harnessing must be <= 200 lines."""
        pkg_dir = Path("src/harness/services/recursive_harnessing")
        assert pkg_dir.is_dir(), f"Package directory not found: {pkg_dir}"

        py_files = sorted(pkg_dir.glob("*.py"))
        assert len(py_files) > 0, "No python files found in package directory"

        violations = []
        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            if line_count > 200:
                violations.append((py_file.name, line_count))

        assert not violations, (
            f"The following submodules exceed the 200-line decomposition bound: "
            f"{[f'{name}: {lines} lines' for name, lines in violations]}"
        )

    def test_public_symbols_exported(self) -> None:
        """Verify that public API symbols remain resolvable from package root."""
        assert SurfaceSpec is not None
        assert BRAIN_SURFACE is not None
        assert BRAIN_SURFACE.always_on_max == 32_000
        assert BRAIN_SURFACE.require_always_on_triggers is False
        assert BudgetLedger is not None
        assert expected_rollouts(2) == 8
        assert expected_sessions(2) == 6
        assert blind_select is not None
        assert trivial_selection is not None
        assert run_parallel is not None
        assert run_sequential is not None
        assert run_mode is not None

    def test_ioc_keys_and_resolvers(self) -> None:
        """Verify typed IoC service keys and single-seam resolvers."""
        assert EVIDENCE_ISOLATION_SERVICE_KEY is not None
        assert RECURSIVE_REFINER_SERVICE_KEY is not None
        assert resolve_evidence_isolation(None) is not None
        assert resolve_recursive_refiner(None) is not None

