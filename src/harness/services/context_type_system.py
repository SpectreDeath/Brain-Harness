"""Context Type System service protocol, typed result models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ContextItemModel(BaseModel):
    """Pydantic representation of a typed context item."""

    context_type: str = Field(..., description="Context type (instruction, memory, evidence, tool_output)")
    content: str = Field(..., description="Text content")
    source: str | None = Field(default=None, description="Origin source identifier")
    priority: int = Field(default=0, description="Priority ranking")
    created: float = Field(..., description="Timestamp of creation")
    request_id: str = Field(..., description="Unique 8-char identifier")
    derived_from: str | None = Field(default=None, description="Origin request_id if transformed")


class ContextAddResult(BaseModel):
    """Result of registering a context item."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    item: ContextItemModel | None = Field(default=None, description="Registered context item")
    error: str | None = Field(default=None, description="Error message if rejected")


class ContextTransformResult(BaseModel):
    """Result of transforming a context item."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    item: ContextItemModel | None = Field(default=None, description="Transformed context item")
    error: str | None = Field(default=None, description="Error message if transition not permitted")


class ContextValidateResult(BaseModel):
    """Result of validating raw tool output and elevating to evidence."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    item: ContextItemModel | None = Field(default=None, description="Promoted evidence item")
    error: str | None = Field(default=None, description="Validation failure explanation")


class ContextPromptResult(BaseModel):
    """Result of assembling structured context into a prompt string."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    session_id: str = Field(..., description="Session identifier")
    prompt: str = Field(..., description="Rendered prompt with semantic channel boundaries")
    item_count: int = Field(default=0, description="Number of items rendered")
    used_tokens: int | None = Field(default=None, description="Estimated token count of rendered prompt")
    dropped_items_count: int = Field(default=0, description="Number of lower-priority items dropped due to budget constraints")
    channel_breakdown: dict[str, int] = Field(default_factory=dict, description="Item count breakdown per channel")


class ContextLedgerRecord(BaseModel):
    """Record in the provenance ledger."""

    key: str = Field(..., description="Normalized content key")
    origin_type: str = Field(..., description="Type at first registration")
    origin_id: str = Field(..., description="Request ID of original item")


class ContextLedgerResult(BaseModel):
    """Result of inspecting the provenance ledger."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    session_id: str = Field(..., description="Session identifier")
    total_items: int = Field(default=0, description="Total active items in session")
    items: list[ContextItemModel] = Field(default_factory=list, description="List of items in session")
    ledger: list[ContextLedgerRecord] = Field(default_factory=list, description="Provenance ledger records")


class ContextLineageResult(BaseModel):
    """Result of tracing multi-hop Isnad provenance lineage."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    session_id: str = Field(..., description="Session identifier")
    request_id: str = Field(..., description="Target item request ID")
    lineage: list[ContextItemModel] = Field(default_factory=list, description="Chain of ancestor items from root to target")
    root_id: str | None = Field(default=None, description="Request ID of origin observation root")
    hops: int = Field(default=0, description="Number of derivation hops")
    error: str | None = Field(default=None, description="Error message if resolution fails")


class ContextSnapshotResult(BaseModel):
    """Result of exporting or importing a context session snapshot."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    session_id: str = Field(..., description="Session identifier")
    data: dict[str, Any] = Field(default_factory=dict, description="Serialized session snapshot data")
    error: str | None = Field(default=None, description="Error message if snapshot operation fails")


@runtime_checkable
class ContextTypeService(Protocol):
    """Protocol for Context Type System provenance, validation, and prompt assembly."""

    async def add_context(
        self,
        session_id: str,
        context_type: str,
        content: str,
        source: str | None = None,
        priority: int = 0,
    ) -> ContextAddResult:
        """Register a context item into a typed context store session."""
        ...

    async def transform_context(
        self,
        session_id: str,
        request_id: str,
        to_type: str,
        source: str | None = None,
    ) -> ContextTransformResult:
        """Explicitly transition an item across permitted policy boundaries."""
        ...

    async def validate_tool_output(
        self,
        session_id: str,
        tool_request_id: str,
        strict_mode: bool = False,
    ) -> ContextValidateResult:
        """Validate raw tool execution output and elevate it to evidence."""
        ...

    async def assemble_prompt(
        self,
        session_id: str,
        section_order: list[str] | None = None,
        custom_labels: dict[str, str] | None = None,
        max_tokens: int | None = None,
        channel_quotas: dict[str, float] | None = None,
    ) -> ContextPromptResult:
        """Render typed context items into ordered prompt sections with optional token budgeting."""
        ...

    async def inspect_ledger(
        self,
        session_id: str,
        filter_type: str | None = None,
    ) -> ContextLedgerResult:
        """Audit the provenance ledger and derivation records for a session."""
        ...

    async def get_lineage(
        self,
        session_id: str,
        request_id: str,
    ) -> ContextLineageResult:
        """Trace the full multi-hop derivation chain back to the root observation."""
        ...

    async def export_session(
        self,
        session_id: str,
    ) -> ContextSnapshotResult:
        """Export session state to a portable snapshot dictionary."""
        ...

    async def import_session(
        self,
        session_id: str,
        data: dict[str, Any],
    ) -> ContextSnapshotResult:
        """Restore session state from a portable snapshot dictionary."""
        ...


CONTEXT_TYPE_SYSTEM_KEY: ServiceKey[ContextTypeService] = ServiceKey("service.context_type_system")
