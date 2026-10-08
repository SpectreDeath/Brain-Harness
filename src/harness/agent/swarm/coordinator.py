"""Authoritative Swarm Coordinator orchestrating multi-agent DAGs with token governance."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any, cast

import structlog

from harness.agent.base import AgentTaskResult
from harness.agent.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    AgentContextOptimizer,
)
from harness.agent.session import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.agent.swarm.consensus import ConsensusEngine
from harness.agent.swarm.governor import TokenGovernor
from harness.agent.swarm.models import (
    SwarmDAG,
    SwarmExecutionTree,
    SwarmNode,
    SwarmNodeExecution,
    SwarmTaskResult,
    SwarmWaveMetrics,
)
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    ThreadSpawnStatus,
)

logger = structlog.get_logger()

SWARM_COORDINATOR_KEY: ServiceKey[SwarmCoordinator] = ServiceKey("agent.swarm")


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
                event_type=event_type
                if isinstance(event_type, EventType)
                else EventType.CUSTOM,
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
                {
                    "id": "researcher",
                    "role": "researcher",
                    "task": f"Research and gather facts for: {objective}",
                },
                {
                    "id": "developer",
                    "role": "developer",
                    "task": f"Implement solution based on research for: {objective}",
                    "dependencies": ["researcher"],
                },
                {
                    "id": "critic",
                    "role": "critic",
                    "task": f"Review and validate developer output for: {objective}",
                    "dependencies": ["developer"],
                },
                {
                    "id": "synthesizer",
                    "role": "synthesizer",
                    "task": f"Synthesize final deliverable for: {objective}",
                    "dependencies": ["critic"],
                },
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

    def decompose_with_skills(
        self,
        objective: str,
        skill_names: list[str] | None = None,
        top_k: int = 3,
        include_verifier: bool = True,
    ) -> SwarmDAG:
        """Decompose a high-level objective into a structured SwarmDAG derived from agent skills."""
        try:
            from harness.services.skill_graph import resolve_skill_intelligence

            intelligence = resolve_skill_intelligence(self.context)
        except Exception:
            intelligence = None

        if intelligence is None:
            return self.decompose(objective)

        target_skills: list[str] = []
        if skill_names:
            target_skills = list(skill_names)
        else:
            try:
                guidance = intelligence.compile_execution_guidance(
                    objective, max_skills=top_k, include_verifier=include_verifier
                )
                if guidance and guidance.execution_pipeline:
                    target_skills = list(guidance.execution_pipeline)
            except Exception:
                pass

            if not target_skills:
                try:
                    plan = intelligence.select_skills_for_task(
                        objective, max_skills=top_k, include_verifier=include_verifier
                    )
                    if plan and getattr(plan, "execution_pipeline", None):
                        target_skills = list(plan.execution_pipeline)
                except Exception:
                    pass

            if not target_skills:
                routing = intelligence.route_intent(objective, top_k=top_k)
                target_skills = [
                    m.get("skill_name") or m.get("name")
                    for m in (routing.get("matches") or [])
                    if (m.get("skill_name") or m.get("name"))
                ]
            if not target_skills:
                return self.decompose(objective)

        dag = SwarmDAG()
        prev_node_id: str | None = None

        for skill_name in target_skills:
            skill = intelligence.get_skill(skill_name)
            if not skill:
                continue

            if skill.stages:
                for stage in skill.stages:
                    node_id = f"{skill.name}_stage_{stage.stage_num}"
                    deps = [prev_node_id] if prev_node_id else []
                    task_desc = (
                        f"Execute [{skill.name}] Stage {stage.stage_num} ({stage.name}) "
                        f"for objective: {objective}. Gate: {stage.completion_gate}"
                    )
                    node = SwarmNode(
                        id=node_id,
                        role=f"{skill.name}:{stage.name}",
                        task=task_desc,
                        dependencies=deps,
                        tools=list(skill.tools) if skill.tools else [],
                        allocated_tokens=15_000,
                    )
                    dag.add_node(node)
                    prev_node_id = node_id
            else:
                node_id = f"skill_{skill.name}"
                deps = [prev_node_id] if prev_node_id else []
                node = SwarmNode(
                    id=node_id,
                    role=f"specialist:{skill.name}",
                    task=f"Apply skill [{skill.name}] target: {skill.target} on objective: {objective}",
                    dependencies=deps,
                    tools=list(skill.tools) if skill.tools else [],
                    allocated_tokens=20_000,
                )
                dag.add_node(node)
                prev_node_id = node_id

        if include_verifier and prev_node_id and not any("verifier" in n for n in dag.nodes):
            verifier_id = "adversarial_verifier"
            dag.add_node(
                SwarmNode(
                    id=verifier_id,
                    role="adversarial_verifier",
                    task=f"Rigorously verify outputs and assert invariants for objective: {objective}",
                    dependencies=[prev_node_id],
                    tools=["verify_contract", "arch_lint"],
                    allocated_tokens=10_000,
                )
            )

        if not dag.nodes:
            return self.decompose(objective)

        return dag

    async def dispatch_skill_swarm(
        self,
        objective: str,
        skill_names: list[str] | None = None,
        *,
        max_total_tokens: int = 100_000,
        context: dict[str, Any] | None = None,
        custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
        run_id: str | None = None,
        consensus_threshold: float = 0.66,
        include_verifier: bool = True,
    ) -> SwarmTaskResult:
        """Decompose objective into a skill-driven SwarmDAG and execute with token governance."""
        dag = self.decompose_with_skills(
            objective,
            skill_names=skill_names,
            include_verifier=include_verifier,
        )
        return await self.run_swarm(
            dag=dag,
            objective=objective,
            max_total_tokens=max_total_tokens,
            context=context,
            custom_executor=custom_executor,
            run_id=run_id,
            consensus_threshold=consensus_threshold,
        )

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

        target = (
            dag_or_objective
            if dag_or_objective is not None
            else (dag if dag is not None else objective)
        )
        if target is None:
            raise ValueError("Either dag or objective must be provided to run_swarm")

        effective_max_tokens = (
            max_tokens if max_tokens is not None else max_total_tokens
        )
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

        # Look up optional AgentSessionManager and AgentExecutionGraphService
        session_mgr: AgentSessionManager | None = self.context.optional(
            AGENT_SESSION_MANAGER_KEY
        )
        graph_svc: AgentExecutionGraphService | None = self.context.optional(
            AGENT_GRAPH_STORE_KEY
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
        elif graph_svc is not None:
            graph_svc.register_thread(
                node_id=actual_run_id,
                role="swarm_coordinator",
                task=objective,
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
                logger.info(
                    "Executing swarm wave",
                    run_id=actual_run_id,
                    wave=wave_idx,
                    nodes=wave_node_ids,
                )
                wave_start_time = time.time()
                wave_tokens_before = governor.tokens_consumed

                async def _execute_single_node(
                    node_id: str,
                ) -> tuple[str, Any, int, str | None, float, float]:
                    node = dag.nodes[node_id]
                    node.status = "running"
                    child_sid = f"{actual_run_id}_{node_id}"
                    n_start = time.time()

                    # Create child session in hierarchical session manager or graph service
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
                    elif graph_svc is not None:
                        graph_svc.register_thread(
                            node_id=child_sid,
                            role=node.role,
                            task=node.task,
                            parent_id=actual_run_id,
                            metadata={
                                "node_id": node.id,
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
                        elif graph_svc is not None:
                            graph_svc.update_thread_status(
                                node_id=child_sid,
                                status="failed",
                                completed=True,
                            )
                            graph_svc.close_spawn_edge(
                                parent_id=actual_run_id,
                                child_id=child_sid,
                                status=ThreadSpawnStatus.FAILED,
                            )
                        return node_id, None, 0, node.error, n_start, n_end

                    # Collect upstream context from dependencies with optional compaction
                    context_optimizer: AgentContextOptimizer | None = (
                        self.context.optional(AGENT_CONTEXT_OPTIMIZER_KEY)
                    )

                    upstream_ctx: dict[str, Any] = {}
                    for dep in node.dependencies:
                        if dep in accumulated_results:
                            raw_val = accumulated_results[dep]
                            if context_optimizer is not None:
                                upstream_ctx[dep] = (
                                    context_optimizer.compact_observation(
                                        f"upstream_{dep}", raw_val
                                    )
                                )
                            else:
                                upstream_ctx[dep] = raw_val

                    # Prepare prompt with upstream context
                    enriched_prompt = node.task
                    if upstream_ctx:
                        upstream_summary = "\n".join(
                            f"- Upstream {k}: {v}" for k, v in upstream_ctx.items()
                        )
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
                                node.status = (
                                    "completed"
                                    if agent_res.status == "completed"
                                    else "failed"
                                )
                            else:
                                node.result = f"Completed {node.role} task: {node.task}"
                                node.status = "completed"

                        node.tokens_used = tokens_used
                        governor.record_usage(node.id, tokens_used)
                        n_end = time.time()

                        # Update child session in session manager or graph service
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
                        elif graph_svc is not None:
                            st = "completed" if node.status == "completed" else "failed"
                            edge_st = (
                                ThreadSpawnStatus.COMPLETED
                                if st == "completed"
                                else ThreadSpawnStatus.FAILED
                            )
                            graph_svc.update_thread_status(
                                node_id=child_sid,
                                status=st,
                                tokens_used=tokens_used,
                                completed=True,
                            )
                            graph_svc.close_spawn_edge(
                                parent_id=actual_run_id,
                                child_id=child_sid,
                                status=edge_st,
                            )

                        return node_id, node.result, tokens_used, None, n_start, n_end
                    except Exception as e:
                        node.status = "failed"
                        node.error = str(e)
                        n_end = time.time()
                        logger.error(
                            "Swarm node execution failed",
                            run_id=actual_run_id,
                            node=node_id,
                            error=str(e),
                        )
                        if session_mgr is not None:
                            await session_mgr.fail_session(child_sid, str(e))
                        elif graph_svc is not None:
                            graph_svc.update_thread_status(
                                node_id=child_sid,
                                status="failed",
                                completed=True,
                            )
                            graph_svc.close_spawn_edge(
                                parent_id=actual_run_id,
                                child_id=child_sid,
                                status=ThreadSpawnStatus.FAILED,
                            )
                        return node_id, None, tokens_used, str(e), n_start, n_end

                # Execute wave concurrently
                results = await asyncio.gather(
                    *(_execute_single_node(nid) for nid in wave_node_ids)
                )
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
            elif graph_svc is not None:
                st = "completed" if all_success else "failed"
                graph_svc.update_thread_status(
                    node_id=actual_run_id,
                    status=st,
                    tokens_used=governor.tokens_consumed,
                    completed=True,
                )

            self._emit(
                EventType.AGENT_TASK_COMPLETED
                if all_success
                else EventType.AGENT_TASK_FAILED,
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

    async def get_run_async(
        self, run_id: str
    ) -> SwarmTaskResult | dict[str, Any] | None:
        """Fetch a completed swarm run by ID, falling back to persistent session store."""
        if run_id in self._run_history:
            return self._run_history[run_id]

        session_mgr: AgentSessionManager | None = self.context.optional(
            AGENT_SESSION_MANAGER_KEY
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
        session_mgr: AgentSessionManager | None = self.context.optional(
            AGENT_SESSION_MANAGER_KEY
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
        results: list[dict[str, Any]] = [
            r.to_dict() for r in self._run_history.values()
        ]
        seen_ids = {r["run_id"] for r in results if "run_id" in r}

        session_mgr: AgentSessionManager | None = self.context.optional(
            AGENT_SESSION_MANAGER_KEY
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
        last_run = (
            list(self._run_history.values())[-1].to_dict()
            if self._run_history
            else None
        )
        return {
            "status": "ready",
            "active_swarms": len(self._active_runs),
            "total_runs": len(self._run_history),
            "last_run": last_run,
            "coordinator_available": True,
        }


__all__ = [
    "SWARM_COORDINATOR_KEY",
    "SwarmCoordinator",
]
