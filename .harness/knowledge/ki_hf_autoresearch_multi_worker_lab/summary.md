# Multi-Agent Autoresearch AI Lab Architecture & Heterogeneous Model Workers

**ID:** `ki_hf_autoresearch_multi_worker_lab`  
**Category:** `machine_learning`  
**Origin:** *The Context Course: Projects (Pre-Training & Inference Autoresearch)* (Hugging Face)  
**Provenance Lineage:** Projects/pre-training & inference, Hugging Face, 2026.

## Executive Summary

Based on Andrej Karpathy's autoresearch paradigm, the Context Course projects demonstrate a distributed, multi-agent AI research laboratory. In this setup, autonomous agents execute continuous iterative improvement loops on machine learning workloads (e.g., minimizing validation loss in pre-training or maximizing tokens-per-second in local `llama.cpp` inference).

### Heterogeneous Worker Specialization
Rather than binding the lab to a single model provider, the architecture implements adapter runners for heterogeneous worker personas:
- **Hermes Worker (`hermes_worker.py`)**: Specialized open-weight local orchestrator using NousResearch models.
- **Claude Worker (`print_claude_kickoff.py`)**: High-reasoning architectural auditor designing experiment hypotheses.
- **Codex Worker (`print_codex_kickoff.py`)**: Code generation and refactoring specialist optimizing CUDA/C++ kernels.
- **Pi Worker (`pi_worker.py`)**: Epistemic note-taking, logging, and research hypothesis tracking.
- **OpenCode Worker (`opencode_worker.py`)**: Open-source terminal agent dispatching patches.

### The Autoresearch Improvement Cycle
1. **Hypothesize**: Worker reads `notes.md`, `results.tsv`, and baseline code.
2. **Mutate**: Worker applies code modifications (`train.py` hyperparameters, architecture changes).
3. **Execute**: Worker submits GPU job (`hf_job.py` or local run).
4. **Evaluate & Settle**: Metric parser extracts objective validation scores (`parse_metric.py`). If improved, changes are committed via `submit_patch.py`; if degraded, git state is rolled back.

## Operational Deployment Invariants

1. **Metric Ground-Truth Invariant**: Patch acceptance must be gated on objective, automated metrics recorded in TSV logs, never subjective model claims.
2. **Git Worktree Isolation**: Concurrent workers must operate in isolated Git worktrees to prevent merge conflicts during iterative experimentation.
3. **Do-Not-Repeat Boundary**: Maintain an append-only `do-not-repeat.md` ledger recording rejected hypotheses to prevent cyclical experimentation thrashing.
