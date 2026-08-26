"""System commands — pure async entry points for runtime introspection."""

from __future__ import annotations

from typing import Any


async def list_services(db_path: str = ":memory:") -> dict[str, str | None]:
    """Return a mapping of service key names to provider plugin names.

    Args:
        db_path: SQLite database path for the runtime (default in-memory).
    """
    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path, auto_load_user_plugins=False) as runtime:
        return runtime.context.list_services()


async def run_introspect(db_path: str = ":memory:") -> dict[str, Any]:
    """Return a full status snapshot of the running system.

    Returns a dict with ``plugins``, ``services``, ``tools``, and the
    Mermaid graph string — ready for display or JSON serialisation.
    """
    from harness.creator.introspection import RuntimeIntrospector
    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(
        db_path=db_path,
        auto_load_user_plugins=True,
        lazy_external_plugins=True,
    ) as runtime:
        introspector = RuntimeIntrospector(
            runtime.context,
            runtime.lifecycle,
            runtime.tools,
        )
        report = introspector.get_status_report()
        graph = introspector.generate_mermaid_graph()
        return {**report, "graph": graph}

