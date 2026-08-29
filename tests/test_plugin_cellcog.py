"""Comprehensive unit test suite for the CellCog plugin and service subsystem."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.services.cellcog import (
    CELLCOG_CATALOG,
    CELLCOG_SERVICE_KEY,
    CellCogArtifact,
    CellCogCapabilitiesResult,
    CellCogCapabilityItem,
    CellCogResearchResult,
    CellCogRunResult,
    CellCogService,
    MultimodalCompilationResult,
    MultimodalProtocolCompiler,
    parse_generate_file_tags,
    parse_show_file_tags,
)
from plugins.integration_and_io.cellcog.main import (
    CellCogPlugin,
    cellcog_list_capabilities,
    cellcog_research,
    cellcog_run,
)


@pytest.mark.unit
class TestCellCogPluginSubsystem:
    """Test suite verifying CellCog plugin manifest, service key typing, lifecycle, and tag parsers."""

    @pytest.fixture
    def plugin_dir(self) -> Path:
        return Path(__file__).parent.parent / "plugins" / "integration_and_io" / "cellcog"

    def test_manifest_schema_valid(self, plugin_dir: Path) -> None:
        """Verify plugin.json exists, parses into PluginManifest, and enforces subprocess isolation."""
        manifest_file = plugin_dir / "plugin.json"
        assert manifest_file.exists(), f"Missing plugin.json at {manifest_file}"

        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest = PluginManifest.model_validate(manifest_data)

        assert manifest.name == "plugin.cellcog"
        assert manifest.version == "1.0.0"
        assert manifest.category == "integration_and_io"
        assert manifest.isolation == IsolationMode.SUBPROCESS
        assert manifest.trusted is False
        assert "service.cellcog" in manifest.provides
        assert len(manifest.entrypoints) == 3

        entrypoint_names = {ep.name for ep in manifest.entrypoints}
        assert entrypoint_names == {"cellcog_run", "cellcog_research", "cellcog_list_capabilities"}

    def test_service_key_typed(self) -> None:
        """Verify CELLCOG_SERVICE_KEY is strictly typed ServiceKey[CellCogService]."""
        assert isinstance(CELLCOG_SERVICE_KEY, ServiceKey)
        assert CELLCOG_SERVICE_KEY.name == "service.cellcog"

    def test_show_file_tag_parsing_valid(self) -> None:
        """Verify extraction of valid <SHOW_FILE> paths."""
        prompt = """
        Analyze the following files together:
        <SHOW_FILE>/workspace/data/sales_q4.csv</SHOW_FILE>
        <SHOW_FILE>/workspace/docs/overview.pdf</SHOW_FILE>
        Generate an executive dashboard.
        """
        sanitized, valid, rejected = parse_show_file_tags(prompt)
        assert len(valid) == 2
        assert "/workspace/data/sales_q4.csv" in valid
        assert "/workspace/docs/overview.pdf" in valid
        assert len(rejected) == 0

    def test_show_file_rejects_sensitive_paths(self) -> None:
        """Verify sensitive credentials, .env, and ssh keys are intercepted and redacted."""
        prompt = """
        Please inspect:
        <SHOW_FILE>/workspace/.env</SHOW_FILE>
        <SHOW_FILE>/home/user/.ssh/id_rsa</SHOW_FILE>
        <SHOW_FILE>/workspace/data/valid.csv</SHOW_FILE>
        <SHOW_FILE>/workspace/secret.pem</SHOW_FILE>
        """
        sanitized, valid, rejected = parse_show_file_tags(prompt)
        assert len(valid) == 1
        assert "/workspace/data/valid.csv" in valid

        assert len(rejected) == 3
        assert "/workspace/.env" in rejected
        assert "/home/user/.ssh/id_rsa" in rejected
        assert "/workspace/secret.pem" in rejected

        assert "<SHOW_FILE>/workspace/.env</SHOW_FILE>" not in sanitized
        assert "REDACTED_SENSITIVE_FILE" in sanitized

    def test_generate_file_tag_parsing(self) -> None:
        """Verify extraction of <GENERATE_FILE> output targets."""
        prompt = """
        Create multiple outputs:
        <GENERATE_FILE>/workspace/output/report.pdf</GENERATE_FILE>
        <GENERATE_FILE>/workspace/output/model.glb</GENERATE_FILE>
        """
        _, outputs = parse_generate_file_tags(prompt)
        assert len(outputs) == 2
        assert "/workspace/output/report.pdf" in outputs
        assert "/workspace/output/model.glb" in outputs

    def test_multimodal_protocol_compiler_disk_checks(self) -> None:
        """Verify MultimodalProtocolCompiler handles MIME detection and disk validation."""
        assert MultimodalProtocolCompiler.detect_mime("model.glb") == "model/gltf-binary"
        assert MultimodalProtocolCompiler.detect_mime("video.mp4") == "video/mp4"
        assert MultimodalProtocolCompiler.detect_mime("sheet.xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        with tempfile.TemporaryDirectory() as tmpdir:
            real_file = Path(tmpdir) / "real.csv"
            real_file.write_text("a,b,c\n1,2,3", encoding="utf-8")
            missing_file = Path(tmpdir) / "nonexistent.png"

            prompt = f"<SHOW_FILE>{real_file}</SHOW_FILE><SHOW_FILE>{missing_file}</SHOW_FILE>"
            comp = MultimodalProtocolCompiler.compile_prompt(prompt, check_disk=True)

            assert str(real_file) in comp.valid_inputs
            assert str(missing_file) in comp.missing_files

    def test_cellcog_artifact_model_and_hashing(self) -> None:
        """Verify CellCogArtifact computes correct SHA256 checksum and metadata."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            f.write(b"glTF2.0_test_binary_data")
            tmp_path = f.name

        try:
            art = CellCogArtifact.from_path(tmp_path)
            assert art.filename.endswith(".glb")
            assert art.size_bytes > 0
            assert len(art.checksum_sha256) == 64
            assert art.mime_type == "model/gltf-binary"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_capabilities_catalog(self) -> None:
        """Verify the static capability catalog is populated across 7 categories."""
        service = CellCogService()
        catalog = service.list_capabilities()

        assert catalog.total_capabilities >= 35
        assert "Research & Analysis" in catalog.categories
        assert "Video & Cinema" in catalog.categories
        assert "Images & Design" in catalog.categories
        assert "Audio & Music" in catalog.categories
        assert "Documents & Slides" in catalog.categories
        assert "Apps & Prototypes" in catalog.categories
        assert "Development" in catalog.categories

    @pytest.mark.asyncio
    async def test_plugin_lifecycle_and_context_registration(self) -> None:
        """Verify plugin lifecycle hooks and IoC registration with EventBus linking."""
        ctx = ServiceContext()
        bus = EventBus()
        ctx.provide(EVENT_BUS_KEY, bus)

        service = CellCogService(api_key="test-key")
        plugin = CellCogPlugin(service=service)

        assert plugin.name == "plugin.cellcog"
        assert plugin.version == "1.0.0"
        assert plugin.trusted is False
        assert CELLCOG_SERVICE_KEY in plugin.provides

        await plugin.on_load(ctx)
        assert ctx.has(CELLCOG_SERVICE_KEY)
        resolved = ctx.require(CELLCOG_SERVICE_KEY)
        assert resolved is service
        assert service.event_bus is bus

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_event_bus_telemetry_emission(self) -> None:
        """Verify CellCogService emits telemetry events to EventBus during execution."""
        bus = EventBus()
        events_received: list[HarnessEvent] = []

        async def _capture(evt: HarnessEvent) -> None:
            events_received.append(evt)

        bus.on(EventType.TOOL_INVOKED, _capture)
        bus.on(EventType.TOOL_RESULT, _capture)

        service = CellCogService(api_key="sk_test", event_bus=bus)
        res = await service.execute("Generate dashboard <GENERATE_FILE>/out.html</GENERATE_FILE>")
        assert res.success is True
        assert len(events_received) == 2
        assert events_received[0].event_type == EventType.TOOL_INVOKED
        assert events_received[1].event_type == EventType.TOOL_RESULT

    @pytest.mark.asyncio
    async def test_execution_without_api_key_returns_structured_error(self) -> None:
        """Verify service returns a structured error when API key is missing."""
        service = CellCogService(api_key=None)
        # Explicitly set empty to override any host environment variable
        service.api_key = ""

        res = await service.execute("Generate a 3D model")
        assert res.success is False
        assert res.error is not None
        assert "API key not configured" in res.error

    @pytest.mark.asyncio
    async def test_mock_execution_flow(self) -> None:
        """Verify fallback execution when API key is present but SDK is mocked."""
        service = CellCogService(api_key="sk_test_123")
        res = await service.execute(
            prompt="Create a 3D asset <GENERATE_FILE>/workspace/out.glb</GENERATE_FILE>",
            chat_mode="agent",
            chat_tier="max",
            task_label="asset-gen",
        )
        assert res.success is True
        assert res.chat_mode == "agent"
        assert res.chat_tier == "max"
        assert "/workspace/out.glb" in res.generated_files
        assert len(res.artifacts) == 1
        assert res.artifacts[0].filename == "out.glb"

    @pytest.mark.asyncio
    async def test_mock_research_flow(self) -> None:
        """Verify deep research execution method."""
        service = CellCogService(api_key="sk_test_123")
        res = await service.research(
            topic="Agent Operating Systems",
            attachments=["/workspace/data/benchmarks.csv"],
            chat_tier="flash",
        )
        assert res.success is True
        assert res.chat_tier == "flash"
        assert res.sources_count > 0

    def test_module_tool_handlers(self) -> None:
        """Verify module-level tool functions return dictionaries with expected keys."""
        catalog_dict = cellcog_list_capabilities()
        assert "total_capabilities" in catalog_dict
        assert "categories" in catalog_dict
        assert "capabilities" in catalog_dict
        assert catalog_dict["total_capabilities"] >= 35

        run_dict = cellcog_run(
            prompt="Analyze data <SHOW_FILE>/workspace/data.csv</SHOW_FILE> <GENERATE_FILE>/workspace/out.pdf</GENERATE_FILE>",
            chat_mode="agent",
            chat_tier="flash",
        )
        assert "success" in run_dict
        assert "chat_mode" in run_dict
        assert "attached_files" in run_dict
        assert "artifacts" in run_dict

        research_dict = cellcog_research(
            topic="Quantum Computing Trends",
            attachments=["/workspace/paper.pdf"],
        )
        assert "success" in research_dict
        assert "summary" in research_dict
        assert "sources_count" in research_dict
        assert "artifacts" in research_dict
