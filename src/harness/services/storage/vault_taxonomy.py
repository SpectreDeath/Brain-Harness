"""Controlled hierarchical taxonomy and category normalization for Knowledge Items."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import re
from typing import Any


class TaxonomyDomain(str, Enum):
    """Controlled high-level domains for knowledge classification."""

    AGENT_ORCHESTRATION = "agent_orchestration"
    CONTEXT_ENGINEERING = "context_engineering"
    SECURITY_AND_FORENSICS = "security_and_forensics"
    MEMORY_AND_EPISTEMICS = "memory_and_epistemics"
    DATA_ENGINEERING = "data_engineering"
    INFRASTRUCTURE_AND_RUNTIME = "infrastructure_and_runtime"
    DEVELOPER_EXPERIENCE = "developer_experience"
    SCIENTIFIC_COMPUTING = "scientific_computing"
    GENERAL = "general"


# Controlled domain set for quick lookup
CONTROLLED_DOMAINS: frozenset[str] = frozenset(d.value for d in TaxonomyDomain)

# Canonical mapping for historical or free-form category aliases
LEGACY_CATEGORY_MAP: dict[str, str] = {
    "agent_architecture_and_context_engineering": "context_engineering/architecture",
    "architecture": "developer_experience/architecture",
    "reverse-engineering / differential-analysis / facet-semantics": "security_and_forensics/reverse_engineering",
    "reverse_engineering": "security_and_forensics/reverse_engineering",
    "security": "security_and_forensics",
    "forensics": "security_and_forensics",
    "red_teaming": "security_and_forensics/red_teaming",
    "adversarial_safety": "security_and_forensics/red_teaming",
    "endogenous_memory": "memory_and_epistemics/reflection",
    "endogenous_reflection": "memory_and_epistemics/reflection",
    "reflection": "memory_and_epistemics/reflection",
    "epistemics": "memory_and_epistemics",
    "ontology": "memory_and_epistemics/ontology",
    "harness_engineering": "agent_orchestration/harness",
    "swarm": "agent_orchestration/swarm",
    "agent_orchestration": "agent_orchestration",
    "storage": "data_engineering/storage",
    "lakehouse": "data_engineering/lakehouse",
    "database": "data_engineering/database",
    "gis": "scientific_computing/geospatial",
    "geospatial": "scientific_computing/geospatial",
    "bioinformatics": "scientific_computing/bioinformatics",
    "runtime": "infrastructure_and_runtime",
    "sandbox": "infrastructure_and_runtime/sandbox",
    "kubernetes": "infrastructure_and_runtime/kubernetes",
    "cli": "developer_experience/cli",
    "ui": "developer_experience/ui",
    "python": "developer_experience/python",
    "skills": "developer_experience/skills",
    "general": "general",
    # Extended legacy aliases and specialized domains from vault census
    "architecture_and_deepening": "developer_experience/architecture",
    "software_architecture": "developer_experience/architecture",
    "security_and_sandboxing": "security_and_forensics/sandboxing",
    "geospatial_and_osint": "scientific_computing/geospatial",
    "reverse-engineering / evidence / obligation-tracking": "security_and_forensics/reverse_engineering",
    "integration_and_io": "infrastructure_and_runtime/integration",
    "integration_and_knowledge": "memory_and_epistemics/integration",
    "software_engineering": "developer_experience/software_engineering",
    "data_modeling": "data_engineering/modeling",
    "machine_learning": "scientific_computing/machine_learning",
    "memory_and_introspection": "memory_and_epistemics/reflection",
    "testing_and_verification": "developer_experience/testing",
    "tooling_and_scaffolding": "developer_experience/tooling",
    "reporting_and_visualization": "developer_experience/visualization",
    "repository_auditing": "security_and_forensics/auditing",
    "skill_routing_and_discovery": "agent_orchestration/skills",
    "testing_and_mocks": "developer_experience/testing",
    "skill_engineering": "developer_experience/skills",
    "agent_tooling": "agent_orchestration/tooling",
    "platform_invariants": "infrastructure_and_runtime/platform",
    "engineering_velocity": "developer_experience/velocity",
    "docs_as_code_and_governance": "developer_experience/documentation",
    "kernel": "infrastructure_and_runtime/kernel",
    "testing_and_contracts": "developer_experience/testing",
    "user_interface_and_interaction": "developer_experience/ui",
    "kernel_and_ioc": "infrastructure_and_runtime/kernel",
    "skill_graph_and_routing": "agent_orchestration/skills",
    "skill_graph": "agent_orchestration/skills",
    "testing_and_hygiene": "developer_experience/testing",
    "documentation_hygiene": "developer_experience/documentation",
    "developer_tooling": "developer_experience/tooling",
    "infra_and_cloud": "infrastructure_and_runtime/cloud",
}


def normalize_category(category: str | None) -> str:
    """Normalize a free-form or legacy category string to the controlled taxonomy."""
    if not category:
        return TaxonomyDomain.GENERAL.value
    raw_clean = category.strip().lower()
    root = raw_clean.split("/")[0]
    if root in CONTROLLED_DOMAINS:
        return raw_clean
    if raw_clean in LEGACY_CATEGORY_MAP:
        return LEGACY_CATEGORY_MAP[raw_clean]
    clean = re.sub(r"\s+", "_", raw_clean)
    if clean in LEGACY_CATEGORY_MAP:
        return LEGACY_CATEGORY_MAP[clean]
    if clean.split("/")[0] in CONTROLLED_DOMAINS:
        return clean
    for key, val in LEGACY_CATEGORY_MAP.items():
        if key in raw_clean or key in clean:
            return val
    for domain in CONTROLLED_DOMAINS:
        if domain in raw_clean or domain in clean:
            return domain
    return TaxonomyDomain.GENERAL.value


def get_taxonomy_domain(category: str | None) -> str:
    """Extract root domain string from a normalized or raw category."""
    normalized = normalize_category(category)
    return normalized.split("/")[0]


def is_valid_domain(domain: str) -> bool:
    """Return whether a given domain string is part of the controlled taxonomy."""
    return domain in CONTROLLED_DOMAINS


def resolve_source_target(meta: dict[str, Any]) -> str:
    """Waterfall resolution of source and origin across heterogeneous metadata fields."""
    if meta.get("source_target"):
        return str(meta["source_target"])
    if meta.get("source_repo"):
        return str(meta["source_repo"])
    src = meta.get("source")
    if src:
        if isinstance(src, dict):
            return str(src.get("url") or src.get("git_origin") or src.get("title") or "")
        return str(src)
    for field in ("source_uri", "source_brain", "source_url"):
        if meta.get(field):
            return str(meta[field])
    prov = meta.get("provenance")
    if isinstance(prov, dict) and prov.get("source"):
        return str(prov["source"])
    return ""


def resolve_created_at(meta: dict[str, Any], ki_dir: Path) -> str:
    """Resolve ground-truth creation timestamp without clobbering historical dates."""
    for field in ("created_at", "timestamp", "created"):
        val = meta.get(field)
        if val and isinstance(val, str) and len(val) >= 4:
            return val
    isnad = meta.get("isnad")
    if isinstance(isnad, dict) and isnad.get("timestamp"):
        return str(isnad["timestamp"])
    prov = meta.get("provenance")
    if isinstance(prov, dict):
        for field in ("timestamp", "extracted_at", "date"):
            if prov.get(field):
                return str(prov[field])
    m = re.search(r"(202\d{5}|202\d-\d{2}-\d{2})", ki_dir.name)
    if m:
        raw = m.group(1).replace("-", "")
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00Z"
    try:
        mtime = (ki_dir / "metadata.json").stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def normalize_isnad(meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw isnad strings and merge top-level claims arrays into isnad block."""
    isnad_raw = meta.get("isnad")
    if isinstance(isnad_raw, str):
        isnad_block: dict[str, Any] = {"status": "VERIFIED", "notes": isnad_raw, "claims": []}
    elif isinstance(isnad_raw, dict):
        isnad_block = dict(isnad_raw)
    else:
        isnad_block = {}

    top_claims = meta.get("claims") or meta.get("isnad_claims") or []
    if top_claims and not isnad_block.get("claims"):
        isnad_block["claims"] = top_claims
    return isnad_block
