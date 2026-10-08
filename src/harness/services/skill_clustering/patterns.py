"""Canonical emergent capability patterns recognized across the Brain Harness ecosystem."""

from __future__ import annotations

from typing import Any

CANONICAL_EMERGENT_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "cap_multimedia_vault_distillation",
        "title": "Cryptographically Grounded Multimedia Literature-to-Knowledge-Vault Distillation",
        "keywords": {"youtube", "video", "transcript", "audio", "lecture", "distill", "multimedia", "vault", "isnad"},
        "core_skills": ["youtube-transcript-fetcher", "media-mind-forge", "epistemic-isnad-audit", "media-to-vault-pipeline"],
        "pipeline": ["youtube-transcript-fetcher", "media-mind-forge", "epistemic-isnad-audit", "media-to-vault-pipeline"],
        "rationale": (
            "Combines isolated caption extraction, epistemic isnād provenance verification, "
            "and mental model distillation into a permanent dual-file Knowledge Vault commit "
            "with zero hallucination drift."
        ),
        "outcomes": ["Verified Knowledge Vault item (metadata.json + summary.md)", "Cryptographic isnād hash chain"],
    },
    {
        "id": "cap_foreign_repo_ingestion_deepening",
        "title": "Zero-Shot Foreign Repository Ingestion, IoC Packaging & Architecture Deepening",
        "keywords": {"repo", "github", "ingest", "foreign", "external", "clone", "plugin", "forge", "deepen", "seam"},
        "core_skills": ["repo-reader", "repo-to-plugin-forge", "deepen-architecture", "mind-reader"],
        "pipeline": ["repo-reader", "repo-to-plugin-forge", "deepen-architecture", "adversarial-agent-verifier"],
        "rationale": (
            "Autonomously introspects external git commit histories and codebases, generates sandboxed "
            "Harness plugins with typed ServiceKey contracts, and deepens shallow module seams in-place."
        ),
        "outcomes": ["Sandboxed Harness plugin package", "Architectural visual brief", "Seam verification diffs"],
    },
    {
        "id": "cap_legacy_modernization_safety_net",
        "title": "Zero-Regression Legacy Modernization with Characterization Test Safety Nets",
        "keywords": {"legacy", "modernize", "refactor", "regression", "characterization", "topology", "audit", "safety"},
        "core_skills": ["data-topology-mapper", "legacy-refactoring-guardian", "legacy-modernization-pipeline", "adversarial-agent-verifier"],
        "pipeline": ["data-topology-mapper", "legacy-refactoring-guardian", "legacy-modernization-pipeline", "adversarial-agent-verifier"],
        "rationale": (
            "Constructs causal DAG lineages of legacy data paths before modification, wraps opaque seams "
            "in characterization test safety nets, and applies safe incremental refactoring loops."
        ),
        "outcomes": ["Causal DAG topology map", "Characterization test suite", "Verified modernized code"],
    },
    {
        "id": "cap_context_anti_rot_governance",
        "title": "Continuous Multi-Layer Context Budgeting & Rule 11 Anti-Rot Enforcement",
        "keywords": {"context", "agents.md", "claude.md", "rot", "sync", "budget", "tokens", "lint", "leakage"},
        "core_skills": ["codebase-context-architect", "codebase-context-governor", "context-anti-rot-sync", "agent-instruction-architect"],
        "pipeline": ["codebase-context-governor", "context-anti-rot-sync", "agent-instruction-architect", "codebase-context-architect"],
        "rationale": (
            "Budgets prompt tokens across three operational layers, eliminates lint leakage, "
            "and synchronizes agent instruction files within strict 150-line Rule 11 boundaries."
        ),
        "outcomes": ["Pruned AGENTS.md / CLAUDE.md files", "Zero-rot CI verification report"],
    },
    {
        "id": "cap_adversarial_security_gate",
        "title": "Shift-Left Vulnerability Interception & Adversarial Seam Verification",
        "keywords": {"adversarial", "verify", "security", "pre-commit", "sast", "vulnerability", "gate", "reflection"},
        "core_skills": ["questio-reflection", "pre-commit-security-guard", "adversarial-agent-verifier", "ethical-hacker-networking"],
        "pipeline": ["questio-reflection", "pre-commit-security-guard", "adversarial-agent-verifier"],
        "rationale": (
            "Applies Aquinas-style dialectical objections, Git pre-commit SAST scanning, "
            "and harsh adversarial review before code diffs can finalize context transactions."
        ),
        "outcomes": ["Dialectical objection matrix", "Pre-commit SAST scorecard", "Zero-regression test pass"],
    },
    {
        "id": "cap_agentic_swarm_self_evolution",
        "title": "Autonomous Agentic Swarm with ANN Textual Backpropagation & Consensus Voting",
        "keywords": {"swarm", "multi-agent", "deliberate", "consensus", "ann", "backprop", "reflect", "game-theoretic", "orca"},
        "core_skills": ["orca-orchestrator", "game-theoretic-swarm-deliberator", "sme-ann-backprop", "swarm-reflection-optimizer"],
        "pipeline": ["orca-orchestrator", "game-theoretic-swarm-deliberator", "sme-ann-backprop", "swarm-reflection-optimizer"],
        "rationale": (
            "Orchestrates parallel worker worktrees, resolves strategic choices via game-theoretic "
            "payoff matrices, and executes textual backpropagation to repair failing multi-agent DAGs."
        ),
        "outcomes": ["Consensus decision payload", "Textual gradient update log", "Optimized swarm DAG"],
    },
    {
        "id": "cap_ontological_graph_engineering",
        "title": "Enterprise Ontological Data Modeling & Polyglot Graph Traversal",
        "keywords": {"ontology", "knowledge-graph", "neo4j", "sql", "graph", "recursive", "traversal", "property-graph"},
        "core_skills": ["ontological-engineering-coach", "knowledge-graph-pipeline", "sql-recursive-graph-traversal", "neo4j-knowledge-graph-architect"],
        "pipeline": ["ontological-engineering-coach", "knowledge-graph-pipeline", "sql-recursive-graph-traversal"],
        "rationale": (
            "Balances precision vs coverage using Gruber criteria, ingests structured data into Neo4j "
            "labeled property graphs, and executes recursive relational SQL graph traversals."
        ),
        "outcomes": ["Ontological model definition", "Loaded Neo4j property graph", "Recursive SQL queries"],
    },
    {
        "id": "cap_sparse_neural_calculus",
        "title": "Mathematical Neural Calculus & Extreme-Scale Sparse Acceleration",
        "keywords": {"neural", "scratch", "calculus", "matrix", "topk", "sparse", "cluster", "attention"},
        "core_skills": ["neural-network-from-scratch", "deepselect-topk-optimizer"],
        "pipeline": ["neural-network-from-scratch", "deepselect-topk-optimizer"],
        "rationale": (
            "Derives matrix calculus gradients from scratch and accelerates DeepSeek Sparse Attention "
            "using randomized block scans, monotonic threshold filtering, and threadblock clusters."
        ),
        "outcomes": ["Modular PyTorch / NumPy architecture", "CUDA / Triton cluster optimization plan"],
    },
    {
        "id": "cap_docs_as_code_ast_pipeline",
        "title": "Automated AST Docs-as-Code Auditing & Multi-Package Documentation Suites",
        "keywords": {"doc", "documentation", "diataxis", "ast", "drift", "synchronize", "builder", "suite"},
        "core_skills": ["developer-docs-architect", "repo-doc-synchronizer", "hf-doc-builder-architect"],
        "pipeline": ["repo-doc-synchronizer", "developer-docs-architect", "hf-doc-builder-architect"],
        "rationale": (
            "Extracts live code symbols via AST, audits documentation drift in CI/CD, "
            "and authors comprehensive Diátaxis documentation suites (Tutorials, How-To, Reference, Explanation)."
        ),
        "outcomes": ["AST documentation drift scorecard", "Complete Diátaxis documentation suite"],
    },
    {
        "id": "cap_harness_calibration_evolution",
        "title": "Self-Calibrating Multi-Tier Autonomous Agent Harness Architecture",
        "keywords": {"harness", "calibrate", "benchmark", "compass", "context-staging", "evolution", "substrate"},
        "core_skills": ["agent-harness-architect", "ai-native-harness-engineer", "coding-harness-calibrator", "harness-compass", "pi-coding-harness"],
        "pipeline": ["agent-harness-architect", "coding-harness-calibrator", "ai-native-harness-engineer", "harness-compass"],
        "rationale": (
            "Empirically benchmarks coding agent loops across T0-T4 context staging, enforces 4-gate "
            "behavioral telemetry, and executes constrained harness evolution without human intervention."
        ),
        "outcomes": ["Harness calibration scorecard", "4-gate behavioral pipeline configuration"],
    },
    {
        "id": "cap_enterprise_lakehouse_governance",
        "title": "Enterprise Medallion Lakehouse Governance & Augmented Analytics",
        "keywords": {"data", "lakehouse", "governance", "bigquery", "garf", "analytics", "sql", "contracts"},
        "core_skills": ["data-management-architect", "bigquery-augmented-analytics", "garf-reporting-architect", "structured-data-scout"],
        "pipeline": ["structured-data-scout", "data-management-architect", "bigquery-augmented-analytics", "garf-reporting-architect"],
        "rationale": (
            "Applies DAMA-DMBOK capabilities, Open Data Contracts (ODCS), and BigQuery TVFs "
            "to automate metric anomaly detection and execute causal inference across lakehouses."
        ),
        "outcomes": ["Open Data Contract specification", "BigQuery TVF causality model", "Garf DAG report"],
    },
]

__all__ = ["CANONICAL_EMERGENT_PATTERNS"]
