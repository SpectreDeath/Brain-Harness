"""Comprehensive test suite for deepened Gradio App Architect architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- AST static analysis across Eva J Patel's 5 diagnostic rubrics:
  1. Headless Decoupling
  2. Multi-User Session Isolation
  3. Positional Arity & Cardinality Contracts
  4. Singleton Warm-Loading
  5. Queued Concurrency & Streaming Telemetry
- Production 3-tier scaffolding and manifest generation
- Micro-Kernel IoC ServiceKey registration and resolution (Rule 2 & Rule 49)
- PluginValidator compliance and zero-fork configuration (Rule 34, 38, 44, 45)
- Click CLI commands via CliRunner (Rule 6, 10, 23)
- Canonical Knowledge Vault dual-file format (Rule 40)
- Standalone HTML visual brief generation
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from click.testing import CliRunner
import pytest

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "gradio-app-architect" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gradio_app_engine import (  # noqa: E402
    AppScaffoldConfig,
    AppScaffoldResult,
    ArityContract,
    DiagnosticCheck,
    DiagnosticReport,
    GradioAppArchitectEngine,
)

from harness.commands.gradio_app import gradio_group  # noqa: E402
from harness.creator.skills import SkillValidator  # noqa: E402
from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.gradio_app import (  # noqa: E402
    GRADIO_APP_ARCHITECT_SERVICE_KEY,
    AppScaffoldConfigData,
    DiagnosticReportData,
    GradioAppArchitectService,
)
from plugins.integration_and_io.gradio_app_architect.main import (  # noqa: E402
    GradioAppArchitectPlugin,
)
from plugins.integration_and_io.gradio_app_architect.main import (  # noqa: E402
    plugin as gradio_plugin,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser  # noqa: E402


@pytest.fixture
def engine() -> GradioAppArchitectEngine:
    return GradioAppArchitectEngine()


@pytest.fixture
def service_context() -> ServiceContext:
    ctx = ServiceContext()
    ctx.provide(GRADIO_APP_ARCHITECT_SERVICE_KEY, gradio_plugin)
    return ctx


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    check = DiagnosticCheck(
        rule_id="RULE_01",
        name="Test Check",
        passed=True,
        message="All good",
        severity="info",
    )
    with pytest.raises((AttributeError, TypeError)):
        check.passed = False  # type: ignore

    report = DiagnosticReport(
        target="test.py",
        passed=True,
        checks=(check,),
    )
    with pytest.raises((AttributeError, TypeError)):
        report.passed = False  # type: ignore

    contract = ArityContract(
        func_name="process",
        input_count=2,
        output_count=1,
    )
    with pytest.raises((AttributeError, TypeError)):
        contract.input_count = 3  # type: ignore

    cfg = AppScaffoldConfig(
        app_name="demo_app",
        topology="blocks",
    )
    with pytest.raises((AttributeError, TypeError)):
        cfg.app_name = "other_app"  # type: ignore

    res = AppScaffoldResult(
        files=(("app.py", "print(1)"),),
    )
    with pytest.raises((AttributeError, TypeError)):
        res.files = ()  # type: ignore


# --- 2. AST Static Analysis & Diagnostic Rubrics ---


def test_ast_inspector_clean_code_passes(engine: GradioAppArchitectEngine):
    """Verify clean decoupled application code passes all 5 diagnostic rubrics."""
    clean_code = """
import gradio as gr

def pure_compute(text: str, temp: float) -> str:
    return f"Echo: {text} at {temp}"

def build():
    with gr.Blocks() as demo:
        session_state = gr.State(initial_value=[])
        t_in = gr.Textbox()
        s_in = gr.Slider()
        btn = gr.Button()
        out = gr.Textbox()

        btn.click(
            fn=pure_compute,
            inputs=[t_in, s_in],
            outputs=[out]
        )
    return demo

demo = build()
demo.queue()
"""
    report = engine.audit_code(clean_code, file_path="clean_app.py")
    assert report.passed is True
    assert len(report.errors) == 0


def test_ast_inspector_detects_headless_decoupling_violation(engine: GradioAppArchitectEngine):
    """Verify Rubric 1 flags Gradio imports inside function scope."""
    bad_code = """
def compute_data(x: int):
    import gradio as gr
    return x * 2
"""
    report = engine.audit_code(bad_code, file_path="coupled_app.py")
    assert report.passed is False
    assert any(c.rule_id == "HEADLESS_DECOUPLING" for c in report.errors)


def test_ast_inspector_detects_session_state_violation(engine: GradioAppArchitectEngine):
    """Verify Rubric 2 flags mutable global variables mutated via global statement."""
    bad_code = """
