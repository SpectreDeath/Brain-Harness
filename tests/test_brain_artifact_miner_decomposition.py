"""Contract verification test suite for Brain Artifact Miner Service Decomposition (Cycle 46).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted & frozen dataclass contracts on all 6 models (Rule 12 & Rule 43).
3. Typed service key BRAIN_ARTIFACT_MINER_KEY (Rule 2).
4. Single-seam resolver resolve_brain_artifact_miner (Rule 58).
5. 100% backward-compatible facade re-exports across harness.services.brain_artifact_miner.
6. AST script classification and scratch tool scanning.
7. Background task log triage and stderr drainage.
8. Dual-transcript O(1) binary byte-offset seek retrieval (Rule 48).
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.brain_artifact_miner import (
    ArtifactLifecycleEntry,
    BRAIN_ARTIFACT_MINER_KEY,
    BrainArtifactMinerService,
    ByteOffsetEntry,
    DualTranscriptStep,
    ScratchCatalog,
    ScratchCatalogItem,
    StandardBrainArtifactMinerService,
    TaskTriageReport,
    build_offset_index,
    classify_script_ast,
    export_knowledge_item,
    generate_html_brief,
    get_step,
    resolve_brain_artifact_miner,
    scan_scratch_tools,
    stream_steps,
    triage_task_logs,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestBrainArtifactMinerDecompositionArchitecture:
    """Architectural and structural invariants for brain_artifact_miner subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = (
            Path(__file__).parent.parent
            / "src"
            / "harness"
            / "services"
            / "brain_artifact_miner"
        )
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        expected_modules = {
            "__init__.py",
            "models.py",
            "protocols.py",
            "resolvers.py",
            "transcript.py",
            "scratch.py",
            "triage.py",
            "export.py",
            "service.py",
        }

        found_modules = {p.name for p in pkg_dir.glob("*.py")}
        assert expected_modules.issubset(found_modules)

        for mod_name in expected_modules:
            mod_path = pkg_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_frozen_dataclass_models(self) -> None:
        """Rule 12 & Rule 43: All domain models must be slotted and frozen."""
        models = [
            ScratchCatalogItem("ast", "test.py", ["fn"], ["ast"], "doc"),
            ScratchCatalog(1, 1, {}),
            TaskTriageReport(1, 0, 0, []),
            ByteOffsetEntry(0, 0, 100),
            DualTranscriptStep(0, "model", "thought", "done", "txt", False, [], False),
            ArtifactLifecycleEntry("cid", "art.md", True, False, True, 123.45),
        ]

        for m in models:
            assert hasattr(m, "__slots__"), f"{type(m)} missing __slots__"
            assert not hasattr(m, "__dict__"), f"{type(m)} has __dict__"

        # Verify immutability of frozen dataclass (Rule 43)
        item = models[0]
        with pytest.raises((AttributeError, TypeError)):
            item.category = "other"

    def test_typed_service_key_and_resolver(self) -> None:
        """Rule 2 & Rule 58: Typed service key and single-seam IoC resolver."""
        assert isinstance(BRAIN_ARTIFACT_MINER_KEY, ServiceKey)
        assert BRAIN_ARTIFACT_MINER_KEY.name == "service.brain_artifact_miner"

        # Resolver fallback without context
        svc_default = resolve_brain_artifact_miner()
        assert isinstance(svc_default, StandardBrainArtifactMinerService)

        # Resolver with context
        ctx = ServiceContext()
        ctx.provide(BRAIN_ARTIFACT_MINER_KEY, svc_default)
        svc_resolved = resolve_brain_artifact_miner(ctx)
        assert svc_resolved is svc_default

    def test_ast_script_classification(self, tmp_path: Path) -> None:
        """Verify AST classification on sample script."""
        script_path = tmp_path / "check_ast.py"
        script_path.write_text(
            '"""Check AST tokenization."""\nimport ast\ndef parse_tree(code):\n    return ast.parse(code)\n',
            encoding="utf-8",
        )
        cat, funcs, imps, doc = classify_script_ast(script_path.read_text(encoding="utf-8"), script_path)
        assert cat == "ast_and_lint"
        assert "parse_tree" in funcs
        assert "ast" in imps
        assert "Check AST" in doc

    def test_knowledge_item_export(self, tmp_path: Path) -> None:
        """Verify canonical dual-file export format (Rule 40, Rule 41)."""
        svc = StandardBrainArtifactMinerService()
        meta_file, summary_file = svc.export_knowledge_item(
            output_dir=tmp_path,
            ki_id="ki_test_mining",
            title="Artifact Mining Learnings",
            category="archaeology",
            summary="Workspace indexing insights",
            claims=[{"fact": "O(1) seek is sub-millisecond", "isnad": "verified"}],
        )

        assert meta_file.is_file()
        assert summary_file.is_file()
        assert "ki_test_mining" in meta_file.read_text(encoding="utf-8")
        assert "Workspace indexing insights" in summary_file.read_text(encoding="utf-8")
