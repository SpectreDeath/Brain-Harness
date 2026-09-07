---
name: data-management-architect
description: Architect, govern, engineer, and evaluate enterprise data lifecycles from raw assets to governed data products using DAMA-DMBOK capabilities, Open Data Contracts (ODCS), Medallion lakehouse pipelines, 6-dimension data quality gating, master data golden records, and Level 0-5 maturity roadmaps. Trigger when designing data governance models, establishing data ownership/stewardship, drafting data contracts, building lakehouse pipelines, resolving master entity identities, profiling data quality dimensions, or assessing organizational data maturity.
---

# Data Management Architect: Enterprise Data Lifecycle & Governance Engine

`data-management-architect` is the foundational architectural and operational skill for engineering production-grade enterprise data management systems. Distilled from Daniel García Solla's (*From Data to Value: Understanding Data Management Through a Real World Use Case [Full Book]*, freeCodeCamp / DAMA-DMBOK) comprehensive framework and hands-on laboratory, this skill operationalizes data from raw capture to measurable organizational value.

Rather than treating data management as isolated database administration or ad-hoc dashboarding, `data-management-architect` enforces the **Data-to-Value Lifecycle Continuum**:
1. **Data as an Asset & DIKW Pyramid**: Raw Data $\rightarrow$ Structured Information $\rightarrow$ Contextual Knowledge $\rightarrow$ Measurable Business Value.
2. **Governed Ownership & Decision Rights**: No data asset exists without a designated Data Owner (business authority) and Data Steward (operational quality/definitions).
3. **Contract-First Medallion Architecture**: Producers and consumers bind across machine-readable Open Data Contracts (ODCS) traversing Bronze (raw), Silver (cleansed), and Gold (curated business marts) tiers.
4. **6-Dimension Quality & 5-Pillar Observability**: Datasets must continuously satisfy Accuracy, Completeness, Consistency, Timeliness, Validity, and Uniqueness before ingestion into analytics or AI.
5. **Data Products & Federated Operating Models**: Packaging data assets with discoverable, addressable, trustworthy, and secure interfaces under modern Data Mesh governance.

---

## The 5-Stage Operational Progression

```
[1. Governance & Charter] → [2. Semantic Modeling & Golden Records] → [3. Contracted Ingestion & Pipelines] → [4. 6-Dimension Quality & Observability] → [5. Data Product Packaging & Maturity]
```

See [CARD.md](CARD.md) for the companion quick-reference card, 5-stage reference matrix, and quality checklist.
See [config.default.yaml](config.default.yaml) for operational quality thresholds, maturity scoring rubrics, and contract validation defaults.
See [references/dama_dmbok_quickref.md](references/dama_dmbok_quickref.md) for the DAMA-DMBOK capability matrix, DIKW mapping, and data classification standards.

---

## 1. Governance & Asset Inception (Plan & Charter)

Before provisioning databases or pipelines, establish the organizational control layer across the target data domain:

1. **Formulate the DIKW Value Hypothesis**:
   - Explicitly define the target business outcome (e.g., student attendance optimization, mobility transit fraud reduction, dynamic pricing).
   - Trace the lineage from raw data capture through information aggregation and domain knowledge to executive decision-making.
2. **Appoint Domain Governance Roles**:
   - **Data Owner**: Senior business leader with ultimate decision rights, budget authority, and accountability for data legitimacy in their domain (e.g., Director of Mobility, Registrar).
   - **Data Steward**: Operational subject matter expert responsible for day-to-day data definitions, business glossary terms, reference codes, and quality compliance.
   - **Chief Data Officer (CDO) / Governance Council**: Sets cross-domain data policy, standards, and conflict resolution.
3. **Codify Decision Rights & RACI Matrix**:
   - Specify who is **Responsible**, **Accountable**, **Consulted**, and **Informed** for data creation, schema modification, access grants, and deletion.
4. **Classify Data Security & Ethical Constraints**:
   - Assign data classification tiers:
     - **Tier 1: Public** — Non-sensitive marketing, public course catalogs, open transit stops.
     - **Tier 2: Internal** — General operations, aggregated statistics, non-sensitive schedules.
     - **Tier 3: Confidential** — Proprietary business metrics, financial billing, internal telemetry.
     - **Tier 4: Restricted / PII** — Personally Identifiable Information (student IDs, home addresses, geolocation, payment cards, medical transcripts).
   - Execute Privacy Impact Assessment: enforce GDPR/CCPA compliance, consent tracking, purpose limitation, and strict data minimization.

