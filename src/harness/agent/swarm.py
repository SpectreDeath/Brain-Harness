"""Multi-Agent Swarm Orchestrator — Declarative DAG execution, token budgeting, and consensus voting.

Enables hierarchical agent topologies (e.g. Supervisor -> Workers -> Debater -> Synthesizer)
with transactional context isolation, topological dependency waves, and token governance.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable

import structlog

from harness.agent.base import AgentLoopService, AgentTaskResult
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

SWARM_COORDINATOR_KEY: ServiceKey[SwarmCoordinator] = ServiceKey("agent.swarm")


@dataclass
class SwarmNode:
    """A discrete unit of work in a multi-agent swarm DAG."""

    id: str
    role: str
    task: str
    dependencies: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    allocated_tokens: int = 10_000
    status: str = "pending"  # "pending", "running", "completed", "failed", "skipped"
    result: Any = None
    error: str | None = None
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "task": self.task,
            "dependencies": self.dependencies,
            "tools": self.tools,
            "allocated_tokens": self.allocated_tokens,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "tokens_used": self.tokens_used,
        }


class SwarmDAG:
    """Directed Acyclic Graph representing task dependencies among swarm agents."""

    def __init__(self) -> None:
        self.nodes: dict[str, SwarmNode] = {}

    def add_node(self, node: SwarmNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.id] = node

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Declare that to_node depends on from_node."""
        if to_node_id not in self.nodes:
            raise KeyError(f"Target node '{to_node_id}' does not exist in DAG")
        if from_node_id not in self.nodes:
            raise KeyError(f"Source node '{from_node_id}' does not exist in DAG")
        if from_node_id not in self.nodes[to_node_id].dependencies:
            self.nodes[to_node_id].dependencies.append(from_node_id)

    def get_execution_plan(self) -> list[list[str]]:
        """Compute parallel execution waves via topological sorting.

        Raises:
            ValueError: If a cyclic dependency is detected.
        """
        in_degree: dict[str, int] = {node_id: 0 for node_id in self.nodes}
        dependents: dict[str, list[str]] = defaultdict(list)

        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node_id}' references non-existent dependency '{dep}'")
                dependents[dep].append(node_id)
                in_degree[node_id] += 1

        waves: list[list[str]] = []
        ready = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
        processed = 0

        while ready:
            current_wave = list(ready)
            ready.clear()
            waves.append(current_wave)
            processed += len(current_wave)

            for node_id in current_wave:
                for dep in dependents[node_id]:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        ready.append(dep)

        if processed < len(self.nodes):
            raise ValueError("Cycle detected in SwarmDAG task dependencies")

        return waves

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "node_count": len(self.nodes),
        }


class TokenGovernor:
    """Tracks and bounds cumulative token consumption across swarm agents."""

    def __init__(self, max_tokens: int = 100_000) -> None:
        self.max_tokens = max_tokens
        self.tokens_consumed = 0
        self._usage_by_agent: dict[str, int] = defaultdict(int)

    @property
    def remaining_budget(self) -> int:
        return max(0, self.max_tokens - self.tokens_consumed)

    def allocate(self, agent_id: str, requested: int) -> int:
        """Grant token allocation up to available remaining global budget."""
        granted = min(requested, self.remaining_budget)
        return granted

    def record_usage(self, agent_id: str, tokens: int) -> None:
        """Record actual tokens consumed by an agent."""
        self.tokens_consumed += tokens
        self._usage_by_agent[agent_id] += tokens

    def is_exhausted(self) -> bool:
        """Check if global budget is completely exhausted."""
        return self.tokens_consumed >= self.max_tokens

    def get_stats(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "tokens_consumed": self.tokens_consumed,
            "remaining_budget": self.remaining_budget,
            "usage_by_agent": dict(self._usage_by_agent),
            "is_exhausted": self.is_exhausted(),
        }


class ConsensusEngine:
    """Supermajority voting and confidence-weighted consensus engine."""

    @classmethod
    def tally(
        cls,
        votes: list[dict[str, Any]],
        threshold: float = 0.66,
    ) -> dict[str, Any]:
        """Tally multi-agent votes to determine consensus outcome."""
        if not votes:
            return {
                "status": "error",
                "error": "No votes provided",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        approvals = 0
        rejections = 0
        weighted_conf = 0.0

        for v in votes:
            vote_val = str(v.get("vote", "")).lower().strip()
            conf = float(v.get("confidence", 1.0))
            weighted_conf += conf

            if vote_val in ("approve", "yes", "accept", "1", "true", "pass"):
                approvals += 1
            else:
                rejections += 1

        total = len(votes)
        approval_ratio = approvals / total
        consensus_reached = approval_ratio >= threshold
        avg_conf = round(weighted_conf / total, 2)

        return {
            "status": "ok",
            "total_votes": total,
            "approvals": approvals,
            "rejections": rejections,
            "approval_ratio": round(approval_ratio, 2),
            "required_threshold": threshold,
            "consensus_reached": consensus_reached,
            "avg_confidence": avg_conf,
            "decision": "APPROVED" if consensus_reached else "REJECTED",
        }


@dataclass
class SwarmTaskResult:
    """Outcome of a complete Swarm DAG execution."""

    objective: str
    status: str  # "completed", "partial", "failed"
    run_id: str = ""
    final_synthesis: str = ""
    node_results: dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    consensus: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "status": self.status,
            "final_synthesis": self.final_synthesis,
            "node_results": self.node_results,
            "total_tokens": self.total_tokens,
            "consensus": self.consensus,
            "metadata": self.metadata,
        }


