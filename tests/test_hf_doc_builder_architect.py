"""Contract verification tests for hf-doc-builder-architect skill and services."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.commands.doc_builder import (
    doc_builder_group,
)
from harness.services.doc_builder import (
    DOC_BUILDER_SERVICE_KEY,
    AutodocParameter,
    AutodocSignature,
    DefaultHfDocBuilderService,
    DocAstStaticAnalyzer,
    DocBuilderDomainEngine,
    DocChunk,
    LinkDiagnostic,
    TocDiagnostic,
    virtualize_imports,
)


@pytest.mark.unit
def test_slotted_frozen_dataclasses_immutability() -> None:
    """Rule 12 & Rule 43: Test that all domain dataclasses are slotted and frozen."""
    param = AutodocParameter(
        name="batch_size", type_annotation="int", default_value="32"
    )
    assert param.name == "batch_size"
    assert param.type_annotation == "int"

    # Rule 43: Direct attribute assignment inside pytest.raises
    with pytest.raises((AttributeError, TypeError)):
        param.name = "new_name"  # type: ignore

    sig = AutodocSignature(
        object_path="transformers.Pipeline",
        signature_str="Pipeline(model, tokenizer)",
        parameters=(param,),
        return_type="Pipeline",
    )
    with pytest.raises((AttributeError, TypeError)):
        sig.signature_str = "mutated"  # type: ignore

    diag = LinkDiagnostic(
        source_file="docs/quickstart.md",
        target_link="./models#bert",
        is_valid=False,
        error_reason="Anchor not found",
    )
    with pytest.raises((AttributeError, TypeError)):
        diag.is_valid = True  # type: ignore

    toc_diag = TocDiagnostic(
        entry="quickstart",
        file_path="docs/quickstart.md",
        is_valid=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        toc_diag.is_valid = False  # type: ignore

    chunk = DocChunk(
        chunk_id="c1",
        title="Quickstart",
        heading_level=1,
        content="Getting started guide.",
    )
    with pytest.raises((AttributeError, TypeError)):
        chunk.title = "Changed"  # type: ignore


@pytest.mark.unit
def test_autodoc_inspection_dynamic() -> None:
    """Verify autodoc extraction on standard library module."""
    res = DocBuilderDomainEngine.inspect_autodoc("json", "dumps")
    assert "dumps" in res.object_path
    assert res.return_type is not None
    assert len(res.parameters) > 0
    param_names = [p.name for p in res.parameters]
    assert "obj" in param_names or "args" in param_names


@pytest.mark.unit
def test_static_ast_analyzer() -> None:
    """Verify pure static AST analysis extracts class and function signatures without execution."""
    sample_code = '''
"""Sample module for AST testing."""

class NeuralClassifier:
    """Multi-layer perceptron classifier."""

    def __init__(self, hidden_dim: int = 128, dropout: float = 0.1) -> None:
        """Initialize classifier."""
        self.hidden_dim = hidden_dim

    def forward(self, x: list[float]) -> float:
        """Forward pass."""
        return sum(x)

def compute_loss(predictions: list[float], targets: list[float]) -> float:
    """Compute cross-entropy loss."""
    return 0.5
'''
    sigs = DocAstStaticAnalyzer.parse_source(sample_code)
    assert len(sigs) >= 2

    # Check class signature
    cls_sig = next(s for s in sigs if s.object_path == "NeuralClassifier")
    assert "NeuralClassifier" in cls_sig.signature_str
    assert "Multi-layer perceptron" in cls_sig.docstring
    param_names = [p.name for p in cls_sig.parameters]
    assert "hidden_dim" in param_names
    assert "dropout" in param_names

    # Check function signature
    func_sig = next(s for s in sigs if s.object_path == "compute_loss")
    assert "compute_loss" in func_sig.signature_str
    assert func_sig.return_type == "float"
    assert len(func_sig.parameters) == 2


@pytest.mark.unit
def test_pep302_mock_virtualization() -> None:
    """Verify PEP 302/451 mock virtualization allows importing uninstalled modules and subclassing."""
    with virtualize_imports(packages=("uninstalled_heavy_ai_pkg",)):
        import uninstalled_heavy_ai_pkg
        from uninstalled_heavy_ai_pkg.nn import Module

        # Subclass dynamic proxy class
        class CustomModel(Module):
            def __init__(self) -> None:
                super().__init__()
                self.layer = uninstalled_heavy_ai_pkg.layers.Dense(64)

        model = CustomModel()
        assert model is not None
        assert isinstance(model, Module)


@pytest.mark.unit
def test_link_verification_with_anchors() -> None:
    """Verify link checker handles valid links, extensionless links, and broken anchors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "index.md").write_text(
            "# Home Page\n\nWelcome. See [Guide](./guide) or [Specific Section](./guide#deep-dive) or [Bad Anchor](./guide#missing).\n",
            encoding="utf-8",
        )
        (root / "guide.md").write_text(
            "# User Guide\n\n## Deep Dive\n\nContent here.\n",
            encoding="utf-8",
        )

        report = DocBuilderDomainEngine.verify_links(
            root, check_anchors=True, check_toc=False
        )
        assert report.scanned_files_count == 2
        assert report.total_links_checked == 3
        assert not report.valid
        assert len(report.broken_links) == 1
        assert "missing" in (report.broken_links[0].anchor or "")


@pytest.mark.unit
def test_toc_integrity_and_orphan_detection() -> None:
    """Verify table-of-contents auditor detects broken TOC entries and unlisted orphan docs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "index.md").write_text("# Home\n", encoding="utf-8")
        (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (root / "orphan.md").write_text("# Orphaned Doc\n", encoding="utf-8")

        # Create _toctree.yml missing orphan.md and referencing non_existent.md
        toc_content = """- local: index
