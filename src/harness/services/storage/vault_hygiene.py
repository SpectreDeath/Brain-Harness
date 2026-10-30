"""Automated vault hygiene, category suggestion, and tag normalization."""

from __future__ import annotations

import re
from typing import Any, Sequence

from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.vault_taxonomy import TaxonomyDomain, normalize_category

# Pre-curated high-signal domain tags for known legacy untagged items
KNOWN_UNTAGGED_MAP: dict[str, list[str]] = {
    "ki-5d-complexity-baseline": ["complexity_scoring", "eval_metrics", "cognitive_budget", "architecture"],
    "ki-cli-decomposition-pattern": ["cli", "monolith_decomposition", "click", "refactoring"],
    "ki-deepening-cycle-history": ["architecture_deepening", "seam_isolation", "refactoring", "decomposition"],
    "ki-file-size-hotspots": ["code_hotspots", "rule_11", "refactoring", "file_size"],
    "ki-gradio-app-architect": ["gradio", "ui", "ai_interface", "blocks"],
    "ki-hf-datasets-arrow-streaming": ["pyarrow", "datasets", "streaming", "caching", "zero_copy"],
    "ki-omarchy-quattro-bridge": ["operating_system", "omarchy", "bridge", "plugin_synthesis"],
    "ki-paperless-ai-rag-sqlite-vec": ["sqlite_vec", "rag", "llamaindex", "bm25", "tantivy"],
    "ki-paperless-ngx-architecture": ["paperless", "document_lifecycle", "ingestion", "celery"],
    "ki-rea-facet-availability-semantics": ["reverse_engineering", "facet_availability", "differential_analysis"],
    "ki-rea-reconstruction-obligations": ["reverse_engineering", "reconstruction_obligation", "evidence_ledger"],
    "ki-responsible-ai-prototyping": ["responsible_ai", "lovable", "prototyping", "governance"],
    "ki-topology-map": ["topology", "graph_of_trees", "ioc_container", "plugin_architecture"],
    "ki_20260922_tau_pi_agent_architecture": ["pi_agent", "minimalist_harness", "coding_agent", "terminal"],
    "ki_20261014_70_cycle_deepening_corpus": ["architecture_deepening", "decomposition", "monolith", "slotted_models"],
    "ki_agentwikis_governance": ["agentwikis", "documentation", "trust_semantics", "data_governance"],
    "ki_chatbotx_dynamic_mcp_orpc": ["orpc", "openapi", "mcp_tool", "schema_generation"],
    "ki_chatbotx_isolated_vm_execution": ["isolated_vm", "sandboxing", "multitenancy", "microservices"],
    "ki_chatbotx_omnichannel_messaging_bus": ["messaging_bus", "omnichannel", "graph_flow", "chatbots"],
    "ki_garf_reporting_engine": ["garf", "sql_reporting", "data_pipeline", "google"],
    "ki_google_repos_bridge": ["google_repos", "bridge", "plugin_suite", "architecture"],
}

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    TaxonomyDomain.AGENT_ORCHESTRATION.value: [
        "harness", "agent", "swarm", "worker", "orchestrat", "deliberat", "subagent", "tau", "pi-style",
        "react", "orca", "dag_scheduler", "self_healing", "tool_calling", "openclaw"
    ],
    TaxonomyDomain.CONTEXT_ENGINEERING.value: [
        "context", "prompt", "token", "prun", "headroom", "repo map", "ast repo", "repomap", "compress", "cache drift"
    ],
    TaxonomyDomain.SECURITY_AND_FORENSICS.value: [
        "security", "sandbox", "audit", "forensic", "red-team", "redteam", "vulnerability", "facet", "reconstruction",
        "pyrit", "jailbreak", "isolated-vm", "cgroup", "privilege", "reverse_engineering", "evidence_ledger"
    ],
    TaxonomyDomain.MEMORY_AND_EPISTEMICS.value: [
        "memory", "epistemic", "isnad", "reflection", "vault", "forgetting", "ebbinghaus", "knowledge", "ontology",
        "graph", "retrieval", "neuro_symbolic", "stylometry", "burrows"
    ],
    TaxonomyDomain.DATA_ENGINEERING.value: [
        "lakehouse", "database", "sqlite", "neo4j", "dmbok", "contract", "dataset", "streaming", "arrow", "garf",
        "paperless", "bigquery", "sql", "vector rag", "sqlite-vec", "tantivy", "django", "orm", "queryset"
    ],
    TaxonomyDomain.INFRASTRUCTURE_AND_RUNTIME.value: [
        "runtime", "subprocess", "ipc", "posix", "shm", "socket", "kubernetes", "drift", "proactor", "transport",
        "pipe", "powershell", "windows", "stream_codecs", "app-server"
    ],
    TaxonomyDomain.SCIENTIFIC_COMPUTING.value: [
        "gis", "geospatial", "simulation", "bioinformatics", "protein", "dna", "neural network", "topk",
        "sparse attention", "dsa", "survival", "cuda", "ptx", "warp"
    ],
    TaxonomyDomain.DEVELOPER_EXPERIENCE.value: [
        "cli", "test", "lint", "doc", "documentation", "brief", "mermaid", "architecture", "deepening", "ui",
        "gradio", "frontend", "monolith", "dataclass", "click", "diagram", "svg", "animation", "complexity", "bridge",
        "hotspot", "file_size", "decomposition", "refactoring"
    ],
}


