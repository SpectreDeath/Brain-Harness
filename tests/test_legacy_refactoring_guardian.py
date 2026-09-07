"""Comprehensive unit and integration test suite for legacy-refactoring-guardian.

Asserts:
1. AST Codebase Archaeologist capability tracing, implicit contract discovery, and seam identification.
2. Characterization test harness input matrix generation, golden execution capture, and pytest code emission.
3. Modernization configuration defaults integrity.
4. Full behavioral fidelity between legacy billing and refactored seam billing implementations.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

SKILL_DIR = Path(__file__).parent.parent / ".agents" / "skills" / "legacy-refactoring-guardian"
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXAMPLES_DIR = SKILL_DIR / "examples" / "legacy-billing-service"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from legacy_archaeologist import CapabilityArchaeologist, CapabilityTrace
from char_test_harness import BoundaryMatrixGenerator, GoldenExecutionRunner, TestSuiteEmitter


@pytest.mark.unit
class TestLegacyArchaeologist:
    """Validates AST analysis, call graphs, contracts, and candidate seams."""

    @pytest.fixture
    def billing_file(self) -> Path:
        return EXAMPLES_DIR / "legacy_billing.py"

    def test_trace_file_extracts_parameters_and_calls(self, billing_file: Path) -> None:
        trace = CapabilityArchaeologist.trace_file(billing_file, "process_billing")
        assert trace.function_name == "process_billing"
        assert trace.parameters == ["order_id", "amount_cents", "customer_type", "email"]
        assert trace.cyclomatic_complexity_hint >= 5
        assert "_GLOBAL_DB.save_order" in trace.internal_calls
        assert "_GLOBAL_EMAIL.send" in trace.internal_calls
        assert "max" in trace.internal_calls

    def test_trace_file_discovers_implicit_contracts(self, billing_file: Path) -> None:
        trace = CapabilityArchaeologist.trace_file(billing_file, "process_billing")
        types = [c.contract_type for c in trace.implicit_contracts]
        assert "return_dict" in types
        assert "db_write" in types
        assert "email_send" in types

        # Check return dict fields
        ret_contract = next(c for c in trace.implicit_contracts if c.contract_type == "return_dict")
        assert "status" in ret_contract.fields_or_args
        assert "order_id" in ret_contract.fields_or_args
        assert "total_cents" in ret_contract.fields_or_args
        assert "fee_cents" in ret_contract.fields_or_args

    def test_trace_file_identifies_candidate_seams(self, billing_file: Path) -> None:
        trace = CapabilityArchaeologist.trace_file(billing_file, "process_billing")
        seam_symbols = [s.target_symbol for s in trace.candidate_seams]
        assert "_GLOBAL_DB" in seam_symbols
        assert "_GLOBAL_EMAIL" in seam_symbols
        assert all(s.seam_type == "parameter_injection" for s in trace.candidate_seams)

    def test_mermaid_dag_generation(self, billing_file: Path) -> None:
        trace = CapabilityArchaeologist.trace_file(billing_file, "process_billing")
        assert "graph TD" in trace.mermaid_dag
        assert "Entry: process_billing" in trace.mermaid_dag
        assert "Return Contract" in trace.mermaid_dag
        assert "Side Effect" in trace.mermaid_dag


@pytest.mark.unit
class TestCharTestHarness:
    """Validates deterministic test matrix generation and golden execution capture."""

    @pytest.fixture
    def billing_file(self) -> Path:
        return EXAMPLES_DIR / "legacy_billing.py"

    def test_golden_execution_runner_captures_legacy_quirks(self, billing_file: Path) -> None:
        suite = GoldenExecutionRunner.execute_suite(billing_file, "process_billing")
        assert len(suite.executions) >= 10

        # Find zero amount execution
        zero_exec = next(
            (e for e in suite.executions if len(e.args) >= 2 and e.args[1] == 0),
            None,
        )
        assert zero_exec is not None
        assert zero_exec.status == "SUCCESS"
        # Zero amount legacy quirk: fee_cents is 100
        assert zero_exec.return_value["fee_cents"] == 100
        assert zero_exec.return_value["total_cents"] == 100

    def test_test_suite_emitter_produces_valid_pytest_code(self, billing_file: Path) -> None:
        suite = GoldenExecutionRunner.execute_suite(billing_file, "process_billing")
        code = TestSuiteEmitter.emit_pytest_code(suite)
        assert "class TestCharacterizationProcessBilling:" in code
        assert "def test_case_001(self) -> None:" in code
        assert "assert res ==" in code
        assert "Hugo Teijiz Invariant" in code


@pytest.mark.unit
class TestModernizationConfig:
    """Validates configuration schema and fallback resolution."""

    def test_config_file_exists_and_contains_expected_keys(self) -> None:
        config_path = SKILL_DIR / "config.default.yaml"
        assert config_path.exists()
        text = config_path.read_text(encoding="utf-8")
        assert "test_framework: pytest" in text
        assert "quarantine_defects: true" in text
        assert "capture_side_effects: true" in text
        assert "boundary_test_values:" in text


@pytest.mark.integration
class TestExemplarModernizationFidelity:
    """Validates 100% behavioral fidelity between legacy and refactored seam billing."""

    def test_behavioral_equivalence_across_boundary_inputs(self) -> None:
        from legacy_billing import process_billing as legacy_process, _GLOBAL_DB as leg_db, _GLOBAL_EMAIL as leg_email
        from refactored_billing import process_billing as refactored_process

        test_cases = [
            ("ord-0", 0, "STANDARD", None),
            ("ord-1", 5000, "VIP", "vip@example.com"),
            ("ord-2", 2000, "GOLD", None),
            ("ord-3", 100, "STANDARD", "std@example.com"),
            ("ord-4", -500, "VIP", None),
            ("ord-5", 10000, "GOLD", "gold@example.com"),
        ]

        for order_id, amount, cust_type, email in test_cases:
            leg_db.records.clear()
            leg_email.sent_emails.clear()

            res_leg = legacy_process(order_id, amount, cust_type, email=email)
            db_leg = dict(leg_db.records)
            email_leg = list(leg_email.sent_emails)

            leg_db.records.clear()
            leg_email.sent_emails.clear()

            res_ref = refactored_process(order_id, amount, cust_type, email=email)
            db_ref = dict(leg_db.records)
            email_ref = list(leg_email.sent_emails)

            # Assert complete observable behavioral equivalence
            assert res_leg == res_ref, f"Return mismatch for case {amount} / {cust_type}"
            assert db_leg == db_ref, f"DB write mismatch for case {amount} / {cust_type}"
            assert email_leg == email_ref, f"Email notification mismatch for case {amount} / {cust_type}"
