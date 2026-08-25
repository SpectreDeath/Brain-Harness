"""Neuro-symbolic constraint solver and logic evaluation protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class MathEvalResult(BaseModel):
    """Result of safe mathematical expression evaluation."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    expression: str = Field(default="", description="Original mathematical expression")
    result: Any = Field(default=None, description="Computed scalar value or result")
    error: str | None = Field(default=None, description="Error explanation if evaluation failed")


class ConstraintSolveResult(BaseModel):
    """Result of finding satisfiable variable assignments."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    satisfiable: bool = Field(default=False, description="Whether constraint set is satisfiable")
    solutions_count: int = Field(default=0, description="Number of satisfying solutions discovered")
    solutions: list[dict[str, Any]] = Field(default_factory=list, description="Satisfying variable assignments")
    error: str | None = Field(default=None, description="Error explanation if solve failed")


class LogicQueryResult(BaseModel):
    """Result of evaluating a logic query against facts and Horn clauses."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    proved: bool = Field(default=False, description="Whether the query was proved")
    method: str = Field(default="unproven", description="Proof method: direct_fact, rule_deduction, or unproven")
    rule: str | None = Field(default=None, description="Horn clause rule used if deduced")
    error: str | None = Field(default=None, description="Error explanation if verification failed")


@runtime_checkable
class SymbolicSolverService(Protocol):
    """Protocol for neuro-symbolic constraint solving and logic evaluation (CPU-bound)."""

    def evaluate_math_expression(self, expression: str) -> MathEvalResult:
        """Safely calculate a mathematical expression using AST parsing."""
        ...

    def solve_constraints(
        self,
        variables: list[dict[str, Any]],
        constraints: list[str],
    ) -> ConstraintSolveResult:
        """Find satisfiable assignments for variables across constraints."""
        ...

    def verify_logic_query(
        self,
        facts: list[str],
        rules: list[str] | None = None,
        query: str = "",
    ) -> LogicQueryResult:
        """Evaluate logic query against facts and Horn clause rules."""
        ...


SYMBOLIC_SOLVER_KEY: ServiceKey[SymbolicSolverService] = ServiceKey("service.symbolic_solver")
