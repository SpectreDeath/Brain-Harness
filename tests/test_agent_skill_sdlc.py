import json
import pytest
from pathlib import Path
import sys

sdlc_scripts = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "agent-skill-sdlc" / "scripts"
sys.path.insert(0, str(sdlc_scripts))

from validate_skill import (
    SkillSDLCEngine,
    LocalSalvageEngine,
    SkillSpectorScanner,
    ValidationReport,
    CheckResult,
)
from resolve_config import (
    SkillConfiguration,
    resolve_for_skill,
    resolve_skill_configuration,
    deep_merge,
)


@pytest.mark.unit
def test_local_salvage_engine_markdown_fence():
    raw = '```json\n{\n  "key": "value",\n}\n```'
    salvaged, err = LocalSalvageEngine.salvage(raw)
    assert err is None
    assert salvaged == {"key": "value"}


@pytest.mark.unit
def test_local_salvage_engine_python_literals():
    raw = 'Here is the response: {"active": True, "payload": None, "items": [1, 2, 3,]}'
    salvaged, err = LocalSalvageEngine.salvage(raw)
    assert err is None
    assert salvaged == {"active": True, "payload": None, "items": [1, 2, 3]}


@pytest.mark.unit
def test_local_salvage_empty_string():
    salvaged, err = LocalSalvageEngine.salvage("   ")
    assert salvaged is None
    assert "Empty payload string" in err


@pytest.mark.unit
def test_skillspector_clean_directory(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    safe_script = scripts_dir / "safe.py"
    safe_script.write_text('import sys\nprint("Hello world")\n', encoding="utf-8")
    
    report = SkillSpectorScanner.audit_skill_directory(tmp_path)
    assert report.passed is True
    assert report.risk_score == 0.0
    assert report.risk_band == "SAFE"


@pytest.mark.unit
def test_skillspector_flags_eval(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    bad_script = scripts_dir / "unsafe.py"
    bad_script.write_text('x = eval("1 + 1")\n', encoding="utf-8")
    
    report = SkillSpectorScanner.audit_skill_directory(tmp_path, threshold=20)
    assert report.passed is False
    assert report.risk_score >= 30.0
    assert any(f.pattern == "eval()" for f in report.findings)


@pytest.mark.unit
def test_skillspector_flags_shell_true(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    bad_script = scripts_dir / "unsafe_subproc.py"
    bad_script.write_text('import subprocess\nsubprocess.run("ls", shell=True)\n', encoding="utf-8")
    
    report = SkillSpectorScanner.audit_skill_directory(tmp_path, threshold=20)
    assert report.passed is False
    assert any("shell=True" in f.pattern for f in report.findings)


@pytest.mark.unit
def test_deep_merge_additive_list():
    base = {"line_budget_limit": 500, "supported_clients": ["antigravity"]}
    override = {"line_budget_limit": 600, "extra_supported_clients": ["copilot"]}
    sources = {}
    
    merged = deep_merge(base, override, sources, "override_source")
    assert merged["line_budget_limit"] == 600
    assert "copilot" in merged["supported_clients"]
    assert "antigravity" in merged["supported_clients"]


@pytest.mark.unit
def test_validate_skill_self_sdlc():
    engine = SkillSDLCEngine()
    target = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "agent-skill-sdlc"
    report = engine.validate(target)
    assert report.valid is True
    assert sum(1 for c in report.checks if not c.passed) == 0
