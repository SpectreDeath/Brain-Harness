"""Headless Click CLI commands for Gemini & Vercel Streaming Chatbot.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.gemini_vercel import (
    AuditReportData,
    GeminiVercelStreamingService,
    ScaffoldConfigData,
    ScaffoldResultData,
    StreamSimulationData,
)


def get_gemini_vercel_streaming_service() -> GeminiVercelStreamingService:
    """Retrieve or bootstrap the GeminiVercelStreaming service singleton."""
    try:
        from plugins.integration_and_io.gemini_vercel_streaming_chatbot.main import (
            plugin,
        )
        return plugin
    except Exception:
        # Fallback: bootstrap engine directly
        _ws_root = Path(__file__).resolve().parents[3]
        _skill_scripts = (
            _ws_root / ".agents" / "skills" / "gemini-vercel-streaming-chatbot" / "scripts"
        )
        if str(_skill_scripts) not in sys.path:
            sys.path.insert(0, str(_skill_scripts))

        from plugins.integration_and_io.gemini_vercel_streaming_chatbot.main import (
            GeminiVercelStreamingPlugin,
        )

        return GeminiVercelStreamingPlugin()


@click.group("gemini-vercel")
def gemini_vercel_group() -> None:
    """Gemini & Vercel Streaming Chatbot CLI — Plain-text chunk streaming & edge architecture."""


@gemini_vercel_group.command("inspect")
@click.argument("target", type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def inspect_cmd(target: str, json_output: bool) -> None:
    """Run static analysis against Johnson Samuel's 5 production streaming rubrics.

    TARGET can be a path to a serverless/client file or raw code string.
    """
    target_p = Path(target)
    if target_p.exists() and target_p.is_file():
        source_code = target_p.read_text(encoding="utf-8")
        file_label = str(target_p)
    else:
        source_code = target
        file_label = "<cli-input>"

    svc = get_gemini_vercel_streaming_service()
    report: AuditReportData = svc.audit_code(source_code, file_path=file_label)

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
        return

    click.echo(f"Gemini & Vercel Streaming Audit Scorecard for '{report.target}':")
    click.echo(f"  Overall Status: {'PASSED' if report.passed else 'FAILED'}")
    click.echo("  Checks:")
    for c in report.checks:
        status_tag = "PASS" if c.passed else "FAIL"
        line_tag = f" (line {c.line_number})" if c.line_number else ""
        click.echo(f"    [{status_tag}] {c.name}{line_tag}: {c.message}")

    if report.metrics:
        click.echo("  Metrics:")
        for k, v in report.metrics.items():
            click.echo(f"    - {k}: {v}")


@gemini_vercel_group.command("scaffold")
@click.option("--name", "-n", default="my_streaming_chatbot", help="Application name identifier")
@click.option(
    "--framework",
    "-f",
    default="react",
    type=click.Choice(["react", "solid", "vanilla"], case_sensitive=False),
    help="Frontend framework",
)
@click.option(
    "--language",
    "-l",
    default="javascript",
    type=click.Choice(["javascript", "typescript"], case_sensitive=False),
    help="Programming language",
)
@click.option(
    "--model",
    "-m",
    default="gemini-2.5-flash",
    help="Gemini model identifier",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    help="Target directory to write files",
)
@click.option(
    "--write/--no-write",
    "write_files",
    default=False,
    help="Write files to disk or display manifest",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def scaffold_cmd(
    name: str,
    framework: str,
    language: str,
    model: str,
    output_dir: str,
    write_files: bool,
    json_output: bool,
) -> None:
    """Scaffold a 3-tier production Gemini & Vercel streaming application."""
    svc = get_gemini_vercel_streaming_service()
    cfg = ScaffoldConfigData(
        app_name=name,
        framework=framework,
        language=language,
        model=model,
        output_dir=output_dir,
    )
    result: ScaffoldResultData = svc.scaffold_app(cfg)

    if write_files:
        dest_dir = Path(output_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in result.files.items():
            out_file = dest_dir / fname
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
        result.manifest["written_to"] = str(dest_dir.resolve())

    if json_output:
        click.echo(_json.dumps(result.model_dump(), indent=2))
        return

    click.echo(f"Gemini & Vercel Application Scaffolding for '{name}':")
    click.echo(f"  Framework:         {framework.upper()}")
    click.echo(f"  Language:          {language.upper()}")
    click.echo(f"  Model:             {model}")
    click.echo(f"  Files Generated:   {len(result.files)}")
    for fname in result.files:
        click.echo(f"    + {fname}")
    if write_files:
        click.echo(f"  Destination:       {Path(output_dir).resolve()}")
    else:
        click.echo("  Status:            Preview (Use --write to output files)")


@gemini_vercel_group.command("verify")
@click.option("--prompt", "-p", default="Explain streaming HTTP chunking in simple terms", help="Prompt to simulate streaming")
@click.option("--chunks", "-c", default=5, help="Number of chunks to simulate")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def verify_cmd(prompt: str, chunks: int, json_output: bool) -> None:
    """Simulate unbuffered plain-text chunk streaming with latency metrics."""
    svc = get_gemini_vercel_streaming_service()
    sim_data: StreamSimulationData = svc.simulate_stream(prompt, chunks_count=chunks)

    if json_output:
        click.echo(_json.dumps(sim_data.model_dump(), indent=2))
        return

    click.echo("Unbuffered Plain-Text Chunk Streaming Simulation:")
    click.echo(f"  Prompt:          {sim_data.prompt}")
    click.echo(f"  Total Chunks:    {sim_data.total_chunks}")
    click.echo(f"  Duration:        {sim_data.duration_ms} ms")
    click.echo("  Chunk Stream:")
    for idx, ch in enumerate(sim_data.chunks, 1):
        click.echo(f"    [Chunk {idx:02d}]: {ch!r}")
    click.echo(f"  Reconstructed:   {sim_data.reconstructed_text}")


@gemini_vercel_group.command("brief")
@click.option("--output", "-o", default=None, help="Output file path for HTML brief")
def brief_cmd(output: str | None) -> None:
    """Generate interactive standalone HTML visual brief."""
    svc = get_gemini_vercel_streaming_service()
    brief_path = svc.generate_visual_brief(output)
    click.echo(f"Gemini & Vercel Streaming Visual Brief generated: {brief_path}")
