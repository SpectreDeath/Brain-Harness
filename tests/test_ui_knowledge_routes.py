"""Integration tests for UI knowledge graph endpoints and contradiction resolution."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.ui.server import create_app


@pytest.mark.asyncio
async def test_ui_knowledge_endpoints(tmp_path: Path) -> None:
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir(parents=True)

    # Scaffolding 2 test items
    for item_id, title, cat, tags in [
        ("ki-ui-1", "Agent Swarm Deliberation", "agent_orchestration", ["swarm", "worker"]),
        ("ki-ui-2", "Multi-Agent Consensus", "agent_orchestration", ["swarm", "consensus"]),
    ]:
        item_dir = vault_dir / item_id
        item_dir.mkdir()
        meta = {
            "id": item_id,
            "title": title,
            "category": cat,
            "tags": tags,
            "isnad": {"status": "VERIFIED", "claims": [{"text": "claim", "confidence": 0.9}]},
        }
        (item_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (item_dir / "summary.md").write_text(f"# {title}\nSummary.", encoding="utf-8")

    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)
    bus = EventBus()
    app = create_app(ctx, lifecycle, bus)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/knowledge/graph
        res = await client.get(f"/api/knowledge/graph?vault_dir={vault_dir}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "summary" in data
        assert "graph" in data
        assert "mermaid" in data
        assert data["summary"]["total_nodes"] >= 2

        # 2. GET /api/knowledge/graph with domain filter
        res_filtered = await client.get(f"/api/knowledge/graph?domain=agent_orchestration&vault_dir={vault_dir}")
        assert res_filtered.status_code == 200
        assert len(res_filtered.json()["graph"]["nodes"]) >= 2

        # 3. GET /api/knowledge/graph/html
        res_html = await client.get(f"/api/knowledge/graph/html?vault_dir={vault_dir}")
        assert res_html.status_code == 200
        assert "<!DOCTYPE html>" in res_html.text
        assert "const DATA =" in res_html.text
        assert "graph-canvas" in res_html.text

        # 4. GET /api/knowledge/contradictions
        res_conflicts = await client.get(f"/api/knowledge/contradictions?vault_dir={vault_dir}")
        assert res_conflicts.status_code == 200
        assert res_conflicts.json()["status"] == "ok"

        # 5. POST /api/knowledge/contradictions/resolve
        resolve_payload = {
            "ki_a": "ki-ui-1",
            "ki_b": "ki-ui-2",
            "action": "supersede",
            "reason": "UI test resolution",
            "vault_dir": str(vault_dir),
        }
        res_resolve = await client.post("/api/knowledge/contradictions/resolve", json=resolve_payload)
        assert res_resolve.status_code == 200
        assert res_resolve.json()["status"] == "ok"

        # Verify disk update
        raw_b = json.loads((vault_dir / "ki-ui-2" / "metadata.json").read_text(encoding="utf-8"))
        assert raw_b["status"] == "SUPERSEDED"
        assert raw_b["superseded_by"] == "ki-ui-1"
