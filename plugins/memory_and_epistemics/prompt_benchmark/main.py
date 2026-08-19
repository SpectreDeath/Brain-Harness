"""Prompt benchmark, BLEU/ROUGE ngram similarity, and model evaluation plugin."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"\w+", text)]


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def score_text_similarity_bleu_rouge(reference: str, candidate: str) -> dict[str, Any]:
    """Calculate BLEU-1, BLEU-2, and ROUGE-1 F1 scores."""
    ref_toks = _tokenize(reference)
    cand_toks = _tokenize(candidate)

    if not ref_toks or not cand_toks:
        return {"status": "ok", "bleu_1": 0.0, "bleu_2": 0.0, "rouge_1_f1": 0.0}

    # BLEU-1 (Unigram Precision)
    ref_counts = Counter(ref_toks)
    cand_counts = Counter(cand_toks)
    overlap_1 = sum(min(count, ref_counts.get(tok, 0)) for tok, count in cand_counts.items())
    bleu_1 = overlap_1 / len(cand_toks)

    # BLEU-2 (Bigram Precision)
    ref_bi = Counter(_ngrams(ref_toks, 2))
    cand_bi = Counter(_ngrams(cand_toks, 2))
    if cand_bi:
        overlap_2 = sum(min(count, ref_bi.get(bg, 0)) for bg, count in cand_bi.items())
        bleu_2 = overlap_2 / len(cand_bi)
    else:
        bleu_2 = 0.0

    # ROUGE-1 Recall & F1
    recall_1 = overlap_1 / len(ref_toks)
    f1 = (2 * bleu_1 * recall_1) / (bleu_1 + recall_1) if (bleu_1 + recall_1) > 0 else 0.0

    return {
        "status": "ok",
        "reference_tokens": len(ref_toks),
        "candidate_tokens": len(cand_toks),
        "bleu_1": round(bleu_1, 4),
        "bleu_2": round(bleu_2, 4),
        "rouge_1_recall": round(recall_1, 4),
        "rouge_1_f1": round(f1, 4),
    }


def evaluate_model_outputs(test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate candidate outputs against test assertions."""
    passed = 0
    evaluations: list[dict[str, Any]] = []

    for case in test_cases:
        out = case.get("output", "")
        exp_contains = case.get("expected_contains", [])
        not_contains = case.get("must_not_contain", [])

        case_passed = True
        failures: list[str] = []

        for kw in exp_contains:
            if kw.lower() not in out.lower():
                case_passed = False
                failures.append(f"Missing expected keyword '{kw}'")

        for kw in not_contains:
            if kw.lower() in out.lower():
                case_passed = False
                failures.append(f"Contains forbidden keyword '{kw}'")

        if case_passed:
            passed += 1

        evaluations.append({
            "test_id": case.get("id", len(evaluations) + 1),
            "passed": case_passed,
            "failures": failures,
        })

    total = len(test_cases)
    pass_rate = round(passed / total, 4) if total > 0 else 1.0

    return {
        "status": "ok",
        "total_test_cases": total,
        "passed_count": passed,
        "pass_rate": pass_rate,
        "evaluations": evaluations,
    }


def generate_regression_matrix(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize and rank benchmark runs."""
    ranked = sorted(runs, key=lambda r: (r.get("pass_rate", 0.0), -r.get("avg_latency", 999.0)), reverse=True)
    return {
        "status": "ok",
        "total_runs": len(runs),
        "top_performer": ranked[0] if ranked else None,
        "ranking": ranked,
    }
