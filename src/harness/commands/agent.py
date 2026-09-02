"""Agent commands — pure async entry points for agent task execution."""

from __future__ import annotations

from typing import Any

from harness.services.llm import LiteLLMService, LLMResponse


class FallbackLLM(LiteLLMService):
    """Stub LLM returned when no real provider is configured.

    Gives the agent a coherent response so the harness is immediately
    runnable without an API key for demos and smoke tests.
    """

    async def complete(self, messages: Any, **kwargs: Any) -> LLMResponse:
        return LLMResponse(
            content="FINAL ANSWER: Task completed successfully via Harness fallback agent."
        )

    async def stream(self, messages: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        yield "FINAL ANSWER: Task completed successfully via Harness fallback agent."


async def run_agent(
    task: str,
    max_steps: int = 10,
    fallback_llm: Any | None = None,
) -> Any:
    """Execute an autonomous agent task inside a short-lived runtime.

    Args:
        task: The natural-language task description for the agent.
        max_steps: Maximum thought/action steps before giving up.
        fallback_llm: Optional LLM instance to use when no LLM provider is
            registered. Defaults to :class:`FallbackLLM`.

    Returns:
        The ``TaskResult`` from ``HarnessRuntime.run_task()``.
    """
    from harness.kernel.runtime import HarnessRuntime

    llm = fallback_llm or FallbackLLM()

    async with HarnessRuntime.create(db_path=":memory:", fallback_llm=llm) as runtime:
        return await runtime.run_task(task, max_steps=max_steps)


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.group("agent")
def agent_group() -> None:
    """Run and manage autonomous agent loops."""


@agent_group.command("run")
@click.argument("task")
@click.option("--max-steps", default=10, help="Maximum thought/action steps")
def agent_run(task: str, max_steps: int) -> None:
    """Execute an autonomous task using the active agent loop."""
    click.echo(f"🤖 Starting agent task: {task}")
    result = _run_async(run_agent(task, max_steps=max_steps))

    click.echo(f"Status: {result.status}")
    click.echo(f"Steps:  {len(result.steps)}")
    click.echo(f"Result: {result.final_answer}")


__all__ = [
    "FallbackLLM",
    "agent_group",
    "run_agent",
]
