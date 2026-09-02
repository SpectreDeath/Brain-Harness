"""Runtime commands — pure async entry points for harness lifecycle and declarative configuration."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

import structlog

if TYPE_CHECKING:
    from harness.kernel.reconciler import HarnessConfigTree
    from harness.kernel.runtime import HarnessRuntime

logger = structlog.get_logger()


@dataclass
class RuntimeRunResult:
    """Outcome of bootstrapping the Harness runtime."""

    runtime: HarnessRuntime
    summary: dict[str, str] = field(default_factory=dict)
    enabled_count: int = 0
    services_count: int = 0
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "enabled_count": self.enabled_count,
            "services_count": self.services_count,
            "status": self.status,
        }


@dataclass
class ConfigValidationResult:
    """Outcome of validating a declarative configuration file."""

    config_path: Path
    valid: bool
    version: str = ""
    plugins_count: int = 0
    error_message: str | None = None
    config_tree: HarnessConfigTree | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_path": str(self.config_path),
            "valid": self.valid,
            "version": self.version,
            "plugins_count": self.plugins_count,
            "error_message": self.error_message,
        }


@dataclass
class ConfigApplyResult:
    """Outcome of applying and reconciling a declarative configuration file."""

    config_path: Path
    reconciled: bool
    plugins_enabled: list[str] = field(default_factory=list)
    status: str = "applied"

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_path": str(self.config_path),
            "reconciled": self.reconciled,
            "plugins_enabled": self.plugins_enabled,
            "status": self.status,
        }


async def run_harness_cmd(
    event_log_path: Path | str | None = None,
    db_path: str = ":memory:",
    blocking: bool = False,
    shutdown_event: asyncio.Event | None = None,
) -> RuntimeRunResult:
    """Start the Harness runtime with built-in and discovered plugins.

    Args:
        event_log_path: Optional path to append-only event log file.
        db_path: SQLite database path.
        blocking: If True, waits until shutdown_event is triggered.
        shutdown_event: Optional event to signal shutdown when blocking.

    Returns:
        RuntimeRunResult with active runtime and status metrics.
    """
    from harness.kernel.runtime import HarnessRuntime

    log_p = Path(event_log_path).resolve() if event_log_path else None
    if log_p and not log_p.parent.exists():
        log_p = None

    runtime = HarnessRuntime.create(event_log_path=log_p, db_path=db_path)
    await runtime.start()

    summary = runtime.summary()
    enabled_count = sum(1 for s in summary.values() if s == "enabled")
    services_count = len(runtime.context.list_services())

    result = RuntimeRunResult(
        runtime=runtime,
        summary=summary,
        enabled_count=enabled_count,
        services_count=services_count,
        status="running",
    )

    if blocking:
        if shutdown_event:
            await shutdown_event.wait()
        else:
            try:
                while True:
                    await asyncio.sleep(1)
            except (asyncio.CancelledError, KeyboardInterrupt):
                pass
        await runtime.stop()
        result.status = "stopped"

    return result


@asynccontextmanager
async def start_harness(
    event_log_path: Path | str | None = None,
    db_path: str = ":memory:",
) -> AsyncIterator[HarnessRuntime]:
    """Async context manager providing a started HarnessRuntime with auto-cleanup."""
    from harness.kernel.runtime import HarnessRuntime

    log_p = Path(event_log_path).resolve() if event_log_path else None
    runtime = HarnessRuntime.create(event_log_path=log_p, db_path=db_path)
    await runtime.start()
    try:
        yield runtime
    finally:
        await runtime.stop()


def validate_config_cmd(config_path: Path | str) -> ConfigValidationResult:
    """Validate the syntax and Pydantic schema of a declarative configuration file."""
    from harness.kernel.reconciler import HarnessConfigTree

    p = Path(config_path).resolve()
    if not p.exists():
        return ConfigValidationResult(
            config_path=p,
            valid=False,
            error_message=f"File not found: {p}",
        )

    text = p.read_text(encoding="utf-8")
    try:
        try:
            import yaml
            data = yaml.safe_load(text)
        except ImportError:
            data = json.loads(text)

        tree = HarnessConfigTree.model_validate(data)
        return ConfigValidationResult(
            config_path=p,
            valid=True,
            version=tree.version,
            plugins_count=len(tree.plugins),
            config_tree=tree,
        )
    except Exception as e:
        return ConfigValidationResult(
            config_path=p,
            valid=False,
            error_message=str(e),
        )


async def apply_config_cmd(config_path: Path | str) -> ConfigApplyResult:
    """Apply and reconcile a declarative configuration file against Harness."""
    from harness.kernel.runtime import HarnessRuntime

    p = Path(config_path).resolve()
    val_res = validate_config_cmd(p)
    if not val_res.valid:
        raise ValueError(f"Invalid configuration file: {val_res.error_message}")

    runtime = HarnessRuntime.from_config(p)
    await runtime.start()
    enabled = [name for name, state in runtime.summary().items() if state == "enabled"]
    await runtime.stop()

    return ConfigApplyResult(
        config_path=p,
        reconciled=True,
        plugins_enabled=enabled,
        status="applied",
    )


# --- Click CLI adapters ---
import sys
import click
from harness.commands._utils import _run_async


@click.command("run")
def run_cli() -> None:
    """Start the harness (interactive mode)."""
    click.echo("🔧 Harness v0.1.0")
    click.echo("━" * 40)

    async def _run() -> None:
        event_log = Path(".harness") / "events.jsonl"
        click.echo("⟳ Loading built-in and ecosystem plugins...")

        res = await run_harness_cmd(
            event_log_path=event_log if event_log.parent.exists() else None,
            blocking=False,
        )
        runtime = res.runtime
        click.echo(f"  ✓ {res.enabled_count}/{len(res.summary)} plugins enabled\n")

        for name, state in res.summary.items():
            icon = "✓" if state == "enabled" else "✗"
            click.echo(f"  {icon} {name:<30} [{state}]")

        click.echo(f"\n  Services: {res.services_count}\n")
        click.echo("Harness is running. Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            click.echo("\n⟳ Shutting down...")
            await runtime.stop()
            click.echo("✓ Harness stopped.")

    try:
        _run_async(_run())
    except KeyboardInterrupt:
        pass


@click.command("ui")
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8080, help="Port to listen on")
@click.option("--db", "db_path", default=":memory:", help="SQLite database path (default: :memory:)")
def ui_cli(host: str, port: int, db_path: str) -> None:
    """Launch the real-time web control room dashboard."""
    import uvicorn

    from harness.commands.agent import FallbackLLM
    from harness.kernel.runtime import HarnessRuntime
    from harness.ui.server import create_app

    runtime = HarnessRuntime.create(db_path=db_path, fallback_llm=FallbackLLM())
    _run_async(runtime.start())

    app = create_app(runtime)

    click.echo(f"🚀 Harness Web Dashboard launching at http://{host}:{port} (db: {db_path})")
    uvicorn.run(app, host=host, port=port, log_level="warning")


@click.command("apply")
@click.option("-f", "--file", "config_file", required=True, type=click.Path(exists=True), help="Path to declarative config file (.yaml/.json)")
def apply_cli(config_file: str) -> None:
    """Apply and reconcile a declarative configuration tree against Harness."""

    async def _apply() -> None:
        p = Path(config_file).resolve()
        click.echo(f"🔄 Reconciling configuration from {p.name}...")
        await apply_config_cmd(p)
        click.echo("✓ Declarative reconciliation applied successfully.")

    _run_async(_apply())


@click.group("config")
def config_group() -> None:
    """Manage and validate declarative configuration trees."""


@config_group.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def config_validate(config_file: str) -> None:
    """Validate syntax and schema of a declarative configuration file."""
    p = Path(config_file).resolve()
    res = validate_config_cmd(p)
    if res.valid:
        click.echo(f"✓ Configuration file {p.name} is valid (version: {res.version}, plugins: {res.plugins_count})")
    else:
        click.echo(f"✗ Configuration validation failed: {res.error_message}", err=True)
        sys.exit(1)


__all__ = [
    "ConfigApplyResult",
    "ConfigValidationResult",
    "RuntimeRunResult",
    "apply_cli",
    "apply_config_cmd",
    "config_group",
    "run_cli",
    "run_harness_cmd",
    "start_harness",
    "ui_cli",
    "validate_config_cmd",
]
