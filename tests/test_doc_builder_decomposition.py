"""Contract verification tests for doc_builder package decomposition.

Conforms to:
- Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
- Rule 43: Immutability verification using direct attribute assignment inside pytest.raises.
- Rule 49: Authoritative in-memory domain engine for micro-kernel IoC elevation.
- Rule 58: Single-seam resolver fallback invariant.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from harness.kernel.context import ServiceContext, ServiceKey


@pytest.mark.unit
def test_submodule_direct_imports() -> None:
    """Verify that all decomposed submodules can be imported independently."""
    from harness.services.doc_builder.ast_analyzer import (
        DocAstStaticAnalyzer,
        TocIntegrityAuditor,
    )
    from harness.services.doc_builder.engine import DocBuilderDomainEngine
    from harness.services.doc_builder.models import (
        AutodocParameter,
        AutodocSignature,
        AutodocSignatureData,
        DocChunk,
        DocChunkData,
        DocFormatConvertData,
        DocFormatConvertResult,
        DocLintResult,
        DocLintResultData,
        LinkDiagnostic,
        LinkDiagnosticData,
        LinkValidationReport,
        LinkValidationReportData,
        TocDiagnostic,
    )
    from harness.services.doc_builder.service import (
        DOC_BUILDER_SERVICE_KEY,
        DefaultHfDocBuilderService,
        HfDocBuilderProtocol,
        HfDocBuilderService,
        resolve_doc_builder,
    )
    from harness.services.doc_builder.virtualizer import (
        MockModule,
        ZeroDepMockFinder,
        ZeroDepMockLoader,
        virtualize_imports,
    )

    # Assert all imported symbols exist and are callable/constructible
    assert AutodocParameter is not None
    assert AutodocSignature is not None
    assert AutodocSignatureData is AutodocSignature
    assert LinkDiagnostic is not None
    assert LinkDiagnosticData is LinkDiagnostic
    assert TocDiagnostic is not None
    assert LinkValidationReport is not None
    assert LinkValidationReportData is LinkValidationReport
    assert DocFormatConvertResult is not None
    assert DocFormatConvertData is DocFormatConvertResult
    assert DocLintResult is not None
    assert DocLintResultData is DocLintResult
    assert DocChunk is not None
    assert DocChunkData is DocChunk

    assert MockModule is not None
    assert ZeroDepMockFinder is not None
    assert ZeroDepMockLoader is not None
    assert virtualize_imports is not None

    assert DocAstStaticAnalyzer is not None
    assert TocIntegrityAuditor is not None
    assert DocBuilderDomainEngine is not None

    assert HfDocBuilderProtocol is not None
    assert DefaultHfDocBuilderService is not None
    assert HfDocBuilderService is DefaultHfDocBuilderService
    assert DOC_BUILDER_SERVICE_KEY is not None
    assert resolve_doc_builder is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility() -> None:
    """Verify that the package __init__.py re-exports all expected symbols."""
    import harness.services.doc_builder as db

    expected_symbols = [
        "DOC_BUILDER_SERVICE_KEY",
        "AutodocParameter",
        "AutodocSignature",
        "AutodocSignatureData",
        "DefaultHfDocBuilderService",
        "DocAstStaticAnalyzer",
        "DocBuilderDomainEngine",
        "DocChunk",
        "DocChunkData",
        "DocFormatConvertData",
        "DocFormatConvertResult",
        "DocLintResult",
        "DocLintResultData",
        "HfDocBuilderProtocol",
        "HfDocBuilderService",
        "LinkDiagnostic",
        "LinkDiagnosticData",
        "LinkValidationReport",
        "LinkValidationReportData",
        "MockModule",
        "TocDiagnostic",
        "TocIntegrityAuditor",
        "ZeroDepMockFinder",
        "ZeroDepMockLoader",
        "virtualize_imports",
        "resolve_doc_builder",
    ]

    for sym in expected_symbols:
        assert hasattr(db, sym), f"Missing expected symbol in doc_builder facade: {sym}"


@pytest.mark.unit
def test_slotted_frozen_dataclasses_immutability_and_validation() -> None:
    """Rule 12 & Rule 43: Test slotted and frozen immutability across models."""
    from harness.services.doc_builder.models import (
        AutodocParameter,
        AutodocSignature,
        DocChunk,
        DocFormatConvertResult,
        DocLintResult,
        LinkDiagnostic,
        LinkValidationReport,
        TocDiagnostic,
    )

    param = AutodocParameter(
        name="max_tokens", type_annotation="int", default_value="2048"
    )
    assert param.name == "max_tokens"
    with pytest.raises((AttributeError, TypeError)):
        param.name = "mutated"  # type: ignore

    # Validation: empty name must fail
    with pytest.raises(ValueError):
        AutodocParameter(name="")

    sig = AutodocSignature(
        object_path="transformers.AutoModel",
        signature_str="AutoModel.from_pretrained(pretrained_model_name_or_path)",
        parameters=(param,),
        return_type="AutoModel",
    )
    with pytest.raises((AttributeError, TypeError)):
        sig.signature_str = "mutated"  # type: ignore
    with pytest.raises(ValueError):
        AutodocSignature(object_path="", signature_str="foo()")

    link_diag = LinkDiagnostic(
        source_file="docs/index.md",
        target_link="./guide#getting-started",
        anchor="getting-started",
        is_valid=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        link_diag.is_valid = False  # type: ignore
    with pytest.raises(ValueError):
        LinkDiagnostic(source_file="", target_link="foo")

    toc_diag = TocDiagnostic(entry="overview", file_path="overview.md", is_valid=True)
    with pytest.raises((AttributeError, TypeError)):
        toc_diag.is_valid = False  # type: ignore
    with pytest.raises(ValueError):
        TocDiagnostic(entry="")

    report = LinkValidationReport(
        scanned_files_count=1,
        total_links_checked=1,
        broken_links=(link_diag,),
        valid=False,
    )
    with pytest.raises((AttributeError, TypeError)):
        report.valid = True  # type: ignore

    conv_res = DocFormatConvertResult(
        source_path="intro.rst",
        target_format="mdx",
        converted_content="<Tip>Hello</Tip>",
        svelte_components_injected=("<Tip>",),
    )
    with pytest.raises((AttributeError, TypeError)):
        conv_res.target_format = "html"  # type: ignore
    with pytest.raises(ValueError):
        DocFormatConvertResult(source_path="")

    lint_res = DocLintResult(
        file_path="snippet.py", issues_count=1, diagnostics=("Trailing space",)
    )
    with pytest.raises((AttributeError, TypeError)):
        lint_res.issues_count = 0  # type: ignore
    with pytest.raises(ValueError):
        DocLintResult(file_path="")

    chunk = DocChunk(
        chunk_id="chunk_1",
        title="Installation",
        heading_level=2,
        content="pip install harness",
        tokens_estimate=5,
    )
    with pytest.raises((AttributeError, TypeError)):
        chunk.title = "mutated"  # type: ignore
    with pytest.raises(ValueError):
        DocChunk(chunk_id="", title="Installation", heading_level=1, content="")


@pytest.mark.unit
def test_zero_dep_mock_virtualization() -> None:
    """Verify PEP 302/451 mock virtualization intercepts missing heavy packages."""
    import sys
    from harness.services.doc_builder.virtualizer import virtualize_imports

    test_fake_pkg = "nonexistent_heavy_ml_lib"
    assert test_fake_pkg not in sys.modules

    with virtualize_imports((test_fake_pkg,)):
        import nonexistent_heavy_ml_lib  # type: ignore

        # Attributes and submodules resolve recursively
        sub = nonexistent_heavy_ml_lib.layers.AttentionBlock
        assert sub is not None
        inst = sub()
        assert inst is not None
        assert isinstance(inst, sub)

    # After exiting context, module is evicted from sys.modules
    assert test_fake_pkg not in sys.modules


@pytest.mark.unit
def test_doc_ast_static_analyzer() -> None:
    """Verify static AST extraction of signatures and parameters."""
    from harness.services.doc_builder.ast_analyzer import DocAstStaticAnalyzer

    sample_code = '''
def process_data(input_path: str, batch_size: int = 64) -> bool:
    """Process data in batches from given path."""
    return True

class PipelineRunner:
    """Runner for asynchronous pipelines."""
    def __init__(self, mode: str = "fast", retries: int = 3):
        pass
'''
    sigs = DocAstStaticAnalyzer.parse_source(sample_code)
    assert len(sigs) >= 2

    # Check function signature
    func_sig = next((s for s in sigs if s.object_path == "process_data"), None)
    assert func_sig is not None
    assert func_sig.return_type == "bool"
    assert len(func_sig.parameters) == 2
    assert func_sig.parameters[0].name == "input_path"
    assert func_sig.parameters[1].name == "batch_size"
    assert func_sig.parameters[1].default_value == "64"

    # Check class signature
    cls_sig = next((s for s in sigs if s.object_path == "PipelineRunner"), None)
    assert cls_sig is not None
    assert len(cls_sig.parameters) == 2
    assert cls_sig.parameters[0].name == "mode"


@pytest.mark.unit
def test_toc_integrity_auditor() -> None:
    """Verify TOC auditing against documentation directory."""
    from harness.services.doc_builder.ast_analyzer import TocIntegrityAuditor

    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir)
        (docs_path / "intro.md").write_text("# Intro", encoding="utf-8")
        (docs_path / "guide.mdx").write_text("# Guide", encoding="utf-8")
        (docs_path / "orphan.md").write_text("# Orphaned", encoding="utf-8")

        # Create _toctree.yml referencing intro and guide
        (docs_path / "_toctree.yml").write_text(
            "- local: intro\n- local: guide\n- local: nonexistent\n",
            encoding="utf-8",
        )

        diags, orphans = TocIntegrityAuditor.audit_toc(docs_path)

        # 3 entries in TOC: 2 valid, 1 invalid
        assert len(diags) == 3
        valid_diags = [d for d in diags if d.is_valid]
        invalid_diags = [d for d in diags if not d.is_valid]
        assert len(valid_diags) == 2
        assert len(invalid_diags) == 1
        assert invalid_diags[0].entry == "nonexistent"

        # orphan.md should be flagged as orphaned
        assert "orphan.md" in orphans


@pytest.mark.unit
def test_domain_engine_features() -> None:
    """Verify format conversion, linting, and chunking via domain engine."""
    from harness.services.doc_builder.engine import DocBuilderDomainEngine

    # 1. Format conversion
    sample_rst = ".. note:: This is an important note."
    conv_res = DocBuilderDomainEngine.convert_format(sample_rst)
    assert "<Tip>" in conv_res.converted_content
    assert "</Tip>" in conv_res.converted_content
    assert "<Tip>" in conv_res.svelte_components_injected

    # 2. Lint style
    sample_py = "```python\ndef test():  \n    pass\n```"
    lint_res = DocBuilderDomainEngine.lint_style(sample_py, fix=True)
    assert lint_res.issues_count > 0
    assert lint_res.formatted_content is not None
    assert "def test():\n" in lint_res.formatted_content

    # 3. Chunk markdown
    sample_md = """# Title
