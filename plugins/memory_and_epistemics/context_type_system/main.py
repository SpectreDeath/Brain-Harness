"""Context Type System Plugin & HarnessPlugin Service Implementation."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.context_type_system import (
    CONTEXT_TYPE_SYSTEM_KEY,
    ContextAddResult,
    ContextItemModel,
    ContextLedgerRecord,
    ContextLedgerResult,
    ContextLineageResult,
    ContextPromptResult,
    ContextSnapshotResult,
    ContextTransformResult,
    ContextTypeService,
    ContextValidateResult,
)

from .engine import (
    BudgetConfig,
    ContextAssembler,
    ContextItem,
    ContextSessionManager,
    ContextType,
    ContextTypeError,
    validate_tool_result,
)

logger = structlog.get_logger(__name__)

# Global session manager instance for standalone tool execution
_SESSION_MANAGER = ContextSessionManager()
_ASSEMBLER = ContextAssembler()


def _get_manager() -> ContextSessionManager:
    return _SESSION_MANAGER


def context_add(
    session_id: str,
    context_type: str,
    content: str,
    source: str | None = None,
    priority: int = 0,
) -> dict[str, Any]:
    """Register a typed context item into a session, checking origin ledger against protected channels."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    try:
        item = store.add_context(
            context_type=context_type,
            content=content,
            source=source,
            priority=priority,
        )
        return {
            "status": "ok",
            "item": item.to_dict(),
            "error": None,
        }
    except (ContextTypeError, ValueError) as e:
        logger.warn("context_add_rejected", session_id=session_id, error=str(e))
        return {
            "status": "error",
            "item": None,
            "error": str(e),
        }


def context_transform(
    session_id: str,
    request_id: str,
    to_type: str,
    source: str | None = None,
) -> dict[str, Any]:
    """Explicitly transition a context item across permitted policy boundaries, recording derivation lineage."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    item = store.get_item(request_id)
    if item is None:
        return {
            "status": "error",
            "item": None,
            "error": f"Item with request_id '{request_id}' not found in session '{session_id}'",
        }
    try:
        new_item = store.transform(item, to_type=to_type, source=source)
        return {
            "status": "ok",
            "item": new_item.to_dict(),
            "error": None,
        }
    except (ContextTypeError, ValueError) as e:
        logger.warn("context_transform_rejected", session_id=session_id, request_id=request_id, error=str(e))
        return {
            "status": "error",
            "item": None,
            "error": str(e),
        }


def context_validate_tool_output(
    session_id: str,
    tool_request_id: str,
    strict_mode: bool = False,
) -> dict[str, Any]:
    """Validate raw tool execution output and elevate it to evidence if passing validation criteria."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    tool_item = store.get_item(tool_request_id)
    if tool_item is None:
        return {
            "status": "error",
            "item": None,
            "error": f"Tool output item with request_id '{tool_request_id}' not found in session '{session_id}'",
        }
    if tool_item.context_type != ContextType.TOOL_OUTPUT:
        return {
            "status": "error",
            "item": None,
            "error": f"Item '{tool_request_id}' is of type '{tool_item.context_type.value}', expected 'tool_output'",
        }
    try:
        evidence_item = validate_tool_result(store, tool_item, strict_mode=strict_mode)
        return {
            "status": "ok",
            "item": evidence_item.to_dict(),
            "error": None,
        }
    except ContextTypeError as e:
        logger.warn("tool_validation_failed", session_id=session_id, request_id=tool_request_id, error=str(e))
        return {
            "status": "error",
            "item": None,
            "error": str(e),
        }


