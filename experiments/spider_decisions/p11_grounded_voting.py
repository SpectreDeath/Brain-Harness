"""Phase 11.2-11.4: Compare raw vs KI-verification-grounded CISC swarm voting across 12 disputes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import bootstrap, load_vault_model, write_json, write_md  # noqa: E402

bootstrap()


@dataclass(slots=True, frozen=True)
class DisputeSpec:
    """Slotted immutable specification for a synthetic swarm architecture dispute."""

    dispute_id: int
    topic: str
    correct_choice: str
    choice_kis: dict[str, str | None]
    votes: list[dict[str, Any]]
    category: str  # "flipped_expected", "control", "overwhelming_plurality"


DISPUTES: tuple[DisputeSpec, ...] = (
    DisputeSpec(
        dispute_id=1,
        topic="Vector index asymmetric rescoring budget",
        correct_choice="scann_anisotropic_rescore",
        choice_kis={
            "scann_anisotropic_rescore": "ki_google_research_scann_anisotropic_vq",
            "arrow_mmap_flat_scan": "ki-hf-datasets-arrow-streaming",
            "brute_force_cache": None,
        },
        votes=[
            {"choice": "arrow_mmap_flat_scan", "confidence": 0.94},
            {"choice": "arrow_mmap_flat_scan", "confidence": 0.92},
            {"choice": "scann_anisotropic_rescore", "confidence": 0.88},
            {"choice": "scann_anisotropic_rescore", "confidence": 0.86},
            {"choice": "brute_force_cache", "confidence": 0.45},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=2,
        topic="Uncertainty guard OOD human escalation gate",
        correct_choice="aspest_band_escalation",
        choice_kis={
            "aspest_band_escalation": "ki_google_research_aspest_active_selective_prediction",
            "three_layer_heuristics": "ki_njoku_uncertainty_aware_systems",
        },
        votes=[
            {"choice": "three_layer_heuristics", "confidence": 0.93},
            {"choice": "three_layer_heuristics", "confidence": 0.91},
            {"choice": "three_layer_heuristics", "confidence": 0.89},
            {"choice": "aspest_band_escalation", "confidence": 0.90},
            {"choice": "aspest_band_escalation", "confidence": 0.89},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=3,
        topic="Swarm multi-trace confidence aggregation strategy",
        correct_choice="cisc_softmax_wqd",
        choice_kis={
            "cisc_softmax_wqd": "ki_google_research_cisc_confidence_voting",
            "unweighted_majority": None,
        },
        votes=[
            {"choice": "unweighted_majority", "confidence": 0.92},
            {"choice": "unweighted_majority", "confidence": 0.90},
            {"choice": "unweighted_majority", "confidence": 0.89},
            {"choice": "cisc_softmax_wqd", "confidence": 0.91},
            {"choice": "cisc_softmax_wqd", "confidence": 0.89},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=4,
        topic="Distribution-shift calibration evaluation metric",
        correct_choice="selectivity_sweep_brier",
        choice_kis={
            "selectivity_sweep_brier": "ki_google_research_uq_benchmark_2019_calibration_shift",
            "single_static_threshold": "ki_njoku_uncertainty_aware_systems",
        },
        votes=[
            {"choice": "single_static_threshold", "confidence": 0.95},
            {"choice": "single_static_threshold", "confidence": 0.93},
            {"choice": "selectivity_sweep_brier", "confidence": 0.89},
            {"choice": "selectivity_sweep_brier", "confidence": 0.88},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=5,
        topic="Lazily-staged plugin disk artifact cache policy",
        correct_choice="superblock_dual_lru",
        choice_kis={
            "superblock_dual_lru": "ki_airllm_plus_superblock_prefetch_runtime",
            "xxhash_arrow_stream": "ki-hf-datasets-arrow-streaming",
            "unbounded_cache": None,
        },
        votes=[
            {"choice": "xxhash_arrow_stream", "confidence": 0.92},
            {"choice": "xxhash_arrow_stream", "confidence": 0.91},
            {"choice": "superblock_dual_lru", "confidence": 0.87},
            {"choice": "superblock_dual_lru", "confidence": 0.86},
            {"choice": "unbounded_cache", "confidence": 0.50},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=6,
        topic="MoE layer offloading pinned host buffer bound",
        correct_choice="mxfp4_capped_pinned_2gib",
        choice_kis={
            "mxfp4_capped_pinned_2gib": "ki_airllm_layerwise_streaming_and_moe_expert_offload",
            "unbounded_pin_all": None,
        },
        votes=[
            {"choice": "unbounded_pin_all", "confidence": 0.94},
            {"choice": "unbounded_pin_all", "confidence": 0.92},
            {"choice": "mxfp4_capped_pinned_2gib", "confidence": 0.86},
            {"choice": "mxfp4_capped_pinned_2gib", "confidence": 0.85},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=7,
        topic="Untrusted external plugin filesystem isolation",
        correct_choice="gvisor_sentry_gofer_fd",
        choice_kis={
            "gvisor_sentry_gofer_fd": "ki_google_gvisor_sentry_gofer_sandbox",
            "ad_hoc_runner_env": "ki_self_20260904_scratch_01",
        },
        votes=[
            {"choice": "ad_hoc_runner_env", "confidence": 0.93},
            {"choice": "ad_hoc_runner_env", "confidence": 0.90},
            {"choice": "gvisor_sentry_gofer_fd", "confidence": 0.88},
            {"choice": "gvisor_sentry_gofer_fd", "confidence": 0.85},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=8,
        topic="Latent sequence pretraining bypass prevention",
        correct_choice="vqvae_discrete_latent_plan",
        choice_kis={
            "vqvae_discrete_latent_plan": "ki_google_research_latent_programmer_vqvae",
            "direct_autoregressive": None,
        },
        votes=[
            {"choice": "direct_autoregressive", "confidence": 0.91},
            {"choice": "direct_autoregressive", "confidence": 0.90},
            {"choice": "direct_autoregressive", "confidence": 0.88},
            {"choice": "vqvae_discrete_latent_plan", "confidence": 0.90},
            {"choice": "vqvae_discrete_latent_plan", "confidence": 0.89},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=9,
        topic="Structured long-context attention complexity routing",
        correct_choice="etcmodel_global_local_attn",
        choice_kis={
            "etcmodel_global_local_attn": "ki_google_research_etcmodel_long_structured_attention",
            "complexity_tier_only": "ki-5d-complexity-baseline",
        },
        votes=[
            {"choice": "complexity_tier_only", "confidence": 0.94},
            {"choice": "complexity_tier_only", "confidence": 0.92},
            {"choice": "etcmodel_global_local_attn", "confidence": 0.87},
            {"choice": "etcmodel_global_local_attn", "confidence": 0.86},
        ],
        category="flipped_expected",
    ),
    DisputeSpec(
        dispute_id=10,
        topic="AST graph absorption linear solver layer (control)",
        correct_choice="gfsa_richardson_absorption",
        choice_kis={
            "gfsa_richardson_absorption": "ki_google_research_gfsa_automaton_layer",
            "dense_mlp_pooling": None,
        },
        votes=[
            {"choice": "gfsa_richardson_absorption", "confidence": 0.95},
            {"choice": "gfsa_richardson_absorption", "confidence": 0.92},
            {"choice": "dense_mlp_pooling", "confidence": 0.70},
        ],
        category="control",
    ),
    DisputeSpec(
        dispute_id=11,
        topic="Multimodal config override immutability (control)",
        correct_choice="locked_dataclass_registry",
        choice_kis={
            "locked_dataclass_registry": "ki_google_research_imp_multimodal_config_registry",
            "mutable_yaml_dict": "ki_self_20260907_01",
        },
        votes=[
            {"choice": "locked_dataclass_registry", "confidence": 0.94},
            {"choice": "locked_dataclass_registry", "confidence": 0.91},
            {"choice": "mutable_yaml_dict", "confidence": 0.72},
        ],
        category="control",
    ),
    DisputeSpec(
        dispute_id=12,
        topic="Chunked vocab loss vs overwhelming unverified plurality (stress)",
        correct_choice="chunked_vocab_ce",
        choice_kis={
            "chunked_vocab_ce": "ki_airllm_chunked_vocab_cross_entropy",
            "full_logits_materialized": "ki_hf_autoresearch_multi_worker_lab",
        },
        votes=[
            {"choice": "full_logits_materialized", "confidence": 0.95},
            {"choice": "full_logits_materialized", "confidence": 0.95},
            {"choice": "full_logits_materialized", "confidence": 0.95},
            {"choice": "full_logits_materialized", "confidence": 0.95},
            {"choice": "chunked_vocab_ce", "confidence": 0.75},
        ],
        category="overwhelming_plurality",
    ),
)


def _ki_multiplier(vault_model: Any, ki_id: str | None) -> tuple[float, str]:
    if ki_id is None:
        return (0.4, "none")
    safe_id = ki_id.replace("-", "_")
    ent = vault_model.entities.get(safe_id) or vault_model.entities.get(ki_id)
    assert ent is not None, f"Expected KI not found in vault model: {ki_id}"
    verified = bool(ent.attributes.get("isnad_verified"))
    return (1.0, "verified") if verified else (0.6, "unverified")


def main() -> int:
    from harness.agent.swarm.consensus import ConsensusEngine

    vault = load_vault_model()
    rows: list[dict[str, Any]] = []

    raw_correct_cnt = 0
    grounded_correct_cnt = 0
    total_flips = 0
    flips_toward_correct = 0
    flips_toward_incorrect = 0

    for d in DISPUTES:
        choice_meta: dict[str, dict[str, Any]] = {}
        for ch, kid in d.choice_kis.items():
            mult, status = _ki_multiplier(vault, kid)
            choice_meta[ch] = {"ki_id": kid, "status": status, "multiplier": mult}

        raw_res = ConsensusEngine.evaluate_cisc_consensus(d.votes, normalization="softmax", temperature=2.5)
        grounded_votes = [
            {
                "choice": v["choice"],
                "confidence": round(float(v["confidence"]) * choice_meta[v["choice"]]["multiplier"], 6),
            }
            for v in d.votes
        ]
        grounded_res = ConsensusEngine.evaluate_cisc_consensus(grounded_votes, normalization="softmax", temperature=2.5)

        raw_win = str(raw_res["winner"])
        grd_win = str(grounded_res["winner"])
        raw_ok = raw_win == d.correct_choice
        grd_ok = grd_win == d.correct_choice
        flipped = raw_win != grd_win

        if raw_ok:
            raw_correct_cnt += 1
        if grd_ok:
            grounded_correct_cnt += 1
        if flipped:
            total_flips += 1
            if grd_ok and not raw_ok:
                flips_toward_correct += 1
            elif raw_ok and not grd_ok:
                flips_toward_incorrect += 1

        rows.append(
            {
                "dispute_id": d.dispute_id,
                "topic": d.topic,
                "category": d.category,
                "correct_choice": d.correct_choice,
                "choice_evidence": choice_meta,
                "raw_winner": raw_win,
                "raw_correct": raw_ok,
                "raw_weights": raw_res["weights"],
                "grounded_winner": grd_win,
                "grounded_correct": grd_ok,
                "grounded_weights": grounded_res["weights"],
                "flipped": flipped,
            }
        )

    n = len(DISPUTES)
    raw_acc = round(raw_correct_cnt / n, 4)
    grd_acc = round(grounded_correct_cnt / n, 4)

    summary_metrics = {
        "disputes_total": n,
        "raw_correct": raw_correct_cnt,
        "raw_accuracy": raw_acc,
        "grounded_correct": grounded_correct_cnt,
        "grounded_accuracy": grd_acc,
        "accuracy_delta": round(grd_acc - raw_acc, 4),
        "total_flips": total_flips,
        "flips_toward_correct": flips_toward_correct,
        "flips_toward_incorrect": flips_toward_incorrect,
    }
    res_path = write_json(11, "results", {"metrics": summary_metrics, "disputes": rows})

    md_lines = [
        "# Phase 11 — Evidence-Grounded CISC Swarm Voting Summary",
        "",
        f"Evaluated **{n}** disputes (`verified=1.0x`, `unverified=0.6x`, `no KI=0.4x`) using `ConsensusEngine.evaluate_cisc_consensus(..., normalization='softmax', temperature=2.5)`.",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Raw CISC accuracy | {raw_correct_cnt}/{n} ({100.0 * raw_acc:.1f}%) |",
        f"| Evidence-grounded accuracy | {grounded_correct_cnt}/{n} ({100.0 * grd_acc:.1f}%) |",
        f"| Total winner flips | {total_flips} |",
        f"| Flips toward **correct** (verified KI) | {flips_toward_correct} |",
        f"| Flips toward **incorrect** | {flips_toward_incorrect} |",
        "",
        "## Per-Dispute Breakdown",
        "",
        "| # | Topic | Raw Winner | Grounded Winner | Correct Choice | Flipped | Grounded OK |",
        "|---:|---|---|---|---|---|---|",
    ]
    for r in rows:
        md_lines.append(
            f"| {r['dispute_id']} | {r['topic']} | `{r['raw_winner']}` (`{r['raw_correct']}`) "
            f"| `{r['grounded_winner']}` | `{r['correct_choice']}` | {r['flipped']} | {r['grounded_correct']} |"
        )
    md_lines.append("")
    md_path = write_md(11, "summary", "\n".join(md_lines))

    print(
        f"Raw acc={raw_correct_cnt}/{n} ({raw_acc:.4f}), Grounded acc={grounded_correct_cnt}/{n} ({grd_acc:.4f}), "
        f"flips={total_flips} (to_correct={flips_toward_correct}, to_incorrect={flips_toward_incorrect})"
    )
    print(f"Results: {res_path}")
    print(f"Summary: {md_path}")
    return 0 if (grd_acc >= raw_acc and flips_toward_incorrect == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
