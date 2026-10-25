"""Contract and hygiene test suite for icm-workspace-architect skill."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
import yaml

from harness.creator.skills import SkillValidator
from harness.services.icm_architect import DefaultIcmArchitectService, IcmFormType
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.fixture
def skill_dir() -> Path:
    p = Path(__file__).parent.parent / ".agents" / "skills" / "icm-workspace-architect"
    return p


def test_skill_files_exist(skill_dir: Path) -> None:
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "CARD.md").exists()
    assert (skill_dir / "config.default.yaml").exists()
    assert (skill_dir / "scripts" / "icm_links.py").exists()
    assert (skill_dir / "scripts" / "icm_index.py").exists()
    assert (skill_dir / "scripts" / "icm_quotes.py").exists()
    assert (skill_dir / "scripts" / "icm_viz.py").exists()


@pytest.mark.asyncio
async def test_skill_validator(skill_dir: Path) -> None:
    report = await SkillValidator.validate_async(skill_dir)
    assert report.valid is True, f"Skill validation failed: {report.errors}"


def test_card_parser(skill_dir: Path) -> None:
    card_def = SkillCardParser.parse_directory(skill_dir)
    assert card_def is not None
    assert card_def.name == "icm-workspace-architect"
    assert len(card_def.stages) >= 3


def test_config_defaults(skill_dir: Path) -> None:
    conf_path = skill_dir / "config.default.yaml"
    data = yaml.safe_load(conf_path.read_text(encoding="utf-8"))
    assert "budgets" in data
    assert data["budgets"]["max_step_tokens"] == 8000
    assert data["budgets"]["entry_file_max_lines"] == 60
    assert "forms" in data
    assert "pipeline" in data["forms"]["supported_forms"]


def test_walk_test_on_scaffolded_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = DefaultIcmArchitectService()
        res = svc.scaffold_form(target_dir=tmpdir, form=IcmFormType.PIPELINE, name="Walk Test Workspace")
        assert res.status == "ok"

        # Walk Test 1: Where am I? (AGENTS.md exists and <60 lines)
        agents_file = Path(tmpdir) / "AGENTS.md"
        assert agents_file.exists()
        assert len(agents_file.read_text(encoding="utf-8").splitlines()) < 60

        # Walk Test 2: Exact Inputs?
        stage_contract = Path(tmpdir) / "stages" / "01_research" / "CONTEXT.md"
        assert stage_contract.exists()
        text = stage_contract.read_text(encoding="utf-8")
        assert "## Inputs" in text
        assert "## Process" in text
        assert "## Outputs" in text
        assert "## Check" in text

        # Walk Test 6: Links resolve?
        link_res = svc.verify_links(root=tmpdir)
        assert link_res.valid is True
        assert len(link_res.broken_links) == 0

        # Audit passes
        audit = svc.audit_workspace(root=tmpdir)
        assert audit.valid is True
        assert audit.invariants_passed == 10


def test_canonical_workspace_template_scaffolding() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = DefaultIcmArchitectService()
        ws_res = svc.scaffold_workspace(
            target_dir=tmpdir,
            template_name="workspace-builder",
            name="Canonical Builder",
            variables={"BRAND_NAME": "ICM Builder"},
        )
        assert ws_res.status == "ok"
        assert len(ws_res.created_files) > 0
        agents_or_claude = (Path(tmpdir) / "AGENTS.md").exists() or (Path(tmpdir) / "CLAUDE.md").exists()
        assert agents_or_claude is True
