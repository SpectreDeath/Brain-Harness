"""Unit and contract tests for plugin.icm_architect."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.icm_architect import (
    ICM_ARCHITECT_SERVICE_KEY,
    DefaultIcmArchitectService,
    IcmFormType,
    IcmWorkspaceRole,
    resolve_icm_architect_service,
)
from harness.creator.validator import PluginValidator
from plugins.developer_tooling.icm_architect.main import (
    IcmArchitectPlugin,
    icm_audit_workspace,
    icm_interpolate_template,
    icm_rebuild_index,
    icm_scaffold_form,
    icm_scaffold_workspace,
    icm_verify_links,
    icm_verify_quotes,
    plugin,
)


def test_plugin_metadata() -> None:
    assert plugin.name == "plugin.icm_architect"
    assert plugin.version == "1.0.0"
    assert ICM_ARCHITECT_SERVICE_KEY in plugin.provides
    assert plugin.requires == []


@pytest.mark.asyncio
async def test_plugin_on_load() -> None:
    context = ServiceContext()
    p = IcmArchitectPlugin()
    await p.on_load(context)
    svc = context.require(ICM_ARCHITECT_SERVICE_KEY)
    assert svc is not None


def test_scaffold_pipeline_and_audit() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ws_path = tmp_path / "test_pipeline"

        # Scaffold
        scaffold_res = plugin.scaffold(target_dir=ws_path, form=IcmFormType.PIPELINE, name="Test Pipeline")
        assert scaffold_res.status == "ok"
        assert (ws_path / "AGENTS.md").exists()
        assert (ws_path / "CONTEXT.md").exists()
        assert (ws_path / "stages" / "01_research" / "CONTEXT.md").exists()

        # Audit
        audit = plugin.audit(root=ws_path)
        assert audit.form_detected == "pipeline"
        assert audit.total_files >= 6
        assert audit.files_by_role[IcmWorkspaceRole.CATALOG.value] >= 3
        assert audit.files_by_role[IcmWorkspaceRole.CONTRACT.value] >= 4
        assert audit.files_by_role[IcmWorkspaceRole.FACTORY.value] >= 1

        # Link verification
        link_report = plugin.verify_links(root=ws_path)
        assert link_report.valid is True
        assert link_report.broken_links == []


def test_frozen_dataclass_immutability() -> None:
    svc = DefaultIcmArchitectService()
    report = svc.audit_workspace(".")
    # Rule 43: Frozen dataclass mutation assertion invariant
    with pytest.raises((AttributeError, TypeError)):
        report.total_files = 999  # type: ignore[misc]


def test_quote_verification() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        raw_dir = root / "sources" / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "interview.txt").write_text("Interpretable context methodology replaces complex frameworks.", encoding="utf-8")

        # Create note with quote
        (root / "concept.md").write_text(
            '# Concept\n\n"Interpretable context methodology replaces complex frameworks." (interview)\n',
            encoding="utf-8",
        )

        svc = DefaultIcmArchitectService()
        res = svc.verify_quotes(root=root)
        assert res.total_quotes == 1
        assert res.verified_quotes == 1
        assert res.broken_quotes == []


def test_index_rebuilding() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        shelf = root / "records"
        shelf.mkdir()
        (shelf / "rec1.md").write_text("---\ntitle: Record Alpha\nstatus: active\n---\n# Record Alpha\n", encoding="utf-8")
        (shelf / "rec2.md").write_text("---\ntitle: Record Beta\nstatus: archived\n---\n# Record Beta\n", encoding="utf-8")

        svc = DefaultIcmArchitectService()
        idx_report = svc.rebuild_index(folders=["records"], root=root)
        assert len(idx_report.index_files_written) == 1
        assert (shelf / "_index.md").exists()

        content = (shelf / "_index.md").read_text(encoding="utf-8")
        assert "Record Alpha" in content
        assert "(active)" in content
        assert "Record Beta" in content
        assert "(archived)" in content


def test_top_level_tool_entrypoints() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        res = icm_scaffold_form(target_dir=tmpdir, form="record_library", name="Test Records")
        assert res["status"] == "ok"
        audit = icm_audit_workspace(root=tmpdir)
        assert audit["form_detected"] == "record_library"


def test_template_interpolation_and_workspace_scaffold() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tpl_file = tmp_path / "sample_tpl.md"
        tpl_file.write_text(
            "# {{BRAND_NAME}}\n\n"
            "{{?INCLUDE_SPECS}}\n"
            "## Specifications\n"
            "- Resolution: {{RESOLUTION}}\n"
            "{{/INCLUDE_SPECS}}\n"
            "{{?EXCLUDED_SECTION}}\n"
            "## Excluded\n"
            "Should not appear.\n"
            "{{/EXCLUDED_SECTION}}\n\n"
            "Remaining: {{UNRESOLVED_VAR}}\n",
            encoding="utf-8",
        )

        out_file = tmp_path / "rendered.md"
        res = icm_interpolate_template(
            template_path=str(tpl_file),
            variables={
                "BRAND_NAME": "Acme AI",
                "INCLUDE_SPECS": "true",
                "RESOLUTION": "1920x1080",
                "EXCLUDED_SECTION": "false",
            },
            output_path=str(out_file),
        )

        assert res["status"] == "ok"
        assert res["variables_applied"]["BRAND_NAME"] == "Acme AI"
        assert "UNRESOLVED_VAR" in res["unresolved_placeholders"]

        rendered = out_file.read_text(encoding="utf-8")
        assert "Acme AI" in rendered
        assert "## Specifications" in rendered
        assert "Resolution: 1920x1080" in rendered
        assert "## Excluded" not in rendered

        # Test workspace scaffold from canonical template
        ws_dir = tmp_path / "my_workspace"
        scaffold_res = icm_scaffold_workspace(
            target_dir=str(ws_dir),
            template_name="workspace-builder",
            name="My Workspace",
            variables={"BRAND_NAME": "Acme AI"},
        )
        assert scaffold_res["status"] == "ok"
        assert (ws_dir / "AGENTS.md").exists() or (ws_dir / "CLAUDE.md").exists()


@pytest.mark.asyncio
async def test_plugin_validator_compliance() -> None:
    p_dir = Path(__file__).parent
    report = await PluginValidator.validate(p_dir)
    assert report.valid is True, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
