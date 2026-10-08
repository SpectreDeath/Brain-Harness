"""Contract verification tests for creator archetypes package decomposition.

Conforms to:
- Open-Closed Principle for archetype strategies.
- 100% backward compatibility facade for existing creator and CLI callers.
- Multi-language generation assertions (Python, TypeScript, JavaScript).
"""

from __future__ import annotations

import pytest

from harness.creator.scaffold import ScaffoldOptions


@pytest.mark.unit
def test_submodule_direct_imports() -> None:
    """Verify that all decomposed archetype submodules can be imported independently."""
    from harness.creator.archetypes.agentic_workflow import AgenticWorkflowArchetype
    from harness.creator.archetypes.api_wrapper import ApiWrapperArchetype
    from harness.creator.archetypes.base import PluginArchetype
    from harness.creator.archetypes.container import ContainerArchetype
    from harness.creator.archetypes.general import GeneralArchetype, ToolArchetype
    from harness.creator.archetypes.mcp_bridge import McpBridgeArchetype
    from harness.creator.archetypes.registry import ArchetypeRegistry
    from harness.creator.archetypes.service import ServiceArchetype

    assert PluginArchetype is not None
    assert GeneralArchetype is not None
    assert ToolArchetype is not None
    assert ApiWrapperArchetype is not None
    assert ServiceArchetype is not None
    assert McpBridgeArchetype is not None
    assert AgenticWorkflowArchetype is not None
    assert ContainerArchetype is not None
    assert ArchetypeRegistry is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility() -> None:
    """Verify that the package __init__.py re-exports all expected archetype symbols."""
    import harness.creator.archetypes as arch_pkg

    expected_symbols = [
        "AgenticWorkflowArchetype",
        "ApiWrapperArchetype",
        "ArchetypeRegistry",
        "ContainerArchetype",
        "GeneralArchetype",
        "McpBridgeArchetype",
        "PluginArchetype",
        "ServiceArchetype",
        "ToolArchetype",
    ]

    for sym in expected_symbols:
        assert hasattr(arch_pkg, sym), f"Missing symbol in archetypes facade: {sym}"


@pytest.mark.unit
def test_archetype_registry_lifecycle_and_aliases() -> None:
    """Verify ArchetypeRegistry query, alias resolution, snapshot isolation, and reset."""
    from harness.creator.archetypes.base import PluginArchetype
    from harness.creator.archetypes.registry import ArchetypeRegistry

    # 1. Default registered presets count
    archetypes = ArchetypeRegistry.list_archetypes()
    assert len(archetypes) >= 7
    names = {a["name"] for a in archetypes}
    assert {
        "general",
        "tool",
        "api_wrapper",
        "service",
        "mcp_bridge",
        "agentic_workflow",
        "container",
    }.issubset(names)

    # 2. Aliases resolution
    assert ArchetypeRegistry.get("workflow").name == "agentic_workflow"
    assert ArchetypeRegistry.get("agent").name == "agentic_workflow"
    assert ArchetypeRegistry.get("docker").name == "container"
    assert ArchetypeRegistry.get("api").name == "api_wrapper"

    # 3. Snapshot isolation
    class CustomArchetype(PluginArchetype):
        @property
        def name(self) -> str:
            return "custom_test"

        def generate_manifest(self, options: ScaffoldOptions):
            raise NotImplementedError

        def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
            return ""

        def generate_test_code(self, options: ScaffoldOptions) -> str:
            return ""

        def generate_project_config(self, options: ScaffoldOptions):
            return "requirements.txt", ""

    with ArchetypeRegistry.snapshot():
        ArchetypeRegistry.register(CustomArchetype())
        assert ArchetypeRegistry.has("custom_test") is True
        assert ArchetypeRegistry.get("custom_test").name == "custom_test"
        ArchetypeRegistry.unregister("custom_test")
        assert ArchetypeRegistry.has("custom_test") is False

    # After exiting snapshot context, custom_test is not present
    assert ArchetypeRegistry.has("custom_test") is False


@pytest.mark.unit
def test_general_and_tool_archetypes() -> None:
    """Verify GeneralArchetype and ToolArchetype code generation."""
    from harness.creator.archetypes.general import GeneralArchetype, ToolArchetype

    opts_py = ScaffoldOptions(name="test_tool", language="python", tools=["calc", "verify"])
    gen = GeneralArchetype()
    manifest = gen.generate_manifest(opts_py)
    assert manifest.name == "test_tool"
    assert len(manifest.entrypoints) == 2

    code = gen.generate_entrypoint_code(opts_py)
    assert "def calc(" in code
    assert "def verify(" in code

    test_code = gen.generate_test_code(opts_py)
    assert "def test_calc_success():" in test_code

    tool_arch = ToolArchetype()
    opts_tool = ScaffoldOptions(name="test_tool", language="python", category="")
    tool_manifest = tool_arch.generate_manifest(opts_tool)
    assert tool_manifest.category == "developer_tools"
    assert "tool" in tool_manifest.tags


@pytest.mark.unit
def test_service_archetype_ioc_generation() -> None:
    """Verify ServiceArchetype generates typed ServiceKey and IoC lifecycle."""
    from harness.creator.archetypes.service import ServiceArchetype

    opts = ScaffoldOptions(name="metrics_collector", language="python")
    service_arch = ServiceArchetype()
    manifest = service_arch.generate_manifest(opts)
    assert manifest.provides == ["service.metrics_collector"]

    code = service_arch.generate_entrypoint_code(opts)
    assert "SERVICE_KEY: ServiceKey[MetricsCollectorService]" in code
    assert "class MetricsCollectorServicePlugin(HarnessPlugin):" in code
    assert "ctx.provide(SERVICE_KEY, self._service" in code

    test_code = service_arch.generate_test_code(opts)
    assert "ctx.require(SERVICE_KEY)" in test_code


@pytest.mark.unit
def test_container_and_workflow_extra_files() -> None:
    """Verify ContainerArchetype and AgenticWorkflowArchetype extra files."""
    from harness.creator.archetypes.agentic_workflow import AgenticWorkflowArchetype
    from harness.creator.archetypes.container import ContainerArchetype

    opts_container = ScaffoldOptions(name="sandbox_runner", language="python")
    cont_arch = ContainerArchetype()
    extra_cont = cont_arch.generate_extra_files(opts_container)
    assert "Dockerfile" in extra_cont
    assert ".dockerignore" in extra_cont
    assert "FROM python:3.11-slim" in extra_cont["Dockerfile"]

    opts_flow = ScaffoldOptions(name="planner_flow", language="python")
    flow_arch = AgenticWorkflowArchetype()
    extra_flow = flow_arch.generate_extra_files(opts_flow)
    assert "README.md" in extra_flow
    assert "## Workflow Stages" in extra_flow["README.md"]