def suggest_category_for_item(ki: KnowledgeItemRecord) -> str:
    """Propose a canonical TaxonomyDomain category for an uncategorized item."""
    if ki.category and ki.category != "general":
        return ki.category

    text = f"{ki.id} {ki.title} {' '.join(ki.tags)} {ki.source_target or ''}".lower()
    scores: dict[str, int] = {}
    for domain, kws in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in kws:
            pattern = rf"\b{re.escape(kw)}"
            if re.search(pattern, text):
                score += 1
        if score > 0:
            scores[domain] = score

    if not scores:
        return TaxonomyDomain.DEVELOPER_EXPERIENCE.value

    best_domain = max(scores.items(), key=lambda x: x[1])[0]
    return best_domain


def suggest_tags_for_item(ki: KnowledgeItemRecord) -> list[str]:
    """Suggest 2-5 high-signal domain tags for untagged items without mega-tags."""
    if ki.tags:
        return list(ki.tags)

    if ki.id in KNOWN_UNTAGGED_MAP:
        return list(KNOWN_UNTAGGED_MAP[ki.id])

    words = re.findall(r"[a-z0-9_-]{3,}", f"{ki.id} {ki.title}".lower())
    stop_words = {"the", "and", "for", "with", "pattern", "architecture", "baseline", "cycle", "history"}
    extracted = [w for w in words if w not in stop_words and not w.isdigit()]
    return extracted[:4] or ["general_concept"]


def audit_vault_hygiene(items: Sequence[KnowledgeItemRecord]) -> dict[str, Any]:
    """Audit items requiring category assignment or tag triage."""
    uncategorized: list[dict[str, Any]] = []
    untagged: list[dict[str, Any]] = []

    for ki in items:
        if not ki.category or ki.category == "general":
            proposed_cat = suggest_category_for_item(ki)
            uncategorized.append({
                "id": ki.id,
                "title": ki.title,
                "current_category": ki.category or "general",
                "proposed_category": proposed_cat,
            })

        if not ki.tags:
            proposed_tags = suggest_tags_for_item(ki)
            untagged.append({
                "id": ki.id,
                "title": ki.title,
                "proposed_tags": proposed_tags,
            })

    return {
        "uncategorized_count": len(uncategorized),
        "untagged_count": len(untagged),
        "uncategorized": uncategorized,
        "untagged": untagged,
    }
