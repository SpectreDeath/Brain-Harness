# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
salvage.py — Deterministic Multi-Pass Cognitive Salvage Pipeline for LLM Structured Outputs.

Operationalizes local zero-token string salvage before triggering expensive LLM reprompts:
  Pass 1: Strip markdown code fences and conversational preamble/postscript
  Pass 2: Slice text between outermost { ... } or [ ... ]
  Pass 3: Eliminate trailing commas before closing braces/brackets
  Pass 4: Normalize unquoted object keys and Python boolean/null literals
  Pass 5: AST literal_eval fallback for Python dictionary structures
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 standard streams entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class StringSalvageEngine:
    @classmethod
    def salvage(cls, raw_text: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        """Execute 5-pass salvage heuristics on malformed structured output."""
        if not raw_text or not raw_text.strip():
            return None, "Empty payload string provided"

        text = raw_text.strip()

        # Pass 1: Strip markdown code fences
        fence_match = re.search(r"^```(?:json|yaml)?\s*\n([\s\S]*?)\n```", text, re.MULTILINE)
        if fence_match:
            text = fence_match.group(1).strip()
        elif text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text).strip()

        # Pass 2: Slice outermost braces or brackets
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        first_bracket = text.find("[")
        last_bracket = text.rfind("]")

        sliced = text
        if first_brace != -1 and last_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            sliced = text[first_brace : last_brace + 1]
        elif first_bracket != -1 and last_bracket != -1:
            sliced = text[first_bracket : last_bracket + 1]

        # Pass 3: Strip trailing commas: ,\s*([}\]]) -> \1
        cleaned = re.sub(r",\s*([}\]])", r"\1", sliced)

        # Direct JSON load attempt
        try:
            return json.loads(cleaned), None
        except json.JSONDecodeError:
            pass

        # Pass 4: Normalize Python literals & quote styles
        subbed = cleaned
        subbed = re.sub(r"\bTrue\b", "true", subbed)
        subbed = re.sub(r"\bFalse\b", "false", subbed)
        subbed = re.sub(r"\bNone\b", "null", subbed)

        # Unquoted keys normalization: {foo: "bar"} -> {"foo": "bar"}
        subbed = re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:", r'\1"\2":', subbed)

        # Single-quote strings to double-quotes (where not internal apostrophes)
        subbed = re.sub(r"'([^'\n\r]*)'", r'"\1"', subbed)
        subbed = re.sub(r",\s*([}\]])", r"\1", subbed)

        try:
            return json.loads(subbed), None
        except json.JSONDecodeError:
            pass

        # Pass 5: AST literal_eval fallback (for raw Python dict syntax)
        try:
            py_obj = ast.literal_eval(cleaned)
            if isinstance(py_obj, (dict, list)):
                return py_obj, None
        except (ValueError, SyntaxError):
            pass

        return None, "Failed to parse JSON after 5-pass local salvage heuristics"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic local string salvage utility for structured model outputs."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input file path containing raw LLM output, or raw string if prefixed with 'text:'.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate that salvaged output is well-formed JSON and exit 0 on success.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Optional file path to write repaired JSON to.",
    )

    args = parser.parse_args()

    # Load input
    if args.input.startswith("text:"):
        raw_text = args.input[5:]
    else:
        path = Path(args.input)
        if not path.exists():
            sys.stderr.write(f"Error: Input file does not exist: {path}\n")
            return 1
        raw_text = path.read_text(encoding="utf-8")

    salvaged_data, error_msg = StringSalvageEngine.salvage(raw_text)

    if salvaged_data is None:
        sys.stderr.write(f"Salvage Error: {error_msg}\n")
        return 1

    formatted_json = json.dumps(salvaged_data, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(formatted_json, encoding="utf-8")

    if args.validate:
        print(f"Salvage Success: Successfully salvaged {type(salvaged_data).__name__} with {len(salvaged_data)} items.")
    else:
        print(formatted_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
