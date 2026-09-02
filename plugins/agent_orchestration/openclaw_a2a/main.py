"""OpenClaw A2A Plugin — A2A v1.0 Agent-to-Agent protocol adapter for multi-agent swarm federation."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.openclaw_bridge import (
    OPENCLAW_A2A_KEY,
    OpenClawA2AService,
    OpenClawA2ATask,
)

logger = structlog.get_logger(__name__)


class OpenClawA2AServiceImpl(OpenClawA2AService):
    """In-memory and remote federation implementation of A2A v1.0 protocol."""

    def __init__(self) -> None:
        self._tasks: dict[str, OpenClawA2ATask] = {}
        self._agent_registry: dict[str, dict[str, Any]] = {
            "harness_lead": {
                "archetype": "orchestrator",
                "capabilities": ["task_planning", "tool_repair", "code_review"],
                "protocol_version": "1.0.0",
            },
            "openclaw_worker": {
                "archetype": "executor",
                "capabilities": ["bash", "browser", "computer_use", "channel_dispatch"],
                "protocol_version": "1.0.0",
            },
        }

    async def send_task(
        self,
        recipient_agent: str,
        task_payload: dict[str, Any],
        sender_agent: str = "harness_lead",
    ) -> OpenClawA2ATask:
        """Dispatches an asynchronous task to a remote or local A2A agent."""
        task_id = f"a2a_{uuid.uuid4().hex[:12]}"
        task = OpenClawA2ATask(
            task_id=task_id,
            sender_agent=sender_agent,
            recipient_agent=recipient_agent,
            task_payload=task_payload,
            status="pending",
            created_at=time.time(),
        )
        self._tasks[task_id] = task
        logger.info(
            "openclaw_a2a_task_dispatched",
            task_id=task_id,
            sender=sender_agent,
            recipient=recipient_agent,
        )
        return task

    async def poll_task(self, task_id: str) -> OpenClawA2ATask:
        """Polls the execution status and observation of an A2A task."""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"A2A Task with id '{task_id}' not found.")
        return task

    async def complete_task(
        self,
        task_id: str,
        observation: dict[str, Any],
        tokens_used: int = 0,
    ) -> OpenClawA2ATask:
        """Marks a local or federated task as completed with observation payload."""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"A2A Task with id '{task_id}' not found.")

        completed_task = OpenClawA2ATask(
            task_id=task.task_id,
            sender_agent=task.sender_agent,
            recipient_agent=task.recipient_agent,
            task_payload=task.task_payload,
            status="completed",
            observation=observation,
            tokens_used=tokens_used,
            created_at=task.created_at,
            completed_at=time.time(),
        )
        self._tasks[task_id] = completed_task
        logger.info("openclaw_a2a_task_completed", task_id=task_id, tokens=tokens_used)
        return completed_task

    def resolve_agent_capabilities(self, agent_id: str) -> dict[str, Any]:
        """Resolves registered capabilities and tool archetypes for an agent."""
        if agent_id in self._agent_registry:
            return self._agent_registry[agent_id]
        return {
            "archetype": "general_agent",
            "capabilities": ["generic_tool_calling"],
            "protocol_version": "1.0.0",
        }


class OpenClawA2APlugin(HarnessPlugin):
    """Harness plugin registering OpenClaw A2A protocol federation service and tools."""

    name = "plugin.openclaw_a2a"
    version = "1.0.0"
    description = "A2A v1.0 Agent-to-Agent protocol federation adapter"

    def __init__(self) -> None:
        super().__init__()
        self.service = OpenClawA2AServiceImpl()

    def register_services(self, context: ServiceContext) -> None:
        """Register the typed OpenClawA2AService into the IoC container."""
        context.provide(OPENCLAW_A2A_KEY, self.service)
        logger.info("openclaw_a2a_service_registered")

    async def openclaw_a2a_send_task(
        self,
        recipient_agent: str,
        task_payload: dict[str, Any],
        sender_agent: str = "harness_lead",
    ) -> dict[str, Any]:
        """Tool handler for openclaw_a2a_send_task."""
        task = await self.service.send_task(recipient_agent, task_payload, sender_agent)
        return task.to_dict()

    async def openclaw_a2a_poll_task(self, task_id: str) -> dict[str, Any]:
        """Tool handler for openclaw_a2a_poll_task."""
        task = await self.service.poll_task(task_id)
        return task.to_dict()

    async def openclaw_a2a_complete_task(
        self,
        task_id: str,
        observation: dict[str, Any],
        tokens_used: int = 0,
    ) -> dict[str, Any]:
        """Tool handler for openclaw_a2a_complete_task."""
        task = await self.service.complete_task(task_id, observation, tokens_used)
        return task.to_dict()

    async def openclaw_a2a_resolve_capabilities(self, agent_id: str) -> dict[str, Any]:
        """Tool handler for openclaw_a2a_resolve_capabilities."""
        return self.service.resolve_agent_capabilities(agent_id)
