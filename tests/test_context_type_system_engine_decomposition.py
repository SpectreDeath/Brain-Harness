"""Contract tests for Cycle 69: Context Type System Engine Decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.context_type_system import (
    CONTEXT_TYPE_SYSTEM_KEY,
    ContextTypeService,
    resolve_context_type_system,
)
from plugins.memory_and_epistemics.context_type_system.engine import (
    ALLOWED_TRANSITIONS,
    PROTECTED_TYPES,
    SECTION_LABELS,
    SECTION_ORDER,
    BudgetConfig,
    ContextAssembler,
    ContextItem,
    ContextObserver,
    ContextSessionManager,
    ContextStore,
    ContextType,
    ContextTypeError,
    transition_allowed,
    validate_tool_result,
)
from plugins.memory_and_epistemics.context_type_system.engine.assembler import (
    ContextAssembler as ModularAssembler,
)
from plugins.memory_and_epistemics.context_type_system.engine.models import (
    BudgetConfig as ModularBudgetConfig,
    ContextItem as ModularContextItem,
    ContextType as ModularContextType,
)
from plugins.memory_and_epistemics.context_type_system.engine.session import (
    ContextSessionManager as ModularSessionManager,
)
from plugins.memory_and_epistemics.context_type_system.engine.store import (
    ContextStore as ModularStore,
)
from plugins.memory_and_epistemics.context_type_system.main import (
    ContextTypeSystemPlugin,
    plugin,
)


def test_submodule_line_count_bounds():
    """Rule 11: All submodules in engine/ must not exceed 200 lines."""
    engine_dir = Path(__file__).resolve().parent.parent / "plugins" / "memory_and_epistemics" / "context_type_system" / "engine"
    assert engine_dir.is_dir(), f"Directory not found: {engine_dir}"

    submodules = list(engine_dir.glob("*.py"))
    assert len(submodules) >= 6, f"Expected at least 6 submodules, found {len(submodules)}"

    for py_file in submodules:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        line_count = len(lines)
        assert line_count <= 200, f"{py_file.name} exceeded line limit: {line_count} > 200 lines"


def test_modular_exports_and_aliases():
    """Verify facade re-exports match granular submodules."""
    assert ModularContextType is ContextType
    assert ModularContextItem is ContextItem
    assert ModularBudgetConfig is BudgetConfig
    assert ModularAssembler is ContextAssembler
    assert ModularStore is ContextStore
    assert ModularSessionManager is ContextSessionManager


def test_slotted_dataclass_architecture():
    """Rule 12: High-volume internal entities must use slots=True."""
    assert hasattr(ContextItem, "__slots__")
    assert hasattr(BudgetConfig, "__slots__")

    item = ContextItem(
        context_type=ContextType.EVIDENCE,
        content="Slotted verification test content",
        source="test_runner",
        priority=10,
    )
    assert item.context_type == ContextType.EVIDENCE
    assert item.estimate_tokens(char_per_token=4.0) > 0
    assert "source=test_runner" in item.describe()


def test_channel_boundaries_and_rejections():
    """Verify semantic channel separation and transition guardrails."""
    assert ContextType.INSTRUCTION in PROTECTED_TYPES
    assert (ContextType.TOOL_OUTPUT, ContextType.EVIDENCE) in ALLOWED_TRANSITIONS
    assert (ContextType.EVIDENCE, ContextType.MEMORY) in ALLOWED_TRANSITIONS
    assert transition_allowed(ContextType.TOOL_OUTPUT, ContextType.EVIDENCE)
    assert not transition_allowed(ContextType.EVIDENCE, ContextType.INSTRUCTION)

    store = ContextStore()
    t_item = store.add_context(
        context_type=ContextType.TOOL_OUTPUT,
        content="System metrics: healthy",
        source="monitor",
    )
    ev_item = store.transform(t_item, ContextType.EVIDENCE)
    assert ev_item.context_type == ContextType.EVIDENCE

    with pytest.raises(ContextTypeError):
        store.transform(ev_item, ContextType.INSTRUCTION)


def test_o1_lookup_and_multi_hop_isnad_lineage():
    """Verify O(1) indexed lookup and full Isnad derivation DAG chain."""
    store = ContextStore()
    item1 = store.add_context(ContextType.TOOL_OUTPUT, "Log payload bytes", source="collector")
    item2 = store.transform(item1, ContextType.EVIDENCE, source="analyst")
    item3 = store.transform(item2, ContextType.MEMORY, source="curator")

    # O(1) indexed item lookup
    found = store.get_item(item3.request_id)
    assert found is not None
    assert found.request_id == item3.request_id

    # Lineage chain
    chain = store.get_lineage(item3.request_id)
    assert len(chain) == 3
    assert chain[0].request_id == item1.request_id
    assert chain[1].request_id == item2.request_id
    assert chain[2].request_id == item3.request_id


def test_assembler_quotas_and_knapsack_pruning():
    """Verify prompt assembly with channel quotas and token limits."""
    store = ContextStore()
    store.add_context(ContextType.INSTRUCTION, "Critical system instruction that must be retained.", priority=100)
    store.add_context(ContextType.EVIDENCE, "First long factual evidence chunk that consumes the quota.", priority=80)
    store.add_context(ContextType.EVIDENCE, "Second long factual evidence chunk that will overflow the quota.", priority=20)
    store.add_context(ContextType.TOOL_OUTPUT, "Verbose low priority debug dump that should not fit.", priority=1)

    assembler = ContextAssembler()
    detailed = assembler.assemble_detailed(
        items=store.items(),
        max_tokens=40,
        channel_quotas={ContextType.INSTRUCTION: 0.5, ContextType.EVIDENCE: 0.5},
    )

    assert detailed["item_count"] > 0
    assert detailed["dropped_items_count"] > 0
    assert "Instructions:" in detailed["prompt"]
    assert "Critical system instruction" in detailed["prompt"]


def test_single_seam_resolver_and_plugin_singleton():
    """Rule 45 & Rule 58: Plugin singleton and single-seam resolver."""
    assert isinstance(plugin, ContextTypeSystemPlugin)
    assert isinstance(plugin, HarnessPlugin)
    assert isinstance(plugin, ContextTypeService)

    # Resolution without context -> returns fallback singleton
    resolved_default = resolve_context_type_system(None)
    assert isinstance(resolved_default, ContextTypeService)

    # Resolution with ServiceContext containing service
    ctx = ServiceContext()
    ctx.provide(CONTEXT_TYPE_SYSTEM_KEY, plugin, provider=plugin.name)
    resolved_ctx = resolve_context_type_system(ctx)
    assert resolved_ctx is plugin