> **Completion criterion**: Domain charter established with formal Data Owner/Steward designation, RACI decision rights, and 4-tier data security classification.

---

## 2. Semantic Modeling & Golden Record Architecture (Model & Master)

Design technology-independent information architectures and resolve fragmented entity identities across operational silos:

1. **Author the 3-Tier Data Model**:
   - **Conceptual Data Model**: Map high-level business entities and semantic relationships (e.g., `Candidate` $\rightarrow$ `Student` $\rightarrow$ `Enrollment` $\rightarrow$ `Course`) independent of storage technology.
   - **Logical Data Model**: Specify normalized entities, attributes, primary/foreign keys, domain data types, and business constraints (e.g., intermediate `Enrollment` resolving M:N relationships).
   - **Physical & Dimensional Model**: Design optimized relational/columnar schemas (fact tables for measurable events like `fact_mobility_trips`, dimension tables like `dim_student`, `dim_vehicle`, `dim_date`).
   - Define Slowly Changing Dimension (SCD) policies (Type 1 overwrite, Type 2 historical row versioning with `valid_from`/`valid_to`, Type 3 previous-value column).
2. **Establish Reference & Master Data Architecture**:
   - **Reference Data**: Standardize lookup codes and taxonomies (e.g., ISO-3166 country codes, academic grade scales, payment status codes).
   - **Master Data**: Identify core business entities whose identity spans multiple applications (e.g., `Student`, `Faculty`, `Transit Provider`).
3. **Execute Entity Resolution & Survivorship**:
   - Deploy matching algorithms: deterministic match keys (National ID, Tax ID) followed by normalized fuzzy matching (Levenshtein distance, Jaro-Winkler) for names and addresses.
   - Codify **Survivorship Rules** to construct the canonical **Golden Record**:
     - *Source Authority Hierarchy*: Official registrar system takes precedence over mobility app for student legal names.
     - *Timestamp Recency*: Most recent verified update wins for residential address.
     - *Completeness / Non-Null Preference*: Populate missing fields from secondary sources.
     - *Manual Steward Override*: Flag ambiguous match candidates ($0.75 \le \text{confidence} < 0.90$) for human review.

### Executable Seam: `scripts/golden_record_resolver.py`
Resolve multi-source entity feeds into canonical Golden Records:
```python
from scripts.golden_record_resolver import GoldenRecordResolver, EntityRecord, SurvivorshipRule

resolver = GoldenRecordResolver(
    match_keys=["national_id", "email_normalized"],
    fuzzy_keys=[("full_name", 0.85)],
    survivorship_rules={
        "full_name": SurvivorshipRule.SOURCE_PRIORITY,
        "campus_distance_km": SurvivorshipRule.MOST_RECENT,
        "rideshare_benefit_approved": SurvivorshipRule.SOURCE_PRIORITY,
    },
    source_priority=["registrar_system", "mobility_portal", "admissions_crm"],
)
golden_records = resolver.resolve(records)
```

> **Completion criterion**: Conceptual/logical/dimensional models formalized; Master Data entity resolution and attribute survivorship rules codified.

---

## 3. Contracted Ingestion & Pipeline Orchestration (Integrate & Engineer)

Transform raw data feeds into robust, reproducible analytical assets through contract-first lakehouse engineering:

1. **Draft Machine-Readable Open Data Contracts (ODCS)**:
   - Formulate explicit agreements between data producers (e.g., external mobility provider, student portal) and data consumers.
   - Specify field types, physical formats, nullability, primary keys, description semantics, and update frequencies.
   - Codify operational SLAs: maximum ingestion latency, freshness guarantees, and breaking-change notification windows.
2. **Implement Medallion Lakehouse Tiers**:
   - **Bronze Layer (Raw Ingestion)**: Immutable, append-only landing zone storing raw payloads in native formats (JSON, Parquet, Avro) with ingestion metadata (`_ingested_at`, `_source_file`).
   - **Silver Layer (Cleansed & Standardized)**: Deduplicated, cleansed, and validated data. Enforce schema compliance, normalize addresses, resolve master entity IDs, and mask PII.
   - **Gold Layer (Curated Business Marts)**: Business-ready dimensional star schemas, aggregated metrics, and semantic data products optimized for BI and machine learning.
3. **Orchestrate Idempotent Pipeline DAGs**:
   - Implement pipeline jobs with deterministic idempotency: re-running a pipeline for date $T$ must produce identical results without duplicate rows.
   - Choose appropriate ingestion paradigms: Batch (scheduled ETL/ELT via dbt/Airflow), Streaming (real-time telemetry via Kafka/Spark Structured Streaming), or Event-Driven APIs.

