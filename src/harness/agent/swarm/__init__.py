"""Authoritative Swarm Coordinator and Orchestration package (decomposed).

Exposes typed models, token governor, consensus engine, wave scheduler, tree renderer,
coordinator, and plugin. Preserves 100% backward compatibility for all module-level imports
from `harness.agent.swarm`.
"""

from __future__ import annotations

# 1. Models & Dataclasses
from harness.agent.swarm.models import (
    SwarmDAG,
    SwarmExecutionTree,
    SwarmNode,
    SwarmNodeExecution,
    SwarmTaskResult,
    SwarmWaveMetrics,
)

# 2. Token Governor
from harness.agent.swarm.governor import TokenGovernor

# 3. Consensus Engine & Pluggable Strategies
from harness.agent.swarm.consensus import (
    BinaryThresholdStrategy,
    BordaConsensusStrategy,
    ConsensusEngine,
    DefaultConsensusEngine,
    SwarmConsensusProtocol,
    WeightedMajorityStrategy,
)

# 4. Wave Scheduler & Tree Renderer
from harness.agent.swarm.wave_scheduler import SwarmWaveScheduler
from harness.agent.swarm.tree_renderer import SwarmTreeRenderer

# 5. Swarm Coordinator & ServiceKey
from harness.agent.swarm.coordinator import (
    SWARM_COORDINATOR_KEY,
    SwarmCoordinator,
)

# 6. Plugin
from harness.agent.swarm.plugin import SwarmCoordinatorPlugin

# 7. Re-exports for backward compatibility
from harness.agent.base import AgentTaskResult
from harness.agent.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    AgentContextOptimizer,
)
from harness.agent.session import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    ThreadSpawnStatus,
)

__all__ = [
    # Models & Dataclasses
    "SwarmDAG",
    "SwarmExecutionTree",
    "SwarmNode",
    "SwarmNodeExecution",
    "SwarmTaskResult",
    "SwarmWaveMetrics",
    # Components & Engines
    "BinaryThresholdStrategy",
    "BordaConsensusStrategy",
    "ConsensusEngine",
    "DefaultConsensusEngine",
    "SwarmConsensusProtocol",
    "SwarmCoordinator",
    "SwarmCoordinatorPlugin",
    "SwarmTreeRenderer",
    "SwarmWaveScheduler",
    "TokenGovernor",
    "WeightedMajorityStrategy",
    "SWARM_COORDINATOR_KEY",
    # Re-exported context & graph symbols
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "AGENT_GRAPH_STORE_KEY",
    "AGENT_SESSION_MANAGER_KEY",
    "AgentContextOptimizer",
    "AgentExecutionGraphService",
    "AgentSessionManager",
    "AgentTaskResult",
    "ThreadSpawnStatus",
]