Introductory text.

## Section 1
Content of section 1.

### Subsection 1.1
Detailed content here.
"""
    chunks = DocBuilderDomainEngine.chunk_markdown(sample_md)
    assert len(chunks) == 3
    assert chunks[0].title == "Title"
    assert chunks[1].title == "Section 1"
    assert chunks[2].title == "Subsection 1.1"


@pytest.mark.unit
def test_resolve_doc_builder_single_seam() -> None:
    """Rule 58: Verify resolve_doc_builder provides working fallback and IoC resolution."""
    from harness.services.doc_builder.service import (
        DOC_BUILDER_SERVICE_KEY,
        DefaultHfDocBuilderService,
        HfDocBuilderProtocol,
        resolve_doc_builder,
    )

    # 1. Standalone fallback when ctx is None
    svc_none = resolve_doc_builder(None)
    assert isinstance(svc_none, HfDocBuilderProtocol)
    assert isinstance(svc_none, DefaultHfDocBuilderService)

    # 2. Standalone fallback when ctx does not provide key
    empty_ctx = ServiceContext()
    svc_empty = resolve_doc_builder(empty_ctx)
    assert isinstance(svc_empty, HfDocBuilderProtocol)
    assert isinstance(svc_empty, DefaultHfDocBuilderService)

    # 3. Resolves custom service provided in context
    custom_ctx = ServiceContext()

    class CustomDocBuilderService(DefaultHfDocBuilderService):
        pass

    custom_instance = CustomDocBuilderService()
    custom_ctx.provide(DOC_BUILDER_SERVICE_KEY, custom_instance)

    svc_custom = resolve_doc_builder(custom_ctx)
    assert svc_custom is custom_instance
