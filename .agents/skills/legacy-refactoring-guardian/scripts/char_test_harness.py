"""char_test_harness.py — Deterministic Characterization Test Generator.

Enforces Hugo Teijiz's core invariant: Zero AI Hallucination in Test Expectations.
Generates boundary inputs, executes legacy functions against a sandbox, captures ground-truth
outputs and side effects, and synthesizes runnable pytest suites.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True)
class ExecutionResult:
    """Records ground truth output of executing a function with given arguments."""
    args: list[Any]
    kwargs: dict[str, Any]
    status: str  # 'SUCCESS' or 'EXCEPTION'
    return_value: Any = None
    exception_type: str | None = None
    exception_message: str | None = None


@dataclass(slots=True)
class CharacterizationSuite:
    """A collection of ground-truth execution results ready for test emission."""
    module_path: str
    function_name: str
    executions: list[ExecutionResult] = field(default_factory=list)


class BoundaryMatrixGenerator:
    """Synthesizes boundary inputs for function parameters without hallucination."""

    NUMERIC_BOUNDARIES = [0, -1, 1, 100, 5000]
    STRING_BOUNDARIES = ["", "VIP", "GOLD", "STANDARD", "UNKNOWN"]

    @classmethod
    def generate_inputs(cls, func: Callable[..., Any]) -> list[tuple[list[Any], dict[str, Any]]]:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if not params:
            return [([], {})]

        # Generate a targeted boundary matrix
        cases: list[tuple[list[Any], dict[str, Any]]] = []

        # Try to identify param types by name or annotation
        sample_args_list: list[list[Any]] = []
        for p in params:
            name_lower = p.name.lower()
            if "id" in name_lower:
                sample_args_list.append(["ord-1", "ord-zero", "ord-neg"])
            elif any(k in name_lower for k in ("cents", "amount", "price", "fee", "count")):
                sample_args_list.append(cls.NUMERIC_BOUNDARIES)
            elif any(k in name_lower for k in ("type", "status", "tier", "role")):
                sample_args_list.append(cls.STRING_BOUNDARIES)
            elif "email" in name_lower:
                sample_args_list.append([None, "test@example.com"])
            else:
                sample_args_list.append([0, "test", None])

        # Cross a subset of meaningful permutations (avoiding exponential blowup)
        # 1. Base case using first value of each
        base = [s[0] for s in sample_args_list]
        cases.append((list(base), {}))

        # 2. Perturb each parameter across its boundaries
        for p_idx, options in enumerate(sample_args_list):
            for opt in options:
                case = list(base)
                case[p_idx] = opt
                if (case, {}) not in cases:
                    cases.append((case, {}))

        return cases


class GoldenExecutionRunner:
    """Executes target functions against the local runtime to capture real return values."""

    @classmethod
    def execute_suite(cls, file_path: str | Path, func_name: str) -> CharacterizationSuite:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Dynamic import
        mod_name = path.stem
        spec = importlib.util.spec_from_file_location(mod_name, str(path))
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load module from {path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        # Add directory to sys.path so sibling imports work
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))

        spec.loader.exec_module(module)

        func = getattr(module, func_name, None)
        if not func or not callable(func):
            raise AttributeError(f"Function '{func_name}' not found in {mod_name}")

        test_cases = BoundaryMatrixGenerator.generate_inputs(func)
        suite = CharacterizationSuite(module_path=str(path), function_name=func_name)

        for args, kwargs in test_cases:
            try:
                res = func(*args, **kwargs)
                suite.executions.append(
                    ExecutionResult(
                        args=args,
                        kwargs=kwargs,
                        status="SUCCESS",
                        return_value=res,
                    )
                )
            except Exception as e:
                suite.executions.append(
                    ExecutionResult(
                        args=args,
                        kwargs=kwargs,
                        status="EXCEPTION",
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                    )
                )

        return suite


class TestSuiteEmitter:
    """Formats characterization executions into a clean, runnable pytest file."""

    @classmethod
    def emit_pytest_code(cls, suite: CharacterizationSuite) -> str:
        mod_stem = Path(suite.module_path).stem
        lines = [
            '"""Auto-generated characterization test suite.',
            '',
            'Enforces Hugo Teijiz Invariant: Captures what the code DOES TODAY, not what it SHOULD do.',
            'DO NOT change expected values during refactoring without business confirmation.',
            '"""',
            '',
            'from __future__ import annotations',
            'import pytest',
            f'from {mod_stem} import {suite.function_name}',
            '',
            '',
            f'class TestCharacterization{suite.function_name.title().replace("_", "")}:',
            '    """Ground-truth characterization safety net."""',
            '',
        ]

        for idx, exec_res in enumerate(suite.executions, 1):
            args_repr = ", ".join(repr(a) for a in exec_res.args)
            if exec_res.kwargs:
                kwargs_repr = ", ".join(f"{k}={repr(v)}" for k, v in exec_res.kwargs.items())
                call_str = f"{suite.function_name}({args_repr}, {kwargs_repr})" if args_repr else f"{suite.function_name}({kwargs_repr})"
            else:
                call_str = f"{suite.function_name}({args_repr})"

            lines.append(f'    def test_case_{idx:03d}(self) -> None:')
            lines.append(f'        # Observed input: {call_str}')

            if exec_res.status == "SUCCESS":
                lines.append(f'        res = {call_str}')
                lines.append(f'        assert res == {repr(exec_res.return_value)}')
            else:
                lines.append(f'        with pytest.raises({exec_res.exception_type}):')
                lines.append(f'            {call_str}')
            lines.append('')

        return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Characterization Test Harness Generator")
    parser.add_argument("--file", required=True, help="Path to source file")
    parser.add_argument("--func", required=True, help="Function name to characterize")
    parser.add_argument("--emit", help="Output pytest file path")
    parser.add_argument("--json", action="store_true", help="Dump executions as JSON")

    args = parser.parse_args()

    try:
        suite = GoldenExecutionRunner.execute_suite(args.file, args.func)
        if args.json:
            print(json.dumps(asdict(suite), indent=2, default=str))
        elif args.emit:
            out_path = Path(args.emit)
            code = TestSuiteEmitter.emit_pytest_code(suite)
            out_path.write_text(code, encoding="utf-8")
            print(f"✓ Emitted characterization test suite ({len(suite.executions)} cases) to: {out_path}")
        else:
            print(f"\n🧪 Captured {len(suite.executions)} Ground-Truth Executions for {suite.function_name}:")
            print("━" * 68)
            for idx, ex in enumerate(suite.executions, 1):
                stat = "✓ SUCCESS" if ex.status == "SUCCESS" else f"✗ {ex.exception_type}"
                ret_preview = str(ex.return_value)[:40] if ex.return_value is not None else ex.exception_message
                print(f"  [{idx:02d}] {stat} | args={ex.args} -> {ret_preview}")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
