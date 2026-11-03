"""Contract tests for Track 7: CI, dependencies, and test markers."""

import ast
from pathlib import Path
import yaml
import pytest


def test_ci_workflow_structure() -> None:
    """Verifies that CI workflow defines frontend job, Python 3.10 matrix, and resilient distillation."""
    ci_path = Path(".github/workflows/ci.yml")
    assert ci_path.exists(), "ci.yml must exist"

    content = ci_path.read_text(encoding="utf-8")
    config = yaml.safe_load(content)

    jobs = config.get("jobs", {})
    assert "frontend" in jobs, "CI must contain a frontend job"
    frontend_job = jobs["frontend"]
    steps = frontend_job.get("steps", [])
    step_runs = [s.get("run", "") for s in steps if "run" in s]
    combined_runs = " ".join(step_runs)

    assert "npm ci" in combined_runs, "Frontend job must install dependencies via npm ci"
    assert "npm run lint" in combined_runs, "Frontend job must run lint"
    assert "npm run build" in combined_runs, "Frontend job must build frontend"

    assert "test" in jobs, "CI must contain a test job"
    test_job = jobs["test"]
    matrix = test_job.get("strategy", {}).get("matrix", {})
    includes = matrix.get("include", [])
    python_versions = {inc.get("python-version") for inc in includes}
    assert "3.10" in python_versions, "CI matrix must include Python 3.10"
    assert "3.12" in python_versions, "CI matrix must include Python 3.12"

    # Distillation continue-on-error verification
    test_steps = test_job.get("steps", [])
    distill_step = next((s for s in test_steps if s.get("name") == "Continuous Knowledge Distillation"), None)
    assert distill_step is not None, "Distillation step must exist"
    assert distill_step.get("continue-on-error") is True, "Distillation step must have continue-on-error: true"


def test_slow_marker_on_neural_network_cli() -> None:
    """Verifies that the slow neural network training test is marked @pytest.mark.slow."""
    nn_test_path = Path("tests/test_neural_network_from_scratch.py")
    assert nn_test_path.exists()

    content = nn_test_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "test_cli_verify_json":
            dec_names = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Attribute):
                    dec_names.append(dec.attr)
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    dec_names.append(dec.func.attr)
            assert "slow" in dec_names, "test_cli_verify_json must be decorated with @pytest.mark.slow"
            assert "unit" not in dec_names, "test_cli_verify_json must not be marked unit"
            found = True
            break
    assert found, "test_cli_verify_json was not found in test_neural_network_from_scratch.py"


def test_trust_and_isolation_docs_dependencies() -> None:
    """Verifies that docs/reference/trust_and_isolation.md documents wasmtime, docker, and package policy."""
    doc_path = Path("docs/reference/trust_and_isolation.md")
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")

    assert "Wasmtime WebAssembly Isolation" in text
    assert "Docker Container Extra" in text
    assert "uv.lock" in text and "Multi-OS Pip Installation" in text
