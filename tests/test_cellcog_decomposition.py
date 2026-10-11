"""Contract verification test suite for CellCog multimodal service decomposition.

Verifies:
1. Architectural bounds: all submodules <= 200 lines (Rule 11).
2. Slotted & frozen dataclass immutability (Rule 12, Rule 43).
3. Protocol conformance & single-seam IoC resolution (Rule 2, Rule 49, Rule 58).
4. Backward-compatible facade re-exports and tag parsing.
5. Plugin module singleton export (Rule 45).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.cellcog import (
    CELLCOG_CATALOG,
    CELLCOG_SERVICE_KEY,
    CellCogArtifact,
    CellCogCapabilitiesResult,
    CellCogCapabilityItem,
    CellCogResearchResult,
    CellCogRunResult,
    CellCogService,
    CellCogServiceProtocol,
    MultimodalCompilationResult,
    MultimodalProtocolCompiler,
    parse_generate_file_tags,
    parse_show_file_tags,
    resolve_cellcog_service,
)


class TestCellCogDecomposition:
    """Contract tests verifying the architectural invariants of CellCog decomposition."""

    def test_submodule_line_bounds(self) -> None:
        """Verify all submodules in src/harness/services/cellcog/ are <= 200 lines per Rule 11."""
        cellcog_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "cellcog"
        assert cellcog_dir.is_dir(), f"Expected directory at {cellcog_dir}"

        py_files = list(cellcog_dir.glob("*.py"))
        assert len(py_files) >= 8, f"Expected at least 8 submodules, found {len(py_files)}"

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                line_count <= 200
            ), f"{py_file.name} has {line_count} lines, exceeding the 200-line limit (Rule 11)"

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify slotted/frozen immutability on domain entities per Rule 12 & Rule 43."""
        # 1. CellCogArtifact
        art = CellCogArtifact(
            path="output/model.glb",
            filename="model.glb",
            mime_type="model/gltf-binary",
            size_bytes=1024,
            checksum_sha256="abc123sha",
        )
        assert hasattr(art, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            art.size_bytes = 2048  # type: ignore[misc]

        # 2. MultimodalCompilationResult
        comp = MultimodalCompilationResult(
            sanitized_prompt="Build 3D asset",
            valid_inputs=("input.png",),
            output_destinations=("model.glb",),
        )
        assert hasattr(comp, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            comp.sanitized_prompt = "Mutated prompt"  # type: ignore[misc]

        # 3. CellCogRunResult
        run_res = CellCogRunResult(
            success=True,
            message="Asset generated",
            chat_id="chat-1",
        )
        assert hasattr(run_res, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            run_res.success = False  # type: ignore[misc]

        # 4. CellCogResearchResult
        res_res = CellCogResearchResult(
            success=True,
            summary="Research summary",
            sources_count=3,
        )
        assert hasattr(res_res, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            res_res.sources_count = 5  # type: ignore[misc]

        # 5. CellCogCapabilityItem
        item = CellCogCapabilityItem(
            name="3d-model-generation-cellcog",
            category="Images & Design",
            description="Production 3D assets",
        )
        assert hasattr(item, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            item.name = "mutated"  # type: ignore[misc]

        # 6. CellCogCapabilitiesResult
        cap_res = CellCogCapabilitiesResult(
            total_capabilities=1,
            categories=("Images & Design",),
            capabilities=(item,),
        )
        assert hasattr(cap_res, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            cap_res.total_capabilities = 2  # type: ignore[misc]

    def test_protocol_conformance_and_single_seam_resolver(self) -> None:
        """Verify protocol conformance and single-seam IoC resolution per Rule 49 & 58."""
        service = CellCogService()
        assert isinstance(service, CellCogServiceProtocol)
        assert isinstance(CELLCOG_SERVICE_KEY, ServiceKey)
        assert CELLCOG_SERVICE_KEY.name == "service.cellcog"

        # Fallback resolution with no context
        resolved_default = resolve_cellcog_service(None)
        assert isinstance(resolved_default, CellCogServiceProtocol)

        # Context-based resolution
        ctx = ServiceContext()
        custom_service = CellCogService(api_key="custom_token")
        ctx.provide(CELLCOG_SERVICE_KEY, custom_service)

        resolved_ctx = resolve_cellcog_service(ctx)
        assert resolved_ctx is custom_service

    def test_backward_compatible_facade_and_tag_compilation(self) -> None:
        """Verify backward-compatible facade re-exports and multimodal tag compilation."""
        assert len(CELLCOG_CATALOG) >= 35

        prompt = (
            "Analyze document <SHOW_FILE>data/report.pdf</SHOW_FILE> "
            "and render 3D view to <GENERATE_FILE>output/view.glb</GENERATE_FILE>."
        )

        sanitized, valid_inputs, rejected_inputs = parse_show_file_tags(prompt)
        assert valid_inputs == ("data/report.pdf",)
        assert len(rejected_inputs) == 0

        _, output_destinations = parse_generate_file_tags(prompt)
        assert output_destinations == ("output/view.glb",)

        comp = MultimodalProtocolCompiler.compile_prompt(prompt)
        assert comp.valid_inputs == ("data/report.pdf",)
        assert comp.output_destinations == ("output/view.glb",)

    def test_plugin_module_singleton_export(self) -> None:
        """Verify plugin module-level singleton export per Rule 45."""
        from plugins.integration_and_io.cellcog.main import CellCogPlugin, plugin

        assert isinstance(plugin, CellCogPlugin)
        assert CELLCOG_SERVICE_KEY in plugin.provides
        assert plugin.name == "plugin.cellcog"
