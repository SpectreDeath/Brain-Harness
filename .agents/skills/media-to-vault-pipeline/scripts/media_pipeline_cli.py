#!/usr/bin/env python3
"""Media to Vault Pipeline CLI — thin headless adapter for multimedia distillation & vault commit.

Deepened architecture:
- Thin CLI adapter delegating to media_pipeline_engine.MediaPipelineEngine
- Composite 'run' subcommand executing complete end-to-end workflow in one atomic call
- Retains 100% backward compatibility for granular subcommands (fetch-transcript, distill-seams, verify-isnad, commit-vault, scaffold-skill)
- Default-to-file JSON output via --output (Rule 4)
- UTF-8 standard stream reconfigure on Windows (Rule 23)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import core domain engine and entities
try:
    from media_pipeline_engine import (
        DistillationResult,
        EpistemicClaim,
        IsnadLedger,
        MediaPipelineEngine,
        PipelineExecutionReport,
        ProceduralStep,
        SkillScaffoldResult,
        TranscriptSegment,
        VaultCommitResult,
    )
except ImportError:
    from .media_pipeline_engine import (  # type: ignore
        DistillationResult,
        EpistemicClaim,
        IsnadLedger,
        MediaPipelineEngine,
        PipelineExecutionReport,
        ProceduralStep,
        SkillScaffoldResult,
        TranscriptSegment,
        VaultCommitResult,
    )


def write_output(data: Any, output_path: str | Path) -> None:
    """Writes JSON payload to output file destination (Rule 4)."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Success! Output written to: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Media to Vault Pipeline CLI — multimedia transcript distillation & vault commit."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run (composite end-to-end execution)
    p_run = subparsers.add_parser("run", help="Execute complete end-to-end media-to-vault pipeline in one step.")
    p_run.add_argument("--source", required=True, help="YouTube URL or local transcript file path.")
    p_run.add_argument("--ki-id", required=True, help="Unique Knowledge Item ID (e.g., ki_video_01).")
    p_run.add_argument("--skill-name", required=True, help="Target skill name to scaffold.")
    p_run.add_argument("--vault-root", default=None, help="Optional custom Knowledge Vault root path.")
    p_run.add_argument("--skills-root", default=None, help="Optional custom agent skills root path.")
    p_run.add_argument("--output", required=True, help="Output JSON execution report destination.")

    # Subcommand: fetch-transcript
    p_fetch = subparsers.add_parser("fetch-transcript", help="Fetch spoken transcript from URL or file.")
    p_fetch.add_argument("--source", required=True, help="YouTube URL or local transcript file path.")
    p_fetch.add_argument("--output", required=True, help="Output JSON transcript destination.")

    # Subcommand: distill-seams
    p_distill = subparsers.add_parser("distill-seams", help="Apply dual-lens cognitive distillation seam (Rule 41).")
    p_distill.add_argument("--transcript", required=True, help="Input JSON transcript file path.")
    p_distill.add_argument("--output", required=True, help="Output JSON distilled seams destination.")

    # Subcommand: verify-isnad
    p_verify = subparsers.add_parser("verify-isnad", help="Verify isnad provenance for extracted claims.")
    p_verify.add_argument("--distilled", required=True, help="Input JSON distilled seams file path.")
    p_verify.add_argument("--output", required=True, help="Output JSON isnad verification ledger.")

    # Subcommand: commit-vault
    p_commit = subparsers.add_parser("commit-vault", help="Commit canonical dual-file item to Knowledge Vault (Rule 40).")
    p_commit.add_argument("--distilled", required=True, help="Input JSON distilled seams file path.")
    p_commit.add_argument("--ki-id", required=True, help="Unique Knowledge Item ID (e.g., ki_video_01).")
    p_commit.add_argument("--vault-root", default=None, help="Root directory for Knowledge Vault.")
    p_commit.add_argument("--output", required=True, help="Output JSON commit report destination.")

    # Subcommand: scaffold-skill
    p_scaffold = subparsers.add_parser("scaffold-skill", help="Scaffold production agent skill from distilled steps.")
    p_scaffold.add_argument("--distilled", required=True, help="Input JSON distilled seams file path.")
    p_scaffold.add_argument("--skill-name", required=True, help="Target skill name.")
    p_scaffold.add_argument("--skills-root", default=None, help="Root directory for agent skills.")
    p_scaffold.add_argument("--output", required=True, help="Output JSON scaffolding report destination.")

    args = parser.parse_args()
    engine = MediaPipelineEngine()

    try:
        if args.command == "run":
            report = engine.execute_pipeline(
                source=args.source,
                ki_id=args.ki_id,
                skill_name=args.skill_name,
                vault_root=args.vault_root,
                skills_root=args.skills_root,
            )
            write_output(report.to_dict(), args.output)

        elif args.command == "fetch-transcript":
            res_fetch = engine.fetch_transcript(args.source)
            write_output(res_fetch, args.output)

        elif args.command == "distill-seams":
            with open(args.transcript, "r", encoding="utf-8") as f:
                t_data = json.load(f)
            res_distill = engine.distill_seams(t_data)
            write_output(res_distill, args.output)

        elif args.command == "verify-isnad":
            with open(args.distilled, "r", encoding="utf-8") as f:
                d_data = json.load(f)
            res_verify = engine.verify_isnad(d_data)
            write_output(res_verify, args.output)
            if not res_verify["all_verified"]:
                sys.exit(1)

        elif args.command == "commit-vault":
            with open(args.distilled, "r", encoding="utf-8") as f:
                d_data = json.load(f)
            res_commit = engine.commit_vault(d_data, args.ki_id, args.vault_root)
            write_output(res_commit, args.output)

        elif args.command == "scaffold-skill":
            with open(args.distilled, "r", encoding="utf-8") as f:
                d_data = json.load(f)
            res_scaffold = engine.scaffold_skill(d_data, args.skill_name, args.skills_root)
            write_output(res_scaffold, args.output)

        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error executing media_pipeline_cli {args.command}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
