"""Failing-first contract tests for Phase 2 RepoOntologyModelSource seam and Triad/Auditor wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.services.deep_auditor import DefaultDeepRepoAuditorService
from harness.services.ontology_spider import (
    AttributeEntropyRank,
    OntologySpiderKernelService,
    RepoOntologyAnalysisReport,
)
from harness.services.repo_triad_forge import RepoInspectionData
from plugins.memory_and_epistemics.ontology_spider.adapter import HAS_ONTOLOGY_SPIDER

skip_if_no_engine = pytest.mark.skipif(
    not HAS_ONTOLOGY_SPIDER,
    reason="Ontology-Spider engine is not installed",
)


def _create_research_monorepo(tmp_path: Path) -> tuple[Path, Path]:
    """Create a synthetic nested non-git research monorepo plus a mock Knowledge Vault."""
    outer = tmp_path / "cloned-research-master"
    repo = outer / "cloned-research-master"
    repo.mkdir(parents=True)

    # 1. proj_a: JAX tested project cited by proj_b, already learned in vault
    pa = repo / "proj_a"
    pa.mkdir()
    (pa / "README.md").write_text("# Proj A\nSee https://arxiv.org/abs/2305.00001\n", encoding="utf-8")
    (pa / "requirements.txt").write_text("jax\noptax\n", encoding="utf-8")
    (pa / "core.py").write_text("import jax\nimport optax\n", encoding="utf-8")
    (pa / "core_test.py").write_text("def test_a(): assert True\n", encoding="utf-8")

    # 2. proj_b: depends on proj_a, unlearned, tested, has arXiv + gin
    pb = repo / "proj_b"
    pb.mkdir()
    (pb / "README.md").write_text("# Proj B\nLanguage model reasoning https://arxiv.org/abs/2401.12345\n", encoding="utf-8")
    (pb / "setup.py").write_text("from setuptools import setup\n", encoding="utf-8")
    (pb / "config.gin").write_text("train.lr = 1e-4\n", encoding="utf-8")
    (pb / "runner.py").write_text("import jax\nfrom proj_a import core\n", encoding="utf-8")
    (pb / "runner_test.py").write_text("def test_b(): assert True\n", encoding="utf-8")

    # 3 & 4. proj_c <-> proj_d import cycle
    pc = repo / "proj_c"
    pc.mkdir()
    (pc / "requirements.txt").write_text("tensorflow\n", encoding="utf-8")
    (pc / "c.py").write_text("import tensorflow as tf\nfrom proj_d import d\n", encoding="utf-8")

    pd = repo / "proj_d"
    pd.mkdir()
    (pd / "requirements.txt").write_text("tensorflow\n", encoding="utf-8")
    (pd / "d.py").write_text("import tensorflow as tf\nfrom proj_c import c\n", encoding="utf-8")

    # 5 & 6. Sanitized-ID collision pair: widget-caption vs widget_caption
    wc1 = repo / "widget-caption"
    wc1.mkdir()
    (wc1 / "README.md").write_text("# Widget Caption Hyphen\n", encoding="utf-8")
    (wc1 / "app.py").write_text("import numpy as np\n", encoding="utf-8")

    wc2 = repo / "widget_caption"
    wc2.mkdir()
    (wc2 / "README.md").write_text("# Widget Caption Underscore\n", encoding="utf-8")
    (wc2 / "app.py").write_text("import numpy as np\n", encoding="utf-8")

    # Vault containing KI referencing proj_a
    vault = tmp_path / "vault"
    ki = vault / "ki_proj_a_learned"
    ki.mkdir(parents=True)
    (ki / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_proj_a_learned",
                "title": "Learned Proj A",
                "tags": ["proj_a", "jax"],
                "isnad": {"status": "VERIFIED"},
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    return outer, vault


def test_repo_ontology_analysis_report_frozen_slotted() -> None:
    """Verify Rule 12 & Rule 43 immutability on RepoOntologyAnalysisReport."""
    rank = AttributeEntropyRank("primary_framework", 1.0, 1.0, 2, 1.0, 1.0, False)
    rep = RepoOntologyAnalysisReport(
        repo_root="/outer",
        resolved_root="/outer/inner",
        entities_count=10,
        assertions_count=20,
        projects_count=6,
        cycle_violations=(),
        dependency_hubs=(("proj_a", 1),),
        top_discriminating_attributes=(rank,),
        unlearned_tested_projects=("proj_b",),
        gruber_scorecard={"overall_score": 0.9},
    )
    with pytest.raises((AttributeError, TypeError)):
        rep.projects_count = 99  # type: ignore[misc]


@skip_if_no_engine
def test_repo_ontology_model_source_and_kernel_analyze(tmp_path: Path) -> None:
    """RepoOntologyModelSource resolves nested archive, keeps collisions distinct, detects cycles & gaps."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import RepoOntologyModelSource

    outer, vault = _create_research_monorepo(tmp_path)
    model = RepoOntologyModelSource(outer, vault_dir=vault).load()

    raw_names = {
        ent.attributes.get("raw_name")
        for ent in model.entities.values()
        if "raw_name" in ent.attributes
    }
    assert {"proj_a", "proj_b", "proj_c", "proj_d", "widget-caption", "widget_caption"}.issubset(raw_names)
    assert model.entities["proj_a"].attributes["harness_learned"] is True
    assert model.entities["proj_b"].attributes["harness_learned"] is False

    report = OntologySpiderKernelService().analyze_repository(outer, vault_dir=vault)
    assert Path(report.resolved_root).name == "cloned-research-master"
    assert report.projects_count == 6
    assert len(report.cycle_violations) >= 1
    cycle_path = report.cycle_violations[0]["details"].get("cycle_path", "")
    assert "proj_c" in cycle_path and "proj_d" in cycle_path
    assert any(hub == "proj_a" for hub, _ in report.dependency_hubs)
    assert "proj_b" in report.unlearned_tested_projects
    assert report.top_discriminating_attributes[0].is_identifier_like is False


@skip_if_no_engine
def test_deep_auditor_and_repo_triad_forge_wire_repo_ontology(tmp_path: Path) -> None:
    """DeepRepoAuditorService and RepoTriadForgePlugin surface ontology_analysis and ontology_summary."""
    from plugins.software_engineering.repo_triad_forge.main import plugin as triad_plugin

    outer, _vault = _create_research_monorepo(tmp_path)

    auditor = DefaultDeepRepoAuditorService()
    audit_payload = auditor.run_full_audit(outer, output_dir=tmp_path / "auditor_briefs")
    report_dict = audit_payload["report"]
    assert report_dict.get("ontology_analysis") is not None
    assert report_dict["ontology_analysis"]["projects_count"] == 6
    assert len(report_dict["ontology_analysis"]["cycle_violations"]) >= 1
    assert len(audit_payload["ki_candidates"]) == 4

    triad_ins = triad_plugin.inspect(str(outer))
    assert isinstance(triad_ins, RepoInspectionData)
    assert Path(triad_ins.resolved_root).name == "cloned-research-master"
    assert triad_ins.ontology_summary.get("projects_count") == 6
    assert len(triad_ins.ontology_summary.get("cycle_violations", [])) >= 1
    kis = triad_plugin.extract_kis(str(outer))
    assert len(kis) >= 3
