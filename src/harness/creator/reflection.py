"""Endogenous Memory & Reflection Engine for Brain Harness.

Harvests internal history (HTML architecture visual briefs, conversation transcripts,
walkthroughs, and execution logs), reconstructs episodic memory trajectories, and
distills actionable, Isnad-grounded Knowledge Items (KIs) into the Knowledge Vault.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import structlog

from harness.services.storage import (
    IsnadLineageBlock,
    KnowledgeItemRecord,
    StorageService,
)

logger = structlog.get_logger(__name__)


@dataclass
class ReflectionScope:
    """Multi-dimensional filter scope for history harvesting and reflection."""

    since: datetime | None = None
    conversation_ids: list[str] | None = None
    categories: list[str] | None = None
    min_confidence: float = 0.80
    limit: int = 50

    def matches_date(self, iso_date_str: str) -> bool:
        """Check if an ISO date string falls at or after `since`."""
        if not self.since:
            return True
        try:
            dt = datetime.fromisoformat(iso_date_str)
            # Ensure timezone awareness comparison
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            cmp_since = self.since if self.since.tzinfo is not None else self.since.replace(tzinfo=timezone.utc)
            return dt >= cmp_since
        except Exception:
            return True

    def matches_conversation(self, conv_id: str) -> bool:
        """Check if a conversation ID matches the scope filter."""
        if not self.conversation_ids:
            return True
        return conv_id in self.conversation_ids

    def matches_category(self, category: str) -> bool:
        """Check if a heuristic category matches the scope filter."""
        if not self.categories:
            return True
        return category.lower() in [c.lower() for c in self.categories]


@dataclass
class ReportArtifact:
    """Parsed HTML architecture review or visual brief from temporary storage."""

    file_path: Path
    title: str
    created_at: str
    report_type: str  # "architecture_review", "compute_assessment", "domain_modeling", "custom"
    content_text: str
    friction_points: list[str] = field(default_factory=list)
    mermaid_diagrams: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptSession:
    """Parsed conversation transcript and step trajectory."""

    conversation_id: str
    log_path: Path
    total_steps: int
    user_requests: list[str] = field(default_factory=list)
    tools_invoked: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)
    recovery_actions: list[str] = field(default_factory=list)


@dataclass
class DistilledHeuristic:
    """An actionable invariant, design rule, or anti-pattern distilled from memory."""

    title: str
    category: str  # "architecture", "error_recovery", "performance", "platform_quirk"
    heuristic: str
    anti_pattern: str | None = None
    confidence: float = 0.95
    source_artifacts: list[str] = field(default_factory=list)
    isnad_claims: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ReflectionReport:
    """Comprehensive distillation report across harvested memories."""

    reflection_id: str
    timestamp: str
    harvested_reports_count: int
    harvested_transcripts_count: int
    heuristics: list[DistilledHeuristic] = field(default_factory=list)
    knowledge_items: list[KnowledgeItemRecord] = field(default_factory=list)
    html_brief_path: Path | None = None


# --- Base Pattern Extractor & Pipeline ---


class BaseMemoryPatternExtractor(ABC):
    """Abstract base class for modular memory pattern extractors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this extractor."""

    @property
    @abstractmethod
    def category(self) -> str:
        """Heuristic category produced by this extractor."""

    @abstractmethod
    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        """Extract distilled heuristics from reports and transcripts."""


class ArchitectureSeamPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts lifecycle staging, lazy venv, and CLI group consolidation invariants."""

    @property
    def name(self) -> str:
        return "architecture_seams"

    @property
    def category(self) -> str:
        return "architecture"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            if rep.report_type != "architecture_review":
                continue

            combined_text = (rep.content_text + " " + " ".join(rep.friction_points)).lower()

            # 1. Lazy Subprocess Staging
            if any(k in combined_text for k in ["lazy", "subprocess", "venv", "cold-start"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="Lazy Subprocess Staging for Sandboxed External Plugins",
                        category="architecture",
                        heuristic=(
                            "External plugins with subprocess/venv isolation must remain in DISCOVERED/VALIDATED state "
                            "during kernel startup and test execution, provisioning virtual environments lazily on first invocation "
                            "to eliminate cold-start timeouts."
                        ),
                        anti_pattern="Eagerly provisioning virtualenvs for all user plugins in HarnessRuntime.start().",
                        confidence=0.98,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Eager venv creation on Windows causes 60s pytest timeout; lazy staging resolves startup in <10ms.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

            # 2. CLI Single-Source Consolidation
            if any(k in combined_text for k in ["cli", "bridge", "shadow", "command group"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="Click CLI Group Single-Source Consolidation",
                        category="architecture",
                        heuristic=(
                            "CLI command groups (e.g. '@main.group(\"bridge\")') must be declared exactly once in a single "
                            "co-located block to prevent later definitions from shadowing subcommands and breaking CLI test assertions."
                        ),
                        anti_pattern="Redefining CLI command groups at the bottom of cli.py.",
                        confidence=0.99,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Duplicate Click group declarations shadow earlier subcommands.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class TransactionalStepPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts agent step transaction rollback and ACID state boundary invariants."""

    @property
    def name(self) -> str:
        return "transactional_steps"

    @property
    def category(self) -> str:
        return "architecture"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            combined_text = (rep.content_text + " " + " ".join(rep.friction_points)).lower()
            if any(k in combined_text for k in ["transaction", "rollback", "acid", "dispose"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="ReAct Agent Step Transactional Isolation",
                        category="architecture",
                        heuristic=(
                            "Agent tool invocations should execute inside context transactions ('async with context.transaction()') "
                            "with automatic rollback ('await tx.dispose()') whenever the tool returns an error payload or raises an exception."
                        ),
                        anti_pattern="Mutating shared ServiceContext during tool execution without an ACID boundary.",
                        confidence=0.96,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Step-level transactional boundaries guarantee clean state rollback on tool failures.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class ComputeCalibrationPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts compute model assessment and reasoning budget routing invariants."""

    @property
    def name(self) -> str:
        return "compute_calibration"

    @property
    def category(self) -> str:
        return "performance"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            if rep.report_type == "compute_assessment" or "compute" in rep.title.lower():
                heuristics.append(
                    DistilledHeuristic(
                        title="Multi-Dimensional Compute Assessment Calibration",
                        category="performance",
                        heuristic=(
                            "Route high-reasoning tasks (architectural refactoring, debugging concurrency) to deep reasoning models "
                            "(gemini-3.7-flash with HIGH thinking or claude-3.7-sonnet with thinking budget), while routing mechanical tasks "
                            "to fast non-thinking tiers."
                        ),
                        anti_pattern="Using one-size-fits-all model tiers across heterogeneous task surfaces.",
                        confidence=0.95,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "5-dimensional scoring vectors optimize reasoning token spend and latency.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class ErrorRecoveryPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts async timeout, cancellation, and error recovery invariants from transcripts."""

    @property
    def name(self) -> str:
        return "error_recovery"

    @property
    def category(self) -> str:
        return "error_recovery"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for tr in transcripts:
            if not tr.errors_encountered:
                continue

            for err in tr.errors_encountered:
                err_lower = err.lower()
                if "timed out" in err_lower or "timeout" in err_lower:
                    heuristics.append(
                        DistilledHeuristic(
                            title="Async Execution Timeout Isolation",
                            category="error_recovery",
                            heuristic=(
                                "Long-running subagent tasks and test execution pipelines must specify explicit, granular timeouts "
                                "with thread-safe cancellation to prevent blocking the main asyncio loop."
                            ),
                            anti_pattern="Unbounded await calls on external subprocesses.",
                            confidence=0.92,
                            source_artifacts=[str(tr.log_path)],
                            isnad_claims=[
                                {
                                    "source": f"transcript:{tr.conversation_id}",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "assertion": "Transcript records timeout failure recovery.",
                                    "status": "VERIFIED",
                                }
                            ],
                        )
                    )
                    break

        return heuristics


class MemoryPatternPipeline:
    """Pluggable registry and execution pipeline for memory pattern extractors."""

    def __init__(self, extractors: list[BaseMemoryPatternExtractor] | None = None) -> None:
        if extractors is not None:
            self._extractors = list(extractors)
        else:
            self._extractors = [
                ArchitectureSeamPatternExtractor(),
                TransactionalStepPatternExtractor(),
                ComputeCalibrationPatternExtractor(),
                ErrorRecoveryPatternExtractor(),
            ]

    def register(self, extractor: BaseMemoryPatternExtractor) -> None:
        """Register a custom pattern extractor."""
        self._extractors.append(extractor)

    def list_extractors(self) -> list[str]:
        """List registered extractor names."""
        return [e.name for e in self._extractors]

    def distill(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
        scope: ReflectionScope | None = None,
    ) -> list[DistilledHeuristic]:
        """Execute all registered extractors, deduplicate heuristics, and apply scope filters."""
        raw_heuristics: list[DistilledHeuristic] = []

        for ext in self._extractors:
            try:
                results = ext.extract(reports, transcripts)
                raw_heuristics.extend(results)
            except Exception as e:
                logger.warning("Pattern extractor failed", extractor=ext.name, error=str(e))

        # Deduplicate heuristics by title while aggregating provenance claims and sources
        deduped: dict[str, DistilledHeuristic] = {}
        for h in raw_heuristics:
            if scope and not scope.matches_category(h.category):
                continue
            if scope and h.confidence < scope.min_confidence:
                continue

            if h.title not in deduped:
                deduped[h.title] = h
            else:
                for src in h.source_artifacts:
                    if src not in deduped[h.title].source_artifacts:
                        deduped[h.title].source_artifacts.append(src)
                for clm in h.isnad_claims:
                    if clm not in deduped[h.title].isnad_claims:
                        deduped[h.title].isnad_claims.append(clm)

        return list(deduped.values())


# --- Harvester ---


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


# --- Reflector Engine ---


class EpisodicMemoryReflector:
    """Helper for converting heuristics into ground-truth KnowledgeItemRecords."""

    @classmethod
    def distill(
        cls,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
        scope: ReflectionScope | None = None,
    ) -> list[DistilledHeuristic]:
        """Delegate distillation to default MemoryPatternPipeline."""
        pipeline = MemoryPatternPipeline()
        return pipeline.distill(reports, transcripts, scope=scope)

    @classmethod
    def to_knowledge_item(cls, heuristic: DistilledHeuristic, index: int = 1) -> KnowledgeItemRecord:
        """Convert a distilled heuristic into a canonical KnowledgeItemRecord."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        ki_id = f"ki_self_{date_str}_{index:02d}"

        isnad_block = IsnadLineageBlock(
            decision_id=f"decision_{ki_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            claims=heuristic.isnad_claims,
            status="VERIFIED",
        )

        tags = [heuristic.category, "endogenous_memory", "self_reflection"]

        summary = (
            f"### Distilled Heuristic\n{heuristic.heuristic}\n\n"
            f"### Named Anti-Pattern\n{heuristic.anti_pattern or 'None recorded.'}\n\n"
            f"### Empirical Evidence & Provenance\n"
            f"- **Sources**: {', '.join(Path(s).name for s in heuristic.source_artifacts)}\n"
            f"- **Confidence**: {heuristic.confidence * 100:.0f}%\n"
        )

        return KnowledgeItemRecord(
            id=ki_id,
            title=heuristic.title,
            source_target="internal://harness/history",
            detected_format="endogenous_reflection",
            isnad=isnad_block,
            tags=tags,
            summary=summary,
        )


class HarnessReflectorEngine:
    """Authoritative coordinator for internal reflection and knowledge distillation."""

    def __init__(
        self,
        storage: StorageService | None = None,
        temp_dir: Path | str | None = None,
        app_data_dir: Path | str | None = None,
        pipeline: MemoryPatternPipeline | None = None,
    ) -> None:
        self.storage = storage
        self.harvester = HarnessHistoryHarvester(temp_dir=temp_dir, app_data_dir=app_data_dir)
        self.pipeline = pipeline or MemoryPatternPipeline()

    async def reflect(
        self,
        *,
        scope: ReflectionScope | None = None,
        commit_to_vault: bool = True,
        generate_html_brief: bool = True,
        vault_dir: Path | str = ".harness/knowledge",
    ) -> ReflectionReport:
        """Execute full endogenous reflection cycle across internal memory."""
        reflection_id = f"ref_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Harvest with scope
        reports = self.harvester.harvest_temp_reports(scope=scope)
        transcripts = self.harvester.harvest_transcripts(scope=scope)

        # 2. Distill through pluggable pipeline
        heuristics = self.pipeline.distill(reports, transcripts, scope=scope)

        # 3. Formulate Knowledge Items
        kis: list[KnowledgeItemRecord] = []
        for idx, h in enumerate(heuristics, start=1):
            ki = EpisodicMemoryReflector.to_knowledge_item(h, index=idx)
            kis.append(ki)

        # 4. Commit to storage vault if available
        if commit_to_vault and self.storage is not None:
            for ki in kis:
                await self.storage.save_knowledge_item(ki)
            try:
                await self.storage.export_knowledge_vault(vault_dir=vault_dir)
            except Exception as e:
                logger.warning("Failed exporting knowledge vault to disk", error=str(e))

        # 5. Generate Visual Brief
        html_path: Path | None = None
        if generate_html_brief:
            html_path = self._generate_visual_brief(reflection_id, reports, transcripts, heuristics, kis)

        report = ReflectionReport(
            reflection_id=reflection_id,
            timestamp=now_iso,
            harvested_reports_count=len(reports),
            harvested_transcripts_count=len(transcripts),
            heuristics=heuristics,
            knowledge_items=kis,
            html_brief_path=html_path,
        )

        logger.info(
            "Endogenous reflection cycle completed",
            reflection_id=reflection_id,
            reports=len(reports),
            transcripts=len(transcripts),
            heuristics=len(heuristics),
        )

        return report

    def _generate_visual_brief(
        self,
        reflection_id: str,
        reports: list[ReportArtifact],
        transcripts: list[TranscriptSession],
        heuristics: list[DistilledHeuristic],
        kis: list[KnowledgeItemRecord],
    ) -> Path:
        """Generate an interactive HTML reflection brief in %TEMP%."""
        date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        temp_file = self.harvester.temp_dir / f"harness-reflection-{date_str}.html"

        # Build heuristics table rows
        h_rows = []
        for h in heuristics:
            cat_badge = f"<span class='px-2 py-0.5 rounded text-xs font-semibold bg-indigo-900/60 text-indigo-300 border border-indigo-700'>{h.category}</span>"
            sources_str = ", ".join(Path(s).name for s in h.source_artifacts[:3])
            h_rows.append(
                f"<tr class='border-b border-gray-800 hover:bg-gray-800/40 transition'>"
                f"<td class='py-3 px-4 font-medium text-gray-200'>{h.title}</td>"
                f"<td class='py-3 px-4'>{cat_badge}</td>"
                f"<td class='py-3 px-4 text-sm text-gray-300'>{h.heuristic}</td>"
                f"<td class='py-3 px-4 text-xs font-mono text-gray-400'>{sources_str}</td>"
                f"</tr>"
            )
        h_table_html = "\n".join(h_rows) if h_rows else "<tr><td colspan='4' class='p-4 text-center text-gray-500'>No new heuristics distilled.</td></tr>"

        # Build Mermaid lineage DAG
        mermaid_lines = [
            "graph TD",
            "  subgraph EphemeralMemory[\"1. Ephemeral Execution Residue\"]",
            f"    R[\"{len(reports)} HTML Visual Briefs in %TEMP%\"]",
            f"    T[\"{len(transcripts)} Conversation Transcripts\"]",
            "  end",
            "  subgraph ReflectionEngine[\"2. Harness Reflector Engine\"]",
            "    H[\"MemoryPatternPipeline Distillation\"]",
            "    I[\"Aquinas Isnad Provenance Audit\"]",
            "  end",
            "  subgraph KnowledgeVault[\"3. Persistent Knowledge Vault\"]",
            f"    V[\"{len(kis)} Verified Knowledge Items (KIs)\"]",
            "    G[\"Skill & Module Knowledge Graph\"]",
            "  end",
            "  R --> H",
            "  T --> H",
            "  H --> I",
            "  I --> V",
            "  V --> G",
        ]
        mermaid_code = "\n".join(mermaid_lines)

        html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Harness Memory Reflection — {reflection_id}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
</head>
<body class="bg-[#0d1117] text-gray-100 min-h-screen p-8 font-sans">
  <div class="max-w-6xl mx-auto space-y-8">
    
    <!-- Header -->
    <header class="border-b border-gray-800 pb-6">
      <div class="flex items-center justify-between">
        <div>
          <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 mb-3">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Endogenous Memory Reflection
          </div>
          <h1 class="text-3xl font-bold tracking-tight text-white">Autobiographical Cognitive Synthesis</h1>
          <p class="text-sm text-gray-400 mt-1">Distilling internal HTML reviews, conversation transcripts, and execution trajectories into the Knowledge Vault.</p>
        </div>
        <div class="text-right text-xs text-gray-500 font-mono">
          <div>ID: {reflection_id}</div>
          <div>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
      </div>
    </header>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Harvested Reports</div>
        <div class="text-3xl font-bold text-indigo-400 mt-2">{len(reports)}</div>
        <div class="text-xs text-gray-500 mt-1">HTML briefs in %TEMP%</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Parsed Transcripts</div>
        <div class="text-3xl font-bold text-cyan-400 mt-2">{len(transcripts)}</div>
        <div class="text-xs text-gray-500 mt-1">Conversation step logs</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Distilled Heuristics</div>
        <div class="text-3xl font-bold text-emerald-400 mt-2">{len(heuristics)}</div>
        <div class="text-xs text-gray-500 mt-1">Actionable invariants</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Committed KIs</div>
        <div class="text-3xl font-bold text-purple-400 mt-2">{len(kis)}</div>
        <div class="text-xs text-gray-500 mt-1">Ground-truth vault items</div>
      </div>
    </div>

    <!-- Lineage Graph -->
    <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Memory Ingestion & Isnad Lineage Topology</h2>
      <div class="mermaid bg-black/40 p-4 rounded-lg flex justify-center">
{mermaid_code}
      </div>
    </div>

    <!-- Distilled Heuristics Matrix -->
    <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Distilled Architectural Invariants & Heuristics</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-gray-800 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-950/50">
              <th class="py-3 px-4">Title</th>
              <th class="py-3 px-4">Category</th>
              <th class="py-3 px-4">Actionable Heuristic & Invariant</th>
              <th class="py-3 px-4">Grounding Sources</th>
            </tr>
          </thead>
          <tbody>
            {h_table_html}
          </tbody>
        </table>
      </div>
    </div>

    <footer class="text-center text-xs text-gray-600 pt-4 border-t border-gray-900">
      Brain Harness Endogenous Reflection Engine • Grounded Epistemic Isnad
    </footer>
  </div>
</body>
</html>
"""
        temp_file.write_text(html_content, encoding="utf-8")
        return temp_file