history = []

def on_click(msg: str):
    global history
    history.append(msg)
    return history
"""
    report = engine.audit_code(bad_code, file_path="global_leak.py")
    assert report.passed is False
    assert any(c.rule_id == "SESSION_STATE_ISOLATION" for c in report.errors)


def test_ast_inspector_detects_positional_arity_mismatch(engine: GradioAppArchitectEngine):
    """Verify Rubric 3 flags input count mismatches between event and handler signature."""
    bad_code = """
import gradio as gr

def handler(a: str, b: str) -> str:
    return a + b

with gr.Blocks() as demo:
    t1 = gr.Textbox()
    btn = gr.Button()
    out = gr.Textbox()
    # Handler expects 2 parameters, but inputs list provides only 1 component
    btn.click(fn=handler, inputs=[t1], outputs=[out])
"""
    report = engine.audit_code(bad_code, file_path="arity_mismatch.py")
    assert report.passed is False
    assert any(c.rule_id == "POSITIONAL_ARITY_CONTRACT" for c in report.errors)


def test_ast_inspector_detects_heavy_loader_in_callback(engine: GradioAppArchitectEngine):
    """Verify Rubric 4 flags heavy model instantiation inside functions."""
    bad_code = """
def handle_event(prompt: str):
    from transformers import pipeline
    model = pipeline("text-generation")
    return model(prompt)
"""
    report = engine.audit_code(bad_code, file_path="cold_load.py")
    assert report.passed is False
    assert any(c.rule_id == "SINGLETON_WARM_LOAD" for c in report.errors)


def test_ast_inspector_detects_unqueued_streaming_generator(engine: GradioAppArchitectEngine):
    """Verify Rubric 5 flags generator functions using yield when demo.queue() is missing."""
    bad_code = """
import gradio as gr

def stream_response(prompt: str):
    for tok in prompt:
        yield tok

with gr.Blocks() as demo:
    btn = gr.Button()
    out = gr.Textbox()
    btn.click(fn=stream_response, inputs=[btn], outputs=[out])
    # demo.queue() is deliberately missing
"""
    report = engine.audit_code(bad_code, file_path="unqueued_stream.py")
    assert report.passed is False
    assert any(c.rule_id == "QUEUED_STREAMING_TELEMETRY" for c in report.errors)


def test_ast_inspector_handles_syntax_error(engine: GradioAppArchitectEngine):
    """Verify syntax errors in audited source code are gracefully handled."""
    invalid_syntax = "def broken_func(:\n    pass"
    report = engine.audit_code(invalid_syntax, file_path="syntax_err.py")
    assert report.passed is False
    assert any(c.rule_id == "PYTHON_SYNTAX_VALID" for c in report.checks)


# --- 3. Production Scaffolding & Manifest Generation ---


def test_scaffolder_generates_all_3_layers(engine: GradioAppArchitectEngine):
    """Verify app scaffolder creates logic.py, app.py, requirements.txt, and README.md."""
    cfg = AppScaffoldConfig(
        app_name="sentiment_classifier",
        topology="blocks",
        concurrency_limit=8,
    )
    result = engine.scaffold_app(cfg)
    file_map = dict(result.files)

    assert "logic.py" in file_map
    assert "app.py" in file_map
    assert "requirements.txt" in file_map
    assert "README.md" in file_map

    # Check decoupled logic has zero gradio imports
    assert "gradio" not in file_map["logic.py"]
    assert "def process_query(" in file_map["logic.py"]

    # Check app.py has gr.Blocks, gr.State, and queue
    assert "gr.Blocks(" in file_map["app.py"]
    assert "gr.State(" in file_map["app.py"]
    assert "demo.queue(" in file_map["app.py"]
    assert "default_concurrency_limit=8" in file_map["app.py"]

    # Check manifest metadata
    assert result.manifest["app_name"] == "sentiment_classifier"
    assert result.manifest["files_count"] == 4


# --- 4. Micro-Kernel IoC Service Registration & Resolution (Rule 2 & Rule 49) ---


def test_ioc_service_registration_and_execution(service_context: ServiceContext):
    """Verify GradioAppArchitectService resolves via ServiceKey and executes cleanly."""
    svc: GradioAppArchitectService = service_context.require(
        GRADIO_APP_ARCHITECT_SERVICE_KEY
    )
    assert svc is not None

    # Test audit_code via service seam
    rep_data = svc.audit_code("def foo(): return 1")
    assert isinstance(rep_data, DiagnosticReportData)
    assert rep_data.passed is True

    # Test scaffold_app via service seam
    cfg_data = AppScaffoldConfigData(
        app_name="assistant_bot",
        topology="blocks",
    )
    scaffold_res = svc.scaffold_app(cfg_data)
    assert "app.py" in scaffold_res.files
    assert scaffold_res.manifest["app_name"] == "assistant_bot"

    # Test visual brief via service seam
    brief_p = svc.generate_visual_brief()
    assert brief_p.exists()
    assert "html" in brief_p.suffix


# --- 5. Plugin Validator Compliance (Rule 34, 38, 44, 45) ---


def test_plugin_validation_sync():
    """Verify gradio_app_architect plugin passes PluginValidator checks."""
    plugin_dir = (
        _ws_root / "plugins" / "integration_and_io" / "gradio_app_architect"
    )
    assert plugin_dir.exists()

    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, f"Plugin validation failed: {report.errors}"


@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Verify plugin on_load registers GRADIO_APP_ARCHITECT_SERVICE_KEY in context."""
    ctx = ServiceContext()
    p = GradioAppArchitectPlugin()
    assert GRADIO_APP_ARCHITECT_SERVICE_KEY in p.provides

    await p.on_load(ctx)
    resolved = ctx.require(GRADIO_APP_ARCHITECT_SERVICE_KEY)
    assert resolved is p

    await p.on_unload(ctx)