### Executable Seam: `scripts/data_contract_validator.py`
Validate datasets against Open Data Contract definitions:
```python
from scripts.data_contract_validator import DataContractValidator

validator = DataContractValidator.from_yaml("contracts/mobility_trips_contract.yaml")
result = validator.validate_dataset(incoming_records)
assert result.is_compliant is True, f"Contract breached: {result.violations}"
```

> **Completion criterion**: Versioned Open Data Contract compiled and validated; Bronze/Silver/Gold pipeline DAG staged with idempotent recovery.

---

## 4. 6-Dimension Quality Gating & Observability (Validate & Monitor)

Eliminate silent data corruption through automated statistical profiling and continuous multi-pillar telemetry:

1. **Execute Comprehensive Data Profiling**:
   - Profile incoming columns for null percentage, cardinality, distinct count, data type compliance, min/max ranges, and value distributions.
   - Detect anomalies and outliers before propagating data downstream.
2. **Assert the 6 Canonical DAMA Data Quality Dimensions**:
   - **Accuracy**: Data reflects the real-world state (e.g., GPS coordinates fall within university municipality).
   - **Completeness**: Required attributes are populated without unexpected nulls or blanks.
   - **Consistency**: Values across systems and tables do not contradict each other (e.g., active mobility benefit matches enrolled student status).
   - **Timeliness / Freshness**: Data is available within agreed SLA intervals (e.g., trip events posted within 15 minutes of completion).
   - **Validity**: Values conform to standard syntaxes, ranges, and reference sets (e.g., valid email regex, valid ISO country codes).
   - **Uniqueness**: No duplicate records exist for the same logical event or primary key.
3. **Instrument 5-Pillar Data Observability**:
   - **Freshness**: Continuously monitor time-since-last-update against SLO thresholds.
   - **Volume**: Track record counts per partition; flag unexpected spikes or drops.
   - **Schema**: Monitor drift, unexpected new columns, or altered data types in real time.
   - **Distribution**: Monitor mean, variance, and frequency quantiles for statistical drift.
   - **Lineage**: Track upstream sources and downstream consumers via OpenLineage to determine blast radius.
4. **Wire Circuit Breakers & Quarantine**:
   - If quality assertions fail critical thresholds, automatically pause downstream pipeline steps and route defective records to a quarantine table for steward remediation.

### Executable Seam: `scripts/data_quality_profiler.py`
Profile datasets and evaluate 6-dimension quality scorecards:
```python
from scripts.data_quality_profiler import DataQualityProfiler

profiler = DataQualityProfiler()
scorecard = profiler.profile(dataset, rules_config="config.default.yaml")
print(f"Overall Quality Score: {scorecard.overall_score:.2f}/100")
assert scorecard.passed is True
```

> **Completion criterion**: Automated 6-dimension data quality profile report generated; quality assertions passed; 5-pillar observability SLIs/SLOs wired to circuit breakers.

---

## 5. Data Product Packaging & Value Delivery (Serve & Mature)

Package analytical assets into governed, self-describing Data Products and assess organizational maturity:

1. **Package as a Governed Data Product (F.A.T.S.I.S / DATS)**:
   - **Findable**: Registered in the enterprise Data Catalog with searchable business descriptions and tags.
   - **Addressable**: Accessible via stable, standardized endpoints (REST API, SQL semantic layer, Parquet/S3 uri).
   - **Trustworthy**: Accompanied by published Data Contracts, freshness SLOs, and quality scorecards.
   - **Self-Describing**: Embedded technical schema, documentation, usage guidelines, and sample queries.
   - **Interoperable**: Adheres to global standards (JSON, Parquet, ISO codes) for seamless joining.
   - **Secure**: Integrated with IAM, RBAC, column-level masking, and audit logging.
2. **Publish the Governed Semantic Layer**:
   - Maintain standardized metric definitions in a centralized semantic layer (e.g., Cube, dbt semantic layer) to prevent conflicting KPI calculations across departmental dashboards.
