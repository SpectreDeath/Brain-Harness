"""Plugin Archetypes package facade.

Polymorphic template and code generation strategies:
    - GeneralArchetype: Standard multi-tool execution boilerplate
    - ToolArchetype: LLM skill / tool provider with typed signatures
    - ApiWrapperArchetype: Async HTTP client wrapper using httpx
    - ServiceArchetype: Full HarnessPlugin subclass registering custom ServiceKeys
    - McpBridgeArchetype: Model Context Protocol (MCP) server bridge client
    - AgenticWorkflowArchetype: Autonomous agent workflow loop with multi-step planning
    - ContainerArchetype: Containerized plugin with Dockerfile and sandbox container isolation
    - ArchetypeRegistry: Central strategy registry for archetype lookup and management
"""

from __future__ import annotations

from harness.creator.archetypes.agentic_workflow import (
    AgenticWorkflowArchetype,
)
from harness.creator.archetypes.api_wrapper import (
    ApiWrapperArchetype,
)
from harness.creator.archetypes.base import (
    PluginArchetype,
)
from harness.creator.archetypes.container import (
    ContainerArchetype,
)
from harness.creator.archetypes.general import (
    GeneralArchetype,
    ToolArchetype,
)
from harness.creator.archetypes.mcp_bridge import (
    McpBridgeArchetype,
)
from harness.creator.archetypes.registry import (
    ArchetypeRegistry,
)
from harness.creator.archetypes.service import (
    ServiceArchetype,
)

__all__ = [
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
