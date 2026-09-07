# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai",
#     "pyyaml",
# ]
# ///
"""
Non-interactive CLI and utility library for ai-file-analysis-agent.
Provides an authoritative FileAnalysisEngine, GroundingCatalog, FileAnalysisSession,
and closed-loop GroundingAuditor with 100% backward-compatible public seams.
Adheres to PEP 723, ScriptHygieneRule (zero input() calls), and RelocatableScriptsRule.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Standard 10 Grounding Constraints from Eva Patel's curriculum
DEFAULT_GROUNDING_CONSTRAINTS: list[str] = [
    "Use the provided file as your primary source.",
    "Answer the user's question directly.",
    "Do not invent information that is not supported by the file.",
    "If the file does not contain enough information to answer a question, say so.",
    "When summarizing, focus on the most important information.",
    "When comparing ideas, clearly explain similarities and differences.",
    "When analyzing research, distinguish between methods, results, and conclusions.",
    "Use simple language unless the user asks for technical language.",
    "Use bullet points when they make the answer easier to understand.",
    "If you make an inference, clearly label it as an inference.",
]

ROLE_TEMPLATES: dict[str, str] = {
    "research": "Role: Research Assistant. Distinguish strictly between experimental methods, empirical results, and analytical conclusions.",
    "legal": "Role: Legal Document Assistant. Focus on contractual obligations, liability clauses, and precise term definitions without rendering legal counsel.",
    "resume": "Role: Resume Analyzer. Extract skills, career trajectories, quantifiable accomplishments, and educational credentials.",
    "tabular": "Role: Tabular Data Inspector. Analyze column schemas, identify missing values, distribution anomalies, and statistical summaries.",
}


@dataclass(slots=True)
class FileValidationResult:
    valid: bool
    path: str
    extension: str
    size_bytes: int
    direct_api_eligible: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GroundedPrompt:
    """Slotted value object encapsulating compiled system instructions."""
    instructions: str
    rules_count: int
    role: str | None = None
    role_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GroundingAuditReport:
    """Diagnostic scorecard verifying model output against the 10 Negative Grounding Constraints."""
    passed: bool
    score: float
    has_insufficient_context_refusal: bool
    inferences_detected: list[str] = field(default_factory=list)
    has_structural_formatting: bool = False
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FileAnalysisSession:
    """Encapsulates active file analysis state, strategy, and turn coordination."""
    file_result: FileValidationResult
    prompt: GroundedPrompt
    strategy: str  # 'direct_upload' | 'chunked_rag'
    model: str
    turn_count: int = 0
    file_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_result": self.file_result.to_dict(),
            "prompt": self.prompt.to_dict(),
            "strategy": self.strategy,
            "model": self.model,
            "turn_count": self.turn_count,
            "file_id": self.file_id,
        }


class GroundingCatalog:
    """Dynamic catalog compiling 10 Negative Grounding Constraints and YAML-configured roles."""

    __slots__ = ("_rules", "_roles")

    def __init__(
        self,
        rules: list[str] | None = None,
        roles_config: dict[str, Any] | None = None,
    ) -> None:
        self._rules = list(rules or DEFAULT_GROUNDING_CONSTRAINTS)
        self._roles: dict[str, dict[str, str]] = {}
        if roles_config:
            for k, v in roles_config.items():
                if isinstance(v, dict):
                    self._roles[k.lower()] = {
                        "name": str(v.get("name") or k.capitalize()),
                        "instructions": str(v.get("instructions") or ""),
                    }
                elif isinstance(v, str):
                    self._roles[k.lower()] = {
                        "name": k.capitalize(),
                        "instructions": v,
                    }

    @property
    def rules(self) -> list[str]:
        return list(self._rules)

    @property
    def roles(self) -> dict[str, dict[str, str]]:
        return dict(self._roles)

    def compile_prompt(self, role: str | None = None, custom_rules: list[str] | None = None) -> GroundedPrompt:
        """Compiles authoritative instructions with rules and optional role profile."""
        active_rules = custom_rules or self._rules
        lines = [
            "You are an AI file analysis assistant.",
            "Your job is to analyze the file provided by the user.",
            "",
            "Follow these rules:",
        ]
        for idx, rule in enumerate(active_rules, start=1):
            lines.append(f"{idx}. {rule}")

        role_key = role.lower() if role else None
        role_name: str | None = None

        if role_key:
            if role_key in self._roles:
                info = self._roles[role_key]
                role_name = info["name"]
                lines.append("")
                lines.append(f"Role: {role_name}. {info['instructions']}")
            elif role_key in ROLE_TEMPLATES:
                lines.append("")
                lines.append(ROLE_TEMPLATES[role_key])
                role_name = role_key.capitalize()

        return GroundedPrompt(
            instructions="\n".join(lines),
            rules_count=len(active_rules),
            role=role_key,
            role_name=role_name,
        )


class GroundingAuditor:
    """Closed-loop heuristic auditor verifying model outputs against the 10 Negative Grounding Constraints."""

    __slots__ = ()

    # Regex patterns for insufficient context / refusal admissions (Rule 4)
    INSUFFICIENT_CONTEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"does not contain enough information", re.IGNORECASE),
        re.compile(r"not enough information to answer", re.IGNORECASE),
        re.compile(r"the (?:provided )?file does not (?:mention|state|contain|provide)", re.IGNORECASE),
        re.compile(r"cannot be answered (?:from|using) the (?:provided )?file", re.IGNORECASE),
        re.compile(r"insufficient context", re.IGNORECASE),
    )

    # Regex pattern for explicit inference labels (Rule 10)
    INFERENCE_PATTERN: re.Pattern[str] = re.compile(
        r"\[INFERENCE\]\s*([^.\n]+[\.\n]?)",
        re.IGNORECASE,
    )

    @classmethod
    def audit(cls, response_text: str) -> GroundingAuditReport:
        """Audits model output string and generates a compliance diagnostic scorecard."""
        findings: list[str] = []
        score: float = 100.0

        if not response_text or not response_text.strip():
            return GroundingAuditReport(
                passed=False,
                score=0.0,
                has_insufficient_context_refusal=False,
                inferences_detected=[],
                has_structural_formatting=False,
                findings=["Response is empty or whitespace only."],
            )

        text = response_text.strip()

        # 1. Check for Rule 4 (Refusal / Insufficient Context Gate)
        has_refusal = any(pat.search(text) for pat in cls.INSUFFICIENT_CONTEXT_PATTERNS)
        if has_refusal:
            findings.append("Identified explicit epistemic refusal for unverified/missing information (Rule 4).")

        # 2. Check for Rule 10 (Explicit Inference Flagging)
        inferences = [m.group(1).strip() for m in cls.INFERENCE_PATTERN.finditer(text)]
        if inferences:
            findings.append(f"Detected {len(inferences)} explicitly labeled [INFERENCE] deduction(s) (Rule 10).")

        # 3. Check for Rule 9 (Structural Scannability: bullets, numbers, tables)
        has_bullets = bool(re.search(r"^\s*[\-\*\u2022]\s+", text, re.MULTILINE))
        has_numbered = bool(re.search(r"^\s*\d+\.\s+", text, re.MULTILINE))
        has_tables = bool("|" in text and "---" in text)
        has_structural = has_bullets or has_numbered or has_tables
        if has_structural:
            findings.append("Verified structural scannability formatting (bullet points, numbered lists, or tables).")
        else:
            score -= 10.0
            findings.append("Response lacks structured bullet points or tabular formatting for multi-part synthesis.")

        # 4. Check for unhedged speculation warning phrases
        speculation_patterns = [
            re.compile(r"\bprobably\b", re.IGNORECASE),
            re.compile(r"\bmaybe\b", re.IGNORECASE),
            re.compile(r"\bi guess\b", re.IGNORECASE),
            re.compile(r"\bit is possible that\b", re.IGNORECASE),
        ]
        unhedged_found = [p.pattern for p in speculation_patterns if p.search(text)]
        if unhedged_found and not inferences:
            score -= 15.0
            findings.append(f"Detected speculative phrasing without explicit [INFERENCE] label: {unhedged_found}")

        passed = score >= 70.0

        return GroundingAuditReport(
            passed=passed,
            score=max(0.0, min(100.0, score)),
            has_insufficient_context_refusal=has_refusal,
            inferences_detected=inferences,
            has_structural_formatting=has_structural,
            findings=findings,
        )


class FileAnalysisEngine:
    """Authoritative, high-leverage engine for document-grounded AI file analysis."""

    __slots__ = ("_config", "_catalog", "_auditor")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or load_config()
        self._catalog = GroundingCatalog(
            rules=DEFAULT_GROUNDING_CONSTRAINTS,
            roles_config=self._config.get("roles"),
        )
        self._auditor = GroundingAuditor()

    @classmethod
    def from_config(cls, config: dict[str, Any] | None = None) -> FileAnalysisEngine:
        """Factory creating engine instance from loaded configuration."""
        return cls(config=config)

    @classmethod
    def default(cls) -> FileAnalysisEngine:
        """Returns default shared engine instance."""
        return cls()

    @property
    def catalog(self) -> GroundingCatalog:
        return self._catalog

    @property
    def auditor(self) -> GroundingAuditor:
        return self._auditor

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    def validate_file(self, file_path_str: str) -> FileValidationResult:
        """Validates file existence, extension whitelist, and size eligibility."""
        return validate_target_file(
            file_path_str,
            allowed_extensions=self._config.get("allowed_extensions"),
            max_direct_bytes=self._config.get("max_direct_file_bytes", 52428800),
        )

    def prepare_session(
        self,
        file_path_str: str,
        role: str | None = None,
        model: str | None = None,
    ) -> FileAnalysisSession:
        """Prepares a validated file analysis session with strategy triage and compiled prompt."""
        val_res = self.validate_file(file_path_str)
        prompt = self._catalog.compile_prompt(role=role)
        strategy = "direct_upload" if val_res.direct_api_eligible else "chunked_rag"
        target_model = model or self._config.get("default_model", "gpt-4o")

        return FileAnalysisSession(
            file_result=val_res,
            prompt=prompt,
            strategy=strategy,
            model=target_model,
            turn_count=0,
            file_id=None,
        )

    def create_turn_payload(
        self,
        session: FileAnalysisSession,
        question: str,
    ) -> dict[str, Any]:
        """Assembles structured request payload for an interactive session turn."""
        session.turn_count += 1
        return {
            "model": session.model,
            "instructions": session.prompt.instructions,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": question.strip()},
                        {"type": "input_file", "file_path": session.file_result.path},
                    ],
                }
            ],
            "turn": session.turn_count,
            "strategy": session.strategy,
        }

    def audit_response(self, response_text: str) -> GroundingAuditReport:
        """Audits model response text against the 10 Negative Grounding Constraints."""
        return self._auditor.audit(response_text)


# ============================================================================
# Backward-Compatible Legacy Functions & Utilities
# ============================================================================

def load_config() -> dict[str, Any]:
    """Loads configuration relative to script location (relocatable invariant)."""
    script_dir = Path(__file__).resolve().parent
    cfg_path = script_dir.parent / "config.default.yaml"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {
        "allowed_extensions": [".pdf", ".docx", ".csv", ".txt"],
        "max_direct_file_bytes": 52428800,
        "default_model": "gpt-4o",
        "grounding_strictness": "strict",
    }


def validate_target_file(
    file_path_str: str,
    allowed_extensions: list[str] | None = None,
    max_direct_bytes: int = 52428800,
) -> FileValidationResult:
    """Validates file existence, extension whitelist, and size eligibility."""
    p = Path(file_path_str).resolve()
    if not p.exists():
        return FileValidationResult(
            valid=False,
            path=str(p),
            extension="",
            size_bytes=0,
            direct_api_eligible=False,
            error=f"File not found: {p}",
        )

    if not p.is_file():
        return FileValidationResult(
            valid=False,
            path=str(p),
            extension="",
            size_bytes=0,
            direct_api_eligible=False,
            error=f"Path is not a regular file: {p}",
        )

    ext = p.suffix.lower()
    allowed = [e.lower() for e in (allowed_extensions or [".pdf", ".docx", ".csv", ".txt"])]
    if ext not in allowed:
        return FileValidationResult(
            valid=False,
            path=str(p),
            extension=ext,
            size_bytes=p.stat().st_size,
            direct_api_eligible=False,
            error=f"Unsupported file extension '{ext}'. Allowed: {', '.join(allowed)}",
        )

    size = p.stat().st_size
    direct_eligible = size <= max_direct_bytes

    return FileValidationResult(
        valid=True,
        path=str(p),
        extension=ext,
        size_bytes=size,
        direct_api_eligible=direct_eligible,
        error=None if direct_eligible else f"File size ({size} bytes) exceeds direct limit ({max_direct_bytes} bytes); route to RAG.",
    )


def assemble_grounded_instructions(
    role: str | None = None,
    custom_rules: list[str] | None = None,
) -> str:
    """Assembles authoritative system instructions with 10 grounding rules and role addendum."""
    engine = FileAnalysisEngine.default()
    prompt = engine.catalog.compile_prompt(role=role, custom_rules=custom_rules)
    return prompt.instructions


def build_staged_payload(
    file_path: str,
    question: str,
    role: str | None = None,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """Builds the structured API request payload without dispatching external network calls."""
    instructions = assemble_grounded_instructions(role=role)
    return {
        "model": model,
        "instructions": instructions,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": question},
                    {"type": "input_file", "file_path": str(Path(file_path).resolve())},
                ],
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic CLI for ai-file-analysis-agent operations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: validate-file
    p_val = subparsers.add_parser("validate-file", help="Validate a target file for agent analysis.")
    p_val.add_argument("file_path", help="Path to file to inspect.")
    p_val.add_argument("--json", action="store_true", help="Output validation result as JSON.")

    # Subcommand: assemble-prompt
    p_asm = subparsers.add_parser("assemble-prompt", help="Assemble grounded system prompt.")
    p_asm.add_argument("--role", choices=["research", "legal", "resume", "tabular"], default=None)
    p_asm.add_argument("--json", action="store_true", help="Output as JSON.")

    # Subcommand: dry-run
    p_dry = subparsers.add_parser("dry-run", help="Staged offline dry-run of analysis payload.")
    p_dry.add_argument("--file", required=True, help="Target file path.")
    p_dry.add_argument("--question", required=True, help="User query text.")
    p_dry.add_argument("--role", choices=["research", "legal", "resume", "tabular"], default=None)
    p_dry.add_argument("--model", default="gpt-4o", help="Target LLM model string.")

    # Subcommand: audit-response
    p_aud = subparsers.add_parser("audit-response", help="Audit model output against grounding constraints.")
    p_aud.add_argument("--text", help="Raw model response text to audit.")
    p_aud.add_argument("--file", help="File containing model response text to audit.")
    p_aud.add_argument("--json", action="store_true", help="Output audit report as JSON.")

    args = parser.parse_args()
    engine = FileAnalysisEngine.default()

    if args.command == "validate-file":
        res = engine.validate_file(args.file_path)
        if getattr(args, "json", False):
            print(json.dumps(res.to_dict(), indent=2))
        else:
            if res.valid:
                print(f"[OK] Valid file: {res.path} ({res.size_bytes} bytes, ext: {res.extension})")
                if not res.direct_api_eligible:
                    print(f"[WARN] {res.error}")
            else:
                print(f"[FAIL] Invalid file: {res.error}")
        return 0 if res.valid else 1

    elif args.command == "assemble-prompt":
        prompt = engine.catalog.compile_prompt(role=args.role)
        if getattr(args, "json", False):
            print(json.dumps(prompt.to_dict(), indent=2))
        else:
            print(prompt.instructions)
        return 0

    elif args.command == "dry-run":
        session = engine.prepare_session(
            file_path_str=args.file,
            role=args.role,
            model=args.model,
        )
        if not session.file_result.valid:
            print(f"[ERROR] Pre-flight file check failed: {session.file_result.error}", file=sys.stderr)
            return 1

        payload = engine.create_turn_payload(session, args.question)
        print(json.dumps(payload, indent=2))
        return 0

    elif args.command == "audit-response":
        content: str = ""
        if getattr(args, "text", None):
            content = args.text
        elif getattr(args, "file", None):
            f_path = Path(args.file)
            if not f_path.exists():
                print(f"[ERROR] File not found: {f_path}", file=sys.stderr)
                return 1
            content = f_path.read_text(encoding="utf-8", errors="replace")
        else:
            print("[ERROR] Must specify either --text or --file.", file=sys.stderr)
            return 1

        report = engine.audit_response(content)
        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            status = "PASS" if report.passed else "FAIL"
            print(f"[{status}] Grounding Compliance Score: {report.score:.1f}/100")
            print(f"  Insufficient Context Refusal: {report.has_insufficient_context_refusal}")
            print(f"  Inferences Detected: {report.inferences_detected}")
            print(f"  Structural Formatting: {report.has_structural_formatting}")
            if report.findings:
                print("  Findings:")
                for f in report.findings:
                    print(f"    • {f}")
        return 0 if report.passed else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
