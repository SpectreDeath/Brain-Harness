"""Execution engines for CellCog multimodal tasks and deep research workflows."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Sequence

import structlog

from harness.services.cellcog.compiler import MultimodalProtocolCompiler
from harness.services.cellcog.models import (
    DEFAULT_CHAT_MODE,
    DEFAULT_CHAT_TIER,
    DEFAULT_RESEARCH_TIMEOUT_SEC,
    DEFAULT_TIMEOUT_SEC,
    ENV_CELLCOG_API_KEY,
    CellCogArtifact,
    CellCogResearchResult,
    CellCogRunResult,
)

logger = structlog.get_logger(__name__)


async def execute_cellcog_task(
    client: Any,
    is_configured: bool,
    prompt: str,
    chat_mode: str = DEFAULT_CHAT_MODE,
    chat_tier: str = DEFAULT_CHAT_TIER,
    timeout: int = DEFAULT_TIMEOUT_SEC,
    task_label: str = "task",
    check_disk: bool = False,
    emit_telemetry: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
) -> CellCogRunResult:
    """Execute an any-to-any multimodal task via CellCog SDK or verified mock."""
    comp = MultimodalProtocolCompiler.compile_prompt(prompt, check_disk=check_disk)

    if emit_telemetry:
        await emit_telemetry(
            "TOOL_INVOKED",
            {
                "action": "execute_start", "task_label": task_label,
                "chat_mode": chat_mode, "chat_tier": chat_tier,
                "inputs_count": len(comp.valid_inputs),
                "outputs_count": len(comp.output_destinations),
            },
        )

    if not is_configured:
        err_msg = f"CellCog API key not configured. Set {ENV_CELLCOG_API_KEY}."
        if emit_telemetry:
            await emit_telemetry("TOOL_ERROR", {"action": "execute_failed", "task_label": task_label, "error": err_msg})
        return CellCogRunResult(
            success=False, message="", chat_mode=chat_mode, chat_tier=chat_tier,
            attached_files=comp.valid_inputs, generated_files=comp.output_destinations, error=err_msg,
        )

    if client is None:
        # Mock fallback when SDK is not present in local test environment
        artifacts = tuple(CellCogArtifact.from_path(p) for p in comp.output_destinations)
        if emit_telemetry:
            await emit_telemetry("TOOL_RESULT", {"action": "execute_completed", "task_label": task_label, "mock": True})
        return CellCogRunResult(
            success=True,
            message=f"[MOCK] CellCog successfully executed task '{task_label}' in mode '{chat_mode}' (tier: '{chat_tier}').",
            chat_id=f"mock-chat-{task_label}", chat_mode=chat_mode, chat_tier=chat_tier,
            attached_files=comp.valid_inputs, generated_files=comp.output_destinations,
            downloaded_files=comp.output_destinations, artifacts=artifacts,
            raw_response={"status": "completed", "mock": True},
        )

    try:
        result = client.create_chat(
            prompt=comp.sanitized_prompt, chat_mode=chat_mode, chat_tier=chat_tier,
            timeout=timeout, task_label=task_label,
        )
        message = result.get("message", "") if isinstance(result, dict) else str(result)
        chat_id = result.get("chat_id", "") if isinstance(result, dict) else ""
        downloaded = tuple(result.get("downloaded_files", [])) if isinstance(result, dict) else comp.output_destinations
        artifacts = tuple(CellCogArtifact.from_path(p) for p in downloaded)

        if emit_telemetry:
            await emit_telemetry(
                "TOOL_RESULT",
                {"action": "execute_completed", "task_label": task_label, "chat_id": chat_id, "downloaded_count": len(downloaded)},
            )

        return CellCogRunResult(
            success=True, message=message, chat_id=chat_id, chat_mode=chat_mode, chat_tier=chat_tier,
            attached_files=comp.valid_inputs, generated_files=comp.output_destinations,
            downloaded_files=downloaded, artifacts=artifacts,
            raw_response=result if isinstance(result, dict) else {"result": result},
        )
    except Exception as ex:
        logger.error("cellcog_execution_failed", error=str(ex), exc_info=True)
        if emit_telemetry:
            await emit_telemetry("TOOL_ERROR", {"action": "execute_failed", "task_label": task_label, "error": str(ex)})
        return CellCogRunResult(
            success=False, message="", chat_mode=chat_mode, chat_tier=chat_tier,
            attached_files=comp.valid_inputs, generated_files=comp.output_destinations, error=str(ex),
        )


async def execute_cellcog_research(
    execute_fn: Callable[..., Coroutine[Any, Any, CellCogRunResult]],
    topic: str,
    attachments: Sequence[str] | None = None,
    chat_tier: str = DEFAULT_CHAT_TIER,
    timeout: int = DEFAULT_RESEARCH_TIMEOUT_SEC,
) -> CellCogResearchResult:
    """Execute deep multi-source research via CellCog team mode."""
    prompt_parts = [f"Conduct deep research on: {topic}"]
    if attachments:
        for att in attachments:
            prompt_parts.append(f"<SHOW_FILE>{att}</SHOW_FILE>")

    full_prompt = "\n".join(prompt_parts)
    run_res = await execute_fn(
        prompt=full_prompt,
        chat_mode="team",
        chat_tier=chat_tier,
        timeout=timeout,
        task_label="deep-research",
    )

    if not run_res.success:
        return CellCogResearchResult(
            success=False,
            summary="",
            chat_id=run_res.chat_id,
            chat_tier=chat_tier,
            attached_files=run_res.attached_files,
            generated_files=run_res.generated_files,
            artifacts=run_res.artifacts,
            error=run_res.error,
        )

    sources = run_res.raw_response.get("sources") if isinstance(run_res.raw_response, dict) else None
    if isinstance(sources, list):
        sources_count = len(sources)
    elif run_res.raw_response.get("mock"):
        sources_count = 5
    else:
        sources_count = 1

    findings = tuple(run_res.raw_response.get("findings", [])) if isinstance(run_res.raw_response, dict) else ()

    return CellCogResearchResult(
        success=True,
        summary=run_res.message,
        sources_count=sources_count,
        chat_id=run_res.chat_id,
        chat_tier=chat_tier,
        attached_files=run_res.attached_files,
        generated_files=run_res.generated_files,
        artifacts=run_res.artifacts,
        findings=findings,
        raw_response=run_res.raw_response,
    )
