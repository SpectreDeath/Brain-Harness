"""Tests for Ontology-Spider Brain Harness Plugin and VaultModelSource seam integration."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import tempfile
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.ontology_spider.adapter import (
    HAS_ONTOLOGY_SPIDER,
    HarnessVaultModelSource,
)
from plugins.memory_and_epistemics.ontology_spider.main import (
    ONTOLOGY_SPIDER_KEY,
    OntologySpiderPlugin,
    load_vault_ontology,
    query_ontology,
    validate_ontology,
)
from plugins.memory_and_epistemics.ontology_spider.service import OntologySpiderService

skip_if_no_engine = pytest.mark.skipif(
    not HAS_ONTOLOGY_SPIDER,
    reason="Ontology-Spider engine is not installed (install via: pip install -e <path-to-Ontology-Spider>)",
)


@pytest.fixture
def vault_sample_path() -> Path:
    """Portable fixture resolving bundled vault sample JSON within the plugin directory."""
    p = Path(__file__).parent / "fixtures" / "vault_sample.json"
    assert p.exists(), f"Vault sample fixture not found at: {p}"
    return p


@pytest.mark.unit
@skip_if_no_engine
def test_harness_vault_adapter_loads_sample(vault_sample_path: Path) -> None:
    adapter = HarnessVaultModelSource(vault_sample_path)
    model = adapter.load()

    assert model.uri == "urn:vault:demo_vault"
    assert "spec_core" in model.entities
    assert "spec_seam" in model.entities
    assert "impl_plugin" in model.entities


@pytest.mark.unit
@skip_if_no_engine
def test_ontology_spider_service_transitive_query_and_proof(vault_sample_path: Path) -> None:
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


@pytest.mark.unit
@skip_if_no_engine
def test_vault_directory_loading() -> None:
    """Verify loading a directory-based knowledge vault structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Item 1: service_a
        ki_a = root / "service_a"
        ki_a.mkdir()
        (ki_a / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "service_a",
                    "type": "microservice",
                    "title": "Service A",
                    "dependencies": ["service_b"],
                }
            ),
            encoding="utf-8",
        )

        # Item 2: service_b
        ki_b = root / "service_b"
        ki_b.mkdir()
        (ki_b / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "service_b",
                    "type": "microservice",
                    "title": "Service B",
                    "dependencies": ["database_c"],
                }
            ),
            encoding="utf-8",
        )

        # Item 3: database_c
        ki_c = root / "database_c"
        ki_c.mkdir()
        (ki_c / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "database_c",
                    "type": "database",
                    "title": "Database C",
                    "dependencies": [],
                }
            ),
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


@pytest.mark.unit
@skip_if_no_engine
def test_schema_validation_detects_cycles() -> None:
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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_lifecycle_and_ioc_registration() -> None:
    """Verify plugin registers services into IoC container even when engine is absent (offline mode)."""
    ctx = ServiceContext()
    p = OntologySpiderPlugin()

    await p.on_load(ctx)
    svc = ctx.require(ONTOLOGY_SPIDER_KEY)
    assert isinstance(svc, OntologySpiderService)

    await p.on_enable()
    await p.on_disable()
    await p.on_unload()


@pytest.mark.unit
@skip_if_no_engine
def test_standalone_entrypoints(vault_sample_path: Path) -> None:
    loaded = load_vault_ontology(vault_sample_path)
    assert loaded["entities_count"] == 5  # 3 items + 2 item types
    assert loaded["assertions_count"] >= 2

    query_res = query_ontology(vault_sample_path, "query transitive depends_on from impl_plugin")
    assert len(query_res["answers"]) == 2

    val_res = validate_ontology(vault_sample_path)
    assert isinstance(val_res, list)


@pytest.mark.unit
@skip_if_no_engine
def test_engine_zero_brain_harness_imports() -> None:
    """Verify that Ontology-Spider engine imports ZERO Brain Harness code (Track 2 guardrail)."""
    spec = importlib.util.find_spec("ontology_spider")
    engine_root = None
    if spec and spec.origin:
        engine_root = Path(spec.origin).parent
    elif "ONTOLOGY_SPIDER_ROOT" in os.environ:
        p = Path(os.environ["ONTOLOGY_SPIDER_ROOT"])
        if (p / "src" / "ontology_spider").exists():
            engine_root = p / "src" / "ontology_spider"
        elif (p / "ontology_spider").exists():
            engine_root = p / "ontology_spider"
        elif p.exists():
            engine_root = p

    if not engine_root or not engine_root.exists():
        pytest.skip("Could not locate ontology_spider source directory to inspect AST imports")

    for py_file in engine_root.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not (
                        alias.name == "harness"
                        or alias.name.startswith("harness.")
                        or alias.name.startswith("plugins.")
                    ), f"Forbidden import {alias.name} in {py_file}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not (
                        node.module == "harness"
                        or node.module.startswith("harness.")
                        or node.module.startswith("plugins.")
                    ), f"Forbidden import from {node.module} in {py_file}"


