# Data Governance, Stewardship Roles, and RACI Decision Rights

**ID:** `ki_solla_dmbok_governance_decision_rights`  
**Category:** `data_engineering`  
**Origin:** *From Data to Value: Understanding Data Management Through a Real World Use Case* (Daniel García Solla, freeCodeCamp / DAMA-DMBOK)  
**Provenance Lineage:** Sections: "Data Governance" & "Data Security and Privacy", freeCodeCamp, 2026.

## Executive Summary
Data Governance defines how an organization exercises authority, control, and decision rights over its data assets throughout their lifecycle. Without formal governance, systems diverge into ungoverned silos, security controls erode, and decisions are made on conflicting metrics. Governance separates strategic business ownership from operational stewardship and technical engineering through formal RACI accountability matrices.

### Governance Roles & Separation of Concerns
1. **Chief Data Officer (CDO) / Governance Council**: Defines organizational data strategy, chairs the Data Governance Council, establishes cross-domain policies, and resolves jurisdictional disputes.
2. **Data Owner**: Senior business executive (e.g., Director of Mobility, Academic Registrar) who holds authority, budget, and ultimate accountability for the data within their domain. Approves access requests, classification tiers, and retention rules.
3. **Data Steward**: Operational subject matter expert embedded in the business domain. Responsible for maintaining data definitions, business glossaries, valid reference codes, data quality rules, and investigating data defects.
4. **Data Architect & Engineers**: Technical custodians who implement physical storage, pipeline orchestration, security masking, and automated data quality assertions.

### Decision Rights & The RACI Framework
For every data asset, the RACI roles must be formally codified:
- **Responsible (R)**: The engineer or analyst performing the work (e.g., building ingestion pipeline, updating schema).
- **Accountable (A)**: The single Data Owner with veto power and sign-off authority.
- **Consulted (C)**: Data Stewards, Privacy Officers, and downstream consumers providing input.
- **Informed (I)**: Consumers, BI analysts, and stakeholders notified of changes.

### 4-Tier Data Classification Standard
1. **Tier 1: Public**: Approved for public distribution (course catalogs, public transit stops). Zero damage if leaked.
2. **Tier 2: Internal**: Standard business operations and non-sensitive metrics. Moderate internal damage if leaked.
3. **Tier 3: Confidential**: Proprietary operational or financial information (tuition strategies, vendor contracts). Serious harm if disclosed.
4. **Tier 4: Restricted / PII**: Personally Identifiable Information and regulatory protected data (student IDs, residential addresses, GPS tracks, payment details). Requires encryption at rest/transit, dynamic masking, and strict purpose limitation.

## Core Architectural Invariants
1. **Single Accountable Owner Rule**: Every data domain must have exactly one designated business Data Owner.
2. **Least Privilege Invariant**: Access to Tier 3 and Tier 4 data must be governed by RBAC/ABAC with explicit expiration and audit logging.
