"""Comprehensive test suite for skills ecosystem hygiene and storage lineage."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillChainResult,
    SkillStageDefinition,
)
from harness.services.storage import (
    KNOWLEDGE_VAULT_KEY,
    STORAGE_SERVICE_KEY,
    IsnadLineageBlock,
    IsnadLineageNode,
    KnowledgeItemRecord,
    SQLiteStorageService,
    StoragePlugin,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    find_skill_chain,
    index_skill_catalog,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestSkillsEcosystemHygiene:
    """Validate all active skills in .agents/skills against craft standards."""

    @pytest.fixture
    def skills_root(self) -> Path:
        root = Path(__file__).parent.parent / ".agents" / "skills"
        if not root.exists():
            root = Path(".agents/skills")
        return root

    def test_all_skills_directory_structure(self, skills_root: Path) -> None:
        assert skills_root.exists(), f"Skills root missing: {skills_root}"
        skill_dirs = [d for d in skills_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
        assert len(skill_dirs) >= 10, f"Expected >= 10 skills, found {len(skill_dirs)}"

        for sdir in skill_dirs:
            skill_file = sdir / "SKILL.md"
            card_file = sdir / "CARD.md"
            assert skill_file.exists(), f"SKILL.md missing in {sdir.name}"
            assert card_file.exists(), f"CARD.md missing in {sdir.name}"

    @pytest.mark.asyncio
    async def test_all_skills_validation_pipeline(self, skills_root: Path) -> None:
        skill_dirs = [d for d in skills_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
        for sdir in skill_dirs:
            report = await SkillValidator.validate_async(sdir)
            assert report.valid is True, f"Skill {sdir.name} validation failed: {report.errors}"

    def test_all_skills_parser_and_pillars(self, skills_root: Path) -> None:
        discovered = SkillCardParser.scan_root(skills_root)
        assert len(discovered) >= 10, f"Expected >= 10 skills parsed, found {len(discovered)}"

        for name, node in discovered.items():
            assert node.name == name
            assert len(node.stages) >= 2, f"Skill {name} has too few stages ({len(node.stages)})"
            assert len(node.anti_patterns) >= 1, f"Skill {name} missing anti-patterns"
            assert len(node.invariants) >= 1, f"Skill {name} missing invariants"
            assert all(inv.is_blocking for inv in node.invariants), f"Skill {name} invariants must be blocking"


@pytest.mark.unit
@pytest.mark.asyncio
class TestStorageKnowledgeAndIsnadLineage:
    """Test deepened StorageService with Isnad provenance and Knowledge Items."""

    async def test_knowledge_item_crud_and_isnad(self) -> None:
        storage = SQLiteStorageService(":memory:")

        # Create Isnad Lineage Block
        node_code = IsnadLineageNode(
            node_type="primary_code",
            uri="file:///src/harness/kernel/service.py#L42-L68",
            sha256_hash=storage.compute_sha256("test_code_content"),
            verified=True,
        )
        node_test = IsnadLineageNode(
            node_type="verification_test",
            uri="file:///tests/kernel/test_service.py#L15-L35",
            sha256_hash=storage.compute_sha256("test_test_content"),
            verified=True,
        )

        isnad_block = IsnadLineageBlock(
            decision_id="dec_20260822_01",
            claims=[
                {
                    "assertion": "Service registration requires generic ServiceKey[T]",
                    "lineage": [node_code.model_dump(), node_test.model_dump()],
                }
            ],
            status="VERIFIED",
        )

        ki = KnowledgeItemRecord(
            id="ki_20260822_01",
            title="Typed Service Key Registration in Plugin Systems",
            source_target="file:///src/harness/kernel/service.py",
            detected_format="harness_instance",
            isnad=isnad_block,
            tags=["architecture", "ioc_container", "storage"],
            summary="Service registration must always use typed ServiceKey[T].",
        )

        # Save KI
        await storage.save_knowledge_item(ki)

        # Retrieve KI
        retrieved = await storage.get_knowledge_item("ki_20260822_01")
        assert retrieved is not None
        assert retrieved.id == "ki_20260822_01"
        assert retrieved.title == "Typed Service Key Registration in Plugin Systems"
        assert "ioc_container" in retrieved.tags

        # List KIs by tag
        tagged = await storage.list_knowledge_items(tag="architecture")
        assert len(tagged) == 1
        assert tagged[0].id == "ki_20260822_01"

        missing_tag = await storage.list_knowledge_items(tag="nonexistent")
        assert len(missing_tag) == 0

        storage.close()

    async def test_sync_knowledge_vault_from_real_disk(self) -> None:
        """Test sync_knowledge_vault against active .harness/knowledge directory."""
        storage = SQLiteStorageService(":memory:")
        vault_path = Path(__file__).parent.parent / ".harness" / "knowledge"
        assert vault_path.exists()

        synced_count = await storage.sync_knowledge_vault(vault_path)
        assert synced_count >= 14

        items = await storage.list_knowledge_items()
        assert len(items) == synced_count

        # Check retrieval of specific distilled items
        ki_01 = await storage.get_knowledge_item("ki_20260823_01")
        assert ki_01 is not None
        assert "Subprocess" in ki_01.title
        assert "sandbox" in ki_01.tags

        storage.close()

    async def test_export_knowledge_vault_roundtrip(self, tmp_path: Path) -> None:
        """Test roundtrip export and sync fidelity using temporary directory."""
        storage_src = SQLiteStorageService(":memory:")
        vault_path = Path(__file__).parent.parent / ".harness" / "knowledge"
        await storage_src.sync_knowledge_vault(vault_path)

        export_dir = tmp_path / "exported_vault"
        exported_count = await storage_src.export_knowledge_vault(export_dir)
        assert exported_count >= 14

        # Read back into a clean storage instance
        storage_dst = SQLiteStorageService(":memory:")
        synced_back = await storage_dst.sync_knowledge_vault(export_dir)
        assert synced_back == exported_count

        for item in await storage_src.list_knowledge_items():
            dst_item = await storage_dst.get_knowledge_item(item.id)
            assert dst_item is not None
            assert dst_item.title == item.title
            assert dst_item.tags == item.tags

        storage_src.close()
        storage_dst.close()

    async def test_query_knowledge_filtering(self) -> None:
        """Test query_knowledge filtering across query strings, tags, and status."""
        storage = SQLiteStorageService(":memory:")
        vault_path = Path(__file__).parent.parent / ".harness" / "knowledge"
        await storage.sync_knowledge_vault(vault_path)

        # Keyword search
        sandbox_items = await storage.query_knowledge(query="subprocess")
        assert len(sandbox_items) >= 1
        assert any("ki_20260823_01" == item.id for item in sandbox_items)

        # Tag search
        cli_items = await storage.query_knowledge(tag="powershell")
        assert len(cli_items) >= 1
        assert any("ki_20260823_03" == item.id for item in cli_items)

        # Status search
        verified_items = await storage.query_knowledge(status="VERIFIED")
        assert len(verified_items) >= 1

        storage.close()

    async def test_verify_isnad_integrity(self) -> None:
        """Test verify_isnad_integrity on knowledge item lineage nodes."""
        storage = SQLiteStorageService(":memory:")
        vault_path = Path(__file__).parent.parent / ".harness" / "knowledge"
        await storage.sync_knowledge_vault(vault_path)

        res = await storage.verify_isnad_integrity("ki_20260823_01")
        assert res["status"] in ("ok", "warning")
        assert res["ki_id"] == "ki_20260823_01"
        assert len(res["claims_audited"]) >= 1

        storage.close()

    async def test_storage_plugin_provides_both_keys(self) -> None:
        """Test that StoragePlugin provides both STORAGE_SERVICE_KEY and KNOWLEDGE_VAULT_KEY."""
        plugin = StoragePlugin()
        assert STORAGE_SERVICE_KEY in plugin.provides
        assert KNOWLEDGE_VAULT_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        assert ctx.has(STORAGE_SERVICE_KEY)
        assert ctx.has(KNOWLEDGE_VAULT_KEY)
        await plugin.on_unload()


@pytest.mark.unit
class TestSkillGraphTypedModelsAndChaining:
    """Test SkillGraph typed Pydantic models and chaining."""

    def test_skill_card_definition_model(self) -> None:
        stage = SkillStageDefinition(stage_num=1, name="Audit", completion_gate="Audit done")
        ap = SkillAntiPatternDefinition(name="Leaky Seams", symptom="Direct imports", remedy="Use IoC")
        card = SkillCardDefinition(
            name="test-skill",
            category="architecture",
            invocation="/test-skill",
            triggers=["run test"],
            stages=[stage],
            anti_patterns=[ap],
            dependencies=["deepen-architecture"],
        )

        assert card.name == "test-skill"
        assert len(card.stages) == 1
        assert len(card.anti_patterns) == 1
        assert card.stages[0].stage_num == 1

    def test_skill_chaining_pipeline(self) -> None:
        index_skill_catalog(".")
        res = find_skill_chain("structured-data-scout", "data-topology-mapper")
        assert res["status"] == "ok"
        chain_res = SkillChainResult.model_validate(res)
        assert chain_res.status == "ok"
        assert chain_res.length >= 2

    def test_repo_to_plugin_forge_chaining(self) -> None:
        index_skill_catalog(".")
        # Chain from repo-reader to repo-to-plugin-forge to deepen-architecture
        res = find_skill_chain("repo-reader", "repo-to-plugin-forge")
        assert res["status"] == "ok"
        assert "repo-to-plugin-forge" in res["chain"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepoToPluginForgeEndToEnd:
    """Test end-to-end repository AST analysis to PluginCreator scaffolding."""

    async def test_forge_plugin_from_simulated_repo(self, tmp_path: Path) -> None:
        from harness.creator.creator import PluginCreator
        from harness.creator.schema import SchemaInferrer
        from harness.creator.validator import PluginValidator
        from harness.plugins.manifest import IsolationMode

        # 1. Create simulated source repository
        repo_dir = tmp_path / "sample_source_repo"
        repo_dir.mkdir()
        source_code = '''
def process_data(payload: str, count: int = 10) -> dict[str, str]:
    """Process incoming data payload and return status."""
    return {"status": "ok", "payload": payload, "count": str(count)}

def health_check() -> bool:
    """Check service health status."""
    return True
'''
        (repo_dir / "service.py").write_text(source_code, encoding="utf-8")

        # 2. Extract schemas using SchemaInferrer
        def process_data(payload: str, count: int = 10) -> dict[str, str]:
            """Process incoming data payload and return status.

            Args:
                payload: Raw payload data
                count: Processing iterations
            """
            return {"status": "ok", "payload": payload, "count": str(count)}

        params = SchemaInferrer.infer_parameters(process_data)
        assert len(params) == 2
        assert params[0].name == "payload"
        assert params[0].type == "string"
        assert params[0].required is True
        assert params[1].name == "count"
        assert params[1].default == 10
        assert params[1].type == "integer"

        spec = SchemaInferrer.infer_entrypoint_spec(process_data)
        assert spec.name == "process_data"
        assert spec.returns == "object"

        # 3. Scaffold target plugin using PluginCreator
        plugin_dir = tmp_path / "plugins" / "sample_plugin"
        scaffold_res = PluginCreator.scaffold(
            target_dir=plugin_dir,
            name="sample-forged-plugin",
            description="Forged plugin from simulated repo.",
            category="data_engineering",
            preset="tool_provider",
            tools=["process_data", "health_check"],
            isolation=IsolationMode.SUBPROCESS,
            auto_validate=True,
        )

        assert scaffold_res.validation_report is not None
        assert scaffold_res.validation_report.valid is True
        assert (plugin_dir / "plugin.json").exists()
        assert (plugin_dir / "main.py").exists()

        # 4. Run PluginValidator directly
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid is True
        assert len(report.errors) == 0

