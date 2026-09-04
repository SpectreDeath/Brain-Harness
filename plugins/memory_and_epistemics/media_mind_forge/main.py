"""Media Mind Forge Plugin — Cognitive Analysis, Epistemic Distillation, and Skill Synthesis."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

from .engine import MediaMindForgeEngine
from .models import CognitiveAnalysisReport

# Configure standard streams to UTF-8 on Windows (AGENTS.md Rule 23)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class MediaMindForgeService(Protocol):
    """Authoritative service protocol for Media Mind Forge cognitive distillation."""

    def analyze_media(
        self,
        transcript_data: str | dict[str, Any] | Path,
        title: str = "",
        speaker: str = "",
        video_id: str = "",
    ) -> CognitiveAnalysisReport:
        ...

    def distill_knowledge_items(
        self,
        transcript_data: str | dict[str, Any] | Path,
        video_id: str = "",
    ) -> list[dict[str, Any]]:
        ...

    def craft_skill(
        self,
        transcript_data: str | dict[str, Any] | Path,
        skill_name: str,
        output_dir: Path | str,
    ) -> dict[str, str]:
        ...


MEDIA_MIND_FORGE_KEY: ServiceKey[MediaMindForgeService] = ServiceKey("service.media_mind_forge")
_GLOBAL_ENGINE = MediaMindForgeEngine()


def _get_engine() -> MediaMindForgeEngine:
    return _GLOBAL_ENGINE


def _resolve_transcript_input(
    transcript: Any = "",
    file_path: str = "",
    video_url: str = "",
    video_id: str = "",
    **kwargs: Any,
) -> tuple[str | dict[str, Any] | Path | list[dict[str, Any]], str]:
    """Resolve input transcript content and identify video ID."""
    resolved_id = video_id or kwargs.get("id", "")

    # Check transcript_source alias
    actual_transcript = transcript or kwargs.get("transcript_source", "")

    # 1. Check explicit file path
    actual_file_path = file_path or kwargs.get("path", "")
    if actual_file_path and os.path.exists(actual_file_path):
        return Path(actual_file_path), resolved_id

    # 2. Check direct transcript text or data passed
    if actual_transcript:
        if isinstance(actual_transcript, (dict, list, Path)):
            return actual_transcript, resolved_id
        if isinstance(actual_transcript, str) and os.path.exists(actual_transcript):
            return Path(actual_transcript), resolved_id
        return actual_transcript, resolved_id

    # 3. Check video URL or ID via youtube_transcript_fetcher
    target_video = video_url or resolved_id or kwargs.get("url", "")
    if target_video:
        try:
            from plugins.integration_and_io.youtube_transcript_fetcher.main import (
                extract_video_id,
                fetch_transcript,
            )

            resolved_id = extract_video_id(target_video)
            res = fetch_transcript(video_id=resolved_id)
            if res.get("status") == "ok":
                return res, resolved_id
        except Exception:
            pass

    # 4. Fallback: check outputs/transcripts/ directory
    if resolved_id:
        fallback_json = Path("outputs") / "transcripts" / f"{resolved_id}_transcript.json"
        if fallback_json.exists():
            return fallback_json, resolved_id

    return actual_transcript or "", resolved_id


# -----------------------------------------------------------------------------
# Standalone Tool Entrypoints for ToolRegistry and Subprocess RPC
# -----------------------------------------------------------------------------

def media_mind_forge_analyze(
    transcript: Any = "",
    file_path: str = "",
    video_url: str = "",
    video_id: str = "",
    title: str = "",
    speaker: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute dual-lens cognitive analysis combining mind-reader and book-to-skill-forge."""
    input_data, vid = _resolve_transcript_input(
        transcript=transcript,
        file_path=file_path,
        video_url=video_url,
        video_id=video_id,
        **kwargs,
    )

    engine = _get_engine()
    report = engine.analyze(
        transcript_data=input_data,
        title=title or kwargs.get("video_title", ""),
        speaker=speaker or kwargs.get("author_or_speaker", ""),
        video_id=vid,
        **kwargs,
    )

    return {
        "status": "ok",
        "title": report.target_title,
        "speaker": report.speaker,
        "video_id": report.video_id,
        "duration_s": report.total_duration_s,
        "word_count": report.word_count,
        "mental_models_count": len(report.mental_models),
        "heuristics_count": len(report.decision_heuristics),
        "stages_count": len(report.procedural_stages),
        "knowledge_items_count": len(report.knowledge_items),
        "visual_brief_path": report.visual_brief_path,
        "mental_models": [m.model_dump() for m in report.mental_models],
        "decision_heuristics": [h.model_dump() for h in report.decision_heuristics],
        "procedural_stages": [s.model_dump() for s in report.procedural_stages],
        "diagnostic_rubric": [r.model_dump() for r in report.diagnostic_rubric],
        "anti_patterns": [ap.model_dump() for ap in report.anti_patterns],
        "knowledge_items": [ki.model_dump() for ki in report.knowledge_items],
    }


