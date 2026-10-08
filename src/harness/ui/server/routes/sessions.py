"""Agent execution, sessions, telemetry, and timeline endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from harness.ui.server.models import TaskRequest

router = APIRouter()


@router.get("/api/status")
async def get_status(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    return adapter.get_introspector().get_status_report()


@router.get("/api/projection/status")
async def get_projection_status_api(request: Request) -> dict[str, Any]:
    projection_engine = request.app.state.projection_engine
    if projection_engine is not None:
        return projection_engine.get_projection_status()
    return {"status": "uninitialized"}


@router.post("/api/agent/run")
async def run_agent(req: TaskRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    try:
        result = await adapter.run_agent(req.task, max_steps=req.max_steps)
        return {
            "status": "ok",
            "task": result.task,
            "task_status": result.status,
            "final_answer": result.final_answer,
            "steps_count": len(result.steps),
            "session_id": getattr(result, "session_id", None),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/sessions")
async def get_sessions(request: Request, status: str | None = None, limit: int = 50) -> dict[str, Any]:
    adapter = request.app.state.adapter
    from harness.agent.session import AGENT_SESSION_MANAGER_KEY

    sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
    if sess_mgr is None:
        return {"sessions": [], "total": 0}
    sessions = await sess_mgr.list_sessions(status=status, limit=limit)
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions),
    }


@router.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    from harness.agent.session import AGENT_SESSION_MANAGER_KEY

    sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
    if sess_mgr is None:
        return {"status": "error", "error": "No session manager available"}
    session = await sess_mgr.get_session(session_id)
    if session is None:
        return {"status": "error", "error": f"Session '{session_id}' not found"}
    return {"status": "ok", "session": session.to_dict()}


@router.get("/api/sessions/{session_id}/export")
async def export_session_endpoint(session_id: str, request: Request, format: str = "json") -> dict[str, Any]:
    adapter = request.app.state.adapter
    from harness.agent.session import AGENT_SESSION_MANAGER_KEY

    sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
    if sess_mgr is None:
        return {"status": "error", "error": "No session manager available"}
    try:
        content = await sess_mgr.export_session(session_id, format=format)
        return {"status": "ok", "session_id": session_id, "format": format, "content": content}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/graph")
async def get_graph(request: Request) -> dict[str, str]:
    adapter = request.app.state.adapter
    return {"mermaid": adapter.get_introspector().generate_mermaid_graph()}


@router.get("/api/events")
async def get_events(request: Request, limit: int = 50) -> list[dict[str, Any]]:
    adapter = request.app.state.adapter
    if adapter.event_bus is None:
        return []
    return [e.to_dict() for e in adapter.event_bus.log[-limit:]]


@router.get("/api/metrics")
async def get_metrics(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    if adapter.event_bus is None:
        return {
            "total_events": 0,
            "event_counts_by_type": {},
            "tool_invocations": {},
            "tool_results": {},
            "tool_errors": {},
            "total_tokens": 0,
            "llm_calls": 0,
        }
    from harness.events.bus import MetricsProjection

    projection = MetricsProjection()
    for event in adapter.event_bus.log:
        projection.handle(event)
    return projection.get_state()


@router.get("/api/timeline")
async def get_timeline(
    request: Request,
    from_time: str | None = None,
    to_time: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    adapter = request.app.state.adapter
    if adapter.event_bus is None:
        return {"events": [], "total": 0, "summary": {}}

    events: list[dict[str, Any]] = []
    counts_by_type: dict[str, int] = {}
    error_count = 0

    for event in adapter.event_bus.log:
        ts_str = event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp)
        if from_time and ts_str < from_time:
            continue
        if to_time and ts_str > to_time:
            continue
        etype = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        if event_type and etype != event_type and event_type != "*":
            continue
        if source and event.source != source:
            continue

        counts_by_type[etype] = counts_by_type.get(etype, 0) + 1
        if "error" in etype.lower() or "error" in event.source.lower():
            error_count += 1

        events.append(event.to_dict())

    if limit > 0 and len(events) > limit:
        events = events[-limit:]

    return {
        "events": events,
        "total": len(events),
        "summary": {
            "counts_by_type": counts_by_type,
            "error_count": error_count,
            "first_timestamp": events[0]["timestamp"] if events else None,
            "last_timestamp": events[-1]["timestamp"] if events else None,
        },
    }


@router.get("/api/sandboxes")
async def get_sandboxes(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    sandboxes = adapter.get_sandboxes()
    return {"sandboxes": sandboxes, "total": len(sandboxes)}


__all__ = ["router"]
