```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: system-design-architect                                       │
│ Category: engineering / software-architecture                        │
│ Version: 1.0.0                                                       │
│ Invocation: /system-design-architect                                 │
│ Triggers: "system design", "system design interview",                │
│           "design software systems", "capacity estimation",          │
│           "design spotify", "design booking.com", "design whatsapp"  │
│ Requires: "deep-skill-forge", "deepen-architecture",                 │
│           "data-topology-mapper", "epistemic-memory-lifecycle"       │
│ Target: Production distributed system design, scaling & evaluation   │
└──────────────────────────────────────────────────────────────────────┘
```

# System Design Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Requirements & Scope** | Clarify functional/non-functional requirements & calculate capacity | Requirements & Capacity Spec | Core flows locked, SLAs set, QPS & storage estimated |
| **Stage 2: Data & API Modeling** | Define ER models, database paradigms & API contracts | Data Schema & API Contract | Schema indexed, SQL vs NoSQL justified, APIs defined |
| **Stage 3: High-Level Design** | Construct component topology & trace read/write flows | Architecture Topology DAG | Edge/Gateway/Service/Cache mapped, data flows traced |
| **Stage 4: Scale & Reliability** | Eliminate SPOFs, map sharding & prevent race conditions | Failure Mode & Scaling Plan | Bottlenecks mitigated, sharding & locking verified |
| **Stage 5: Trade-offs & Extension** | Reflect on compromises, alternative designs & day-2 ops | Trade-off Matrix & Roadmap | CAP compromises documented, alternatives evaluated |

---

## The 5 Senior Engineering Evaluation Dimensions

| Dimension | Weight | Target Senior / Staff Behavior | Common Red Flag |
|---|---|---|---|
| **1. Communication** | 20% | Collaborative peer dialogue; validates assumptions incrementally | Silent whiteboard drawing or non-stop monologue |
| **2. Structured Thinking** | 20% | Clear 5-step roadmap; deconstructs ambiguous problem spaces | Jumping chaotically between DB and UI before scope |
| **3. Technical Judgment** | 25% | Requirements-driven tool selection; defends architectural choices | Buzzword-driven tooling (Kafka/NoSQL) without rationale |
| **4. Practical Depth** | 25% | Anticipates real-world failure modes, concurrency & stampedes | Assuming 100% happy path; unable to handle crashes |
| **5. Time Management** | 10% | Paces across 45–60 min; aligns early on deep-dive focus | Spending 35 min on high-level boxes with no scaling |

---

## Canonical Case Studies Quick Reference

- **Spotify**: S3 Blob Storage + Global CDN (Range requests `0-1MB`), PostgreSQL metadata + Redis playlists, async Kafka transcoding pipeline. Read:Write = 50:1.
- **Booking.com**: Zero-double-booking guarantee, 2-phase reservation (`Pending` $\rightarrow$ `Reserved` $\rightarrow$ `Confirmed`), Redis Redlock (10–15m TTL) + DB optimistic locking (`version`), CQRS search cluster. Read:Write = 100:1.
- **WhatsApp**: Persistent WebSocket/TCP gateways, ephemeral Redis routing registry (User $\rightarrow$ Gateway), transient Cassandra/ScyllaDB mailboxes, E2EE Signal Protocol double ratchet.

---

## Mandatory Invariants Checklist

- [ ] **Requirements Before Architecture**: Never draw component topology or choose databases without locking functional scope and SLAs at Stage 1.
- [ ] **Quantitative Scale Grounding**: Always estimate peak QPS ($2\times \text{ to } 5\times \text{ average}$) and 5-year storage growth before selecting storage tiers.
- [ ] **No Unjustified Buzzwords**: Every chosen database (SQL vs NoSQL vs In-Memory) and protocol (REST vs gRPC vs WebSocket) must be justified by access patterns.
- [ ] **Mandatory Failure Mode Audit**: Every design must identify single points of failure (SPOFs) and define explicit redundancy and failover strategies.
- [ ] **Concurrency & Locking Discipline**: High-contention reservation and inventory systems must define explicit locking mechanisms (Optimistic vs Pessimistic/Redlock).
- [ ] **Active Time Pacing**: Allocate time proactively across the 5 stages (5–10m requirements, 15–20m data, 15–20m architecture, 10–15m scaling, 5m trade-offs).
