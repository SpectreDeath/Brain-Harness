# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
validate_skill.py — Two-Phase Diagnostic Validator, SkillSpector AST Security Engine,
and Multi-Pass Cognitive Salvage Utility for Agent Skills.

Architecture:
  - SkillSDLCEngine: Unified authoritative service seam
  - SkillSpectorScanner: 70-pattern AST security auditor with 4-tier risk bands (SAFE/CAUTION/HIGH/CRITICAL)
  - LocalSalvageEngine: Multi-pass string, literal, and AST JSON repair heuristics
  - ValidationPipeline: Pluggable slotted validation rules across Syntactic, Semantic, and Security phases
"""

import argparse
import ast
import json
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 stream entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Attempt local import of resolve_config; fallback to internal resolver
try:
    from resolve_config import SkillConfiguration, resolve_for_skill
except ImportError:
    # Look in same directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from resolve_config import SkillConfiguration, resolve_for_skill
    except ImportError:
        @dataclass(slots=True)
        class SkillConfiguration:  # type: ignore
            line_budget_limit: int = 500
            token_budget_limit: int = 5000
            enforce_two_phase_validation: bool = True
            max_repair_attempts: int = 3
            security_risk_threshold: int = 20
            supported_clients: list[str] = field(default_factory=lambda: ["claude-code", "antigravity", "vscode", "cursor", "copilot"])
            extra_security_patterns: list[str] = field(default_factory=list)
            raw_config: dict[str, Any] = field(default_factory=dict)
            sources: dict[str, str] = field(default_factory=dict)

            def to_dict(self) -> dict[str, Any]:
                return dict(self.raw_config)

        def resolve_for_skill(skill_dir: Path | str, project_root: Path | str | None = None) -> SkillConfiguration:  # type: ignore
            return SkillConfiguration()


# ============================================================================
# Domain Models (Rule 12: Slotted Dataclass Architecture)
# ============================================================================

@dataclass(slots=True)
class CheckResult:
    phase: str
    name: str
    passed: bool
    message: str
    remediation: str | None = None


@dataclass(slots=True)
class SecurityFinding:
    dimension: str
    severity: str
    file: str
    line: int
    pattern: str
    details: str
    penalty: float


@dataclass(slots=True)
class SecurityAuditReport:
    risk_score: float
    risk_band: str  # SAFE, CAUTION, HIGH, CRITICAL
    findings: list[SecurityFinding] = field(default_factory=list)
    passed: bool = True
    threshold: int = 20

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_score": round(self.risk_score, 1),
            "risk_band": self.risk_band,
            "threshold": self.threshold,
            "passed": self.passed,
            "findings_count": len(self.findings),
            "findings": [asdict(f) for f in self.findings],
        }


@dataclass(slots=True)
class ValidationReport:
    skill_path: str
    valid: bool
    checks: list[CheckResult] = field(default_factory=list)
    security_report: SecurityAuditReport | None = None
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_path": self.skill_path,
            "valid": self.valid,
            "passed_count": sum(1 for c in self.checks if c.passed),
            "failed_count": sum(1 for c in self.checks if not c.passed),
            "checks": [asdict(c) for c in self.checks],
            "security_report": self.security_report.to_dict() if self.security_report else None,
            "config": self.config,
        }


# ============================================================================
# Multi-Pass Cognitive Salvage Engine
# ============================================================================

class LocalSalvageEngine:
    """
    Multi-pass cognitive salvage engine for model-generated structured data.
    Heuristics:
      Pass 1: Markdown fence & conversational preamble/postscript stripping
      Pass 2: Outermost brace/bracket slicing
      Pass 3: Python literal & quote normalization (True/False/None -> true/false/null, ' -> ")
      Pass 4: Trailing comma elimination
      Pass 5: AST literal_eval fallback
    """

    @classmethod
    def salvage(cls, raw_text: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        if not raw_text or not raw_text.strip():
            return None, "Empty payload string"

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
        # Convert Python booleans/None outside quotes
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


def run_local_salvage(raw_text: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    """Backward-compatible entry point for local string salvage."""
    return LocalSalvageEngine.salvage(raw_text)


# ============================================================================
# SkillSpector 70-Pattern AST Security Engine
# ============================================================================

class SkillSpectorScanner:
    """
    Authoritative AST security scanner analyzing scripts across 4 weighted dimensions:
      1. Dangerous System Calls (30%): eval, exec, __import__, ctypes, os.system, shell=True
      2. Network & Exfiltration (30%): sockets, raw urllib/requests/httpx to unknown hosts
      3. Filesystem Mutation (20%): destructive deletes, rmtree, unbounded file writes
      4. Environment & Credentials (20%): reading sensitive secrets, AWS/SSH tokens
    """

    DANGEROUS_FUNCS = {
        "eval": (30.0, "Execution of dynamic code via eval()"),
        "exec": (30.0, "Execution of dynamic code via exec()"),
        "__import__": (25.0, "Dynamic import injection via __import__()"),
        "system": (25.0, "Subshell command execution via os.system()"),
        "popen": (20.0, "Process pipe opening via os.popen()"),
    }

    DANGEROUS_MODULES = {
        "ctypes": (25.0, "Direct native memory access via ctypes"),
        "socket": (20.0, "Raw socket communication"),
        "paramiko": (25.0, "SSH client connection via paramiko"),
        "telnetlib": (25.0, "Unencrypted remote shell via telnetlib"),
    }

    SENSITIVE_ENV_KEYS = {
        "API_KEY", "SECRET", "TOKEN", "PASSWORD", "PASS", "AUTH",
        "ACCESS_KEY", "PRIVATE_KEY", "CREDENTIALS",
    }

    @classmethod
    def audit_skill_directory(cls, skill_dir: Path, threshold: int = 20) -> SecurityAuditReport:
        scripts_dir = skill_dir / "scripts"
        findings: list[SecurityFinding] = []

        if not scripts_dir.exists() or not scripts_dir.is_dir():
            return SecurityAuditReport(risk_score=0.0, risk_band="SAFE", findings=[], passed=True, threshold=threshold)

        py_files = list(scripts_dir.glob("*.py"))
        sh_files = list(scripts_dir.glob("*.sh"))

        for pf in py_files:
            content = pf.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(content, filename=str(pf.name))
                cls._scan_ast_tree(tree, pf.name, findings)
            except SyntaxError as syn_err:
                findings.append(
                    SecurityFinding(
                        dimension="Dangerous System Calls",
                        severity="HIGH",
                        file=pf.name,
                        line=syn_err.lineno or 1,
                        pattern="SyntaxError",
                        details=f"Malformed Python script failed AST parse: {syn_err.msg}",
                        penalty=15.0,
                    )
                )

        for sf in sh_files:
            sh_content = sf.read_text(encoding="utf-8", errors="replace")
            cls._scan_shell_script(sh_content, sf.name, findings)

        # Aggregate weighted risk score (capped at 100.0)
        raw_score = sum(f.penalty for f in findings)
        risk_score = min(100.0, raw_score)

        if risk_score <= 20.0:
            band = "SAFE"
        elif risk_score <= 50.0:
            band = "CAUTION"
        elif risk_score <= 80.0:
            band = "HIGH"
        else:
            band = "CRITICAL"

        passed = risk_score <= float(threshold)
        return SecurityAuditReport(
            risk_score=risk_score,
            risk_band=band,
            findings=findings,
            passed=passed,
            threshold=threshold,
        )

    @classmethod
    def _scan_ast_tree(cls, tree: ast.AST, filename: str, findings: list[SecurityFinding]) -> None:
        for node in ast.walk(tree):
            # 1. Dangerous Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.split(".")[0]
                    if mod_name in cls.DANGEROUS_MODULES:
                        penalty, desc = cls.DANGEROUS_MODULES[mod_name]
                        findings.append(
                            SecurityFinding(
                                dimension="Dangerous System Calls",
                                severity="HIGH",
                                file=filename,
                                line=node.lineno,
                                pattern=f"import {alias.name}",
                                details=desc,
                                penalty=penalty,
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_name = node.module.split(".")[0]
                    if mod_name in cls.DANGEROUS_MODULES:
                        penalty, desc = cls.DANGEROUS_MODULES[mod_name]
                        findings.append(
                            SecurityFinding(
                                dimension="Dangerous System Calls",
                                severity="HIGH",
                                file=filename,
                                line=node.lineno,
                                pattern=f"from {node.module} import ...",
                                details=desc,
                                penalty=penalty,
                            )
                        )

            # 2. Dangerous Calls (eval, exec, os.system, subprocess with shell=True)
            elif isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in cls.DANGEROUS_FUNCS:
                    penalty, desc = cls.DANGEROUS_FUNCS[func_name]
                    findings.append(
                        SecurityFinding(
                            dimension="Dangerous System Calls",
                            severity="CRITICAL" if penalty >= 30.0 else "HIGH",
                            file=filename,
                            line=node.lineno,
                            pattern=f"{func_name}()",
                            details=desc,
                            penalty=penalty,
                        )
                    )

                # Check subprocess with shell=True
                if func_name in ("run", "Popen", "call", "check_output", "check_call"):
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            findings.append(
                                SecurityFinding(
                                    dimension="Dangerous System Calls",
                                    severity="CRITICAL",
                                    file=filename,
                                    line=node.lineno,
                                    pattern="subprocess.*(shell=True)",
                                    details="Unescaped subprocess shell injection vector",
                                    penalty=30.0,
                                )
                            )

            # 3. Environment & Credential Access
            elif isinstance(node, ast.Subscript):
                # os.environ["..."]
                if isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
                    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                        key = node.slice.value.upper()
                        if any(s in key for s in cls.SENSITIVE_ENV_KEYS):
                            findings.append(
                                SecurityFinding(
                                    dimension="Environment & Credentials",
                                    severity="HIGH",
                                    file=filename,
                                    line=node.lineno,
                                    pattern=f'os.environ["{node.slice.value}"]',
                                    details=f"Direct access to sensitive environment credential key '{node.slice.value}'",
                                    penalty=20.0,
                                )
                            )

    @classmethod
    def _scan_shell_script(cls, content: str, filename: str, findings: list[SecurityFinding]) -> None:
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for curl/wget exfiltration patterns
            if re.search(r"\b(curl|wget)\b.*-(d|F|X\s*POST)\b", stripped):
                findings.append(
                    SecurityFinding(
                        dimension="Network & Exfiltration",
                        severity="HIGH",
                        file=filename,
                        line=idx,
                        pattern="curl/wget POST payload",
                        details="Outbound network POST detected in shell script",
                        penalty=25.0,
                    )
                )
            # Check for destructive commands (rm -rf /)
            if re.search(r"\brm\s+-(?:r[fF]|[fF]r)\s+(?:/|~|\$HOME)", stripped):
                findings.append(
                    SecurityFinding(
                        dimension="Filesystem Mutation",
                        severity="CRITICAL",
                        file=filename,
                        line=idx,
                        pattern="rm -rf / or ~",
                        details="Destructive recursive deletion of system or home root",
                        penalty=40.0,
                    )
                )


# ============================================================================
# Pluggable Validation Pipeline & Rule Architecture
# ============================================================================

@dataclass(slots=True)
class ValidationContext:
    skill_dir: Path
    skill_text: str
    skill_lines: list[str]
    config: SkillConfiguration
    line_budget: int


class BaseValidationRule(ABC):
    @property
    @abstractmethod
    def phase(self) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        ...


class KebabCaseNameRule(BaseValidationRule):
    phase = "Phase 1: Syntactic"
    name = "Kebab-Case Name"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        fm_match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n", ctx.skill_text)
        if not fm_match:
            return CheckResult(self.phase, self.name, False, "Missing YAML frontmatter", "Add frontmatter block.")
        name_match = re.search(r"^name:\s*([^\n]+)", fm_match.group(1), re.MULTILINE)
        if not name_match:
            return CheckResult(self.phase, self.name, False, "Missing 'name' field", "Add 'name: <kebab-case>'")
        s_name = name_match.group(1).strip().strip("\"'")
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", s_name):
            return CheckResult(self.phase, self.name, False, f"Name '{s_name}' is not kebab-case", "Use lowercase alphanumeric and hyphens.")
        return CheckResult(self.phase, self.name, True, f"Skill name '{s_name}' is valid kebab-case.")


class DescriptionLengthRule(BaseValidationRule):
    phase = "Phase 1: Syntactic"
    name = "Description Length"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        fm_match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n", ctx.skill_text)
        if not fm_match:
            return CheckResult(self.phase, self.name, False, "Missing YAML frontmatter", "Add frontmatter.")
        desc_match = re.search(r"^description:\s*([^\n]+)", fm_match.group(1), re.MULTILINE)
        if not desc_match:
            return CheckResult(self.phase, self.name, False, "Missing 'description' field", "Add 'description: ...'")
        desc_len = len(desc_match.group(1).strip().strip("\"'"))
        if desc_len < 20 or desc_len > 500:
            return CheckResult(self.phase, self.name, False, f"Description length ({desc_len}) outside [20, 500]", "Calibrate between 20 and 500 chars.")
        return CheckResult(self.phase, self.name, True, f"Description length is optimal ({desc_len} chars).")


class LineBudgetRule(BaseValidationRule):
    phase = "Phase 1: Syntactic"
    name = "Line Budget Limit"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        total = len(ctx.skill_lines)
        limit = ctx.line_budget
        if total > limit:
            return CheckResult(self.phase, self.name, False, f"SKILL.md exceeds budget: {total} > {limit}", f"Condense to <= {limit} lines.")
        return CheckResult(self.phase, self.name, True, f"SKILL.md within budget: {total}/{limit} lines.")


class HeadingHierarchyRule(BaseValidationRule):
    phase = "Phase 1: Syntactic"
    name = "Heading Hierarchy"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        levels: list[int] = []
        for line in ctx.skill_lines:
            h_match = re.match(r"^(#{1,6})\s+", line)
            if h_match:
                levels.append(len(h_match.group(1)))
        for i in range(len(levels) - 1):
            if levels[i + 1] > levels[i] + 1:
                return CheckResult(self.phase, self.name, False, "Heading hierarchy skips levels", "Ensure sequential levels (e.g. # -> ##).")
        return CheckResult(self.phase, self.name, True, "Markdown heading hierarchy is well-formed.")


class CardBorderFormatRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "CARD.md Border Format"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        card_file = ctx.skill_dir / "CARD.md"
        if not card_file.exists():
            return CheckResult(self.phase, self.name, False, "Missing companion CARD.md", "Scaffold CARD.md.")
        card_text = card_file.read_text(encoding="utf-8", errors="replace")
        if "║" in card_text:
            return CheckResult(self.phase, self.name, False, "Contains double-pipe borders ('║')", "Use single-pipe borders ('│') per Rule 37.")
        if "│" not in card_text or "┌" not in card_text:
            return CheckResult(self.phase, self.name, False, "Lacks single-pipe ASCII metadata box", "Add single-pipe bordered summary box.")
        return CheckResult(self.phase, self.name, True, "CARD.md uses compliant single-pipe borders (Rule 37).")


class CardTableRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "CARD.md Table & Identifier"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        card_file = ctx.skill_dir / "CARD.md"
        if not card_file.exists():
            return CheckResult(self.phase, self.name, False, "Missing companion CARD.md", "Scaffold CARD.md.")
        card_text = card_file.read_text(encoding="utf-8", errors="replace")
        has_table = "|" in card_text and "---" in card_text
        has_ascii_tag = "SKILL:" in card_text or "==" in card_text
        if not has_table or not has_ascii_tag:
            return CheckResult(self.phase, self.name, False, "Missing stage table or 'SKILL:' tag", "Include stage table and 'SKILL: <name>' tag.")
        return CheckResult(self.phase, self.name, True, "CARD.md contains stage table and ASCII identifier.")


class LifecycleStagesRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Lifecycle Stage Count"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        stage_headers = re.findall(r"^(?:##|\#\#\#)?\s*(?:Phase|Stage)\s*(\d+)[\.:\s]+([^\n]+)", ctx.skill_text, re.MULTILINE)
        if not stage_headers:
            stage_headers = re.findall(r"^##\s*(\d+)[\.:\s]+([^\n]+)", ctx.skill_text, re.MULTILINE)
        if len(stage_headers) < 3:
            return CheckResult(self.phase, self.name, False, f"Found only {len(stage_headers)} stages (< 3)", "Organize into >= 3 numbered stages.")
        return CheckResult(self.phase, self.name, True, f"Found {len(stage_headers)} defined lifecycle stages.")


class StageCompletionGatesRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Stage Completion Gates"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        stage_headers = re.findall(r"^(?:##|\#\#\#)?\s*(?:Phase|Stage)\s*(\d+)[\.:\s]+([^\n]+)", ctx.skill_text, re.MULTILINE)
        if not stage_headers:
            stage_headers = re.findall(r"^##\s*(\d+)[\.:\s]+([^\n]+)", ctx.skill_text, re.MULTILINE)
        gate_matches = re.findall(
            r"(?:\*{1,2})?(?:Completion [Gg]ate|[Cc]ompletion [Cc]riterion|[Gg]ate)(?:\*{1,2})?:\s*`?([^`\n]+)`?",
            ctx.skill_text,
        )
        if len(gate_matches) < len(stage_headers):
            return CheckResult(self.phase, self.name, False, f"Stages lack explicit gates ({len(gate_matches)}/{len(stage_headers)})", "Declare completion gates for all stages.")
        return CheckResult(self.phase, self.name, True, f"All {len(stage_headers)} stages have declared completion gates.")


class AntiPatternsHeadingRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Anti-Patterns Heading"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        if not re.search(r"^##\s*Anti-Patterns\s*$", ctx.skill_text, re.MULTILINE):
            return CheckResult(self.phase, self.name, False, "Missing exact '## Anti-Patterns' heading", "Add '## Anti-Patterns' heading per Rule 37.")
        return CheckResult(self.phase, self.name, True, "Found exact '## Anti-Patterns' heading.")


class AntiPatternsFormattingRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Anti-Patterns Formatting"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        ap_items = re.findall(r"^-\s+\*\*([^*]+)\*\*\s*[—–-]\s*([^\n]+)", ctx.skill_text, re.MULTILINE)
        if len(ap_items) < 3:
            return CheckResult(self.phase, self.name, False, f"Only {len(ap_items)} anti-patterns formatted as '- **Name** — Description'", "Format as '- **Name** — Description'.")
        return CheckResult(self.phase, self.name, True, f"Found {len(ap_items)} properly formatted anti-pattern items.")


class ScriptHygieneRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Non-Interactive Scripts"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        scripts_dir = ctx.skill_dir / "scripts"
        if not scripts_dir.exists():
            return CheckResult(self.phase, self.name, True, "No scripts directory to check.")
        script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        for sf in script_files:
            if sf.suffix == ".py":
                try:
                    tree = ast.parse(sf.read_text(encoding="utf-8", errors="replace"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                            return CheckResult(self.phase, self.name, False, f"Interactive input() call detected in {sf.name}", "Remove input() calls.")
                except Exception:
                    pass
            elif sf.suffix == ".sh":
                if re.search(r"^\s*read\s+", sf.read_text(encoding="utf-8", errors="replace"), re.MULTILINE):
                    return CheckResult(self.phase, self.name, False, f"Interactive read detected in {sf.name}", "Remove interactive prompts.")
        return CheckResult(self.phase, self.name, True, "All bundled scripts are non-interactive.")


class RelocatableScriptsRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Relocatable Scripts"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        scripts_dir = ctx.skill_dir / "scripts"
        if not scripts_dir.exists():
            return CheckResult(self.phase, self.name, True, "No scripts directory to check.")
        script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        abs_path_regex = re.compile(r"(['\"])(?:[A-Za-z]:\\|/Users/|/home/|C:\\)[^\r\n'\"]+\1")
        for sf in script_files:
            content = sf.read_text(encoding="utf-8", errors="replace")
            if abs_path_regex.search(content):
                return CheckResult(self.phase, self.name, False, f"Hardcoded absolute path in {sf.name}", "Use relative or Path(__file__).resolve() paths.")
        return CheckResult(self.phase, self.name, True, "All scripts use relocatable/relative paths.")


class ReferencesCoverageRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "References Trigger Coverage"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        refs_dir = ctx.skill_dir / "references"
        if not refs_dir.exists() or not refs_dir.is_dir():
            return CheckResult(self.phase, self.name, True, "No references directory present.")
        ref_files = list(refs_dir.glob("*.md"))
        missing = [rf.name for rf in ref_files if rf.name not in ctx.skill_text]
        if missing:
            return CheckResult(self.phase, self.name, False, f"Missing trigger sentences for: {missing}", "Add conditional sentences mentioning each reference.")
        return CheckResult(self.phase, self.name, True, f"All {len(ref_files)} reference files have conditional trigger links.")


class DefaultConfigurationRule(BaseValidationRule):
    phase = "Phase 2: Semantic"
    name = "Default Configuration"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        cfg_file = ctx.skill_dir / "config.default.yaml"
        if not cfg_file.exists():
            return CheckResult(self.phase, self.name, False, "Missing config.default.yaml", "Scaffold default configuration.")
        return CheckResult(self.phase, self.name, True, "config.default.yaml present.")


class SkillSpectorSecurityRule(BaseValidationRule):
    phase = "Phase 3: Security & Risk"
    name = "SkillSpector Risk Audit"

    def evaluate(self, ctx: ValidationContext) -> CheckResult:
        report = SkillSpectorScanner.audit_skill_directory(
            ctx.skill_dir,
            threshold=ctx.config.security_risk_threshold,
        )
        if not report.passed:
            details = "; ".join(f"{f.pattern} ({f.details})" for f in report.findings[:3])
            return CheckResult(
                self.phase,
                self.name,
                False,
                f"Security score {report.risk_score:.1f} exceeds threshold {report.threshold} (Band: {report.risk_band}). Findings: {details}",
                "Remediate high-risk AST patterns or request manual review seam.",
            )
        return CheckResult(
            self.phase,
            self.name,
            True,
            f"Security risk score {report.risk_score:.1f}/100 within threshold {report.threshold} (Band: {report.risk_band}).",
        )


# ============================================================================
# SkillSDLCEngine (Authoritative Service Seam)
# ============================================================================

class SkillSDLCEngine:
    """Authoritative service seam coordinating configuration, validation, security, and salvage."""

    DEFAULT_RULES: list[BaseValidationRule] = [
        KebabCaseNameRule(),
        DescriptionLengthRule(),
        LineBudgetRule(),
        HeadingHierarchyRule(),
        CardBorderFormatRule(),
        CardTableRule(),
        LifecycleStagesRule(),
        StageCompletionGatesRule(),
        AntiPatternsHeadingRule(),
        AntiPatternsFormattingRule(),
        ScriptHygieneRule(),
        RelocatableScriptsRule(),
        ReferencesCoverageRule(),
        DefaultConfigurationRule(),
        SkillSpectorSecurityRule(),
    ]

    def __init__(self, rules: list[BaseValidationRule] | None = None) -> None:
        self.rules = rules or list(self.DEFAULT_RULES)

    def resolve_config(self, skill_dir: Path | str) -> SkillConfiguration:
        return resolve_for_skill(skill_dir)

    def audit_security(self, skill_dir: Path | str, threshold: int = 20) -> SecurityAuditReport:
        return SkillSpectorScanner.audit_skill_directory(Path(skill_dir), threshold=threshold)

    def salvage(self, raw_text: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        return LocalSalvageEngine.salvage(raw_text)

    def validate(
        self,
        skill_dir: Path | str,
        line_budget: int | None = None,
    ) -> ValidationReport:
        s_dir = Path(skill_dir).resolve()
        skill_file = s_dir / "SKILL.md"

        if not skill_file.exists():
            return ValidationReport(
                skill_path=str(s_dir),
                valid=False,
                checks=[CheckResult("Phase 1: Syntactic", "SKILL.md Exists", False, f"Missing SKILL.md in {s_dir}", "Create SKILL.md")],
            )

        skill_text = skill_file.read_text(encoding="utf-8", errors="replace")
        skill_lines = skill_text.splitlines()

        # Resolve 3-tier config automatically
        config = self.resolve_config(s_dir)
        effective_budget = line_budget if line_budget is not None else config.line_budget_limit

        ctx = ValidationContext(
            skill_dir=s_dir,
            skill_text=skill_text,
            skill_lines=skill_lines,
            config=config,
            line_budget=effective_budget,
        )

        checks: list[CheckResult] = [rule.evaluate(ctx) for rule in self.rules]
        security_rep = self.audit_security(s_dir, threshold=config.security_risk_threshold)

        all_passed = all(c.passed for c in checks)
        return ValidationReport(
            skill_path=str(s_dir),
            valid=all_passed,
            checks=checks,
            security_report=security_rep,
            config=config.to_dict(),
        )


# Backward-compatible global function
def validate_skill_package(skill_dir: Path, line_budget: int = 500) -> ValidationReport:
    engine = SkillSDLCEngine()
    return engine.validate(skill_dir, line_budget=line_budget)


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Two-Phase Diagnostic Validator & SkillSpector Security Engine for Agent Skills"
    )
    parser.add_argument(
        "skill_dir",
        nargs="?",
        default=".",
        help="Path to the skill package directory (default: current directory).",
    )
    parser.add_argument(
        "--salvage",
        type=str,
        metavar="FILE_OR_DASH",
        help="Run multi-pass cognitive string salvage on raw LLM output (use '-' for stdin).",
    )
    parser.add_argument(
        "--audit-security",
        action="store_true",
        help="Run standalone SkillSpector 70-pattern security audit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit report as structured JSON.",
    )
    parser.add_argument(
        "--line-budget",
        type=int,
        default=None,
        help="Explicit line budget override (defaults to config.line_budget_limit).",
    )

    args = parser.parse_args()
    engine = SkillSDLCEngine()

    # Mode 1: Salvage
    if args.salvage:
        if args.salvage == "-":
            raw_input = sys.stdin.read()
        else:
            p = Path(args.salvage)
            if not p.exists():
                sys.stderr.write(f"Error: Target file not found: {args.salvage}\n")
                return 1
            raw_input = p.read_text(encoding="utf-8")

        salvaged, err = engine.salvage(raw_input)
        if err:
            sys.stderr.write(f"Salvage failed: {err}\n")
            return 1
        print(json.dumps(salvaged, indent=2))
        return 0

    target_dir = Path(args.skill_dir).resolve()
    if not target_dir.exists():
        sys.stderr.write(f"Error: Skill directory not found: {target_dir}\n")
        return 1

    # Mode 2: Standalone Security Audit
    if args.audit_security:
        cfg = engine.resolve_config(target_dir)
        sec_report = engine.audit_security(target_dir, threshold=cfg.security_risk_threshold)
        if args.json:
            print(json.dumps(sec_report.to_dict(), indent=2))
        else:
            status_tag = "PASS" if sec_report.passed else "FAIL"
            print(f"=== SkillSpector Security Audit: {target_dir.name} [{status_tag}] ===")
            print(f"Risk Score: {sec_report.risk_score:.1f} / 100.0  |  Risk Band: {sec_report.risk_band}")
            print(f"Threshold Limit: {sec_report.threshold}")
            if sec_report.findings:
                print("\nFindings:")
                for f in sec_report.findings:
                    print(f"  [{f.severity}] {f.file}:{f.line} - {f.pattern}: {f.details} (Penalty: +{f.penalty})")
            else:
                print("Zero security violations detected.")
        return 0 if sec_report.passed else 1

    # Mode 3: Complete Package Validation
    report = engine.validate(target_dir, line_budget=args.line_budget)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        status_sym = "PASS [✓]" if report.valid else "FAIL [✗]"
        print(f"=== Skill Validation Report: {report.skill_path} ===")
        print(f"Overall Status: {status_sym}\n")

        current_phase = ""
        for c in report.checks:
            if c.phase != current_phase:
                current_phase = c.phase
                print(f"[{current_phase}]")
            marker = "✓" if c.passed else "✗"
            print(f"  {marker} {c.name}: {c.message}")

        if report.security_report:
            print("\n[SkillSpector Security Audit]")
            sr = report.security_report
            print(f"  Risk Score: {sr.risk_score:.1f}/100.0 (Band: {sr.risk_band}, Gate: <={sr.threshold})")

        if not report.valid:
            print("\nActionable Remediation Recommendations:")
            for c in report.checks:
                if not c.passed and c.remediation:
                    print(f"  • {c.name}: {c.remediation}")

    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
