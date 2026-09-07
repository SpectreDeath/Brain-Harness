"""legacy_archaeologist.py — AST Capability Tracer & Seam Identifier for Legacy Modernization.

Part of the legacy-refactoring-guardian skill.
Provides deterministic AST analysis of legacy functions, call graphs, implicit contracts, and seams.
"""

from __future__ import annotations

import ast
import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True)
class ImplicitContract:
    """Represents an implicit contract or external dependency observed in the AST."""
    contract_type: str  # 'return_dict', 'db_write', 'event_emit', 'email_send', 'log'
    expression: str
    line_number: int
    fields_or_args: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CandidateSeam:
    """Represents a coupling site suitable for mechanical seam introduction."""
    seam_type: str  # 'parameter_injection', 'global_access', 'external_call'
    target_symbol: str
    line_number: int
    recommendation: str


@dataclass(slots=True)
class CapabilityTrace:
    """Full architectural archaeological trace of a single capability."""
    function_name: str
    file_path: str
    line_start: int
    line_end: int
    parameters: list[str]
    internal_calls: list[str]
    implicit_contracts: list[ImplicitContract]
    candidate_seams: list[CandidateSeam]
    cyclomatic_complexity_hint: int
    mermaid_dag: str


class CapabilityVisitor(ast.NodeVisitor):
    """AST visitor traversing a specific function to map its execution flow."""

    def __init__(self, target_function: str) -> None:
        self.target_function = target_function
        self.func_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None
        self.calls: list[str] = []
        self.contracts: list[ImplicitContract] = []
        self.seams: list[CandidateSeam] = []
        self.complexity_count = 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == self.target_function:
            self.func_node = node
            self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.name == self.target_function:
            self.func_node = node
            self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for child in ast.walk(node):
            # Complexity estimate
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
                self.complexity_count += 1

            # Calls
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child.func)
                if call_name:
                    self.calls.append(call_name)
                    # Detect side effects
                    if any(kw in call_name.lower() for kw in ("save", "insert", "update", "delete", "execute")):
                        self.contracts.append(ImplicitContract("db_write", call_name, child.lineno))
                    elif any(kw in call_name.lower() for kw in ("send", "notify", "mail")):
                        self.contracts.append(ImplicitContract("email_send", call_name, child.lineno))
                    elif any(kw in call_name.lower() for kw in ("emit", "publish", "dispatch")):
                        self.contracts.append(ImplicitContract("event_emit", call_name, child.lineno))
                    elif any(kw in call_name.lower() for kw in ("log", "info", "warning", "error")):
                        self.contracts.append(ImplicitContract("log", call_name, child.lineno))

            # Return dictionaries (Implicit API / service response contracts)
            if isinstance(child, ast.Return) and child.value and isinstance(child.value, ast.Dict):
                keys = []
                for k in child.value.keys:
                    if isinstance(k, ast.Constant):
                        keys.append(str(k.value))
                self.contracts.append(
                    ImplicitContract(
                        contract_type="return_dict",
                        expression="return {...}",
                        line_number=child.lineno,
                        fields_or_args=keys,
                    )
                )

            # Detect global object access (Candidate for parameter injection seam)
            if isinstance(child, ast.Name) and child.id.startswith("_GLOBAL_"):
                self.seams.append(
                    CandidateSeam(
                        seam_type="parameter_injection",
                        target_symbol=child.id,
                        line_number=child.lineno,
                        recommendation=f"Inject {child.id} via optional parameter with default fallback",
                    )
                )

    @staticmethod
    def _get_call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = CapabilityVisitor._get_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""


class CapabilityArchaeologist:
    """Public facade for AST capability extraction and seam discovery."""

    @classmethod
    def trace_file(cls, file_path: str | Path, target_function: str) -> CapabilityTrace:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Target file does not exist: {path}")

        source_code = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source_code, filename=str(path))

        visitor = CapabilityVisitor(target_function)
        visitor.visit(tree)

        if not visitor.func_node:
            raise ValueError(f"Function '{target_function}' not found in {path}")

        node = visitor.func_node
        params = [arg.arg for arg in node.args.args]
        calls_clean = list(dict.fromkeys(visitor.calls))

        # Build Mermaid DAG
        mermaid = cls._generate_mermaid(target_function, params, calls_clean, visitor.contracts)

        return CapabilityTrace(
            function_name=target_function,
            file_path=str(path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            parameters=params,
            internal_calls=calls_clean,
            implicit_contracts=visitor.contracts,
            candidate_seams=visitor.seams,
            cyclomatic_complexity_hint=visitor.complexity_count,
            mermaid_dag=mermaid,
        )

    @staticmethod
    def _generate_mermaid(
        func_name: str,
        params: list[str],
        calls: list[str],
        contracts: list[ImplicitContract],
    ) -> str:
        lines = [
            "graph TD",
            f'    Entry["Entry: {func_name}({", ".join(params)})"]',
            '    Logic["Business Rules & Logic"]',
            "    Entry --> Logic",
        ]
        for c in contracts:
            if c.contract_type == "return_dict":
                fields_str = ", ".join(c.fields_or_args[:4])
                lines.append(f'    Contract["Return Contract: {{{fields_str}...}}"]')
                lines.append("    Logic --> Contract")
            elif c.contract_type in ("db_write", "email_send", "event_emit"):
                clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", c.expression)
                lines.append(f'    SideEffect_{clean_name}["Side Effect: {c.expression}"]')
                lines.append(f"    Logic --> SideEffect_{clean_name}")

        return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="AST Codebase Archaeologist & Capability Tracer")
    parser.add_argument("--file", required=True, help="Path to source file")
    parser.add_argument("--function", required=True, help="Target function name to trace")
    parser.add_argument("--json", action="store_true", help="Output trace as JSON")
    parser.add_argument("--mermaid", action="store_true", help="Print generated Mermaid DAG")

    args = parser.parse_args()

    try:
        trace = CapabilityArchaeologist.trace_file(args.file, args.function)
        if args.json:
            print(json.dumps(asdict(trace), indent=2))
        elif args.mermaid:
            print(trace.mermaid_dag)
        else:
            print(f"\n🏛️  Archaeological Trace: {trace.function_name} ({trace.file_path}:{trace.line_start}-{trace.line_end})")
            print("━" * 68)
            print(f"Parameters: {', '.join(trace.parameters)}")
            print(f"Complexity Hint: {trace.cyclomatic_complexity_hint}")
            print(f"Calls ({len(trace.internal_calls)}): {', '.join(trace.internal_calls)}")
            print(f"\nImplicit Contracts ({len(trace.implicit_contracts)}):")
            for c in trace.implicit_contracts:
                desc = f"[{c.contract_type.upper()}] {c.expression} (L{c.line_number})"
                if c.fields_or_args:
                    desc += f" -> fields: {c.fields_or_args}"
                print(f"  • {desc}")
            print(f"\nCandidate Seams ({len(trace.candidate_seams)}):")
            for s in trace.candidate_seams:
                print(f"  ⚡ [{s.seam_type}] {s.target_symbol} (L{s.line_number}): {s.recommendation}")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
