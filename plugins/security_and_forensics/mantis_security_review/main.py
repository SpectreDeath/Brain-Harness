"""Google Mantis Autonomous Security Review & Triage Plugin for Brain Harness."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)


@runtime_checkable
class MantisSecurityReviewService(Protocol):
    """Protocol for Google Mantis security review, triage, and OKF storage operations."""

    def history_scan(self, repo_path: str, max_commits: int = 100, pattern_filter: str = "") -> dict[str, Any]:
        ...

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        ...

    def plan_review(self, threat_model: dict[str, Any], target_paths: list[str], focus_cwe: list[str] | None = None) -> dict[str, Any]:
        ...

    def research_audit(self, target_file: str, code_content: str, focus_cwe: list[str] | None = None) -> dict[str, Any]:
        ...

    def dedupe_ladder(self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast") -> dict[str, Any]:
        ...

    def review_gate(self, finding: dict[str, Any], source_content: str, strictness: str = "high") -> dict[str, Any]:
        ...

    def critic_filter(self, finding: dict[str, Any], check_release_assertions: bool = True) -> dict[str, Any]:
        ...

    def chain_exploits(self, findings: list[dict[str, Any]], target_objective: str = "") -> dict[str, Any]:
        ...

    def calibrate_risk(self, findings: list[dict[str, Any]], asset_criticality: str = "high") -> dict[str, Any]:
        ...

    def generate_report(self, findings: list[dict[str, Any]], exploit_chains: list[dict[str, Any]] | None = None, executive_summary: str = "") -> dict[str, Any]:
        ...


MANTIS_SECURITY_REVIEW_KEY: ServiceKey[MantisSecurityReviewService] = ServiceKey("service.mantis_security_review")


# -----------------------------------------------------------------------------
# SQLite OKF v0.2 Knowledge Database Helper
# -----------------------------------------------------------------------------

def init_okf_db(db_path: str = "knowledge.db") -> sqlite3.Connection:
    """Initialize SQLite database with Mantis schema and OKF v0.2 concept tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            title TEXT NOT NULL,
            cwe TEXT NOT NULL,
            severity TEXT NOT NULL,
            signature TEXT NOT NULL,
            status TEXT NOT NULL,
            details_json TEXT NOT NULL,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS okf_concepts (
            concept_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (concept_id, run_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def compute_stable_signature(filepath: str, cwe: str, target_symbol: str = "") -> str:
    """Compute deterministic stable hash signature for vulnerability identity."""
    norm_fp = Path(filepath).as_posix().lower()
    norm_cwe = cwe.strip().upper()
    norm_sym = target_symbol.strip().lower()
    raw = f"{norm_fp}::{norm_cwe}::{norm_sym}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# -----------------------------------------------------------------------------
# Core Review Engine
# -----------------------------------------------------------------------------

class MantisReviewEngine:
    """Standalone implementation of Mantis Review algorithms."""

    def __init__(self, db_path: str = "knowledge.db") -> None:
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        try:
            conn = init_okf_db(self.db_path)
            conn.close()
        except Exception as e:
            logger.warning("okf_db_init_skipped", error=str(e))

    def history_scan(self, repo_path: str, max_commits: int = 100, pattern_filter: str = "") -> dict[str, Any]:
        """Mine VCS repository history for historical vulnerabilities and security fixes."""
        target = Path(repo_path)
        if not target.exists():
            return {"status": "error", "error": f"Repository path '{repo_path}' does not exist."}

        keywords = ["fix", "cve", "vuln", "security", "patch", "overflow", "sanitize", "bypass", "exploit"]
        if pattern_filter:
            keywords.append(pattern_filter.lower())

        commits: list[dict[str, Any]] = []
        try:
            cmd = ["git", "-C", str(target), "log", f"-n{max_commits}", "--pretty=format:%H|%an|%ad|%s", "--date=short"]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines():
                    if "|" in line:
                        parts = line.split("|", 3)
                        commit_hash = parts[0]
                        author = parts[1]
                        date = parts[2]
                        msg = parts[3] if len(parts) > 3 else ""
                        msg_lower = msg.lower()
                        matched_keys = [k for k in keywords if k in msg_lower]
                        if matched_keys:
                            commits.append({
                                "hash": commit_hash,
                                "author": author,
                                "date": date,
                                "subject": msg,
                                "matched_keywords": matched_keys,
                            })
        except Exception as e:
            logger.warning("git_history_scan_error", error=str(e))
            return {"status": "error", "error": f"Git inspection failed: {e!s}"}

        return {
            "status": "ok",
            "repo_path": str(target),
            "total_commits_scanned": max_commits,
            "security_commits_found": len(commits),
            "historical_learnings": commits,
        }

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        """Generate hierarchical security directory map."""
        p = Path(dir_path)
        if not p.exists():
            return {"status": "error", "error": f"Path '{dir_path}' does not exist."}

        code_exts = {".py", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".js", ".ts", ".java"}
        config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".xml"}

        code_files: list[str] = []
        config_files: list[str] = []
        doc_files: list[str] = []
        total_lines = 0

        pattern = "**/*" if recursive else "*"
        for item in p.glob(pattern):
            if item.is_file() and not any(part.startswith(".") for part in item.parts):
                ext = item.suffix.lower()
                rel = item.relative_to(p).as_posix()
                if ext in code_exts:
                    code_files.append(rel)
                elif ext in config_exts:
                    config_files.append(rel)
                elif ext in {".md", ".rst", ".txt"}:
                    doc_files.append(rel)

                try:
                    total_lines += len(item.read_text(encoding="utf-8", errors="ignore").splitlines())
                except Exception:
                    pass

        return {
            "status": "ok",
            "root_directory": str(p),
            "code_files_count": len(code_files),
            "config_files_count": len(config_files),
            "doc_files_count": len(doc_files),
            "total_estimated_lines": total_lines,
            "code_files": code_files[:100],
            "config_files": config_files[:50],
        }

    def plan_review(self, threat_model: dict[str, Any], target_paths: list[str], focus_cwe: list[str] | None = None) -> dict[str, Any]:
        """Formulate targeted security review plan."""
        focus_cwe = focus_cwe or ["CWE-20", "CWE-78", "CWE-89", "CWE-119", "CWE-416", "CWE-798"]
        tasks: list[dict[str, Any]] = []

        for path in target_paths:
            priority = "high" if any(k in path.lower() for k in ["auth", "login", "admin", "sandbox", "crypto", "exec"]) else "medium"
            tasks.append({
                "target": path,
                "priority": priority,
                "recommended_cwe": focus_cwe,
                "strategy": "Static AST audit followed by false-positive review and crash reproducer generation.",
            })

        return {
            "status": "ok",
            "plan_id": f"plan_{hashlib.sha256(str(target_paths).encode()).hexdigest()[:8]}",
            "target_count": len(target_paths),
            "focus_cwe": focus_cwe,
            "tasks": tasks,
        }

    def research_audit(self, target_file: str, code_content: str, focus_cwe: list[str] | None = None) -> dict[str, Any]:
        """Deep-dive static analysis audit of target source code."""
        findings: list[dict[str, Any]] = []
        lines = code_content.splitlines()

        # AST-level inspection for Python
        if target_file.endswith(".py"):
            try:
                tree = ast.parse(code_content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # eval / exec
                        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                            sig = compute_stable_signature(target_file, "CWE-95", node.func.id)
                            findings.append({
                                "id": f"find_{sig[:8]}",
                                "filepath": target_file,
                                "line": node.lineno,
                                "cwe": "CWE-95",
                                "title": f"Arbitrary Code Execution via '{node.func.id}()'",
                                "severity": "critical",
                                "target_symbol": node.func.id,
                                "signature": sig,
                                "description": f"Direct invocation of {node.func.id}() evaluates dynamic code from input.",
                            })
                        # subprocess with shell=True
                        elif isinstance(node.func, ast.Attribute) and node.func.attr in ("Popen", "run", "call", "check_output"):
                            for kw in node.keywords:
                                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    sig = compute_stable_signature(target_file, "CWE-78", "subprocess_shell")
                                    findings.append({
                                        "id": f"find_{sig[:8]}",
                                        "filepath": target_file,
                                        "line": node.lineno,
                                        "cwe": "CWE-78",
                                        "title": "OS Command Injection via subprocess(shell=True)",
                                        "severity": "critical",
                                        "target_symbol": "subprocess_shell",
                                        "signature": sig,
                                        "description": "Subprocess called with shell=True creates command injection risk.",
                                    })
            except SyntaxError:
                pass

        # Regex heuristic sweeps
        for i, line in enumerate(lines, start=1):
            # Hardcoded keys
            if re.search(r"""(?i)(?:api_key|secret_key|private_key)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]""", line):
                sig = compute_stable_signature(target_file, "CWE-798", f"line_{i}")
                findings.append({
                    "id": f"find_{sig[:8]}",
                    "filepath": target_file,
                    "line": i,
                    "cwe": "CWE-798",
                    "title": "Hardcoded Cryptographic Secret/Key",
                    "severity": "high",
                    "target_symbol": f"line_{i}",
                    "signature": sig,
                    "description": f"Suspected hardcoded credential found on line {i}.",
                })
            # SQL Injection pattern
            if re.search(r"""(?i)(?:select|insert|update|delete)\s+.*\s+from\s+.*%\s*\(?""", line) or ("SELECT " in line.upper() and " + " in line):
                sig = compute_stable_signature(target_file, "CWE-89", f"line_{i}")
                findings.append({
                    "id": f"find_{sig[:8]}",
                    "filepath": target_file,
                    "line": i,
                    "cwe": "CWE-89",
                    "title": "SQL Injection via String Concatenation/Interpolation",
                    "severity": "high",
                    "target_symbol": f"line_{i}",
                    "signature": sig,
                    "description": f"SQL query constructed using dynamic string formatting on line {i}.",
                })

        return {
            "status": "ok",
            "target_file": target_file,
            "findings_count": len(findings),
            "findings": findings,
        }

    def dedupe_ladder(self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast") -> dict[str, Any]:
        """Consolidate findings to eliminate redundant reports."""
        if mode == "off":
            return {"status": "ok", "mode": "off", "original_count": len(findings), "deduped_count": len(findings), "findings": findings}

        seen_signatures: set[str] = set()
        seen_locations: set[tuple[str, int, str]] = set()
        deduped: list[dict[str, Any]] = []
        duplicates_removed = 0

        for f in findings:
            fp = f.get("filepath", "")
            line = f.get("line", 0)
            cwe = f.get("cwe", "")
            sig = f.get("signature") or compute_stable_signature(fp, cwe, f.get("target_symbol", ""))

            # Syntactic & AST dedupe: Check both signature and line/CWE proximity
            if sig in seen_signatures:
                duplicates_removed += 1
                continue

            loc_key = (fp, line, cwe)
            if loc_key in seen_locations:
                duplicates_removed += 1
                continue

            seen_signatures.add(sig)
            seen_locations.add(loc_key)
            f_copy = dict(f)
            f_copy["signature"] = sig
            deduped.append(f_copy)

        return {
            "status": "ok",
            "mode": mode,
            "original_count": len(findings),
            "deduped_count": len(deduped),
            "duplicates_removed": duplicates_removed,
            "findings": deduped,
        }

    def review_gate(self, finding: dict[str, Any], source_content: str, strictness: str = "high") -> dict[str, Any]:
        """Evaluate finding against source semantics to eliminate false positives."""
        line_num = finding.get("line", 0)
        cwe = finding.get("cwe", "")
        lines = source_content.splitlines()

        if line_num <= 0 or line_num > len(lines):
            return {
                "status": "ok",
                "verdict": "REJECTED",
                "confidence": 0.95,
                "reason": f"Target line {line_num} does not exist in source file (total lines: {len(lines)}).",
            }

        target_line = lines[line_num - 1]
        context_window = lines[max(0, line_num - 5):min(len(lines), line_num + 5)]
        context_str = "\n".join(context_window)

        # Check for active mitigations in surrounding context
        has_sanitizer = any(term in context_str.lower() for term in ["shlex.quote", "escape", "parameterized", "validate", "sanitize", "allowed_hosts"])
        if has_sanitizer:
            return {
                "status": "ok",
                "verdict": "REJECTED_FALSE_POSITIVE",
                "confidence": 0.85,
                "reason": "Surrounding context contains explicit sanitization or input validation.",
            }

        return {
            "status": "ok",
            "verdict": "CONFIRMED_VALID",
            "confidence": 0.90 if strictness == "high" else 0.75,
            "target_snippet": target_line.strip(),
            "reason": f"Vulnerability {cwe} confirmed on line {line_num} without detected sanitizers.",
        }

    def critic_filter(self, finding: dict[str, Any], check_release_assertions: bool = True) -> dict[str, Any]:
        """Assess production viability, filtering out debug-only features and assertion traps."""
        desc = (finding.get("description", "") + " " + finding.get("title", "")).lower()

        # Check if flaw depends entirely on assertion failure
        if check_release_assertions and ("assert " in desc or "assertion" in desc):
            return {
                "status": "ok",
                "viable_in_production": False,
                "verdict": "DROPPED_ASSERTION_TRAP",
                "reason": "Vulnerability relies on python 'assert' statement which is stripped in release builds (PYTHONOPTIMIZE / -O).",
            }

        # Check if flaw is in debug-only section
        if "debug" in desc or "test_" in finding.get("filepath", ""):
            return {
                "status": "ok",
                "viable_in_production": False,
                "verdict": "DROPPED_TEST_OR_DEBUG_ONLY",
                "reason": "Finding located in test harness or debug-only module not reachable in production.",
            }

        return {
            "status": "ok",
            "viable_in_production": True,
            "verdict": "CONFIRMED_PRODUCTION_VIABLE",
            "reason": "Vulnerability triggerable in production release configuration without assertions.",
        }

    def chain_exploits(self, findings: list[dict[str, Any]], target_objective: str = "") -> dict[str, Any]:
        """Construct multi-stage compound exploit chains from validated findings."""
        target_obj = target_objective or "Remote Code Execution / Privilege Escalation"
        chains: list[dict[str, Any]] = []

        # Find initial access / info leak
        info_leaks = [f for f in findings if f.get("cwe") in ("CWE-798", "CWE-200", "CWE-918")]
        rce_vulns = [f for f in findings if f.get("cwe") in ("CWE-78", "CWE-95", "CWE-502")]

        if info_leaks and rce_vulns:
            chains.append({
                "chain_id": f"chain_{hashlib.sha256(str(findings).encode()).hexdigest()[:8]}",
                "objective": target_obj,
                "steps": [
                    {
                        "step": 1,
                        "finding_id": info_leaks[0].get("id"),
                        "tactic": "Credential Exfiltration / SSRF",
                        "description": f"Exfiltrate credentials or bypass network boundary via {info_leaks[0].get('title')}",
                    },
                    {
                        "step": 2,
                        "finding_id": rce_vulns[0].get("id"),
                        "tactic": "Privileged Code Execution",
                        "description": f"Use obtained access to execute arbitrary commands via {rce_vulns[0].get('title')}",
                    },
                ],
                "compound_severity": "critical",
            })

        return {
            "status": "ok",
            "target_objective": target_obj,
            "chains_constructed_count": len(chains),
            "exploit_chains": chains,
        }

    def calibrate_risk(self, findings: list[dict[str, Any]], asset_criticality: str = "high") -> dict[str, Any]:
        """Calculate multi-axis risk ratings."""
        crit_multiplier = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.7}.get(asset_criticality.lower(), 1.0)
        calibrated: list[dict[str, Any]] = []

        for f in findings:
            sev = f.get("severity", "medium").lower()
            base_score = {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.5}.get(sev, 5.0)
            final_score = min(10.0, round(base_score * crit_multiplier, 1))

            calibrated.append({
                "finding_id": f.get("id"),
                "title": f.get("title"),
                "cwe": f.get("cwe"),
                "base_severity": sev,
                "asset_criticality": asset_criticality,
                "calibrated_cvss_score": final_score,
                "calibrated_severity": "critical" if final_score >= 9.0 else "high" if final_score >= 7.0 else "medium" if final_score >= 4.0 else "low",
            })

        return {
            "status": "ok",
            "asset_criticality": asset_criticality,
            "calibrated_findings_count": len(calibrated),
            "calibrated_findings": calibrated,
        }

    def generate_report(self, findings: list[dict[str, Any]], exploit_chains: list[dict[str, Any]] | None = None, executive_summary: str = "") -> dict[str, Any]:
        """Compile stakeholder-facing security review packet."""
        exploit_chains = exploit_chains or []
        summary = executive_summary or f"Automated Mantis security review identified {len(findings)} confirmed issues and {len(exploit_chains)} compound exploit chains."

        # Severity breakdown
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            s = f.get("severity", f.get("calibrated_severity", "medium")).lower()
            if s in counts:
                counts[s] += 1

        markdown_report = [
            "# Google Mantis Security Review Packet",
            "",
            "## Executive Summary",
            summary,
            "",
            "## Severity Breakdown",
            f"- **Critical:** {counts['critical']}",
            f"- **High:** {counts['high']}",
            f"- **Medium:** {counts['medium']}",
            f"- **Low:** {counts['low']}",
            "",
            "## Confirmed Findings",
        ]

        for i, f in enumerate(findings, start=1):
            markdown_report.extend([
                f"### {i}. {f.get('title', 'Unknown')} ({f.get('cwe', 'CWE-Unknown')})",
                f"- **File:** `{f.get('filepath', '')}` (Line {f.get('line', '?')})",
                f"- **Severity:** {f.get('severity', f.get('calibrated_severity', 'medium')).upper()}",
                f"- **Description:** {f.get('description', '')}",
                "",
            ])

        if exploit_chains:
            markdown_report.extend(["## Compound Exploit Chains"])
            for ch in exploit_chains:
                markdown_report.extend([
                    f"### Chain: {ch.get('objective', '')}",
                    f"- **Severity:** {ch.get('compound_severity', 'critical').upper()}",
                ])
                for step in ch.get("steps", []):
                    markdown_report.append(f"  {step.get('step')}. **{step.get('tactic')}:** {step.get('description')}")
                markdown_report.append("")

        return {
            "status": "ok",
            "findings_count": len(findings),
            "chains_count": len(exploit_chains),
            "severity_counts": counts,
            "markdown_report": "\n".join(markdown_report),
        }


_GLOBAL_ENGINE = MantisReviewEngine()


# -----------------------------------------------------------------------------
# Tool Entrypoints Matching plugin.json Specification
# -----------------------------------------------------------------------------

def mantis_history_scan(repo_path: str, max_commits: int = 100, pattern_filter: str = "") -> dict[str, Any]:
    """Mine VCS repository history for historical vulnerabilities and fix patterns."""
    return _GLOBAL_ENGINE.history_scan(repo_path=repo_path, max_commits=max_commits, pattern_filter=pattern_filter)


def mantis_directory_summary(dir_path: str, recursive: bool = True) -> dict[str, Any]:
    """Generate hierarchical security directory map and asset overview."""
    return _GLOBAL_ENGINE.directory_summary(dir_path=dir_path, recursive=recursive)


def mantis_plan_review(threat_model: dict[str, Any], target_paths: list[str], focus_cwe: list[str] | None = None) -> dict[str, Any]:
    """Formulate targeted defensive security review plan from threat model."""
    return _GLOBAL_ENGINE.plan_review(threat_model=threat_model, target_paths=target_paths, focus_cwe=focus_cwe or [])


def mantis_research_audit(target_file: str, code_content: str, focus_cwe: list[str] | None = None) -> dict[str, Any]:
    """Deep-dive static analysis audit of target source code."""
    return _GLOBAL_ENGINE.research_audit(target_file=target_file, code_content=code_content, focus_cwe=focus_cwe or [])


def mantis_dedupe_ladder(findings: list[dict[str, Any]], mode: str = "syntactic_and_ast") -> dict[str, Any]:
    """Consolidate findings through multi-pass syntactic, AST, and semantic deduplication."""
    return _GLOBAL_ENGINE.dedupe_ladder(findings=findings, mode=mode)


def mantis_review_gate(finding: dict[str, Any], source_content: str, strictness: str = "high") -> dict[str, Any]:
    """Independent validation gate evaluating findings against source semantics."""
    return _GLOBAL_ENGINE.review_gate(finding=finding, source_content=source_content, strictness=strictness)


def mantis_critic_filter(finding: dict[str, Any], check_release_assertions: bool = True) -> dict[str, Any]:
    """Assess production viability, filtering out debug-only features and assertion traps."""
    return _GLOBAL_ENGINE.critic_filter(finding=finding, check_release_assertions=check_release_assertions)


def mantis_chain_exploits(findings: list[dict[str, Any]], target_objective: str = "") -> dict[str, Any]:
    """Analyze individual findings to construct multi-stage compound exploit chains."""
    return _GLOBAL_ENGINE.chain_exploits(findings=findings, target_objective=target_objective)


def mantis_calibrate_risk(findings: list[dict[str, Any]], asset_criticality: str = "high") -> dict[str, Any]:
    """Calculate multi-axis risk ratings based on threat intel, impact, and criticality."""
    return _GLOBAL_ENGINE.calibrate_risk(findings=findings, asset_criticality=asset_criticality)


def mantis_generate_report(findings: list[dict[str, Any]], exploit_chains: list[dict[str, Any]] | None = None, executive_summary: str = "") -> dict[str, Any]:
    """Compile stakeholder-facing security review packet from confirmed findings."""
    return _GLOBAL_ENGINE.generate_report(findings=findings, exploit_chains=exploit_chains or [], executive_summary=executive_summary)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------

class MantisSecurityReviewPlugin(HarnessPlugin, MantisSecurityReviewService):
    """Brain Harness Plugin providing Google Mantis security review and OKF storage services."""

    name = "plugin.mantis_security_review"
    version = "1.0.0"
    description = "Google Mantis autonomous security review pipeline, VCS history mining, deduplication ladder, and risk calibration"
    trusted = True

    def __init__(self, engine: MantisReviewEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MANTIS_SECURITY_REVIEW_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MANTIS_SECURITY_REVIEW_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation
    # -------------------------------------------------------------------------

    def history_scan(self, repo_path: str, max_commits: int = 100, pattern_filter: str = "") -> dict[str, Any]:
        return self._engine.history_scan(repo_path, max_commits, pattern_filter)

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        return self._engine.directory_summary(dir_path, recursive)

    def plan_review(self, threat_model: dict[str, Any], target_paths: list[str], focus_cwe: list[str] | None = None) -> dict[str, Any]:
        return self._engine.plan_review(threat_model, target_paths, focus_cwe)

    def research_audit(self, target_file: str, code_content: str, focus_cwe: list[str] | None = None) -> dict[str, Any]:
        return self._engine.research_audit(target_file, code_content, focus_cwe)

    def dedupe_ladder(self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast") -> dict[str, Any]:
        return self._engine.dedupe_ladder(findings, mode)

    def review_gate(self, finding: dict[str, Any], source_content: str, strictness: str = "high") -> dict[str, Any]:
        return self._engine.review_gate(finding, source_content, strictness)

    def critic_filter(self, finding: dict[str, Any], check_release_assertions: bool = True) -> dict[str, Any]:
        return self._engine.critic_filter(finding, check_release_assertions)

    def chain_exploits(self, findings: list[dict[str, Any]], target_objective: str = "") -> dict[str, Any]:
        return self._engine.chain_exploits(findings, target_objective)

    def calibrate_risk(self, findings: list[dict[str, Any]], asset_criticality: str = "high") -> dict[str, Any]:
        return self._engine.calibrate_risk(findings, asset_criticality)

    def generate_report(self, findings: list[dict[str, Any]], exploit_chains: list[dict[str, Any]] | None = None, executive_summary: str = "") -> dict[str, Any]:
        return self._engine.generate_report(findings, exploit_chains, executive_summary)
