"""Tests for Ontology-Spider Brain Harness Plugin and VaultModelSource seam integration."""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.ontology_spider.adapter import HarnessVaultModelSource
from plugins.memory_and_epistemics.ontology_spider.main import (
    ONTOLOGY_SPIDER_KEY,
    OntologySpiderPlugin,
    load_vault_ontology,
    query_ontology,
    validate_ontology,
)
from plugins.memory_and_epistemics.ontology_spider.service import OntologySpiderService


@pytest.fixture
def vault_sample_path() -> Path:
    p = Path("D:/GitHub/projects/Ontology-Spider/examples/vault_sample.json")
    assert p.exists(), f"Vault sample not found at: {p}"
    return p


def test_harness_vault_adapter_loads_sample(vault_sample_path: Path):
    adapter = HarnessVaultModelSource(vault_sample_path)
    model = adapter.load()

    assert model.uri == "urn:vault:demo_vault"
    assert "spec_core" in model.entities
    assert "spec_seam" in model.entities
    assert "impl_plugin" in model.entities


def test_ontology_spider_service_transitive_query_and_proof(vault_sample_path: Path):
    service = OntologySpiderService()
    res = service.query(vault_sample_path, "query transitive depends_on from impl_plugin")

    assert res["statement_type"] == "query"
    dep_vals = [a["value"] for a in res["answers"]]
    assert "spec_seam" in dep_vals
    assert "spec_core" in dep_vals

    core_ans = next(a for a in res["answers"] if a["value"] == "spec_core")
    assert core_ans["path"] == ["impl_plugin", "spec_seam", "spec_core"]
    assert "transitive_closure" in core_ans["rules_fired"]
    assert len(core_ans["provenance"]) >= 2


def test_vault_directory_loading():
    """Verify loading a directory-based knowledge vault structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Item 1: service_a
        ki_a = root / "service_a"
        ki_a.mkdir()
        (ki_a / "metadata.json").write_text(
            json.dumps({
                "id": "service_a",
                "type": "microservice",
                "title": "Service A",
                "dependencies": ["service_b"],
            }),
            encoding="utf-8",
        )

        # Item 2: service_b
        ki_b = root / "service_b"
        ki_b.mkdir()
        (ki_b / "metadata.json").write_text(
            json.dumps({
                "id": "service_b",
                "type": "microservice",
                "title": "Service B",
                "dependencies": ["database_c"],
            }),
            encoding="utf-8",
        )

        # Item 3: database_c
        ki_c = root / "database_c"
        ki_c.mkdir()
        (ki_c / "metadata.json").write_text(
            json.dumps({
                "id": "database_c",
                "type": "database",
                "title": "Database C",
                "dependencies": [],
            }),
            encoding="utf-8",
        )

        service = OntologySpiderService()
        model = service.load_vault(root)
        # 3 items + 2 inferred type entities = 5 entities
        assert len(model.entities) >= 3
        assert "service_a" in model.entities
        assert "service_b" in model.entities
        assert "database_c" in model.entities

        res = service.query(root, "query transitive depends_on from service_a")
        dep_vals = [a["value"] for a in res["answers"]]
        assert "service_b" in dep_vals
        assert "database_c" in dep_vals

        db_ans = next(a for a in res["answers"] if a["value"] == "database_c")
        assert db_ans["path"] == ["service_a", "service_b", "database_c"]


def test_schema_validation_detects_cycles():
    cyclical_vault = {
        "vault_id": "cycle_test",
        "items": [
            {"id": "mod_1", "type": "module"},
            {"id": "mod_2", "type": "module"},
        ],
        "edges": [
            {"from": "mod_1", "rel": "subclass_of", "to": "mod_2"},
            {"from": "mod_2", "rel": "subclass_of", "to": "mod_1"},
        ],
    }
    service = OntologySpiderService()
    violations = service.validate(cyclical_vault)
    assert len(violations) >= 1
    assert any(v["check_type"] == "cycle_violation" for v in violations)


@pytest.mark.asyncio
async def test_plugin_lifecycle_and_ioc_registration():
    ctx = ServiceContext()
    p = OntologySpiderPlugin()

    await p.on_load(ctx)
    svc = ctx.require(ONTOLOGY_SPIDER_KEY)
    assert isinstance(svc, OntologySpiderService)

    await p.on_enable()
    await p.on_disable()
    await p.on_unload()


def test_standalone_entrypoints(vault_sample_path: Path):
    loaded = load_vault_ontology(vault_sample_path)
    assert loaded["entities_count"] == 5  # 3 items + 2 item types
    assert loaded["assertions_count"] >= 2

    query_res = query_ontology(vault_sample_path, "query transitive depends_on from impl_plugin")
    assert len(query_res["answers"]) == 2

    val_res = validate_ontology(vault_sample_path)
    assert isinstance(val_res, list)


def test_engine_zero_brain_harness_imports():
    """Verify that Ontology-Spider engine imports ZERO Brain Harness code (Track 2 guardrail)."""
    engine_root = Path("D:/GitHub/projects/Ontology-Spider/src/ontology_spider")
    for py_file in engine_root.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "harness" not in alias.name.lower(), f"Forbidden import {alias.name} in {py_file}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "harness" not in node.module.lower(), f"Forbidden import from {node.module} in {py_file}"