- local: guide
- local: non_existent
"""
        (root / "_toctree.yml").write_text(toc_content, encoding="utf-8")

        report = DocBuilderDomainEngine.verify_links(
            root, check_anchors=True, check_toc=True
        )
        assert not report.valid

        # Verify broken TOC entry flagged
        invalid_toc = [t for t in report.toc_diagnostics if not t.is_valid]
        assert len(invalid_toc) == 1
        assert invalid_toc[0].entry == "non_existent"

        # Verify orphan page detected
        assert "orphan.md" in report.orphaned_files


@pytest.mark.unit
def test_mdx_format_conversion() -> None:
    """Verify format conversion injects Svelte tags for callouts and Sphinx directives."""
    raw_md = "# Title\n\n> [!NOTE]\nThis is a note callout.\n\n> [!WARNING]\nWatch out!\n\n.. note::\nSphinx note text.\n"
    res = DocBuilderDomainEngine.convert_format(raw_md, target_format="mdx")
    assert "<Tip>" in res.converted_content
    assert "</Tip>" in res.converted_content
    assert "<Warning>" in res.converted_content
    assert "</Warning>" in res.converted_content
    assert "<Tip>" in res.svelte_components_injected
    assert "<Warning>" in res.svelte_components_injected


@pytest.mark.unit
def test_doc_style_linting_and_fixing() -> None:
    """Verify codeblock linter detects trailing whitespace and formats correctly."""
    dirty_md = "# Code Guide\n\n```python\nimport sys   \nx = 1\t\n```\n"
    res = DocBuilderDomainEngine.lint_style(dirty_md, fix=False)
    assert res.issues_count >= 1

    res_fixed = DocBuilderDomainEngine.lint_style(dirty_md, fix=True)
    assert res_fixed.formatted_content is not None
    assert "   \n" not in res_fixed.formatted_content
    assert "\t\n" not in res_fixed.formatted_content


@pytest.mark.unit
def test_heading_chunking_with_breadcrumbs() -> None:
    """Verify hierarchical chunking divides text along heading trees with breadcrumbs."""
    markdown_doc = """# Library Documentation
Introduction to the library.

## Installation
Run pip install my-lib.

### GPU Support
Install CUDA binaries.

## Usage
Basic examples.
"""
    chunks = DocBuilderDomainEngine.chunk_markdown(
        markdown_doc, page_title="My Library"
    )
    assert len(chunks) == 4

    gpu_chunk = next(c for c in chunks if c.title == "GPU Support")
    assert gpu_chunk.heading_level == 3
    assert gpu_chunk.breadcrumb == ("My Library", "Installation", "GPU Support")


@pytest.mark.unit
def test_service_ioc_contract() -> None:
    """Verify DefaultHfDocBuilderService implements HfDocBuilderProtocol with service key."""
    service = DefaultHfDocBuilderService()
    assert DOC_BUILDER_SERVICE_KEY.name == "service.doc_builder"

    sig = service.inspect_autodoc("json", "loads")
    assert "loads" in sig.object_path

    chunks = service.chunk_markdown("# Simple Doc\nHello world.")
    assert len(chunks) >= 1


@pytest.mark.unit
def test_backward_compatible_skill_script_adapter() -> None:
    """Verify .agents/skills/.../scripts/doc_builder_engine.py forwards to kernel service."""
    skill_scripts = (
        Path(__file__).resolve().parent.parent
        / ".agents"
        / "skills"
        / "hf-doc-builder-architect"
        / "scripts"
    )
    if str(skill_scripts) not in sys.path:
        sys.path.insert(0, str(skill_scripts))
    import doc_builder_engine

    assert hasattr(doc_builder_engine, "DocBuilderDomainEngine")
    assert hasattr(doc_builder_engine, "AutodocSignature")
    sig = doc_builder_engine.DocBuilderDomainEngine.inspect_autodoc("json", "dumps")
    assert "dumps" in sig.object_path


@pytest.mark.unit
def test_click_cli_commands() -> None:
    """Verify headless Click CLI subcommands execute cleanly via CliRunner (Rule 10)."""
    runner = CliRunner()

    # 1. inspect command
    res_inspect = runner.invoke(
        doc_builder_group,
        ["inspect", "--package", "json", "--object", "dumps", "--json"],
    )
    assert res_inspect.exit_code == 0
    inspect_data = json.loads(res_inspect.output)
    assert "dumps" in inspect_data["object_path"]

    # 2. chunk command
    res_chunk = runner.invoke(
        doc_builder_group,
        ["chunk", "--text", "# Title\n\nIntro\n\n## Sub\n\nDetail", "--json"],
    )
    assert res_chunk.exit_code == 0
    chunk_data = json.loads(res_chunk.output)
    assert len(chunk_data) == 2

    # 3. convert command
    res_convert = runner.invoke(
        doc_builder_group,
        ["convert", "--source", "# Title\n\n> [!NOTE]\nInfo", "--json"],
    )
    assert res_convert.exit_code == 0
    convert_data = json.loads(res_convert.output)
    assert "<Tip>" in convert_data["converted_content"]

    # 4. verify command on empty valid directory
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "index.md").write_text("# Home\nWelcome.", encoding="utf-8")
        res_verify = runner.invoke(
            doc_builder_group, ["verify", "--docs-dir", tmpdir, "--no-toc", "--json"]
        )
        assert res_verify.exit_code == 0
        verify_data = json.loads(res_verify.output)
        assert verify_data["valid"] is True
