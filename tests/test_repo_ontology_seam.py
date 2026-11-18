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
    (pb / "README.md").write_text(
        "# Proj B\nLanguage model reasoning https://arxiv.org/abs/2401.12345\n", encoding="utf-8"
    )
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

    raw_names = {ent.attributes.get("raw_name") for ent in model.entities.values() if "raw_name" in ent.attributes}
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


@skip_if_no_engine
def test_domain_classifier_handles_llm_reasoning_keywords() -> None:
    """_classify_domain maps plural LLMs / self-consistency / prompting repos to nlp_and_llm_project."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import _classify_domain

    readme = (
        '# Code for "Confidence Improves Self-Consistency in LLMs"\n'
        "Self-consistency decoding enhances LLMs performance via confidence prompting.\n"
    )
    assert _classify_domain("cisc", readme) == "nlp_and_llm_project"


@skip_if_no_engine
def test_domain_classifier_routes_selective_prediction_and_systems() -> None:
    """Selective prediction maps to privacy/safety and user-space kernels map to systems."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import _classify_domain

    asp_readme = (
        "# Active Selective Prediction\nASPEST: Bridging Active Learning and Selective Prediction with abstention.\n"
    )
    gvisor_readme = "# gVisor\nAn application kernel written in Go using seccomp-bpf and syscall interception.\n"
    assert _classify_domain("active_selective_prediction", asp_readme) == "privacy_fairness_safety_project"
    assert _classify_domain("gvisor", gvisor_readme) == "systems_and_runtime_project"


@skip_if_no_engine
def test_vault_matching_avoids_title_false_positives_and_reads_sources_and_hyphens(tmp_path: Path) -> None:
    """_discover_vault_learned_projects reads structured sources/paths without matching generic title words."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import RepoOntologyModelSource

    repo = tmp_path / "repo"
    for name in ("adk-python", "earthengine-api", "rpc"):
        d = repo / name
        d.mkdir(parents=True)
        (d / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        (d / "main.py").write_text("import json\n", encoding="utf-8")
        (d / "main_test.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    vault = tmp_path / "vault"
    # Unrelated Codex RPC KI must NOT mark repo unit "rpc" as learned via free-text title token
    k_rpc = vault / "ki_20260823_repo_05"
    k_rpc.mkdir(parents=True)
    (k_rpc / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_20260823_repo_05",
                "title": "App-Server Daemon RPC Gate",
                "source_target": "external/codex-main/codex-main",
                "tags": ["json_rpc", "ipc"],
            }
        ),
        encoding="utf-8",
    )

    # Multi-source bridge KI must mark "adk-python" via sources[].repo / path
    k_bridge = vault / "ki_google_repos_bridge"
    k_bridge.mkdir(parents=True)
    (k_bridge / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_google_repos_bridge",
                "title": "Google Multi-Repo Bridge",
                "sources": [{"repo": "google/adk-python", "path": "external/Google/adk-python"}],
                "tags": ["google_repos", "bridge"],
            }
        ),
        encoding="utf-8",
    )

    # Hyphenated source_target must preserve "earthengine-api" / "earthengine_api"
    k_ee = vault / "ki_20260908_ee_01"
    k_ee.mkdir(parents=True)
    (k_ee / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_20260908_ee_01",
                "title": "Earth Engine Spatial Analytics",
                "source_target": "external/Google/earthengine-api",
                "tags": ["earth_engine"],
            }
        ),
        encoding="utf-8",
    )

    model = RepoOntologyModelSource(repo, vault_dir=vault).load()
    assert model.entities["adk_python"].attributes["harness_learned"] is True
    assert model.entities["adk_python"].attributes["learned_ki_id"] == "ki_google_repos_bridge"
    assert model.entities["earthengine_api"].attributes["harness_learned"] is True
    assert model.entities["rpc"].attributes["harness_learned"] is False
    assert model.entities["rpc"].attributes["learned_ki_id"] == ""


@skip_if_no_engine
def test_multilanguage_go_bazel_and_tests_discovery(tmp_path: Path) -> None:
    """Go imports, Bazel BUILD deps, and non-Python tests surface cross-unit dependencies and test flags."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import RepoOntologyModelSource

    repo = tmp_path / "go_repo"
    repo.mkdir()
    (repo / "go.mod").write_text("module example.com/sandbox\n\ngo 1.22\n", encoding="utf-8")
    (repo / "README.md").write_text("# Sandbox\nApplication kernel syscall isolation.\n", encoding="utf-8")

    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "sentry.go").write_text("package pkg\n", encoding="utf-8")
    (pkg / "sentry_test.go").write_text("package pkg\n", encoding="utf-8")

    runsc = repo / "runsc"
    runsc.mkdir()
    (runsc / "boot.go").write_text(
        'package runsc\n\nimport (\n\t"fmt"\n\t"example.com/sandbox/pkg"\n)\n',
        encoding="utf-8",
    )

    model = RepoOntologyModelSource(repo).load()
    assert model.entities["pkg"].attributes["has_tests"] is True
    assert model.entities["pkg"].attributes["primary_language"] == "go"
    assert model.entities["runsc"].attributes["primary_language"] == "go"
    edges = {(a.relation.subject, a.relation.object) for a in model.query(predicate="depends_on_project")}
    assert ("runsc", "pkg") in edges


