#!/usr/bin/env python3
"""Static Cypher Safety & Trail Semantics Linter.

Provides zero-dependency static analysis of Cypher queries to intercept:
- Unbounded variable-length traversals (OOM protection)
- Single-clause diamond topologies prone to Cypher Trail Semantics row drops
- Direct mutation within MERGE patterns (duplicate node prevention)
- String-interpolated queries (injection & plan cache blowout protection)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
import sys
from typing import Any

# Rule 23: UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class LintSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(slots=True, frozen=True)
class LintDiagnostic:
    """Individual diagnostic finding from Cypher static linting."""
    rule_id: str
    severity: LintSeverity
    message: str
    line: int = 1
    snippet: str = ""
    remedy: str = ""

    def __post_init__(self) -> None:
        assert self.rule_id, "rule_id must not be empty"
        assert self.message, "message must not be empty"


@dataclass(slots=True, frozen=True)
class CypherLintReport:
    """Aggregated report across all evaluated static rules."""
    query: str
    valid: bool
    diagnostics: list[LintDiagnostic] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(d.severity == LintSeverity.ERROR for d in self.diagnostics)

    @property
    def has_warnings(self) -> bool:
        return any(d.severity == LintSeverity.WARNING for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": sum(1 for d in self.diagnostics if d.severity == LintSeverity.ERROR),
            "warning_count": sum(1 for d in self.diagnostics if d.severity == LintSeverity.WARNING),
            "diagnostics": [
                {
                    "rule_id": d.rule_id,
                    "severity": d.severity.value,
                    "message": d.message,
                    "snippet": d.snippet,
                    "remedy": d.remedy,
                }
                for d in self.diagnostics
            ],
        }


class CypherLinter:
    """Authoritative zero-dependency static analyzer for declarative Cypher queries."""

    # Unbounded traversal regex: -[*]-> or -[:REL*]-> or -[*0..]-> without an upper limit
    # Safe variants have e.g. *1..4 or *..5
    UNBOUNDED_TRAVERSAL_PATTERN = re.compile(
        r"-\s*\[\s*(?:\w+)?\s*(?::\s*[\w|]+)?\s*\*(?:0|1)?(?:\.\.)?\s*\]\s*->?",
        re.IGNORECASE,
    )

    # MERGE clause containing timestamp() or datetime() or mutation fields in match block
    MERGE_MUTATION_PATTERN = re.compile(
        r"MERGE\s*\([^)]*?(?:timestamp\s*\(\)|datetime\s*\(\)|created_at|updated_at)[^)]*?\)",
        re.IGNORECASE,
    )

    # Single MATCH clause with multiple hops forming diamond/cyclic patterns
    # (3 or more relationship arrows in a single clause before WITH/RETURN)
    MULTI_HOP_MATCH_PATTERN = re.compile(
        r"MATCH\s+((?:\([^)]+\)\s*<?-[^()\r\n]+-?>?\s*){3,}\([^)]+\))",
        re.IGNORECASE,
    )

    # Python f-string or string concatenation inside query string
    INTERPOLATION_PATTERN = re.compile(
        r"(?:\{[a-zA-Z_]\w*\}|%s|%d|\"\"\s*\+\s*\w+)",
    )

    @classmethod
    def lint(cls, query: str) -> CypherLintReport:
        """Lint a Cypher query string against production safety invariants."""
        diagnostics: list[LintDiagnostic] = []
        clean_query = query.strip()

        if not clean_query:
            diagnostics.append(
                LintDiagnostic(
                    rule_id="CYPHER-000",
                    severity=LintSeverity.ERROR,
                    message="Empty Cypher query string",
                    remedy="Provide a non-empty Cypher query statement.",
                )
            )
            return CypherLintReport(query=query, valid=False, diagnostics=diagnostics)

        # 1. Check Unbounded Variable-Length Traversal
        for match in cls.UNBOUNDED_TRAVERSAL_PATTERN.finditer(clean_query):
            snippet = match.group(0)
            # Verify if it really lacks an upper bound (e.g. does not have ..N)
            if not re.search(r"\.\.\s*\d+", snippet):
                diagnostics.append(
                    LintDiagnostic(
                        rule_id="CYPHER-001",
                        severity=LintSeverity.ERROR,
                        message="Unbounded variable-length graph traversal detected",
                        snippet=snippet,
                        remedy="Specify an explicit upper hop bound (e.g. -[:REL*1..4]->) to prevent combinatorial memory blowout.",
                    )
                )

        # 2. Check MERGE Mutation Isolation
        for match in cls.MERGE_MUTATION_PATTERN.finditer(clean_query):
            snippet = match.group(0)
            diagnostics.append(
                LintDiagnostic(
                    rule_id="CYPHER-002",
                    severity=LintSeverity.ERROR,
                    message="Mutable property or timestamp call inside MERGE match pattern",
                    snippet=snippet,
                    remedy="Isolate MERGE to immutable natural identity keys; move mutable fields to ON CREATE SET / ON MATCH SET.",
                )
            )

        # 3. Check Cypher Trail Semantics Trap on Multi-Hop Diamond Traversal
        # Check if query has chained multi-hop matches without a WITH clause
        if "WITH" not in clean_query.upper():
            for match in cls.MULTI_HOP_MATCH_PATTERN.finditer(clean_query):
                snippet = match.group(0)
                diagnostics.append(
                    LintDiagnostic(
                        rule_id="CYPHER-003",
                        severity=LintSeverity.WARNING,
                        message="Chained multi-hop match without WITH boundary may trigger Trail Semantics row drops on diamond topologies",
                        snippet=snippet[:80] + "...",
                        remedy="Split diamond traversals across separate MATCH and WITH clauses to reset relationship uniqueness scopes.",
                    )
                )

        # 4. Check String Interpolation / Parameterization
        for match in cls.INTERPOLATION_PATTERN.finditer(clean_query):
            snippet = match.group(0)
            diagnostics.append(
                LintDiagnostic(
                    rule_id="CYPHER-004",
                    severity=LintSeverity.WARNING,
                    message="Potential raw string interpolation detected in query structure",
                    snippet=snippet,
                    remedy="Use parameterized Cypher ($param or $batch) to leverage query plan caching and prevent injection.",
                )
            )

        # 5. Check Anchor Query Indexability
        # If query begins with bare MATCH (n) without label or where condition
        if re.search(r"MATCH\s*\(\s*[a-zA-Z_]\w*\s*\)\s*(?:WHERE|-[^->]+->)", clean_query, re.IGNORECASE):
            if not re.search(r"MATCH\s*\(\s*[a-zA-Z_]\w*\s*:\s*\w+", clean_query, re.IGNORECASE):
                diagnostics.append(
                    LintDiagnostic(
                        rule_id="CYPHER-005",
                        severity=LintSeverity.WARNING,
                        message="Anchor match lacks node label; will trigger expensive AllNodesScan",
                        snippet=clean_query[:50],
                        remedy="Specify a label on start nodes (e.g. MATCH (n:Person)) backed by an underlying range or text index.",
                    )
                )

        is_valid = not any(d.severity == LintSeverity.ERROR for d in diagnostics)
        return CypherLintReport(query=query, valid=is_valid, diagnostics=diagnostics)

    @classmethod
    def lint_file(cls, path: Path | str) -> CypherLintReport:
        """Read and lint Cypher queries from a file."""
        p = Path(path)
        if not p.exists():
            return CypherLintReport(
                query="",
                valid=False,
                diagnostics=[
                    LintDiagnostic(
                        rule_id="CYPHER-FILE-404",
                        severity=LintSeverity.ERROR,
                        message=f"File does not exist: {p}",
                        remedy="Check the input file path.",
                    )
                ],
            )
        content = p.read_text(encoding="utf-8")
        return cls.lint(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Static Cypher Safety & Trail Semantics Linter")
    parser.add_argument("--query", "-q", type=str, help="Raw Cypher query string to lint")
    parser.add_argument("--file", "-f", type=str, help="Path to Cypher file to lint")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if args.query:
        report = CypherLinter.lint(args.query)
    elif args.file:
        report = CypherLinter.lint_file(args.file)
    else:
        parser.print_help()
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        status_symbol = "✓ PASS" if report.valid else "✗ FAIL"
        print(f"Cypher Lint Status: {status_symbol}")
        if report.diagnostics:
            print("-" * 60)
            for d in report.diagnostics:
                print(f"[{d.severity.value}] {d.rule_id}: {d.message}")
                if d.snippet:
                    print(f"  Snippet: {d.snippet}")
                if d.remedy:
                    print(f"  Remedy:  {d.remedy}")
                print()

    sys.exit(0 if report.valid else 1)


if __name__ == "__main__":
    main()