3. **Execute 6-Capability Maturity Assessment**:
   - Evaluate organizational practices across 6 domains (Governance, Architecture, Modeling, Quality, Security, DataOps) across **Levels 0 to 5**:
     - *Level 0 (No Capability)*: Ad-hoc, chaotic, unorganized actions.
     - *Level 1 (Initial)*: Heroic individual effort, no standardized control or repeatable processes.
     - *Level 2 (Managed)*: Documented processes and tools; localized replication.
     - *Level 3 (Defined)*: Formalized enterprise-wide policies, standards, and architectures.
     - *Level 4 (Measured)*: Quantitatively managed via automated metrics, audits, and SLAs.
     - *Level 5 (Optimized)*: Continuous improvement, predictive quality, and automated optimization.
   - Generate strategic gap analysis and prioritized remediation roadmaps.

### Executable Seam: `scripts/maturity_assessor.py`
Run the automated Data Management Maturity assessment:
```python
from scripts.maturity_assessor import MaturityAssessor

assessor = MaturityAssessor.from_yaml("assessment_input.yaml")
report = assessor.evaluate()
print(report.generate_summary_markdown())
```

> **Completion criterion**: Governed Data Product specification published in catalog with lineage; semantic layer deployed; Level 0–5 maturity scorecard evaluated.

---

## Deepened Kernel Integration: DataManagementEngine & Headless CLI

In addition to standalone utility scripts, `data-management-architect` provides a unified kernel engine (`DataManagementEngine` registered via `DATA_MANAGEMENT_SERVICE_KEY`) and a headless Click CLI interface (`harness data ...`).

### 1. Unified Engine Facade (`harness.services.data_management`)
Orchestrate end-to-end Medallion pipelines across Bronze, Silver, and Gold tiers with automated contract gating, 6-dimension quality scoring, and golden record resolution:
```python
from harness.services.data_management import DataManagementEngine, MedallionPipelineConfig

engine = DataManagementEngine()
result = engine.execute_medallion_pipeline(
    records=raw_records,
    config=MedallionPipelineConfig(
        contract_path="contracts/mobility_trips_contract.yaml",
        quality_config_path="config.default.yaml",
        source_system="admissions_crm",
        min_quality_score=75.0,
    ),
)
print(f"Pipeline Succeeded: {result.success}, Processed: {result.records_gold_count} Gold records")
```

### 2. Headless CLI Seam (`harness data ...`)
Execute governance and data management workflows directly from shell scripts or CI pipelines:
```bash
# Validate dataset against Open Data Contract
harness data validate --dataset records.json --contract contract.yaml

# Profile 6-dimension data quality scorecard
harness data profile --dataset records.json --rules config.yaml

# Resolve Master Data Golden Records across sources
harness data resolve --dataset multi_source.json --keys national_id,email

# Assess DAMA-DMBOK organizational maturity
harness data maturity --survey responses.yaml

# Run end-to-end Medallion Lakehouse pipeline
harness data pipeline --dataset raw.json --contract contract.yaml --quality config.yaml --source mobility_portal
```

---

## Visual Brief Pillar

The visual architecture and methodology flowchart must be maintained as an interactive HTML document:
- Location: `%TEMP%\book-to-skill-forge-<timestamp>.html` (or project artifact directory)
- Must render the **5-Stage Methodology Flowchart DAG** via Mermaid.js
- Must render the **Diagnostic Evaluation Scorecard Table** detailing stage gates and artifacts
- Must render the **Anti-Pattern Defense Matrix** with positive invariant rules

---

## Mandatory Checkpoint Gate

All data management implementations must enforce human-in-the-loop review at critical lifecycle junctures:
- Architectural changes (schema migrations, contract breaking versions, new master entities) require `RequestFeedback: true` in task planning.
- The agent must **STOP and wait** for explicit Data Owner / Steward approval before dropping columns, altering survivorship rules, or deprecating data products.

---

## Anti-Patterns

- **The Passive Data Swamp** — Dumping unstructured raw files into object storage without ownership, schema enforcement, classification, or metadata discovery.
- **Uncontracted Producer Drift** — Upstream producers unilaterally altering schema types, field names, or semantics without machine-readable contract checks.
- **Fragmented Identity & Split Brain** — Allowing multiple operational systems to hold conflicting master records without deterministic entity resolution and survivorship rules.
- **Post-Mortem Quality Inspection** — Discovering data errors only after executive dashboards break or ML pipelines fail downstream.
- **Monolithic Silo Bottlenecks** — Concentrating all data modeling and pipeline changes in a central bottleneck team instead of federated computational domain ownership.
- **Zombie Data Accumulation** — Indefinitely retaining obsolete, non-compliant, or unused data without lifecycle retention schedules and secure disposal procedures.
- **Metric Anarchy** — Allowing disparate departments to compute core business KPIs with divergent SQL formulas without a governed semantic layer.