def context_assemble_prompt(
    session_id: str,
    section_order: list[str] | None = None,
    custom_labels: dict[str, str] | None = None,
    max_tokens: int | None = None,
    channel_quotas: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Render typed context items into ordered prompt sections with token budgeting and channel quotas."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    items = store.items()
    detailed = _ASSEMBLER.assemble_detailed(
        items=items,
        section_order=section_order,
        custom_labels=custom_labels,
        max_tokens=max_tokens,
        channel_quotas=channel_quotas,
    )
    return {
        "status": "ok",
        "session_id": session_id,
        "prompt": detailed["prompt"],
        "item_count": detailed["item_count"],
        "used_tokens": detailed["used_tokens"],
        "dropped_items_count": detailed["dropped_items_count"],
        "channel_breakdown": detailed["channel_breakdown"],
    }


def context_inspect_ledger(
    session_id: str,
    filter_type: str | None = None,
) -> dict[str, Any]:
    """Audit provenance records, origin types, transition history, and ledger keys for a context session."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    items = store.items()
    if filter_type:
        try:
            target_t = ContextType(filter_type)
            items = [i for i in items if i.context_type == target_t]
        except ValueError:
            items = []

    return {
        "status": "ok",
        "session_id": session_id,
        "total_items": len(items),
        "items": [i.to_dict() for i in items],
        "ledger": store.get_ledger(),
    }


def context_get_lineage(
    session_id: str,
    request_id: str,
) -> dict[str, Any]:
    """Trace the full multi-hop derivation chain back to the root observation (Isnad lineage audit)."""
    manager = _get_manager()
    store = manager.get_session(session_id)
    target_item = store.get_item(request_id)
    if target_item is None:
        return {
            "status": "error",
            "session_id": session_id,
            "request_id": request_id,
            "lineage": [],
            "root_id": None,
            "hops": 0,
            "error": f"Item '{request_id}' not found in session '{session_id}'",
        }

    chain = store.get_lineage(request_id)
    root_id = chain[0].request_id if chain else None
    hops = max(0, len(chain) - 1)

    return {
        "status": "ok",
        "session_id": session_id,
        "request_id": request_id,
        "lineage": [i.to_dict() for i in chain],
        "root_id": root_id,
        "hops": hops,
        "error": None,
    }


def context_export_session(
    session_id: str,
) -> dict[str, Any]:
    """Export session state as a portable snapshot dictionary."""
    manager = _get_manager()
    snapshot = manager.export_session(session_id)
    return {
        "status": "ok",
        "session_id": session_id,
        "data": snapshot,
        "error": None,
    }


def context_import_session(
    session_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Restore a session from a snapshot dictionary."""
    manager = _get_manager()
    try:
        manager.import_session(session_id, data)
        return {
            "status": "ok",
            "session_id": session_id,
            "data": data,
            "error": None,
        }
    except Exception as e:
        logger.error("context_import_failed", session_id=session_id, error=str(e))
        return {
            "status": "error",
            "session_id": session_id,
            "data": {},
            "error": str(e),
        }


class ContextTypeSystemPlugin(HarnessPlugin, ContextTypeService):
    """Harness Plugin implementing ContextTypeService and registering CONTEXT_TYPE_SYSTEM_KEY."""

    name = "plugin.context_type_system"
    version = "1.1.0"
    description = "Context provenance, type channel separation, origin ledger verification, token budgeting, and prompt assembly engine"
    trusted = True

    def __init__(self) -> None:
        self._manager = _get_manager()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CONTEXT_TYPE_SYSTEM_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(CONTEXT_TYPE_SYSTEM_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # ContextTypeService Protocol Implementation
    async def add_context(
        self,
        session_id: str,
        context_type: str,
        content: str,
        source: str | None = None,
        priority: int = 0,
    ) -> ContextAddResult:
        res = context_add(session_id, context_type, content, source=source, priority=priority)
        item_model = ContextItemModel(**res["item"]) if res["item"] else None
        return ContextAddResult(status=res["status"], item=item_model, error=res["error"])

    async def transform_context(
        self,
        session_id: str,
        request_id: str,
        to_type: str,
        source: str | None = None,
    ) -> ContextTransformResult:
        res = context_transform(session_id, request_id, to_type, source=source)
        item_model = ContextItemModel(**res["item"]) if res["item"] else None
        return ContextTransformResult(status=res["status"], item=item_model, error=res["error"])

    async def validate_tool_output(
        self,
        session_id: str,
        tool_request_id: str,
        strict_mode: bool = False,
    ) -> ContextValidateResult:
        res = context_validate_tool_output(session_id, tool_request_id, strict_mode=strict_mode)
        item_model = ContextItemModel(**res["item"]) if res["item"] else None
        return ContextValidateResult(status=res["status"], item=item_model, error=res["error"])

    async def assemble_prompt(
        self,
        session_id: str,
        section_order: list[str] | None = None,
        custom_labels: dict[str, str] | None = None,
        max_tokens: int | None = None,
        channel_quotas: dict[str, float] | None = None,
    ) -> ContextPromptResult:
        res = context_assemble_prompt(
            session_id=session_id,
            section_order=section_order,
            custom_labels=custom_labels,
            max_tokens=max_tokens,
            channel_quotas=channel_quotas,
        )
        return ContextPromptResult(**res)

    async def inspect_ledger(
        self,
        session_id: str,
        filter_type: str | None = None,
    ) -> ContextLedgerResult:
        res = context_inspect_ledger(session_id, filter_type=filter_type)
        items = [ContextItemModel(**i) for i in res["items"]]
        ledger_records = [ContextLedgerRecord(**r) for r in res["ledger"]]
        return ContextLedgerResult(
            status=res["status"],
            session_id=res["session_id"],
            total_items=res["total_items"],
            items=items,
            ledger=ledger_records,
        )

    async def get_lineage(
        self,
        session_id: str,
        request_id: str,
    ) -> ContextLineageResult:
        res = context_get_lineage(session_id, request_id)
        lineage_models = [ContextItemModel(**i) for i in res["lineage"]]
        return ContextLineageResult(
            status=res["status"],
            session_id=res["session_id"],
            request_id=res["request_id"],
            lineage=lineage_models,
            root_id=res["root_id"],
            hops=res["hops"],
            error=res["error"],
        )

    async def export_session(
        self,
        session_id: str,
    ) -> ContextSnapshotResult:
        res = context_export_session(session_id)
        return ContextSnapshotResult(**res)

    async def import_session(
        self,
        session_id: str,
        data: dict[str, Any],
    ) -> ContextSnapshotResult:
        res = context_import_session(session_id, data)
        return ContextSnapshotResult(**res)
