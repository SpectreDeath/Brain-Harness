"""CellCog SDK adapter and telemetry emission helper."""

from __future__ import annotations

from typing import Any

import structlog

from harness.services.cellcog.models import ENV_CELLCOG_API_KEY

logger = structlog.get_logger(__name__)


def create_cellcog_client(api_key: str | None, agent_provider: str) -> Any:
    """Instantiate the underlying CellCogClient or log fallback."""
    if not api_key:
        raise ValueError(
            f"CellCog API key not configured. Set the {ENV_CELLCOG_API_KEY} environment variable."
        )

    try:
        from cellcog import CellCogClient  # type: ignore[import-not-found]
        return CellCogClient(
            api_key=api_key,
            agent_provider=agent_provider,
        )
    except ImportError:
        logger.info("cellcog_sdk_not_installed_using_mock_fallback")
        return None


async def emit_cellcog_telemetry(event_bus: Any, event_type_name: str, payload: dict[str, Any]) -> None:
    """Emit telemetry event to EventBus if present."""
    if event_bus is None:
        return
    try:
        from harness.events.types import EventType, tool_event
        etype = getattr(EventType, event_type_name, EventType.TOOL_INVOKED)
        evt = tool_event(etype, tool_name="service.cellcog", source="service.cellcog", **payload)
        await event_bus.emit(evt)
    except Exception as ex:
        logger.debug("cellcog_telemetry_emission_failed", error=str(ex))
