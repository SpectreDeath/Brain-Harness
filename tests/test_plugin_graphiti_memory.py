"""Tests for Graphiti Memory Plugin and Kernel Service Integration."""

import pytest
from datetime import datetime, timezone

from harness.kernel.context import ServiceContext
from harness.services.graphiti import (
    GRAPHITI_MEMORY_KEY,
    EpisodeResult,
    SearchResult,
    EntityResult,
    FactResult,
    GraphitiStatusResult,
)
from plugins.memory_and_epistemics.graphiti_memory import (
    GraphitiMemoryPlugin,
    GraphitiMemoryEngine,
    graphiti_add_episode,
    graphiti_search,
    graphiti_get_entity,
    graphiti_invalidate_fact,
    graphiti_get_status,
)


@pytest.mark.unit
def test_standalone_tools_basic_flow():
    """Test standard episodic ingestion and search flow."""
    group_id = f"test_group_{int(datetime.now(timezone.utc).timestamp())}"

    # 1. Add episode
    res = graphiti_add_episode(
        content="Bob lives in Paris. Bob uses Rust for systems programming.",
        group_id=group_id,
        source_description="test_turn"
    )
    assert res["status"] == "ok"
    assert res["extracted_nodes_count"] >= 2
    assert res["extracted_edges_count"] >= 2
    assert "Bob" in res["extracted_entities"]

    # 2. Search
    search_res = graphiti_search(query="Where does Bob live?", group_id=group_id)
    assert search_res["status"] == "ok"
    assert search_res["results_count"] >= 1
    assert any("Paris" in f["fact"] for f in search_res["facts"])

    # 3. Get Entity
    ent_res = graphiti_get_entity("Bob", group_id=group_id)
    assert ent_res["status"] == "ok"
    assert ent_res["entity"]["name"] == "Bob"
    assert len(ent_res["entity"]["relations"]) >= 2

    # 4. Status
    status_res = graphiti_get_status(group_id=group_id)
    assert status_res["status"] == "ok"
    assert status_res["total_episodes"] >= 1
    assert status_res["total_facts"] >= 2
    assert status_res["active_facts"] >= 2


@pytest.mark.unit
def test_bitemporal_edge_invalidation():
    """Test bi-temporal edge invalidation when contradictory facts are ingested."""
    group_id = f"test_invalidation_{int(datetime.now(timezone.utc).timestamp())}"

    # Fact 1: Alice lives in Berlin
    res1 = graphiti_add_episode("Alice lives in Berlin.", group_id=group_id)
    assert res1["status"] == "ok"
    assert res1["invalidated_edges_count"] == 0

    search1 = graphiti_search("Where does Alice live?", group_id=group_id)
    assert len(search1["facts"]) == 1
    assert "Berlin" in search1["facts"][0]["fact"]

    # Fact 2: Alice moved to Tokyo (contradicts lives in Berlin)
    res2 = graphiti_add_episode("Alice moved to Tokyo.", group_id=group_id)
    assert res2["status"] == "ok"
    assert res2["invalidated_edges_count"] == 1

    # Active search should return Tokyo only
    active_search = graphiti_search("Where does Alice live?", group_id=group_id, include_invalidated=False)
    assert len(active_search["facts"]) == 1
    assert "Tokyo" in active_search["facts"][0]["fact"]

    # Historical search should return both Berlin and Tokyo
    historical_search = graphiti_search("Where does Alice live?", group_id=group_id, include_invalidated=True)
    assert len(historical_search["facts"]) >= 2
    facts_text = [f["fact"] for f in historical_search["facts"]]
    assert any("Berlin" in t for t in facts_text)
    assert any("Tokyo" in t for t in facts_text)


@pytest.mark.unit
def test_manual_fact_invalidation():
    """Test manual invalidation of specific fact edges."""
    group_id = f"test_manual_{int(datetime.now(timezone.utc).timestamp())}"

    res = graphiti_add_episode("Carol prefers Vim.", group_id=group_id)
    search_res = graphiti_search("What does Carol prefer?", group_id=group_id)
    assert len(search_res["facts"]) >= 1

    edge_uuid = search_res["facts"][0]["edge_uuid"]
    inv_res = graphiti_invalidate_fact(edge_uuid, reason="Switched to Neovim")
    assert inv_res["status"] == "ok"
    assert inv_res["invalidated_at"] is not None

    # Verify active search no longer finds it
    active_res = graphiti_search("What does Carol prefer?", group_id=group_id, include_invalidated=False)
    assert len(active_res["facts"]) == 0


@pytest.mark.unit
def test_multi_tenant_partition_isolation():
    """Test that group_id provides strict partition isolation."""
    group_alpha = "tenant_alpha"
    group_beta = "tenant_beta"

    graphiti_add_episode("Project Apollo uses PostgreSQL.", group_id=group_alpha)
    graphiti_add_episode("Project Gemini uses MongoDB.", group_id=group_beta)

    # Search in Alpha
    alpha_search = graphiti_search("PostgreSQL", group_id=group_alpha)
    assert len(alpha_search["facts"]) >= 1
    assert all("PostgreSQL" in f["fact"] for f in alpha_search["facts"])

    # Alpha search for MongoDB returns nothing
    alpha_gemini = graphiti_search("MongoDB", group_id=group_alpha)
    assert len(alpha_gemini["facts"]) == 0

    # Beta search for MongoDB succeeds
    beta_search = graphiti_search("MongoDB", group_id=group_beta)
    assert len(beta_search["facts"]) >= 1


@pytest.mark.asyncio
async def test_harness_plugin_service_lifecycle():
    """Test HarnessPlugin service registration and IoC context resolution."""
    plugin = GraphitiMemoryPlugin()
    ctx = ServiceContext()

    assert GRAPHITI_MEMORY_KEY in plugin.provides

    await plugin.on_load(ctx)
    await plugin.on_enable()

    # Resolve from ServiceContext
    service = ctx.require(GRAPHITI_MEMORY_KEY)
    assert service is not None

    group_id = f"ioc_test_{int(datetime.now(timezone.utc).timestamp())}"

    # Test protocol method add_episode
    ep_res: EpisodeResult = await service.add_episode(
        content="David implements GraphitiService.",
        group_id=group_id,
    )
    assert ep_res.status == "ok"
    assert ep_res.extracted_nodes_count >= 2

    # Test protocol method search
    search_res: SearchResult = await service.search(
        query="Who implements GraphitiService?",
        group_id=group_id,
    )
    assert search_res.status == "ok"
    assert search_res.results_count >= 1
    assert isinstance(search_res.facts[0], FactResult)

    # Test protocol method get_entity
    ent_res: EntityResult | None = await service.get_entity("David", group_id=group_id)
    assert ent_res is not None
    assert ent_res.name == "David"

    # Test protocol method get_status
    status_res: GraphitiStatusResult = await service.get_status(group_id=group_id)
    assert status_res.status == "ok"
    assert status_res.total_episodes >= 1

    await plugin.on_disable()
    await plugin.on_unload()
