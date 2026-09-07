# The DIKW Pyramid & Data Lifecycle Asset Progression

**ID:** `ki_solla_dikw_data_asset_continuum`  
**Category:** `data_engineering`  
**Origin:** *From Data to Value: Understanding Data Management Through a Real World Use Case* (Daniel García Solla, freeCodeCamp / DAMA-DMBOK)  
**Provenance Lineage:** Section: "Data Management Fundamentals", freeCodeCamp, 2026.

## Executive Summary
Data is an organizational asset, but raw data alone does not create economic or strategic value. Raw observations must traverse the DIKW (Data $\rightarrow$ Information $\rightarrow$ Knowledge $\rightarrow$ Value) pyramid through structured metadata, quality profiling, and operational context. Managing data as an asset requires governing it across its 5-phase continuous lifecycle (Plan $\rightarrow$ Create/Acquire $\rightarrow$ Store/Maintain $\rightarrow$ Use/Share $\rightarrow$ Archive/Dispose).

### The DIKW Pyramid
1. **Data**: Unprocessed facts, strings, numbers, or timestamps devoid of interpretive context (e.g., `18.2`, `"ALU-2026-8942"`).
2. **Information**: Data structured with schema, data types, and descriptive metadata answering *Who, What, When, Where* (e.g., `"Student ALU-2026-8942 lives 18.2 km from campus and booked a transit trip on 2026-03-09"`).
3. **Knowledge**: Synthesized information combined with rules, experience, and domain context answering *How* and *Why* (e.g., `"Students living > 15 km away have a 68% likelihood of utilizing subsidized taxi benefits during examination weeks"`).
4. **Value**: Measurable organizational outcome, cost reduction, or strategic advantage (e.g., optimized transit route scheduling, 22% lower subsidy overhead, improved academic retention).

## The 5-Phase Data Lifecycle
1. **Plan**: Define business objectives, required data models, metadata standards, and privacy requirements before collection.
2. **Create / Acquire**: Capture data via operational applications, third-party provider feeds, or batch/streaming APIs under explicit contracts.
3. **Store / Maintain**: Persist data in secure, accessible storage tiers (RDBMS, Lakehouse, Object storage) with automated backups and master entity survivorship.
4. **Use / Share**: Deliver governed data products to authorized business consumers, BI dashboards, analytical semantic layers, and ML feature stores.
5. **Archive / Dispose**: Enforce data retention schedules, migrate stale data to cold storage, and securely purge non-compliant or expired PII records.

## Core Architectural Invariants
1. **Context-Required Invariant**: Raw data must never be exposed to decision-makers without metadata documenting units, calculation logic, and freshness.
2. **Lifecycle Continuity Invariant**: Real-world data moves through lifecycle phases iteratively; data enrichment and schema evolution must maintain backwards compatibility.
