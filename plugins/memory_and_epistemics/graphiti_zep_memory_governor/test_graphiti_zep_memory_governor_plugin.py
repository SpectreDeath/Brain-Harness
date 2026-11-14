"""Plugin and IoC contract tests for plugin.graphiti_zep_memory_governor."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.graphiti_zep_memory import (  # noqa: E402
    GRAPHITI_ZEP_MEMORY_KEY,
    GraphitiZepMemoryProtocol,
)
from plugins.memory_and_epistemics.graphiti_zep_memory_governor.main import (  # noqa: E402
    GraphitiZepMemoryGovernorPlugin,
    plugin,
    zep_cluster_and_compile_ontology,
    zep_normalize_bitemporal_edges,
    zep_rerank_hybrid_search,
    zep_resolve_entities_and_endpoints,
)


@pytest.mark.asyncio
async def test_plugin_ioc_registration_and_validator() -> None:
    assert isinstance(plugin, GraphitiZepMemoryGovernorPlugin)
    assert isinstance(plugin, GraphitiZepMemoryProtocol)

    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(GRAPHITI_ZEP_MEMORY_KEY)
    assert resolved is plugin

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c for c in report.checks if not c.passed]}"


def test_plugin_entrypoint_functions() -> None:
    temp_res = zep_normalize_bitemporal_edges(
        fact="Team plans to launch before Tuesday",
        reference_time="2026-11-01T00:00:00Z",
        valid_at="2026-11-04T00:00:00Z",
        invalid_at="2026-11-05T00:00:00Z",
    )
    assert temp_res["future_assertion_detected"] is True
    assert temp_res["soft_deadline_cleared"] is True
    assert temp_res["normalized_invalid_at"] is None

    dedup_res = zep_resolve_entities_and_endpoints(
        extracted_entities=[{"name": "XY", "labels": ["Entity"]}],
        existing_entities=[],
        edge_endpoints=[("XY", "dangling-v1")],
        kept_edge_endpoints=[],
    )
    assert dedup_res["llm_deferred_names"] == ("XY",)
    assert dedup_res["pruned_endpoints"] == ("dangling-v1",)

    rerank_res = zep_rerank_hybrid_search(method="rrf", ranked_lists=[["a", "b"], ["b", "c"]])
    assert rerank_res["ranked_uuids"][0] == "b"

    onto_res = zep_cluster_and_compile_ontology(
        neighbor_projection={
            "n1": [{"node_uuid": "n2", "edge_count": 2}],
            "n2": [{"node_uuid": "n1", "edge_count": 2}],
        },
        episode_batches=[{"group_id": "grp-1"}],
        entity_schemas=[
            {
                "name": "Person",
                "description": "Human user",
                "fields": [{"name": "email", "type": "text", "description": "Email address", "identity": True}],
            }
        ],
    )
    assert onto_res["sequential_groups_verified"] is True
    assert onto_res["ontology_valid"] is True
