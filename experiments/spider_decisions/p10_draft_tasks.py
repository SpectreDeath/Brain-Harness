"""Phase 10.2: Draft 20 developer task intents and expected skills for skill-routing evaluation."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import WORKSPACE, bootstrap, write_json, write_md  # noqa: E402

bootstrap()

DRAFT_TASKS: tuple[tuple[str, str, str], ...] = (
    (
        "audit this repository's architecture and synthesize KIs",
        "deep-repo-auditor",
        "4-axis repo audit & KI synthesis",
    ),
    (
        "find the next research project to learn using ontology queries",
        "ontology-spider",
        "vault/repo ontology queries & learning target discovery",
    ),
    (
        "reverse engineer this compiled .pyc bytecode and extract semantic signatures",
        "rea-reverse-engineering",
        "REA toolkit binary/bytecode signature extraction",
    ),
    (
        "verify unbroken chain-of-custody isnad provenance before committing to memory",
        "epistemic-isnad-audit",
        "epistemic provenance chain validation",
    ),
    (
        "run automated GenAI red-teaming and jailbreak vulnerability scorecards with PyRIT",
        "ai-red-teaming-architect",
        "PyRIT GenAI red-teaming & scorecards",
    ),
    (
        "execute Google Mantis security review and taint analysis across commit history",
        "mantis-security-review",
        "VCS commit history security & AST taint review",
    ),
    (
        "decompose a monolithic Python module into slotted subpackages under 200 lines",
        "monolith-decomposition-engine",
        "slotted domain decomposition <= 200 lines",
    ),
    (
        "compress LLM prompt context, deduplicate tool observations, and prevent cache drift",
        "headroom-context-optimizer",
        "Headroom observation compression & cache alignment",
    ),
    (
        "apply compiler-style 3-pass deterministic prompt pruning and expired tool elimination",
        "prompt-pruning-architect",
        "3-pass deterministic prompt pruning",
    ),
    (
        "deliberate strategic actions across a multi-persona swarm using Borda and consensus voting",
        "game-theoretic-swarm-deliberator",
        "multi-persona payoff matrix & Borda/consensus voting",
    ),
    (
        "govern working memory retention with Ebbinghaus forgetting curves and decay multipliers",
        "ebbinghaus-memory-governor",
        "Ebbinghaus decay curves & stability reinforcement",
    ),
    (
        "architect an uncertainty-aware RAG guard with semantic gating and logit entropy abstention",
        "uncertainty-aware-ai-architect",
        "3-layer uncertainty & logit entropy abstention",
    ),
    (
        "optimize high-throughput TopK selection and sparse attention workloads on GPU",
        "deepselect-topk-optimizer",
        "DeepSeek Sparse Attention / TopK CUDA optimization",
    ),
    (
        "extract spoken dialogue and timed captions from a YouTube video URL",
        "youtube-transcript-fetcher",
        "YouTube transcript & timed caption extraction",
    ),
    (
        "detect metric anomalies and ARIMA_PLUS causal attribution inside BigQuery",
        "bigquery-augmented-analytics",
        "BigQuery TVF anomaly & counterfactual attribution",
    ),
    (
        "simulate a natural disaster on 3D geospatial map tiles with WebGL building collapse",
        "geospatial-disaster-simulation",
        "Mercator DEM tiles & Three.js WebGL collapse physics",
    ),
    (
        "build a reactive Gradio web interface with isolated session state and queued streaming",
        "gradio-app-architect",
        "Gradio Blocks reactive UI & gr.State isolation",
    ),
    (
        "shift security left with git pre-commit hooks, DevSkim SAST, and Gitleaks secret scanning",
        "pre-commit-security-guard",
        "pre-commit SAST + Gitleaks secret scanning",
    ),
    (
        "mine operational skills and plan evolutions from IDE brain artifact stores and transcripts",
        "brain-artifact-miner",
        "brain artifact & trajectory skill distillation",
    ),
    (
        "refine an agent harness using contrastive Propose-Probe-Compose task-level recursion",
        "recursive-harness-refiner",
        "contrastive task-level harness recursion",
    ),
)


def main() -> int:
    skills_root = WORKSPACE / ".agents" / "skills"
    tasks: list[dict[str, Any]] = []
    for idx, (intent, expected_skill, domain_note) in enumerate(DRAFT_TASKS, start=1):
        skill_dir = skills_root / expected_skill
        assert skill_dir.is_dir(), f"Expected skill directory missing: {skill_dir}"
        tasks.append(
            {
                "id": idx,
                "task_intent": intent,
                "expected_skill": expected_skill,
                "domain_note": domain_note,
            }
        )

    json_path = write_json(10, "task_set_draft", tasks)

    md_lines = [
        "# Phase 10 — Skill Routing Task Set Review Sheet (20 Intents)",
        "",
        "Review each `expected_skill` under `.agents/skills/` and edit `APPROVED_SKILL` if you want to override any row (or reply `proceed`).",
        "",
        "| # | task_intent | expected_skill | domain_note | APPROVED_SKILL |",
        "|---:|---|---|---|---|",
    ]
    for t in tasks:
        md_lines.append(
            f"| {t['id']} | {t['task_intent']} | `{t['expected_skill']}` "
            f"| {t['domain_note']} | `{t['expected_skill']}` |"
        )
    md_lines.append("")
    md_path = write_md(10, "task_set_sheet", "\n".join(md_lines))

    print(f"Verified all {len(tasks)} expected skill dirs under {skills_root}")
    print(f"Draft JSON: {json_path}")
    print(f"Review sheet: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