# --- 6. Headless Click CLI Commands (Rule 6, 10, 23) ---


def test_cli_inspect_command():
    """Verify 'harness gradio inspect' analyzes code and emits output."""
    runner = CliRunner()

    # Passing code
    res_pass = runner.invoke(
        gradio_group,
        ["inspect", "def pure(): return 42"],
    )
    assert res_pass.exit_code == 0
    assert "PASSED" in res_pass.output

    # JSON output
    res_json = runner.invoke(
        gradio_group,
        ["inspect", "def pure(): return 42", "--json-output"],
    )
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["passed"] is True
    assert len(data["checks"]) == 5


def test_cli_scaffold_command(tmp_path: Path):
    """Verify 'harness gradio scaffold' creates application files."""
    runner = CliRunner()

    # Preview mode
    res_prev = runner.invoke(
        gradio_group,
        ["scaffold", "--name", "cli_test_app", "--topology", "blocks"],
    )
    assert res_prev.exit_code == 0
    assert "Files Generated:   4" in res_prev.output
    assert "Preview" in res_prev.output

    # Write mode
    out_dir = tmp_path / "scaffold_out"
    res_write = runner.invoke(
        gradio_group,
        ["scaffold", "--name", "written_app", "--output-dir", str(out_dir), "--write"],
    )
    assert res_write.exit_code == 0
    assert (out_dir / "app.py").exists()
    assert (out_dir / "logic.py").exists()
    assert (out_dir / "requirements.txt").exists()
    assert (out_dir / "README.md").exists()


def test_cli_brief_command(tmp_path: Path):
    """Verify 'harness gradio brief' generates interactive HTML brief."""
    runner = CliRunner()
    out_file = tmp_path / "cli_brief.html"
    res = runner.invoke(gradio_group, ["brief", "--output", str(out_file)])
    assert res.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Gradio App Architect" in content
    assert "mermaid" in content


# --- 7. Skill & Knowledge Vault Integrity (Rule 40, 44) ---


def test_skill_validator_and_card_parser():
    """Verify gradio-app-architect skill passes SkillValidator and SkillCardParser."""
    skill_dir = _ws_root / ".agents" / "skills" / "gradio-app-architect"
    report = SkillValidator.validate_sync(skill_dir)
    assert report.valid is True, f"SkillValidator failed: {report.errors}"

    node = SkillCardParser.parse_directory(skill_dir)
    assert node is not None
    assert node.name == "gradio-app-architect"
    assert len(node.stages) == 5
    assert len(node.anti_patterns) == 6


def test_knowledge_vault_dual_file_format():
    """Verify canonical dual-file format in Knowledge Vault (Rule 40)."""
    ki_dir = _ws_root / ".harness" / "knowledge" / "ki-gradio-app-architect"
    assert ki_dir.exists(), "Knowledge vault directory missing"

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"
    assert meta_file.exists(), "metadata.json missing"
    assert summary_file.exists(), "summary.md missing"

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["id"] == "ki-gradio-app-architect"
    assert "Eva J Patel" in meta_data["title"]
    assert len(meta_data["references"]) >= 3

    summary_text = summary_file.read_text(encoding="utf-8")
    assert "Eva J Patel" in summary_text
    assert "3-Layer Decoupled Architecture" in summary_text
    assert "Anti-Pattern Defenses" in summary_text
