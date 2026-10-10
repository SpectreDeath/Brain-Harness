"""Contract test suite for decomposed mantis_security_review package.

Verifies:
1. Subpackage exports, module layout, and strict Rule 11 line count bounds (< 200 lines).
2. Slotted & frozen domain models (Rule 12).
3. Single-seam resolver factory per Rule 58.
4. Tool and engine submodule operations (vcs, auditor, triage, chains, reporter).
5. Module-level plugin singleton (Rule 45).
"""

from __future__ import annotations

import pathlib
import pytest

from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.mantis_security_review.engine import (
    MANTIS_SECURITY_REVIEW_KEY,
    ExploitChain,
    ExploitStep,
    MantisFinding,
    MantisReviewEngine,
    MantisSecurityReviewService,
    calibrate_risk,
    chain_exploits,
    compute_stable_signature,
    critic_filter,
    dedupe_ladder,
    directory_summary,
    generate_report,
    history_scan,
    init_okf_db,
    plan_review,
    research_audit,
    resolve_mantis_security_review,
    review_gate,
)
from plugins.security_and_forensics.mantis_security_review.main import (
    MantisSecurityReviewPlugin,
    plugin,
)


def test_mantis_subpackage_line_bounds() -> None:
    """Assert all submodules in mantis_security_review and engine are strictly < 200 lines (Rule 11)."""
    plugin_dir = (
        pathlib.Path(__file__).parent.parent
        / "plugins"
        / "security_and_forensics"
        / "mantis_security_review"
    )
    assert plugin_dir.is_dir()

    main_py = plugin_dir / "main.py"
    main_lines = len(main_py.read_text(encoding="utf-8").splitlines())
    assert main_lines < 200, f"main.py has {main_lines} lines, exceeding 200 line bound"

    engine_dir = plugin_dir / "engine"
    assert engine_dir.is_dir()
    py_files = list(engine_dir.glob("*.py"))
    assert len(py_files) >= 10

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines < 200, f"Module {py_file.name} has {lines} lines, exceeding 200 line bound"


def test_mantis_subpackage_exports() -> None:
    """Verify package public exports and types."""
    import plugins.security_and_forensics.mantis_security_review.engine as pkg

    assert hasattr(pkg, "MantisReviewEngine")
    assert hasattr(pkg, "MantisSecurityReviewService")
    assert hasattr(pkg, "MANTIS_SECURITY_REVIEW_KEY")
    assert hasattr(pkg, "resolve_mantis_security_review")


def test_slotted_frozen_dataclass_immutability() -> None:
    """Verify domain dataclasses use slots=True and frozen=True (Rule 12)."""
    finding = MantisFinding(
        id="f1",
        filepath="app.py",
        line=10,
        cwe="CWE-78",
        title="Command Injection",
        severity="critical",
        signature="abc123",
    )
    assert finding.id == "f1"
    assert hasattr(finding, "__slots__")

    # Mutation should raise AttributeError per Rule 43
    with pytest.raises((AttributeError, TypeError)):
        finding.severity = "low"  # type: ignore

    step = ExploitStep(step=1, finding_id="f1", tactic="RCE", description="Exec")
    assert step.step == 1
    with pytest.raises((AttributeError, TypeError)):
        step.tactic = "Bypass"  # type: ignore


def test_single_seam_resolver_contract() -> None:
    """Verify resolve_mantis_security_review adheres to Rule 58 single seam."""
    ctx = ServiceContext()

    resolved_1 = resolve_mantis_security_review(ctx)
    assert isinstance(resolved_1, MantisSecurityReviewService)
    assert ctx.has(MANTIS_SECURITY_REVIEW_KEY)

    # Resolution retrieval
    resolved_2 = resolve_mantis_security_review(ctx)
    assert resolved_2 is resolved_1

    # Instance passthrough
    resolved_3 = resolve_mantis_security_review(resolved_1)
    assert resolved_3 is resolved_1


def test_module_level_singleton_invariant() -> None:
    """Verify plugin entrypoint exports instantiated singleton per Rule 45."""
    assert plugin is not None
    assert isinstance(plugin, MantisSecurityReviewPlugin)
    assert plugin.name == "plugin.mantis_security_review"
    assert MANTIS_SECURITY_REVIEW_KEY in plugin.provides


def test_isolated_submodule_operations(tmp_path: pathlib.Path) -> None:
    """Verify submodules function independently in isolation."""
    # db
    sig = compute_stable_signature("core.py", "CWE-89", "query")
    assert len(sig) == 16

    # auditor
    code = "import os\nos.system('ls')\n"
    plan = plan_review({}, ["core.py"])
    assert plan["status"] == "ok"

    # triage
    finding_dict = {"filepath": "core.py", "line": 2, "cwe": "CWE-78", "title": "Cmd"}
    gate = review_gate(finding_dict, code)
    assert gate["status"] == "ok"

    # chains & risk
    chains = chain_exploits([
        {"id": "f1", "cwe": "CWE-798", "title": "Secret"},
        {"id": "f2", "cwe": "CWE-78", "title": "RCE"},
    ])
    assert chains["chains_constructed_count"] == 1

    risk = calibrate_risk([{"id": "f2", "severity": "critical"}], asset_criticality="critical")
    assert risk["status"] == "ok"

    # report
    rep = generate_report([{"id": "f1", "title": "Secret", "cwe": "CWE-798", "severity": "high"}])
    assert rep["status"] == "ok"
    assert "Google Mantis Security Review Packet" in rep["markdown_report"]
