# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.0.0",
#     "pydantic>=2.0.0",
# ]
# ///
"""Headroom Context Optimizer CLI Runner.

Provides fast, non-interactive context optimization, string salvage,
CCR turn deduplication, and cache drift detection.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import click

# Enforce UTF-8 streams (Rule 23 & 50)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add workspace src to sys.path
workspace_root = Path(__file__).resolve().parents[4]
if str(workspace_root / "src") not in sys.path:
    sys.path.insert(0, str(workspace_root / "src"))
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from harness.services.headroom_optimizer import (
    HEADROOM_CONTEXT_OPTIMIZER_KEY,
    HeadroomContextOptimizerService,
)


def local_string_salvage(raw: str) -> str:
    """Execute 3-stage local string salvage before paying LLM reprompt tokens."""
    text = raw.strip()

    # Stage 1: Strip markdown code fences
    fence_pattern = re.compile(r"^```(?:json|python|text)?\s*([\s\S]*?)\s*```$", re.IGNORECASE)
    match = fence_pattern.search(text)
    if match:
        text = match.group(1).strip()

    # Stage 2: Slice outermost JSON object or array
    start_brace = text.find("{")
    start_bracket = text.find("[")

    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = text.rfind("}")
        if end_brace != -1:
            text = text[start_brace : end_brace + 1]
    elif start_bracket != -1:
        end_bracket = text.rfind("]")
        if end_bracket != -1:
            text = text[start_bracket : end_bracket + 1]

    # Stage 3: Remove trailing commas before closing braces/brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


@click.group()
def cli() -> None:
    """Headroom Context Optimizer CLI runner."""
    pass


@cli.command("salvage")
@click.argument("input_text", type=str)
def salvage_cmd(input_text: str) -> None:
    """Run 3-stage local string salvage on malformed model outputs."""
    repaired = local_string_salvage(input_text)
    click.echo(repaired)


@cli.command("compress")
@click.argument("content", type=str)
@click.option("--type", "content_type", default=None, help="Content type hint (json, code, log, diff, search, text)")
@click.option("--ratio", default=0.6, type=float, help="Target compression ratio")
def compress_cmd(content: str, content_type: str | None, ratio: float) -> None:
    """Compress arbitrary string payload."""
    from plugins.memory_and_epistemics.headroom_context_optimizer.main import plugin
    res = plugin.engine.compress_content(content, content_type=content_type, target_ratio=ratio)
    click.echo(json.dumps({
        "status": res.status,
        "original_tokens": res.original_tokens,
        "compressed_tokens": res.compressed_tokens,
        "savings_ratio": res.savings_ratio,
        "strategy": res.strategy,
        "compressed_text": res.compressed_text,
    }, indent=2))


@cli.command("cache-check")
@click.argument("system_prompt", type=str)
def cache_check_cmd(system_prompt: str) -> None:
    """Inspect system prompt for prompt cache prefix drift."""
    from plugins.memory_and_epistemics.headroom_context_optimizer.main import plugin
    res = plugin.engine.detect_cache_drift(system_prompt)
    click.echo(json.dumps({
        "status": res.status,
        "is_cache_stable": res.is_cache_stable,
        "volatile_items": res.volatile_items,
        "recommendations": res.recommendations,
    }, indent=2))


if __name__ == "__main__":
    cli()
