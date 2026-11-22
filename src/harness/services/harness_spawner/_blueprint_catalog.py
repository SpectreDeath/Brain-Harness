"""Static portfolio catalog of domain harness specs aligned to live graph clusters (Rules 12, 43)."""

from __future__ import annotations

from dataclasses import dataclass

VALID_ICM_FORMS: frozenset[str] = frozenset(
    {"pipeline", "record_library", "knowledge_bundle", "context_map", "system_map"}
)


@dataclass(slots=True, frozen=True)
class CanonicalSpec:
    """Curated domain blueprint mapping live graph clusters/bridges to an ICM harness form."""

    name: str
    domain: str
    title: str
    mission: str
    icm_form: str
    cluster_id: str
    skills: tuple[str, ...]
    query_keywords: tuple[str, ...]
    use_cases: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    tier: int = 1

    def __post_init__(self) -> None:
        if self.icm_form not in VALID_ICM_FORMS:
            raise ValueError(f"Unsupported ICM form: {self.icm_form!r}")
        if not 1 <= len(self.skills) <= 6:
            raise ValueError(f"CanonicalSpec {self.name!r} must declare 1..6 skills")


CANONICAL_SPECS: tuple[CanonicalSpec, ...] = (
    CanonicalSpec(
        name="harness-repo-distiller",
        domain="knowledge_distillation",
        title="Repository & Trajectory Distiller Harness",
        mission=(
            "Ingest external repositories and session trajectories in isolation, verifying verbatim "
            "quotes against raw sources and staging dual-file Knowledge Items for reviewed adoption."
        ),
        icm_form="knowledge_bundle",
        cluster_id="cluster_12_brain_artifact_miner",
        skills=(
            "icm-workspace-architect",
            "repo-triad-forge",
            "epistemic-isnad-audit",
            "brain-artifact-miner",
            "conversation-trajectory-miner",
        ),
        query_keywords=("distill", "trajectory", "epistemic", "triad"),
        use_cases=(
            "Inspect an external GitHub repository in isolation, capture verbatim raw excerpts under sources/raw/, verify quotes with harness icm quotes, and stage dual-file KIs via harness spawn propose.",
            "Mine recorded execution trajectories or session artifacts into candidate skill briefs and isnad-audited concept notes without loading all Prime workspace skills.",
        ),
        out_of_scope=(
            "Production Kubernetes deployment or runtime cluster remediation",
            "Live network packet capture or exploit validation against remote targets",
            "Unreviewed silent auto-adoption into Prime .harness/knowledge/ or raw git merge into main",
        ),
        tier=1,
    ),
    CanonicalSpec(
        name="harness-security-forensics",
        domain="security_and_forensics",
        title="Security Audit, Reverse Engineering & Forensics Harness",
        mission=(
            "Execute commit-history security triage, binary/bundle dissection, and multi-provider "
            "evidence verification tracked as auditable ICM finding records."
        ),
        icm_form="record_library",
        cluster_id="cluster_09_mantis_security_review",
        skills=(
            "icm-workspace-architect",
            "mantis-security-review",
            "rea-reverse-engineering",
            "differential-facet-verifier",
            "ethical-hacker-networking",
        ),
        query_keywords=("mantis", "reverse engineering", "facet", "security"),
        use_cases=(
            "Run commit-history and AST taint triage on a target codebase, record structured findings in records/, rebuild records/_index.md via harness icm index, and stage verified lessons.",
            "Cross-check multi-provider reverse-engineering evidence dossiers with explicit facet availability semantics and network fault isolation checks.",
        ),
        out_of_scope=(
            "Unauthorized offensive testing, active exploitation, or credential harvesting on external networks",
            "Generic frontend CSS styling or full-stack web UI prototyping",
            "Direct unreviewed writes into Prime knowledge vault or dock boundary paths",
        ),
        tier=1,
    ),
    CanonicalSpec(
        name="harness-arch-modernizer",
        domain="architecture",
        title="Architecture Deepening & Monolith Decomposition Harness",
        mission=(
            "Map causal DAG seams, isolate legacy blast radii, and decompose monolithic modules "
            "behind characterization tests with bounded stage contracts."
        ),
        icm_form="system_map",
        cluster_id="cluster_11_architecture_deepening_workflow",
        skills=(
            "icm-workspace-architect",
            "architecture-deepening-workflow",
            "monolith-decomposition-engine",
            "data-topology-mapper",
            "legacy-modernization-pipeline",
        ),
        query_keywords=("deepening", "architecture", "monolith"),
        use_cases=(
            "Inventory domain nouns and workflow verbs under objects/ and processes/ before refactoring tightly coupled modules.",
            "Split monolithic files above 200 lines behind characterization test safety nets cleanly.",
        ),
        out_of_scope=(
            "Ad-hoc binary disassembly or network forensic packet captures",
            "Greenfield visual design or unstructured prose editing",
        ),
        tier=1,
    ),
    CanonicalSpec(
        name="harness-context-economizer",
        domain="context_engineering",
        title="Context & Token Economy Auditor Harness",
        mission=(
            "Audit AGENTS.md, skills, and documentation surfaces for prompt bloat, link drift, "
            "and multi-layer rule collisions prior to spawning or release."
        ),
        icm_form="context_map",
        cluster_id="cluster_19_headroom_context_optimizer",
        skills=(
            "icm-workspace-architect",
            "headroom-context-optimizer",
            "token-economizer",
            "codebase-context-governor",
            "repo-doc-synchronizer",
        ),
        query_keywords=("headroom", "context", "token"),
        use_cases=(
            "Audit AGENTS.md line caps, Rule 44 skill description budgets, and relative documentation links across domain boundaries.",
            "Profile high-token tool observations and compress multi-turn context payloads deterministically.",
        ),
        out_of_scope=(
            "GPU kernel sparse-attention tuning or BigQuery data warehouse ETL",
            "Binary reverse engineering or security exploit triage",
        ),
        tier=1,
    ),
    CanonicalSpec(
        name="harness-knowledge-graph",
        domain="data_engineering",
        title="Knowledge Graph & Ontology Pipeline Harness",
        mission=(
            "Model domain ontologies under Gruber criteria and ingest governed tabular corpora "
            "into Neo4j property graphs or recursive SQL CTE hierarchies."
        ),
        icm_form="knowledge_bundle",
        cluster_id="cluster_13_knowledge_graph_pipeline",
        skills=(
            "icm-workspace-architect",
            "knowledge-graph-pipeline",
            "neo4j-knowledge-graph-architect",
            "sql-recursive-graph-traversal",
            "ontological-engineering-coach",
        ),
        query_keywords=("knowledge graph", "ontology", "neo4j"),
        use_cases=(
            "Validate domain ontology precision and coverage before generating idempotent Cypher ingestion pipelines.",
            "Verify termination bounds on recursive SQL CTE hierarchy queries.",
        ),
        out_of_scope=(
            "Kubernetes cluster security auditing or UI primitive styling",
            "Unverified free-form text clustering without source lineage",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-skill-factory",
        domain="meta_skills",
        title="Skill Authoring & Statistical Assurance Harness",
        mission=(
            "Design, scaffold, and statistically assure new deep-module agent skills before "
            "proposing admission into Prime."
        ),
        icm_form="pipeline",
        cluster_id="cluster_05_deep_skill_forge",
        skills=(
            "icm-workspace-architect",
            "crafting-skills",
            "agent-skill-sdlc",
            "skill-eval-assurance-runner",
        ),
        query_keywords=("skill", "eval", "assurance"),
        use_cases=(
            "Author new SKILL.md and companion CARD.md artifacts through staged ICM contracts and Wilson CI checks.",
            "Validate existing skill frontmatter budgets and negative boundaries prior to PR review.",
        ),
        out_of_scope=(
            "External repository reverse engineering or database schema migrations",
            "Unreviewed silent edits to Prime .agents/skills/",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-data-lakehouse",
        domain="data_engineering",
        title="Lakehouse & Analytical SQL Reporting Harness",
        mission=(
            "Govern Medallion data contracts, BigQuery augmented analytics, and declarative "
            "SQL reporting DAGs cleanly across analytical pipelines."
        ),
        icm_form="pipeline",
        cluster_id="cluster_10_bigquery_augmented_analytics",
        skills=(
            "icm-workspace-architect",
            "bigquery-augmented-analytics",
            "data-management-architect",
            "garf-reporting-architect",
            "paperless-document-pipeline",
        ),
        query_keywords=("bigquery", "garf", "lakehouse"),
        use_cases=(
            "Draft Open Data Contracts and BigQuery anomaly/attribution TVF queries in staged verification pipelines.",
            "Execute declarative reporting DAG checks over structured tabular feeds.",
        ),
        out_of_scope=(
            "Live production OLTP mutations without dry-run gates",
            "Low-level binary disassembly or K8s pod RBAC hardening",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-cloud-k8s",
        domain="infra_and_cloud",
        title="Cloud Infrastructure & Kubernetes Drift Guardian Harness",
        mission=(
            "Detect Kubernetes manifest drift, audit RBAC least-privilege posture, and verify "
            "container sandboxing controls using tracked record shelves."
        ),
        icm_form="record_library",
        cluster_id="cluster_16_cloud_infrastructure_architect",
        skills=(
            "icm-workspace-architect",
            "cloud-infrastructure-architect",
            "kubernetes-drift-guardian",
        ),
        query_keywords=("kubernetes", "cloud", "sandbox"),
        use_cases=(
            "Audit Kubernetes manifests and RBAC bindings for policy drift and track remediation tickets in records/.",
            "Verify container sandbox isolation and Prometheus metric exposition posture.",
        ),
        out_of_scope=(
            "Unauthenticated external cluster mutation or active network exploitation",
            "Text stylometry or BigQuery marketing attribution workflows",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-reverse-engineering",
        domain="reverse_engineering",
        title="Software Reverse Engineering & Obligation Verification Harness",
        mission=(
            "Passively dissect native binaries, managed assemblies, APKs, JS/WASM/EVM bundles, and firmware via REA "
            "and govern behavioral reconstruction obligations through immutable CanonicalEvidence and ROL proofs."
        ),
        icm_form="pipeline",
        cluster_id="cluster_09_mantis_security_review",
        skills=(
            "icm-workspace-architect",
            "rea-reverse-engineering",
            "reconstruction-obligation-ledger",
            "differential-facet-verifier",
            "epistemic-isnad-audit",
        ),
        query_keywords=("reverse engineering", "reconstruction", "obligation", "facet"),
        use_cases=(
            "Dissect binaries, bytecode, or bundles passively via harness rea inspect and extract deterministic semantic signatures.",
            "Ingest multi-provider dissection dossiers into ROL with strict 3-valued facet availability, differential comparison, and ReconstructionProof verification.",
        ),
        out_of_scope=(
            "Mantis commit-history SAST triage or active network port scanning (use harness-security-forensics)",
            "Executing untrusted target binaries or live exploit payloads in-process",
            "Unreviewed silent writes into Prime .harness/knowledge/ without isnad closure",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-ontology-spider",
        domain="ontology_reasoning",
        title="Formal Ontology Reasoning, SHACL-AF Governance & Vault Audit Harness",
        mission=(
            "Query, traverse, and audit Knowledge Vaults and domain ontologies using SWI-Prolog/Python .dialog logic, "
            "Laya attribute-entropy ranking, SHACL-AF policies, PROV-O explainability, and bi-temporal as_of checks."
        ),
        icm_form="system_map",
        cluster_id="cluster_08_ebbinghaus_memory_governor",
        skills=(
            "icm-workspace-architect",
            "ontology-spider",
            "trustgraph-ontology-governor",
            "graphiti-zep-memory-governor",
            "ontological-engineering-coach",
        ),
        query_keywords=("ontology", "trustgraph", "shacl", "gruber", "graphiti"),
        use_cases=(
            "Execute formal .dialog transitive, shortest-path, closed-world negation, and cardinality queries alongside Laya entropy attribute ranking over .harness/knowledge/.",
            "Enforce SHACL-AF triple filtering, cycle-safe subClassOf validation, dual named-graph PROV-O traces, and bi-temporal edge normalization.",
        ),
        out_of_scope=(
            "Neo4j Cypher UNWIND batch ETL or relational recursive SQL CTE pipelines (use harness-knowledge-graph)",
            "Fuzzy embedding similarity searches where exact logical closures are required",
            "Unbounded cyclic traversals without acyclicity verification",
        ),
        tier=2,
    ),
    CanonicalSpec(
        name="harness-memory-graph",
        domain="memory_and_epistemics",
        title="Bi-Temporal Memory Graph, OKF & Epistemic Lifecycle Harness",
        mission=(
            "Govern agent working-memory retention, bi-temporal Graphiti/Zep normalization, MinHash/LSH entity dedup, "
            "RRF/MMR reranking, Git-native OKF BM25 scoping, and 8-state epistemic promotion lifecycles."
        ),
        icm_form="context_map",
        cluster_id="cluster_08_ebbinghaus_memory_governor",
        skills=(
            "icm-workspace-architect",
            "graphiti-zep-memory-governor",
            "ebbinghaus-memory-governor",
            "okf-memory-governor",
            "epistemic-memory-lifecycle",
        ),
        query_keywords=("graphiti", "ebbinghaus", "okf", "epistemic"),
        use_cases=(
            "Normalize bi-temporal assertions against reference timestamps, deduplicate high-entropy entities via MinHash/LSH, and tune RRF/MMR retrieval reranking.",
            "Scope pre-edit OKF knowledge bundles via BM25 ranking and govern cross-turn Ebbinghaus decay multipliers and knowledge promotion gates.",
        ),
        out_of_scope=(
            "Formal SWI-Prolog .dialog closures or SHACL-AF triple policy filtering (use harness-ontology-spider)",
            "Static binary reverse engineering or Kubernetes manifest auditing",
        ),
        tier=2,
    ),
)

__all__ = ["CANONICAL_SPECS", "CanonicalSpec", "VALID_ICM_FORMS"]
