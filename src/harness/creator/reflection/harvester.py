"""Harvester discovering and parsing internal execution residue."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import re
import tempfile
from typing import Any

import structlog

from harness.creator.reflection.models import (
    ReflectionScope,
    ReportArtifact,
    TranscriptSession,
)

logger = structlog.get_logger(__name__)


class HarnessHistoryHarvester:
    """Harvester discovering and parsing internal execution residue."""

    def __init__(
        self,
        temp_dir: Path | str | None = None,
        app_data_dir: Path | str | None = None,
    ) -> None:
        self.temp_dir = Path(temp_dir or tempfile.gettempdir()).resolve()
        if app_data_dir:
            self.app_data_dir = Path(app_data_dir).resolve()
        else:
            user_home = Path.home()
            self.app_data_dir = user_home / ".gemini" / "antigravity-ide"

    def harvest_temp_reports(
        self,
        scope: ReflectionScope | None = None,
    ) -> list[ReportArtifact]:
        """Discover and parse HTML visual briefs and architecture reviews from %TEMP%."""
        limit = scope.limit if scope else 50
        reports: list[ReportArtifact] = []
        if not self.temp_dir.exists():
            return reports

        patterns = ["*architecture-review*.html", "*compute-assessor*.html", "*brief*.html", "*harness*.html"]
        matched_files: dict[str, Path] = {}

        for pat in patterns:
            for p in self.temp_dir.glob(pat):
                if p.is_file() and p.name not in matched_files:
                    matched_files[p.name] = p

        sorted_paths = sorted(
            matched_files.values(),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[: limit * 2]

        for p in sorted_paths:
            try:
                artifact = self._parse_html_report(p)
                if artifact:
                    if scope and not scope.matches_date(artifact.created_at):
                        continue
                    reports.append(artifact)
                    if len(reports) >= limit:
                        break
            except Exception as e:
                logger.warning("Failed parsing temp report", path=str(p), error=str(e))

        return reports

    def _parse_html_report(self, path: Path) -> ReportArtifact | None:
        """Parse text, title, diagrams, and friction points from an HTML report."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text:
            return None

        # Title
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else path.stem.replace("-", " ").title()

        # Report type classification
        report_type = "custom"
        if "architecture-review" in path.name.lower():
            report_type = "architecture_review"
        elif "compute-assessor" in path.name.lower():
            report_type = "compute_assessment"
        elif "domain-modeling" in path.name.lower():
            report_type = "domain_modeling"

        # Extract Mermaid diagrams
        mermaid_diagrams = re.findall(r'<div class=["\']mermaid["\']>(.*?)</div>', text, re.DOTALL)
        if not mermaid_diagrams:
            mermaid_diagrams = re.findall(r"```mermaid(.*?)```", text, re.DOTALL)

        # Extract text snippets and friction points
        clean_text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r"<script.*?>.*?</script>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r"<[^>]+>", " ", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        friction_points: list[str] = []
        for line in text.splitlines():
            if any(k in line.lower() for k in ["friction", "gotcha", "timeout", "bottleneck", "warning", "anti-pattern"]):
                cleaned_line = re.sub(r"<[^>]+>", "", line).strip()
                if cleaned_line and len(cleaned_line) > 10 and cleaned_line not in friction_points:
                    friction_points.append(cleaned_line)

        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

        return ReportArtifact(
            file_path=path,
            title=title,
            created_at=mtime,
            report_type=report_type,
            content_text=clean_text[:5000],
            friction_points=friction_points[:10],
            mermaid_diagrams=[m.strip() for m in mermaid_diagrams[:3]],
            metadata={"file_size": path.stat().st_size},
        )

    def harvest_transcripts(
        self,
        scope: ReflectionScope | None = None,
    ) -> list[TranscriptSession]:
        """Harvest step trajectories and error logs from local conversation logs."""
        limit = scope.limit if scope else 10
        sessions: list[TranscriptSession] = []
        brain_dir = self.app_data_dir / "brain"
        if not brain_dir.exists():
            return sessions

        transcript_files: list[Path] = []
        for conv_dir in brain_dir.iterdir():
            if not conv_dir.is_dir():
                continue
            if scope and not scope.matches_conversation(conv_dir.name):
                continue
            log_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if log_file.exists() and log_file.stat().st_size > 0:
                transcript_files.append(log_file)

        sorted_logs = sorted(
            transcript_files,
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[: limit * 2]

        for log_path in sorted_logs:
            try:
                session = self._parse_transcript_log(log_path)
                if session:
                    sessions.append(session)
                    if len(sessions) >= limit:
                        break
            except Exception as e:
                logger.warning("Failed parsing transcript log", path=str(log_path), error=str(e))

        return sessions

    def _parse_transcript_log(self, path: Path) -> TranscriptSession | None:
        """Parse transcript lines for user requests, tools, and error recoveries."""
        conv_id = path.parent.parent.parent.name
        user_requests: list[str] = []
        tools_invoked: list[str] = []
        errors_encountered: list[str] = []
        recovery_actions: list[str] = []
        total_steps = 0

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                total_steps += 1
                try:
                    step = json.loads(line)
                    step_type = step.get("type")

                    if step_type == "USER_INPUT":
                        content = step.get("content", "")
                        if content and len(content) < 300 and content not in user_requests:
                            user_requests.append(content.strip())

                    elif step_type == "PLANNER_RESPONSE":
                        tool_calls = step.get("tool_calls", [])
                        for tc in tool_calls:
                            t_name = tc.get("toolAction") or tc.get("toolSummary") or "tool"
                            if t_name not in tools_invoked:
                                tools_invoked.append(t_name)

                    status = step.get("status")
                    if status == "ERROR" or "error" in str(step.get("content", "")).lower():
                        err_content = str(step.get("content", ""))[:200]
                        if err_content and err_content not in errors_encountered:
                            errors_encountered.append(err_content)

                except json.JSONDecodeError:
                    continue

        return TranscriptSession(
            conversation_id=conv_id,
            log_path=path,
            total_steps=total_steps,
            user_requests=user_requests[:10],
            tools_invoked=tools_invoked[:20],
            errors_encountered=errors_encountered[:10],
            recovery_actions=recovery_actions[:5],
        )

    def harvest_junit_reports(
        self,
        report_path: Path | str | None = None,
        scope: ReflectionScope | None = None,
    ) -> list[ReportArtifact]:
        """Discover and parse JUnit XML test reports."""
        import xml.etree.ElementTree as ET

        reports: list[ReportArtifact] = []
        candidates: list[Path] = []
        if report_path:
            p = Path(report_path).resolve()
            if p.exists():
                candidates.append(p)
        else:
            for cand in [Path("test-report.xml"), self.temp_dir / "test-report.xml"]:
                if cand.exists():
                    candidates.append(cand)

        for p in candidates:
            try:
                tree = ET.parse(p)
                root = tree.getroot()

                failures: list[dict[str, Any]] = []
                testcases = root.findall(".//testcase")
                for tc in testcases:
                    fail_node = tc.find("failure")
                    err_node = tc.find("error")
                    active_node = fail_node if fail_node is not None else err_node
                    if active_node is not None:
                        cname = tc.get("classname", "")
                        name = tc.get("name", "")
                        msg = active_node.get("message", "")
                        tb = active_node.text or ""
                        failures.append({
                            "test_name": f"{cname}::{name}" if cname else name,
                            "test_file": tc.get("file", cname),
                            "line": tc.get("line"),
                            "message": msg,
                            "traceback": tb,
                        })

                if failures:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
                    summary_text = f"Test Report {p.name}: {len(failures)} failures encountered."
                    friction_points = [f"{f['test_name']}: {f['message'][:80]}" for f in failures]
                    reports.append(
                        ReportArtifact(
                            file_path=p,
                            title=f"CI Test Run Report ({p.name})",
                            created_at=mtime,
                            report_type="test_report",
                            content_text=summary_text,
                            friction_points=friction_points,
                            metadata={"failures": failures, "total_failures": len(failures)},
                        )
                    )
            except Exception as e:
                logger.warning("Failed parsing JUnit test report", path=str(p), error=str(e))

        return reports


__all__ = [
    "HarnessHistoryHarvester",
]