def media_mind_forge_distill_kis(
    transcript: Any = "",
    file_path: str = "",
    video_url: str = "",
    video_id: str = "",
    persist_to_storage: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract Knowledge Items (KIs) with epistemic isnad chains from media transcript."""
    input_data, vid = _resolve_transcript_input(
        transcript=transcript,
        file_path=file_path,
        video_url=video_url,
        video_id=video_id,
        **kwargs,
    )

    engine = _get_engine()
    report = engine.analyze(
        transcript_data=input_data,
        video_id=vid,
        title=kwargs.get("video_title", ""),
        speaker=kwargs.get("author_or_speaker", ""),
        **kwargs,
    )

    ki_payloads = [ki.model_dump() for ki in report.knowledge_items]

    return {
        "status": "ok",
        "video_id": report.video_id,
        "knowledge_items_count": len(ki_payloads),
        "ki_count": len(ki_payloads),
        "knowledge_items": ki_payloads,
    }


def media_mind_forge_craft_skill(
    transcript: Any = "",
    file_path: str = "",
    video_url: str = "",
    video_id: str = "",
    skill_name: str = "ontological-engineering-coach",
    output_dir: str = ".agents/skills",
    **kwargs: Any,
) -> dict[str, Any]:
    """Synthesize complete, validated agent skill package (SKILL.md + CARD.md) from media."""
    input_data, vid = _resolve_transcript_input(
        transcript=transcript,
        file_path=file_path,
        video_url=video_url,
        video_id=video_id,
        **kwargs,
    )

    target_directory = kwargs.get("target_dir") or output_dir

    engine = _get_engine()
    report = engine.analyze(transcript_data=input_data, video_id=vid, **kwargs)

    paths = engine.forge_skill_package(
        report=report,
        output_dir=target_directory,
        skill_name=skill_name,
    )

    return {
        "status": "ok",
        "skill_name": paths["skill_name"],
        "skill_dir": paths["skill_dir"],
        "skill_file": paths["skill_file"],
        "card_file": paths["card_file"],
        "stages_count": len(report.procedural_stages),
        "anti_patterns_count": len(report.anti_patterns),
    }


def media_mind_forge_visual_brief(
    transcript: Any = "",
    file_path: str = "",
    video_url: str = "",
    video_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate self-contained HTML visual brief report in %TEMP%."""
    input_data, vid = _resolve_transcript_input(
        transcript=transcript,
        file_path=file_path,
        video_url=video_url,
        video_id=video_id,
        **kwargs,
    )

    engine = _get_engine()
    report = engine.analyze(transcript_data=input_data, video_id=vid, **kwargs)

    return {
        "status": "ok",
        "visual_brief_path": report.visual_brief_path,
        "title": report.target_title,
        "speaker": report.speaker,
    }


def health() -> dict[str, Any]:
    """Return runtime health status for Media Mind Forge plugin."""
    return {
        "status": "healthy",
        "plugin": "media_mind_forge",
        "service": "media_mind_forge",
        "category": "memory_and_epistemics",
        "capabilities": [
            "epistemic_mind_reader_distillation",
            "procedural_book_to_skill_forge",
            "knowledge_item_isnad_synthesis",
            "visual_brief_generation",
        ],
    }


# -----------------------------------------------------------------------------
# Plugin Class
# -----------------------------------------------------------------------------

class MediaMindForgePlugin(HarnessPlugin):
    """Brain-Harness plugin synthesizing book-to-skill-forge and mind-reader for media."""

    name = "media_mind_forge"
    version = "1.0.0"
    description = "Cognitive analysis, epistemic distillation, and skill forging engine combining book-to-skill-forge and mind-reader"
    trusted = True

    def __init__(self, engine: MediaMindForgeEngine | None = None) -> None:
        self.engine = engine or _get_engine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MEDIA_MIND_FORGE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    @property
    def manifest(self) -> Any:
        from types import SimpleNamespace
        return SimpleNamespace(
            name=self.name,
            version=self.version,
            provides=["service.media_mind_forge"],
            requires=[],
        )

    def register_services(self, ctx: ServiceContext) -> None:
        ctx.provide(MEDIA_MIND_FORGE_KEY, self, provider=self.name)

    async def on_load(self, ctx: ServiceContext) -> None:
        """Register the MediaMindForgeService into the IoC container."""
        ctx.provide(MEDIA_MIND_FORGE_KEY, self, provider=self.name)

    def analyze_media(
        self,
        transcript_data: str | dict[str, Any] | Path,
        title: str = "",
        speaker: str = "",
        video_id: str = "",
    ) -> CognitiveAnalysisReport:
        return self.engine.analyze(
            transcript_data=transcript_data,
            title=title,
            speaker=speaker,
            video_id=video_id,
        )

    def distill_knowledge_items(
        self,
        transcript_data: str | dict[str, Any] | Path,
        video_id: str = "",
    ) -> list[dict[str, Any]]:
        report = self.engine.analyze(transcript_data=transcript_data, video_id=video_id)
        return [ki.model_dump() for ki in report.knowledge_items]

    def craft_skill(
        self,
        transcript_data: str | dict[str, Any] | Path,
        skill_name: str,
        output_dir: Path | str,
    ) -> dict[str, str]:
        report = self.engine.analyze(transcript_data=transcript_data)
        return self.engine.forge_skill_package(report=report, output_dir=output_dir, skill_name=skill_name)

