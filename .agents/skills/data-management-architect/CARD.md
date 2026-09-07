# Skill Summary Card: `data-management-architect`

```
┌────────────────────────────────────────────────────────────┐
│                    SKILL SUMMARY CARD                      │
├────────────────────────────────────────────────────────────┤
│ SKILL:       data-management-architect                     │
│ Category:    data_engineering / enterprise-architecture    │
│ Invocation:  /data-management-architect                    │
│ Trigger:     "enterprise data management",                 │
│              "data governance charter",                    │
│              "data quality profiling",                     │
│              "golden records", "data contracts",           │
│              "data observability", "lakehouse architecture",│
│              "data maturity assessment", "data as a product"│
│ Version:     1.0.0                                         │
│ Provides:    "enterprise_data_lifecycle_architecture"      │
├────────────────────────────────────────────────────────────┤
│ Target:      Architect, govern, engineer, and evaluate     │
│              enterprise data lifecycles from raw assets to │
│              governed data products across DAMA-DMBOK      │
│              capabilities, lakehouses, and modern DataOps. │
└────────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Data Management Lifecycle

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Governance & Charter** | Establish DIKW business value, appoint Owner/Steward, define RACI, classify security | `domain_charter.yaml` & RACI Matrix | Data Owner/Steward signed off; 4-tier classification approved |
| **2. Semantic Modeling** | Build Conceptual, Logical, and Dimensional models; codify Golden Record survivorship | Dimensional Schema & Master Resolution Spec | Models validated; Golden Record entity survivorship codified |
| **3. Contracted Ingestion** | Formulate Open Data Contracts (ODCS); implement Bronze $\rightarrow$ Silver $\rightarrow$ Gold lakehouse tiers | Open Data Contract & Idempotent Pipeline DAG | Validated machine-readable contract; idempotent DAG staged |
| **4. Quality & Observability** | Profile datasets; enforce 6 DAMA quality dimensions; wire 5-pillar observability | 6-Dimension Quality Report & Observability Telemetry | Quality score $\ge$ threshold; SLI/SLO circuit breaker active |
| **5. Products & Maturity** | Package F.A.T.S.I.S Data Products; deploy semantic layer; evaluate Level 0–5 maturity | Governed Data Product Spec & Maturity Roadmap | Catalog product published; Level 0–5 maturity evaluated |

---

## The Three Pillars Cheat Sheet

### 1. The DIKW Pyramid & Asset Progression
- **Data**: Unprocessed facts, strings, numbers (e.g., `42`, `"ALU-8942"`, timestamp).
- **Information**: Contextualized, structured data with schema and metadata (e.g., `"Student ALU-8942 enrolled in Master of AI on 2026-03-09"`).
- **Knowledge**: Synthesized patterns, operational insights, and decision rules (e.g., `"Students living > 15km from campus exhibit 35% higher transit subsidy demand"`).
- **Value**: Measurable organizational impact (e.g., optimized bus route schedules, improved retention, €120k cost savings).

### 2. The 6 DAMA Data Quality Dimensions
- **Accuracy**: Does the data correctly describe the real-world object or event?
- **Completeness**: Are all required attributes populated without unexpected nulls?
- **Consistency**: Are values uniform and non-contradictory across systems?
- **Timeliness / Freshness**: Is the data available within agreed SLA latency?
- **Validity**: Do values conform to expected syntax, schemas, and range constraints?
- **Uniqueness**: Are duplicate entity instances or event records eradicated?

### 3. Open Data Contracts & Medallion Pipeline Invariants
- **Open Data Contract**: Declarative YAML/JSON schema (ODCS) defining schema, types, SLAs, nullability, and quality assertions.
- **Bronze (Raw)**: Append-only, immutable landing zone preserving raw payload and source metadata.
- **Silver (Cleansed)**: Deduplicated, standardized, validated, and PII-masked entity records.
- **Gold (Curated)**: Business-level dimensional models and metrics ready for BI, semantic layers, and ML.

---

## Verification & Quality Checklist

- [ ] **Data Owner and Steward Designated**: Formal business authority and operational steward appointed with contact metadata.
- [ ] **Data Classification Assigned**: Data classified into Tier 1 (Public), Tier 2 (Internal), Tier 3 (Confidential), or Tier 4 (Restricted/PII).
- [ ] **3-Tier Modeling Completed**: Conceptual, Logical, and Dimensional star schemas validated against business glossary.
- [ ] **Master Data Survivorship Codified**: Deterministic + fuzzy entity resolution paired with explicit attribute survivorship rules.
- [ ] **Open Data Contract Enforced**: Pre-ingestion validation asserts schema, field types, and SLA freshness via `data_contract_validator.py`.
- [ ] **6-Dimension Quality Verified**: Automated profiling passes accuracy, completeness, consistency, timeliness, validity, and uniqueness gates.
- [ ] **5-Pillar Observability Wired**: Freshness, Volume, Schema, Distribution, and Lineage tracked with automated alert circuit-breakers.
- [ ] **Level 0–5 Maturity Assessed**: Evaluated across Governance, Architecture, Modeling, Quality, Security, and DataOps via `maturity_assessor.py`.
