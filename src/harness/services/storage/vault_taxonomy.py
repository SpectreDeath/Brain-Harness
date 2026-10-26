"""Controlled hierarchical taxonomy and category normalization for Knowledge Items."""

from __future__ import annotations

from enum import Enum
import re


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
}


def normalize_category(category: str | None) -> str:
    """Normalize a free-form or legacy category string to the controlled taxonomy."""
    if not category:
        return TaxonomyDomain.GENERAL.value

    raw_clean = category.strip().lower()

    # If already a valid controlled domain or hierarchical path under a controlled domain
    root = raw_clean.split("/")[0]
    if root in CONTROLLED_DOMAINS:
        return raw_clean

    if raw_clean in LEGACY_CATEGORY_MAP:
        return LEGACY_CATEGORY_MAP[raw_clean]

    clean = re.sub(r"\s+", "_", raw_clean)
    if clean in LEGACY_CATEGORY_MAP:
        return LEGACY_CATEGORY_MAP[clean]

    root_clean = clean.split("/")[0]
    if root_clean in CONTROLLED_DOMAINS:
        return clean

    # Check substring and key matching
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
