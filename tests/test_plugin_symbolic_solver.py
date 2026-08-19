"""Tests for symbolic_solver plugin."""

from __future__ import annotations

import pytest

from plugins.symbolic_solver.main import (
    evaluate_math_expression,
    solve_constraints,
    verify_logic_query,
)


@pytest.mark.unit
class TestSymbolicSolverPlugin:
    def test_evaluate_math_expression(self) -> None:
        res = evaluate_math_expression("2 ** 8 + (100 * 3.5) / sqrt(25)")
        assert res["status"] == "ok"
        # 256 + 350 / 5 = 256 + 70 = 326.0
        assert res["result"] == 326.0

        # Syntax error handling
        res_err = evaluate_math_expression("2 ++/ 3")
        assert res_err["status"] == "error"

    def test_solve_constraints(self) -> None:
        variables = [
            {"name": "x", "min": 0, "max": 10},
            {"name": "y", "min": 0, "max": 10},
        ]
        constraints = [
            "x + y == 10",
            "x > 6",
        ]
        res = solve_constraints(variables, constraints)
        assert res["status"] == "ok"
        assert res["satisfiable"] is True
        assert res["solutions_count"] >= 1
        for sol in res["solutions"]:
            assert sol["x"] + sol["y"] == 10
            assert sol["x"] > 6

    def test_verify_logic_query(self) -> None:
        facts = ["parent(alice, bob)", "parent(bob, charlie)"]
        rules = ["grandparent(alice, charlie) :- parent(alice, bob), parent(bob, charlie)"]

        # Direct fact
        res1 = verify_logic_query(facts, query="parent(alice, bob)")
        assert res1["proved"] is True
        assert res1["method"] == "direct_fact"

        # Deduced rule
        res2 = verify_logic_query(facts, rules=rules, query="grandparent(alice, charlie)")
        assert res2["proved"] is True
        assert res2["method"] == "rule_deduction"

        # Unproven query
        res3 = verify_logic_query(facts, rules=rules, query="parent(alice, david)")
        assert res3["proved"] is False
