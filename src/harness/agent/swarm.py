"""Multi-Agent Swarm Orchestrator — Declarative DAG execution, token budgeting, and consensus voting.

Enables hierarchical agent topologies (e.g. Supervisor -> Workers -> Debater -> Synthesizer)
with transactional context isolation, topological dependency waves, and token governance.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
import time
from typing import Any, Callable, cast

import structlog

from harness.agent.base import AgentTaskResult
from harness.agent.session import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.graph import DependencyGraph, GraphCycleError
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

    def to_dependency_graph(self) -> DependencyGraph[str]:
        """Convert SwarmDAG into an authoritative DependencyGraph instance."""
        graph = DependencyGraph[str]()
        for node_id, node in self.nodes.items():
            graph.add_node(node_id, data=node)

        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node_id}' references non-existent dependency '{dep}'")
                graph.add_edge(from_node=dep, to_node=node_id)

        return graph

    def get_execution_plan(self) -> list[list[str]]:
        """Compute parallel execution waves via topological sorting.

        Raises:
            ValueError: If a cyclic dependency is detected.
        """
        graph = self.to_dependency_graph()
        try:
            return graph.execution_waves()
        except GraphCycleError as e:
            raise ValueError(f"Cycle detected in SwarmDAG task dependencies: {e}") from e

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
class SwarmNodeExecution:
    """Detailed execution telemetry for an individual Swarm DAG node."""

    id: str
    role: str
    task: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    tokens_used: int = 0
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "task": self.task,
            "dependencies": list(self.dependencies),
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "tokens_used": self.tokens_used,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class SwarmWaveMetrics:
    """Telemetry for a parallel wave of node executions in the Swarm DAG."""

    wave_index: int
    node_ids: list[str]
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_tokens: int = 0
    bottleneck_node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave_index": self.wave_index,
            "node_ids": list(self.node_ids),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "total_tokens": self.total_tokens,
            "bottleneck_node_id": self.bottleneck_node_id,
        }


@dataclass
class SwarmExecutionTree:
    """Hierarchical execution telemetry, critical path analysis, and wave metrics for a Swarm run."""

    run_id: str
    objective: str
    status: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_tokens: int = 0
    nodes: dict[str, SwarmNodeExecution] = field(default_factory=dict)
    waves: list[SwarmWaveMetrics] = field(default_factory=list)
    critical_path: list[str] = field(default_factory=list)
    critical_path_duration: float = 0.0
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)

    def calculate_critical_path(self) -> list[str]:
        """Compute the sequence of dependent nodes that determined the maximum cumulative latency path."""
        if not self.nodes:
            return []

        memo: dict[str, tuple[float, list[str]]] = {}

        def _longest_path(node_id: str) -> tuple[float, list[str]]:
            if node_id in memo:
                return memo[node_id]
            node = self.nodes[node_id]
            dur = node.duration
            if not node.dependencies:
                res = (dur, [node_id])
                memo[node_id] = res
                return res

            best_parent_dur = 0.0
            best_parent_path: list[str] = []
            for dep in node.dependencies:
                if dep in self.nodes:
                    p_dur, p_path = _longest_path(dep)
                    if p_dur > best_parent_dur:
                        best_parent_dur = p_dur
                        best_parent_path = p_path

            res = (best_parent_dur + dur, best_parent_path + [node_id])
            memo[node_id] = res
            return res

        best_total = 0.0
        best_overall_path: list[str] = []
        for nid in self.nodes:
            tot, path = _longest_path(nid)
            if tot > best_total:
                best_total = tot
                best_overall_path = path

        self.critical_path = best_overall_path
        self.critical_path_duration = round(best_total, 4)
        return best_overall_path

    def calculate_bottlenecks(
        self, token_threshold: int = 10_000, duration_threshold: float = 5.0
    ) -> list[dict[str, Any]]:
        """Identify execution bottleneck nodes based on latency and token consumption."""
        bottlenecks = []
        for nid, node in self.nodes.items():
            reasons = []
            if node.duration >= duration_threshold:
                reasons.append(f"high_latency ({round(node.duration, 2)}s)")
            if node.tokens_used >= token_threshold:
                reasons.append(f"high_tokens ({node.tokens_used})")
            if node.status == "failed":
                reasons.append(f"node_failure: {node.error}")

            if reasons:
                bottlenecks.append({
                    "node_id": nid,
                    "role": node.role,
                    "duration": round(node.duration, 4),
                    "tokens_used": node.tokens_used,
                    "reasons": reasons,
                })
        self.bottlenecks = bottlenecks
        return bottlenecks

    def to_mermaid_graph(self) -> str:
        """Render Mermaid DAG topology annotated with execution status and metrics."""
        lines = ["graph TD"]
        for nid, node in self.nodes.items():
            dur_str = f"{round(node.duration, 2)}s"
            tok_str = f"{node.tokens_used}t"
            label = f"{node.id} [{node.role}]<br/>{node.status} | {dur_str} | {tok_str}"
            lines.append(f'    {nid}["{label}"]')
            for dep in node.dependencies:
                lines.append(f"    {dep} --> {nid}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "total_tokens": self.total_tokens,
            "critical_path": self.critical_path,
            "critical_path_duration": self.critical_path_duration,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "waves": [w.to_dict() for w in self.waves],
            "bottlenecks": self.bottlenecks,
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
    execution_tree: SwarmExecutionTree | None = None

    def to_dict(self) -> dict[str, Any]:
        res = {
            "run_id": self.run_id,
            "objective": self.objective,
            "status": self.status,
            "final_synthesis": self.final_synthesis,
            "node_results": self.node_results,
            "total_tokens": self.total_tokens,
            "consensus": self.consensus,
            "metadata": self.metadata,
        }
        if self.execution_tree is not None:
            res["execution_tree"] = self.execution_tree.to_dict()
        return res


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
        dag_or_objective: SwarmDAG | str | None = None,
        *,
        objective: str | None = None,
        dag: SwarmDAG | None = None,
        max_total_tokens: int = 100_000,
        max_tokens: int | None = None,
        context: dict[str, Any] | None = None,
        custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
        run_id: str | None = None,
        consensus_threshold: float = 0.66,
    ) -> SwarmTaskResult:
        """Execute all nodes in the Swarm DAG in topological dependency waves."""
        import uuid

        target = dag_or_objective if dag_or_objective is not None else (dag if dag is not None else objective)
        if target is None:
            raise ValueError("Either dag or objective must be provided to run_swarm")

        effective_max_tokens = max_tokens if max_tokens is not None else max_total_tokens
        actual_run_id = run_id or f"swarm_{uuid.uuid4().hex[:8]}"

        if isinstance(target, str):
            dag = self.decompose(target)
            objective = target
        else:
            dag = target
            objective = objective or "Custom Swarm DAG Execution"

        governor = TokenGovernor(max_tokens=effective_max_tokens)
        execution_plan = dag.get_execution_plan()
        accumulated_results: dict[str, Any] = {}

        # Look up optional AgentSessionManager for persistent hierarchical execution tracking
        session_mgr: AgentSessionManager | None = (
            self.context.optional(AGENT_SESSION_MANAGER_KEY)
            if hasattr(self.context, "optional")
            else None
        )
        if session_mgr is not None:
            await session_mgr.create_session(
                task=objective,
                session_id=actual_run_id,
                metadata={
                    "is_swarm": True,
                    "nodes_total": len(dag.nodes),
                    "waves_total": len(execution_plan),
                    **(context or {}),
                },
            )

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

        swarm_start_time = time.time()
        node_executions: dict[str, SwarmNodeExecution] = {}
        wave_metrics_list: list[SwarmWaveMetrics] = []

        try:
            for wave_idx, wave_node_ids in enumerate(execution_plan, start=1):
                logger.info("Executing swarm wave", run_id=actual_run_id, wave=wave_idx, nodes=wave_node_ids)
                wave_start_time = time.time()
                wave_tokens_before = governor.tokens_consumed

                async def _execute_single_node(node_id: str) -> tuple[str, Any, int, str | None, float, float]:
                    node = dag.nodes[node_id]
                    node.status = "running"
                    child_sid = f"{actual_run_id}_{node_id}"
                    n_start = time.time()

                    # Create child session in hierarchical session manager if present
                    if session_mgr is not None:
                        await session_mgr.create_child_session(
                            parent_session_id=actual_run_id,
                            task=node.task,
                            session_id=child_sid,
                            node_id=node.id,
                            role=node.role,
                            metadata={
                                "dependencies": list(node.dependencies),
                                "allocated_tokens": node.allocated_tokens,
                            },
                        )

                    # Check budget
                    if governor.is_exhausted():
                        node.status = "failed"
                        node.error = "Token budget exhausted before execution"
                        n_end = time.time()
                        if session_mgr is not None:
                            await session_mgr.fail_session(child_sid, node.error)
                        return node_id, None, 0, node.error, n_start, n_end

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
                                    session_id=child_sid,
                                    parent_session_id=actual_run_id,
                                )
                                node.result = agent_res.final_answer or agent_res.status
                                tokens_used = agent_res.total_tokens or 150
                                node.status = "completed" if agent_res.status == "completed" else "failed"
                            else:
                                node.result = f"Completed {node.role} task: {node.task}"
                                node.status = "completed"

                        node.tokens_used = tokens_used
                        governor.record_usage(node.id, tokens_used)
                        n_end = time.time()

                        # Update child session in session manager
                        if session_mgr is not None:
                            if node.status == "completed":
                                await session_mgr.complete_session(
                                    child_sid,
                                    final_answer=str(node.result),
                                    total_tokens=tokens_used,
                                )
                            else:
                                await session_mgr.fail_session(
                                    child_sid,
                                    error_message=node.error or "Node execution failed",
                                )

                        return node_id, node.result, tokens_used, None, n_start, n_end
                    except Exception as e:
                        node.status = "failed"
                        node.error = str(e)
                        n_end = time.time()
                        logger.error("Swarm node execution failed", run_id=actual_run_id, node=node_id, error=str(e))
                        if session_mgr is not None:
                            await session_mgr.fail_session(child_sid, str(e))
                        return node_id, None, tokens_used, str(e), n_start, n_end

                # Execute wave concurrently
                results = await asyncio.gather(*(_execute_single_node(nid) for nid in wave_node_ids))
                wave_end_time = time.time()
                wave_duration = max(0.0, wave_end_time - wave_start_time)
                wave_tokens = governor.tokens_consumed - wave_tokens_before

                slowest_node_id: str | None = None
                max_node_dur = 0.0

                for nid, res, tokens, err, n_start, n_end in results:
                    if err:
                        all_success = False
                    accumulated_results[nid] = res
                    n_dur = max(0.0, n_end - n_start)
                    node_obj = dag.nodes[nid]
                    node_executions[nid] = SwarmNodeExecution(
                        id=nid,
                        role=node_obj.role,
                        task=node_obj.task,
                        dependencies=list(node_obj.dependencies),
                        status=node_obj.status,
                        start_time=n_start,
                        end_time=n_end,
                        duration=n_dur,
                        tokens_used=tokens,
                        result=res,
                        error=err,
                    )
                    if n_dur > max_node_dur:
                        max_node_dur = n_dur
                        slowest_node_id = nid

                wave_metrics_list.append(
                    SwarmWaveMetrics(
                        wave_index=wave_idx,
                        node_ids=list(wave_node_ids),
                        start_time=wave_start_time,
                        end_time=wave_end_time,
                        duration=wave_duration,
                        total_tokens=wave_tokens,
                        bottleneck_node_id=slowest_node_id,
                    )
                )

            swarm_end_time = time.time()
            total_duration = max(0.0, swarm_end_time - swarm_start_time)

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

            # Construct execution tree
            exec_tree = SwarmExecutionTree(
                run_id=actual_run_id,
                objective=objective,
                status=task_status,
                start_time=swarm_start_time,
                end_time=swarm_end_time,
                duration=total_duration,
                total_tokens=governor.tokens_consumed,
                nodes=node_executions,
                waves=wave_metrics_list,
            )
            exec_tree.calculate_critical_path()
            exec_tree.calculate_bottlenecks()

            task_result = SwarmTaskResult(
                run_id=actual_run_id,
                objective=objective,
                status=task_status,
                final_synthesis=final_synthesis,
                node_results=accumulated_results,
                total_tokens=governor.tokens_consumed,
                consensus=consensus_data,
                metadata=governor.get_stats(),
                execution_tree=exec_tree,
            )

            # Store swarm task result in root session metadata and complete in session manager
            if session_mgr is not None:
                root_session = await session_mgr.get_session(actual_run_id)
                if root_session is not None:
                    root_session.metadata["swarm_run"] = task_result.to_dict()
                    root_session.metadata["is_swarm"] = True
                    await session_mgr.store.save(root_session)

                if all_success:
                    await session_mgr.complete_session(
                        actual_run_id,
                        final_answer=final_synthesis,
                        total_tokens=governor.tokens_consumed,
                    )
                else:
                    await session_mgr.fail_session(
                        actual_run_id,
                        error_message=f"Swarm completed with partial failures: {task_status}",
                    )

            self._emit(
                EventType.AGENT_TASK_COMPLETED if all_success else EventType.AGENT_TASK_FAILED,
                task_result.to_dict(),
            )

            self._run_history[actual_run_id] = task_result
            return task_result

        finally:
            self._active_runs.pop(actual_run_id, None)

    execute_dag = run_swarm

    def get_run(self, run_id: str) -> SwarmTaskResult | None:
        """Fetch a completed or archived swarm run by ID from in-memory cache."""
        return self._run_history.get(run_id)

    async def get_run_async(self, run_id: str) -> SwarmTaskResult | dict[str, Any] | None:
        """Fetch a completed swarm run by ID, falling back to persistent session store."""
        if run_id in self._run_history:
            return self._run_history[run_id]

        session_mgr: AgentSessionManager | None = (
            self.context.optional(AGENT_SESSION_MANAGER_KEY)
            if hasattr(self.context, "optional")
            else None
        )
        if session_mgr is not None:
            sess = await session_mgr.get_session(run_id)
            if sess and "swarm_run" in sess.metadata:
                return cast(dict[str, Any], sess.metadata["swarm_run"])
            if sess:
                return sess.to_dict()
        return None

    def analyze_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch post-flight execution analytics and critical path breakdown for a run."""
        run = self.get_run(run_id)
        if not run:
            return None
        if run.execution_tree is not None:
            return run.execution_tree.to_dict()
        return run.to_dict()

    async def get_run_session_tree(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve full hierarchical execution session tree for a swarm run."""
        session_mgr: AgentSessionManager | None = (
            self.context.optional(AGENT_SESSION_MANAGER_KEY)
            if hasattr(self.context, "optional")
            else None
        )
        if session_mgr is not None:
            return await session_mgr.get_session_tree(run_id)
        run = self.get_run(run_id)
        return run.to_dict() if run else None

    def list_runs(self, limit: int = 50) -> list[SwarmTaskResult]:
        """List historical swarm execution outcomes from in-memory cache."""
        runs = list(self._run_history.values())
        return runs[-limit:] if limit > 0 else runs

    async def list_runs_async(self, limit: int = 50) -> list[dict[str, Any]]:
        """List historical swarm execution outcomes from memory and persistent session store."""
        results: list[dict[str, Any]] = [r.to_dict() for r in self._run_history.values()]
        seen_ids = {r["run_id"] for r in results if "run_id" in r}

        session_mgr: AgentSessionManager | None = (
            self.context.optional(AGENT_SESSION_MANAGER_KEY)
            if hasattr(self.context, "optional")
            else None
        )
        if session_mgr is not None:
            sessions = await session_mgr.list_sessions(limit=limit * 2)
            for s in sessions:
                if s.session_id not in seen_ids and s.metadata.get("is_swarm"):
                    swarm_payload = s.metadata.get("swarm_run")
                    if swarm_payload:
                        results.append(swarm_payload)
                        seen_ids.add(s.session_id)
                    else:
                        results.append(s.to_dict())
                        seen_ids.add(s.session_id)

        return results[-limit:] if limit > 0 else results

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