@skip_if_no_engine
def test_portfolio_analysis_and_runner_repo_mode(tmp_path: Path) -> None:
    """Portfolio analysis expands nested monorepos and CLI runner supports --repo + --query."""
    import subprocess
    import sys

    portfolio = tmp_path / "Portfolio"
    outer, vault = _create_research_monorepo(tmp_path / "sub")
    r1 = portfolio / "alpha-kernel"
    (r1 / ".git").mkdir(parents=True)
    (r1 / "go.mod").write_text("module example.com/alpha\n", encoding="utf-8")
    (r1 / "core.go").write_text("package main\n", encoding="utf-8")
    (r1 / "core_test.go").write_text("package main\n", encoding="utf-8")

    # Nested monorepo inside portfolio
    mono = portfolio / "research-mono" / "research-mono"
    for p in ("proj_x", "proj_y"):
        pd = mono / p
        pd.mkdir(parents=True)
        (pd / "README.md").write_text(f"# {p}\nhttps://arxiv.org/abs/2402.00001\n", encoding="utf-8")
        (pd / "mod.py").write_text("import jax\n", encoding="utf-8")
        (pd / "mod_test.py").write_text("def test_x(): pass\n", encoding="utf-8")

    svc = OntologySpiderKernelService()
    port_report = svc.analyze_portfolio(portfolio, vault_dir=vault, max_depth=3, max_files_per_unit=30)
    assert port_report.repos_count == 2
    assert port_report.total_projects_count >= 3
    assert any("proj_x" in u or "alpha_kernel" in u or "alpha-kernel" in u for u in port_report.top_unlearned_targets)

    runner_path = Path(".agents/skills/ontology-spider/scripts/ontology_spider_runner.py")
    proc = subprocess.run(
        [
            sys.executable,
            str(runner_path),
            "--repo",
            str(outer),
            "--vault",
            str(vault),
            "--query",
            "query count recommend research_project [has_tests=true, harness_learned=false]",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["repository"]["projects_count"] == 6
    assert payload["query"]["answers"][0]["value"] >= 1


@skip_if_no_engine
def test_auditor_and_triad_consume_ontology_summary(tmp_path: Path) -> None:
    """DefaultDeepRepoAuditorService and RepoTriadPipelineEngine ground KI candidates in ontology findings."""
    from harness.services.repo_triad_forge import KiCandidateData
    from plugins.software_engineering.repo_triad_forge.main import plugin as triad_plugin

    outer, _vault = _create_research_monorepo(tmp_path)
    auditor = DefaultDeepRepoAuditorService()
    report = auditor.audit_repo(outer)
    cands = auditor.extract_ki_candidates(report)
    assert len(cands) == 4
    joined_evidence = " ".join(" ".join(c.get("evidence", [])) for c in cands)
    assert "proj_b" in joined_evidence or "proj_a" in joined_evidence

    triad_kis = triad_plugin.extract_kis(str(outer))
    assert any(isinstance(k, KiCandidateData) and ("proj_b" in k.id or "ontology" in k.id) for k in triad_kis)


@skip_if_no_engine
def test_generic_unit_tag_match_rejected(tmp_path: Path) -> None:
    """Generic unit names (e.g. runtime) must reject tag-only matches from unrelated KIs."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import RepoOntologyModelSource

    repo = tmp_path / "repo"
    rt = repo / "runtime"
    rt.mkdir(parents=True)
    (rt / "dispatch.py").write_text("def run(): pass\n", encoding="utf-8")

    vault = tmp_path / "vault"
    ki = vault / "ki_unrelated_tool"
    ki.mkdir(parents=True)
    (ki / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_unrelated_tool",
                "title": "Unrelated Framework",
                "source_target": "external/other_project/other_project",
                "tags": ["runtime", "dispatch"],
            }
        ),
        encoding="utf-8",
    )

    model = RepoOntologyModelSource(repo, vault_dir=vault).load()
    attrs = model.entities["runtime"].attributes
    assert attrs["harness_learned"] is False
    assert attrs["learned_match_strength"] == "none"
    assert attrs["is_generic_unit"] is True


@skip_if_no_engine
def test_structured_match_kept_for_generic_name(tmp_path: Path) -> None:
    """Generic unit names keep a structured match when source_target explicitly targets /<unit>."""
    from plugins.memory_and_epistemics.ontology_spider.repo_adapter import RepoOntologyModelSource

    repo = tmp_path / "repo"
    rt = repo / "runtime"
    rt.mkdir(parents=True)
    (rt / "engine.py").write_text("def run(): pass\n", encoding="utf-8")

    vault = tmp_path / "vault"
    ki = vault / "ki_runtime_core"
    ki.mkdir(parents=True)
    (ki / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_runtime_core",
                "title": "Dedicated Runtime Architecture",
                "source_target": "https://github.com/example/runtime",
                "tags": ["runtime"],
            }
        ),
        encoding="utf-8",
    )

    model = RepoOntologyModelSource(repo, vault_dir=vault).load()
    attrs = model.entities["runtime"].attributes
    assert attrs["harness_learned"] is True
    assert attrs["learned_match_strength"] == "structured"
    assert attrs["learned_ki_id"] == "ki_runtime_core"


@skip_if_no_engine
def test_generic_units_excluded_from_unlearned(tmp_path: Path) -> None:
    """Generic helper folders (tests, scripts) with tests are excluded from unlearned_tested_projects."""
    repo = tmp_path / "repo"
    for name in ("tests", "scripts", "real_solver", "real_planner"):
        d = repo / name
        d.mkdir(parents=True)
        (d / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        (d / "mod.py").write_text("import json\n", encoding="utf-8")
        (d / "mod_test.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    vault = tmp_path / "vault"
    vault.mkdir()

    report = OntologySpiderKernelService().analyze_repository(repo, vault_dir=vault)
    assert "real_solver" in report.unlearned_tested_projects
    assert "real_planner" in report.unlearned_tested_projects
    assert "tests" not in report.unlearned_tested_projects
    assert "scripts" not in report.unlearned_tested_projects
