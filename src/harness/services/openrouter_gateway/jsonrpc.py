"""JSON-RPC 2.0 protocol engine for OpenRouter gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.services.openrouter_gateway.models import JSONRPCError, JSONRPCResponse

if TYPE_CHECKING:
    from harness.services.openrouter_gateway.service import OpenRouterGatewayService

logger = structlog.get_logger()


async def execute_jsonrpc_single(
    service: OpenRouterGatewayService,
    request: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, Any]:
    """Process a single JSON-RPC 2.0 request object."""
    req_id = request.get("id")
    if request.get("jsonrpc") != "2.0":
        return JSONRPCResponse(
            id=req_id,
            error=JSONRPCError(code=-32600, message="Invalid Request: jsonrpc must be '2.0'"),
        ).model_dump()

    method = request.get("method", "")
    params = request.get("params", {}) or {}

    try:
        if method == "openrouter.chat":
            resp = await service.chat(
                messages=params.get("messages", []),
                model=params.get("model"),
                reasoning=params.get("reasoning"),
                temperature=params.get("temperature"),
                max_tokens=params.get("max_tokens"),
                order=params.get("order"),
                allow_fallbacks=params.get("allow_fallbacks", True),
                api_key=api_key,
            )
            return JSONRPCResponse(id=req_id, result=resp.model_dump()).model_dump()

        elif method == "openrouter.models":
            models = await service.list_models(
                provider=params.get("provider"),
                modality=params.get("modality"),
                max_price=params.get("max_price"),
                api_key=api_key,
            )
            return JSONRPCResponse(
                id=req_id,
                result=[m.model_dump() for m in models],
            ).model_dump()

        elif method == "openrouter.route":
            route = await service.resolve_route(
                params.get("task_type", "general"),
                tier=params.get("tier", "medium"),
                budget=params.get("budget", "standard"),
            )
            return JSONRPCResponse(id=req_id, result=route.model_dump()).model_dump()

        else:
            return JSONRPCResponse(
                id=req_id,
                error=JSONRPCError(code=-32601, message=f"Method not found: {method}"),
            ).model_dump()

    except Exception as e:
        logger.error("JSON-RPC execution error", method=method, error=str(e))
        return JSONRPCResponse(
            id=req_id,
            error=JSONRPCError(code=-32000, message=str(e)),
        ).model_dump()


async def execute_jsonrpc_dispatch(
    service: OpenRouterGatewayService,
    payload: dict[str, Any] | list[dict[str, Any]],
    api_key: str | None = None,
) -> dict[str, Any]:
    """Dispatch JSON-RPC 2.0 request or batch request."""
    if isinstance(payload, list):
        results = [await execute_jsonrpc_single(service, req, api_key=api_key) for req in payload]
        return {"batch": results}
    return await execute_jsonrpc_single(service, payload, api_key=api_key)