@pytest.mark.unit
def test_missing_engine_error_message() -> None:
    """Verify that when engine is absent, calling service methods surfaces actionable install message."""
    if not HAS_ONTOLOGY_SPIDER:
        service = OntologySpiderService()
        with pytest.raises(RuntimeError) as exc_info:
            service.query("demo.json", "query what is test?")
        assert "pip install -e <path-to-Ontology-Spider>" in str(exc_info.value)
        assert "README.md" in str(exc_info.value)


@pytest.mark.unit
@skip_if_no_engine
def test_canonical_knowledge_vault_edges_isnad_and_temporal_slice(tmp_path: Path) -> None:
    """Verify Rule 40 canonical edges, isnad verification metadata, confidence filter, and as_of slice."""
    from harness.services.storage.isnad_hash import stamp_claim_sha256

    evidence_file = tmp_path / "evidence.py"
    evidence_file.write_bytes(b"def ok():\n    return True\n")
    evidence_sha = stamp_claim_sha256("evidence.py", tmp_path)

    ki_one = tmp_path / "ki-alpha"
    ki_one.mkdir()
    (ki_one / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki-alpha",
                "title": "Alpha Knowledge Item",
                "category": "architecture",
                "tags": ["epistemics", "ontology"],
                "updated_at": "2026-11-10T10:00:00Z",
                "edges": [
                    {
                        "type": "references_code",
                        "target": "src/harness/services/ontology_spider.py",
                        "target_kind": "path",
                        "confidence": 0.95,
                        "valid_from": "2026-11-01T00:00:00Z",
                        "valid_until": "2026-12-31T00:00:00Z",
                    },
                    {
                        "type": "depends_on",
                        "target": "ki-beta",
                        "confidence": 0.4,
                        "valid_from": "2026-11-15T00:00:00Z",
                    },
                ],
                "isnad": {
                    "source_repo": "https://example.invalid/repo",
                    "file": "evidence.py",
                    "verified_at": "2026-11-10T10:00:00Z",
                    "sha256": evidence_sha,
                },
            }
        ),
        encoding="utf-8",
    )

    ki_two = tmp_path / "ki-beta"
    ki_two.mkdir()
    (ki_two / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki-beta",
                "title": "Beta Knowledge Item",
                "category": "architecture",
                "edges": [],
                "isnad": {},
            }
        ),
        encoding="utf-8",
    )

    svc = OntologySpiderService()
    model = svc.load_vault(tmp_path, as_of="2026-11-12T00:00:00Z", min_confidence=0.8)
    assert "ki_alpha" in model.entities
    assert model.entities["ki_alpha"].attributes["isnad_verified"] is True
    assert model.entities["ki_beta"].attributes["isnad_verified"] is False

    res = svc.query(
        tmp_path,
        "query transitive references_code from ki_alpha",
        min_confidence=0.8,
        rank_by_distance=True,
    )
    vals = [a["value"] for a in res["answers"]]
    assert "src_harness_services_ontology_spider_py" in vals
    assert res["answers"][0]["hop_distance"] == 1

    # Edge to ki-beta is gated out at as_of=2026-11-12 (valid_from 2026-11-15) and confidence 0.4 < 0.8
    neg_res = svc.query(tmp_path, "query not ki_alpha depends_on ki_beta", as_of="2026-11-12T00:00:00Z")
    assert neg_res["answers"][0]["value"] == "true"


@pytest.mark.unit
@skip_if_no_engine
@pytest.mark.asyncio
async def test_plugin_exposes_kernel_service_and_new_entrypoints(vault_sample_path: Path) -> None:
    """Verify Rule 49 ONTOLOGY_SPIDER_SERVICE_KEY registration plus export/competency/audit entrypoints."""
    from harness.services.ontology_spider import ONTOLOGY_SPIDER_SERVICE_KEY, OntologySpiderProtocol
    from plugins.memory_and_epistemics.ontology_spider.main import (
        audit_vault_epistemics,
        evaluate_competency_questions,
        export_ontology,
    )

    ctx = ServiceContext()
    p = OntologySpiderPlugin()
    await p.on_load(ctx)
    kernel_svc = ctx.require(ONTOLOGY_SPIDER_SERVICE_KEY)
    assert isinstance(kernel_svc, OntologySpiderProtocol)

    exported_dialog = export_ontology(vault_sample_path, format="dialog")
    assert "dialog urn:vault:demo_vault" in exported_dialog

    scorecard = evaluate_competency_questions(
        vault_sample_path,
        ["query transitive depends_on from impl_plugin"],
    )
    assert scorecard["answered_questions"] == 1
    assert scorecard["violation_count"] == 1
    assert scorecard["coherence"] == 0.75

    audit = audit_vault_epistemics(vault_sample_path)
    assert audit["status"] == "violations_detected"
    assert len(audit["structural_violations"]) == 1
    assert audit["entities_count"] >= 3
