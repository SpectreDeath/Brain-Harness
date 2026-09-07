# The 6 DAMA Quality Dimensions and 5-Pillar Data Observability

**ID:** `ki_solla_six_dimension_quality_observability`  
**Category:** `data_engineering`  
**Origin:** *From Data to Value: Understanding Data Management Through a Real World Use Case* (Daniel García Solla, freeCodeCamp / DAMA-DMBOK)  
**Provenance Lineage:** Sections: "Data Quality" & "Data Observability", freeCodeCamp, 2026.

## Executive Summary
Data quality cannot be inspected into a system post-hoc; it must be engineered into every stage of the lifecycle. The DAMA-DMBOK establishes 6 canonical data quality dimensions that evaluate the fitness of data for operations and analytics. Complementing static quality rules, 5-pillar Data Observability provides continuous dynamic telemetry, inferring internal health from data freshness, volume, distribution, schema, and lineage signals.

### The 6 DAMA Quality Dimensions
1. **Accuracy**: The degree to which data correctly represents the real-world event or object (e.g., coordinates correspond to valid physical municipal locations; taxi fares match calculated meter rates).
2. **Completeness**: Proportion of required attributes populated with non-null values (e.g., student records contain verified identification and enrollment dates).
3. **Consistency**: Absence of logical contradiction across systems and tables (e.g., rideshare subsidy status in mobility matches active tuition enrollment in registrar).
4. **Timeliness (Freshness)**: Availability of data within the expected SLA timeframe from the occurrence of the real-world event.
5. **Validity**: Conformity of data values to defined domain syntaxes, formats, and code ranges (e.g., email matches RFC-5322 regex; status belongs to an approved enum set).
6. **Uniqueness**: Elimination of duplicate records for the same logical event or primary key entity.

### The 5 Pillars of Data Observability
1. **Freshness**: Continuous monitoring of the age of the latest partition against Service Level Objectives (SLOs).
2. **Volume**: Detection of unexpected row count spikes or drops that signal upstream pipeline omissions or dropped connections.
3. **Schema**: Real-time alerting on unexpected schema mutations, dropped columns, or altered data types before downstream consumers break.
4. **Distribution**: Statistical monitoring of mean, variance, and quantiles to detect silent semantic drift or corrupted data inputs.
5. **Lineage**: Upstream and downstream dependency mapping to calculate blast radius and perform instant root cause analysis during incidents.

### Circuit Breaker & Quarantine Gate
When quality assertions or observability SLIs breach critical thresholds, pipelines must trip automated circuit breakers. Defective batches are routed to an isolated quarantine store for Data Steward triage, preventing poisoned data from contaminating Gold business marts or production ML models.

## Core Architectural Invariants
1. **In-Line Quality Gating Invariant**: Data must never progress from Bronze to Silver without automated validation passing all critical quality dimensions.
2. **Deterministic Quarantine Rule**: Defective records must be quarantined alongside failure metadata without halting healthy record propagation.