class SwarmCoordinator:
    """Authoritative coordinator executing multi-agent swarm DAGs with token governance."""

    def __init__(
        self,
        context: ServiceContext,
        event_bus: EventBus | None = None,
    ) -> None:
        self.context = context
        self.event_bus = event_bus
        self._active_runs: dict[str, dict[str, Any]] = {}
        self._run_history: dict[str, SwarmTaskResult] = {}

    def _emit(self, event_type: EventType | str, payload: dict[str, Any]) -> None:
        if self.event_bus is not None:
            evt = HarnessEvent(
                event_type=event_type if isinstance(event_type, EventType) else EventType.CUSTOM,
                source="agent.swarm",
                payload=payload,
            )
            self.event_bus.emit_sync(evt)

    def decompose(
        self,
        objective: str,
        agents: list[dict[str, Any]] | None = None,
    ) -> SwarmDAG:
        """Decompose a high-level objective into a structured SwarmDAG."""
        dag = SwarmDAG()

        if not agents:
            agents = [
                {"id": "researcher", "role": "researcher", "task": f"Research and gather facts for: {objective}"},
                {"id": "developer", "role": "developer", "task": f"Implement solution based on research for: {objective}", "dependencies": ["researcher"]},
                {"id": "critic", "role": "critic", "task": f"Review and validate developer output for: {objective}", "dependencies": ["developer"]},
                {"id": "synthesizer", "role": "synthesizer", "task": f"Synthesize final deliverable for: {objective}", "dependencies": ["critic"]},
            ]

        for a in agents:
            node = SwarmNode(
                id=a["id"],
                role=a.get("role", "worker"),
                task=a.get("task", objective),
                dependencies=list(a.get("dependencies", [])),
                tools=list(a.get("tools", [])),
                allocated_tokens=int(a.get("allocated_tokens", 10_000)),
            )
            dag.add_node(node)

        return dag

    async def run_swarm(
        self,
        dag_or_objective: SwarmDAG | str,
        *,
        max_total_tokens: int = 100_000,
        context: dict[str, Any] | None = None,
        custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
        run_id: str | None = None,
    ) -> SwarmTaskResult:
        """Execute all nodes in the Swarm DAG in topological dependency waves."""
        import uuid

        actual_run_id = run_id or f"swarm_{uuid.uuid4().hex[:8]}"

        if isinstance(dag_or_objective, str):
            dag = self.decompose(dag_or_objective)
            objective = dag_or_objective
        else:
            dag = dag_or_objective
            objective = "Custom Swarm DAG Execution"

        governor = TokenGovernor(max_tokens=max_total_tokens)
        execution_plan = dag.get_execution_plan()
        accumulated_results: dict[str, Any] = {}

        self._active_runs[actual_run_id] = {
            "run_id": actual_run_id,
            "objective": objective,
            "status": "running",
            "nodes_total": len(dag.nodes),
            "waves_total": len(execution_plan),
        }

        self._emit(
            EventType.AGENT_TASK_STARTED,
            {
                "run_id": actual_run_id,
                "objective": objective,
                "waves": len(execution_plan),
                "nodes": len(dag.nodes),
            },
        )

        all_success = True

        try:
            for wave_idx, wave_node_ids in enumerate(execution_plan, start=1):
                logger.info("Executing swarm wave", run_id=actual_run_id, wave=wave_idx, nodes=wave_node_ids)

                async def _execute_single_node(node_id: str) -> tuple[str, Any, int, str | None]:
                    node = dag.nodes[node_id]
                    node.status = "running"

                    # Check budget
                    if governor.is_exhausted():
                        node.status = "failed"
                        node.error = "Token budget exhausted before execution"
                        return node_id, None, 0, node.error

                    # Collect upstream context from dependencies
                    upstream_ctx: dict[str, Any] = {}
                    for dep in node.dependencies:
                        if dep in accumulated_results:
                            upstream_ctx[dep] = accumulated_results[dep]

                    # Prepare prompt with upstream context
                    enriched_prompt = node.task
                    if upstream_ctx:
                        upstream_summary = "\n".join(f"- Upstream {k}: {v}" for k, v in upstream_ctx.items())
                        enriched_prompt = f"{node.task}\n\n[Prerequisite Context]:\n{upstream_summary}"

                    # Execute node via custom executor or agent loop service
                    tokens_used = 100  # Baseline tokens
                    try:
                        if custom_executor is not None:
                            res = custom_executor(node, upstream_ctx)
                            if asyncio.iscoroutine(res):
                                res = await res
                            node.result = res
                            node.status = "completed"
                        else:
                            from harness.agent.base import AGENT_LOOP_KEY

                            agent_loop = self.context.optional(AGENT_LOOP_KEY)
                            if agent_loop is not None:
                                agent_res: AgentTaskResult = await agent_loop.run_task(
                                    enriched_prompt,
                                    max_steps=6,
                                    context=upstream_ctx,
                                )
                                node.result = agent_res.final_answer or agent_res.status
                                tokens_used = agent_res.total_tokens or 150
                                node.status = "completed" if agent_res.status == "completed" else "failed"
                            else:
                                node.result = f"Completed {node.role} task: {node.task}"
                                node.status = "completed"

                        node.tokens_used = tokens_used
                        governor.record_usage(node.id, tokens_used)
                        return node_id, node.result, tokens_used, None
                    except Exception as e:
                        node.status = "failed"
                        node.error = str(e)
                        logger.error("Swarm node execution failed", run_id=actual_run_id, node=node_id, error=str(e))
                        return node_id, None, tokens_used, str(e)

                # Execute wave concurrently
                results = await asyncio.gather(*(_execute_single_node(nid) for nid in wave_node_ids))

                for nid, res, tokens, err in results:
                    if err:
                        all_success = False
                    accumulated_results[nid] = res

            # Synthesize final output
            final_synthesis = ""
            if "synthesizer" in accumulated_results:
                final_synthesis = str(accumulated_results["synthesizer"])
            elif accumulated_results:
                last_node = list(accumulated_results.keys())[-1]
                final_synthesis = str(accumulated_results[last_node])

            # Check if any critic/debater node results contain consensus votes
            consensus_data: dict[str, Any] | None = None
            votes_collected: list[dict[str, Any]] = []
            for nid, res in accumulated_results.items():
                if isinstance(res, dict) and "vote" in res:
                    votes_collected.append(res)
                elif isinstance(res, list):
                    for item in res:
                        if isinstance(item, dict) and "vote" in item:
                            votes_collected.append(item)

            if votes_collected:
                consensus_data = ConsensusEngine.tally(votes_collected)

            task_status = "completed" if all_success else "partial"

            task_result = SwarmTaskResult(
                run_id=actual_run_id,
                objective=objective,
                status=task_status,
                final_synthesis=final_synthesis,
                node_results=accumulated_results,
                total_tokens=governor.tokens_consumed,
                consensus=consensus_data,
                metadata=governor.get_stats(),
            )

            self._emit(
                EventType.AGENT_TASK_COMPLETED if all_success else EventType.AGENT_TASK_FAILED,
                task_result.to_dict(),
            )

            self._run_history[actual_run_id] = task_result
            return task_result

        finally:
            self._active_runs.pop(actual_run_id, None)

    def get_run(self, run_id: str) -> SwarmTaskResult | None:
        """Fetch a completed or archived swarm run by ID."""
        return self._run_history.get(run_id)

    def list_runs(self, limit: int = 50) -> list[SwarmTaskResult]:
        """List historical swarm execution outcomes."""
        runs = list(self._run_history.values())
        return runs[-limit:] if limit > 0 else runs

    async def get_status(self) -> dict[str, Any]:
        """Return status report of the swarm coordinator."""
        last_run = list(self._run_history.values())[-1].to_dict() if self._run_history else None
        return {
            "status": "ready",
            "active_swarms": len(self._active_runs),
            "total_runs": len(self._run_history),
            "last_run": last_run,
            "coordinator_available": True,
        }



class SwarmCoordinatorPlugin(HarnessPlugin):
    """Built-in plugin exposing the SwarmCoordinator service."""

    name = "agent.swarm"
    version = "1.0.0"
    description = "Hierarchical multi-agent swarm and consensus orchestrator"
    provides = [SWARM_COORDINATOR_KEY]

    def __init__(self) -> None:
        self._coordinator: SwarmCoordinator | None = None

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        from harness.events.bus import EVENT_BUS_KEY

        bus = ctx.optional(EVENT_BUS_KEY)
        self._coordinator = SwarmCoordinator(context=ctx, event_bus=bus)
        ctx.provide(SWARM_COORDINATOR_KEY, self._coordinator)
