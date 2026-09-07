# Open Data Contracts and Contract-First Medallion Lakehouse Engineering

**ID:** `ki_solla_contract_first_medallion_lakehouse`  
**Category:** `data_engineering`  
**Origin:** *From Data to Value: Understanding Data Management Through a Real World Use Case* (Daniel García Solla, freeCodeCamp / DAMA-DMBOK)  
**Provenance Lineage:** Sections: "Data Architecture" & "Data Engineering", freeCodeCamp, 2026.

## Executive Summary
Data platforms fail silently when upstream producers alter schemas, change data types, or violate semantic assumptions without notifying consumers. Open Data Contracts (ODCS) turn unstated assumptions into machine-readable, testable obligations. In lakehouse environments, data contracts govern the progression across the Medallion architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold), guaranteeing data reliability, idempotency, and lineage transparency.

### Open Data Contract Standard (ODCS) Specification
A Data Contract binds producers and consumers with explicit terms:
1. **Schema & Types**: Explicit declaration of field names, physical data types, nullability constraints, and primary keys.
2. **Business Semantics**: Column descriptions, allowed enum values, and domain units (e.g., `price` strictly in euros, GPS coordinates as numeric float pairs).
3. **Operational SLAs**: Maximum ingestion latency, delivery frequency (e.g., updates posted every 15 minutes), and freshness commitments.
4. **Change Management Protocol**: Breaking schema changes require major semantic version increments ($X.0.0$) and advance notice to consumers.

### The Medallion Lakehouse Architecture
1. **Bronze Tier (Raw Ingestion)**:
   - Immutable, append-only landing zone preserving the raw input payloads exactly as delivered by sources (JSON, Parquet, CSV).
   - Augmented with technical metadata: `_ingested_at`, `_source_file_id`, and `_batch_id`.
   - Never modified or cleaned in place.
2. **Silver Tier (Cleansed & Conformed)**:
   - Enforces contract schema validation.
   - Cleanses, deduplicates, and standardizes formats (e.g., date formats, address strings).
   - Resolves master entity references (e.g., linking taxi ride events to canonical Student Golden Records).
   - Masks or pseudonymizes sensitive PII attributes.
3. **Gold Tier (Curated Business Marts)**:
   - Star schema dimensional structures optimized for query performance (Fact tables with additive/semi-additive metrics; Conformed Dimension tables).
   - Powers governed BI dashboards, metric semantic layers, and machine learning feature stores.

### Pipeline Idempotency & Determinism
Data pipelines must be strictly idempotent: executing a pipeline multiple times over the same input partition must yield identical results without duplicate records or orphaned state. Write operations use atomic append or merge-upsert (`MERGE INTO target USING staging ON target.id = staging.id`) patterns.

## Core Architectural Invariants
1. **Contract-Before-Code Invariant**: Never deploy a data pipeline ingestion job without an approved, versioned Open Data Contract.
2. **Medallion Progression Rule**: Downstream analytical consumers must query Gold marts or validated Silver views, never raw Bronze buckets directly.
