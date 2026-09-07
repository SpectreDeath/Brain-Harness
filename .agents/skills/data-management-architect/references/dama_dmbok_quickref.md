# DAMA-DMBOK & Enterprise Data Management Quick Reference

This reference synthesizes the core concepts from Daniel García Solla's *From Data to Value: Understanding Data Management Through a Real World Use Case* and the **DAMA-DMBOK (Data Management Body of Knowledge)** framework.

---

## 1. The 11 DAMA-DMBOK Knowledge Areas

```
                         ┌─────────────────────────┐
                         │     DATA GOVERNANCE     │
                         └────────────┬────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
┌────────┴─────────┐         ┌────────┴─────────┐         ┌────────┴─────────┐
│ Data Architecture│         │ Data Development │         │ Data Operations  │
│  & Modeling      │         │ & Interoperability│        │ & Storage        │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
┌────────┴─────────┐         ┌────────┴─────────┐         ┌────────┴─────────┐
│ Data Security &  │         │ Reference &      │         │ Data Warehousing │
│ Privacy          │         │ Master Data (MDM)│         │ & Analytics / BI │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
┌────────┴─────────┐         ┌────────┴─────────┐         ┌────────┴─────────┐
│ Document & Content│        │ Metadata         │         │ Data Quality     │
│ Management       │         │ Management       │         │ Management       │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

1. **Data Governance**: Strategy, stewardship, policy formulation, decision rights (RACI), and regulatory compliance.
2. **Data Architecture**: Enterprise data structures, data domains, information flows, and target state blueprint.
3. **Data Modeling & Design**: Conceptual, Logical, and Physical schemas; ER modeling and dimensional star schemas.
4. **Data Storage & Operations**: RDBMS, NoSQL, object stores, cloud lakehouses, backup, and high-availability ops.
5. **Data Security & Privacy**: Classification, access control (IAM/RBAC/ABAC), encryption, masking, and privacy controls (GDPR/CCPA).
6. **Data Integration & Interoperability**: Ingestion (batch, streaming, API), ETL/ELT pipelines, and Open Data Contracts.
7. **Document & Content Management**: Unstructured information, document capture (OCR), taxonomy indexing, and retention.
8. **Reference & Master Data Management (MDM)**: Standardized codes, entity resolution, golden records, and survivorship rules.
9. **Data Warehousing & Business Intelligence**: Analytical repositories, facts, dimensions, metrics, and semantic layers.
10. **Metadata Management**: Business glossary, technical schemas, operational metrics, data catalogs, and end-to-end lineage.
11. **Data Quality Management**: Profiling, 6-dimension evaluation, validation rules, monitoring, and remediation.

---

## 2. The DIKW Hierarchy (From Data to Value)

| Level | Definition | Characteristics | University & Mobility Example |
|---|---|---|---|
| **Data** | Discrete, unorganized raw facts, symbols, or observations. | Lacks context; raw numbers, strings, or timestamps. | `ALU-8942`, `18.2`, `2026-03-09T08:14:00Z` |
| **Information** | Data organized, contextualized, and given meaning with schema and units. | Answers *Who, What, Where, When*. | *"Student ALU-8942 lives 18.2 km from campus and booked a transit trip on 2026-03-09."* |
| **Knowledge** | Synthesized information combined with experience, context, and rules. | Answers *How* and *Why*; actionable insight. | *"Students living > 15 km away have a 68% likelihood of using mobility subsidies during exam weeks."* |
| **Value** | Tangible business benefit and optimal decision-making. | Measurable ROI, risk mitigation, or operational improvement. | Efficient route capacity planning, 22% lower subsidy overhead, improved graduation retention. |

---

## 3. Data Classification Matrix

| Tier | Sensitivity | Description | Examples | Security Controls |
|---|---|---|---|---|
| **Tier 1** | **Public** | Information approved for public distribution; zero impact if disclosed. | Course catalogs, public transit route maps, press releases. | Integrity protection; open access. |
| **Tier 2** | **Internal** | Normal internal business data; moderate impact if leaked. | Standard operational schedules, internal policies, aggregated metrics. | Authentication required; role-based access. |
| **Tier 3** | **Confidential** | Sensitive commercial, operational, or financial data; serious harm if breached. | Tuition fee strategies, partner contract negotiations, unreleased financials. | Encryption in transit & rest; strict RBAC; audit logging. |
| **Tier 4** | **Restricted / PII** | Highly sensitive personal data, regulatory protected information. | Student IDs, home addresses, geolocation traces, payment cards. | Mandatory encryption, pseudonymization/masking, least privilege, DPIA. |

---

## 4. Medallion Lakehouse Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  BRONZE LAYER   │       │  SILVER LAYER   │       │   GOLD LAYER    │
│  (Raw Ingestion)│ ────> │  (Cleansed MDM) │ ────> │ (Curated Marts) │
└─────────────────┘       └─────────────────┘       └─────────────────┘
 • Immutable append-only   • Schema validated        • Star schema facts & dims
 • Preserves raw payloads  • Deduplicated            • Business metrics & KPIs
 • Ingestion timestamp     • Master entity resolved  • Semantic layer ready
 • Source metadata         • PII masked / redacted   • Optimized for BI & ML
```

---

## 5. The 6 DAMA Data Quality Dimensions

1. **Accuracy**: The degree to which data correctly represents the real-world entity or event.
2. **Completeness**: The proportion of stored data against the potential 100% complete dataset (absence of unexpected nulls).
3. **Consistency**: The absence of contradiction between different representations of the same data item across systems.
4. **Timeliness (Freshness)**: The availability of data within the expected timeframe and SLA from the moment of the event.
5. **Validity**: The conformity of data values to established domain standards, syntaxes, formats, and ranges.
6. **Uniqueness**: The property that no real-world entity or event exists more than once in the dataset.

---

## 6. Data Management Maturity Levels (Level 0 to 5)

- **Level 0 (No Capability)**: Ad-hoc, chaotic activities. No documented data practices.
- **Level 1 (Initial)**: Individual heroics. Specific people manage data with uncoordinated tools.
- **Level 2 (Managed)**: Repeatable processes. Roles and standard tools documented at department level.
- **Level 3 (Defined)**: Enterprise standards. Unified policies, semantic models, and data governance councils active.
- **Level 4 (Measured)**: Quantitatively controlled. Automated quality scorecards, observability SLIs, and audited compliance.
- **Level 5 (Optimized)**: Continuous improvement. Predictive quality, automated contract testing, and data product innovation.
