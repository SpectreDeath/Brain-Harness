"""Neuro-symbolic constraint solver and logic evaluation tools."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

# Allowed safe binary operators
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "sin": math.sin,
    "cos": math.cos,
    "log": math.log,
}


def _safe_eval_node(node: ast.AST, env: dict[str, Any]) -> Any:
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body, env)
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        elif node.id in _SAFE_FUNCTIONS:
            return _SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable or symbol: '{node.id}'")
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval_node(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.Not):
            return not operand
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    elif isinstance(node, ast.BinOp):
        left = _safe_eval_node(node.left, env)
        right = _safe_eval_node(node.right, env)
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    elif isinstance(node, ast.Compare):
        left = _safe_eval_node(node.left, env)
        for op, comparator in zip(node.ops, node.comparators):
            right = _safe_eval_node(comparator, env)
            op_type = type(op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported comparison operator: {op_type}")
            if not _SAFE_OPERATORS[op_type](left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.Call):
        func = _safe_eval_node(node.func, env)
        args = [_safe_eval_node(arg, env) for arg in node.args]
        return func(*args)
    else:
        raise TypeError(f"Unsupported expression construct: {type(node)}")


def evaluate_math_expression(expression: str) -> dict[str, Any]:
    """Safely calculate a mathematical expression using AST parsing."""
    try:
        cleaned = expression.strip()
        parsed = ast.parse(cleaned, mode="eval")
        result = _safe_eval_node(parsed, {})
        return {"status": "ok", "expression": expression, "result": result}
    except Exception as e:
        return {"status": "error", "error": f"Evaluation error: {e!s}"}


def solve_constraints(
    variables: list[dict[str, Any]],
    constraints: list[str],
) -> dict[str, Any]:
    """Find satisfiable assignments for integer/float variables across constraints."""
    try:
        # Parse constraint ASTs
        parsed_constraints = [ast.parse(c.strip(), mode="eval") for c in constraints]

        # Generate search ranges
        var_names: list[str] = []
        var_domains: list[list[Any]] = []

        for v in variables:
            name = v["name"]
            min_v = int(v.get("min", 0))
            max_v = int(v.get("max", 10))
            var_names.append(name)
            var_domains.append(list(range(min_v, max_v + 1)))

        solutions: list[dict[str, Any]] = []

        def _search(index: int, current_env: dict[str, Any]) -> None:
            if len(solutions) >= 10:
                return

            if index == len(var_names):
                # Check all constraints
                for c_ast in parsed_constraints:
                    try:
                        if not bool(_safe_eval_node(c_ast, current_env)):
                            return
                    except Exception:
                        return
                solutions.append(dict(current_env))
                return

            name = var_names[index]
            for val in var_domains[index]:
                current_env[name] = val
                _search(index + 1, current_env)
                if len(solutions) >= 10:
                    break

        _search(0, {})

        return {
            "status": "ok",
            "satisfiable": len(solutions) > 0,
            "solutions_count": len(solutions),
            "solutions": solutions,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _split_top_level_premises(body: str) -> list[str]:
    """Split comma-separated premises taking care not to split inside predicate parentheses."""
    premises: list[str] = []
    current: list[str] = []
    paren_depth = 0
    for char in body:
        if char == "(":
            paren_depth += 1
            current.append(char)
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
            current.append(char)
        elif char == "," and paren_depth == 0:
            premises.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        premises.append("".join(current).strip())
    return [p for p in premises if p]


def verify_logic_query(
    facts: list[str],
    rules: list[str] | None = None,
    query: str = "",
) -> dict[str, Any]:
    """Evaluate logic query against facts database."""
    try:
        fact_set = {f.strip() for f in facts}
        q = query.strip()

        # Direct fact lookup
        if q in fact_set:
            return {"status": "ok", "proved": True, "method": "direct_fact"}

        # Rule evaluation (Horn clauses: Head :- Body1, Body2)
        if rules:
            for rule in rules:
                if ":-" in rule:
                    head, body = rule.split(":-", 1)
                    head = head.strip()
                    premises = _split_top_level_premises(body)
                    if head == q and all(p in fact_set for p in premises):
                        return {
                            "status": "ok",
                            "proved": True,
                            "method": "rule_deduction",
                            "rule": rule,
                        }

        return {"status": "ok", "proved": False, "method": "unproven"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
