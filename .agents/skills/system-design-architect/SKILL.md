---
name: system-design-architect
description: Design, evaluate, and scale production distributed systems using the 5-step senior engineering framework, capacity estimation calculus, and 5-dimension interview scorecards. Do not use for low-level algorithm coding, single-process scripts, or generic prompt drafting.
---

# Senior Software System Design Architect

`system-design-architect` is the definitive system design and architectural engineering skill for designing, evaluating, and scaling production distributed systems. Synthesized directly from the curriculum and masterclass *Design Software Systems Like a Senior Engineer* by Hike Simon and Beau Carnes (freeCodeCamp.org), it enforces the **5-Step System Design Progression** and evaluates architectures across the **5 Senior Engineering Dimensions**.

System design evaluates **how you think and communicate** across ambiguous requirements, not merely whether you memorize static diagrams. This skill operationalizes structured problem decomposition, quantitative capacity calculations, and proactive production failure mode analysis.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and mandatory invariants checklist.
Consult `config.default.yaml` for default capacity thresholds and latency SLO budgets.

---

## The 5-Stage System Design Progression

```
[1. Requirements & Scope Lock] ──► [2. Data & API Modeling] ──► [3. High-Level Architecture]
                                                                        │
                                                                        ▼
[5. Trade-offs & Extension] ◄── [4. Scale & Failure Modes Deep Dive] ◄──┘
```

---

## 1. Requirements Clarification & Scope Lock (5–10 min)

Transform ambiguous, vague problem prompts into locked functional and non-functional specifications before designing:

1. **Clarify Functional Requirements (Core Flows)**:
   - Identify the 3 to 5 non-negotiable user capabilities: *"What functionalities, if removed, mean this system ceases to be itself?"* (e.g. Booking.com must search rooms and reserve inventory; WhatsApp must deliver messages and maintain connections).
   - Isolate edge flows to explicitly mark as out-of-scope for the initial design.
2. **Lock Non-Functional Requirements (SLAs/SLOs)**:
   - **Availability vs Consistency**: State CAP theorem priority (e.g. Booking.com demands strong consistency for room reservations; Spotify prioritizes high availability for streaming).
   - **Latency Bounds**: Read latency SLA (e.g. < 100ms p99) and write latency SLA (e.g. < 200ms p99).
   - **Durability & Security**: Data loss tolerance and encryption requirements (e.g. WhatsApp end-to-end encryption).
3. **Capacity & Scale Estimation (Top-Down vs Bottom-Up)**:
   - Calculate Daily Active Users (DAU), Read:Write Ratio, Average QPS, and Peak QPS ($2\times \text{ to } 5\times \text{ average}$).
   - Estimate Network Ingress and Egress Bandwidth ($\text{QPS} \times \text{payload size}$).
   - Project Storage Growth over 1 to 5 years ($\text{writes/day} \times \text{record size} \times 365 \times 5$).
4. **Establish Bounded Scope**:
   - Explicitly enumerate **In-Scope** versus **Out-of-Scope** components to prevent unbudgeted scope creep.

> **Completion criterion**: Functional requirements cataloged, non-functional SLAs locked, capacity estimates calculated, and scope boundaries agreed upon.

---

## 2. Data & API Modeling (15–20 min)

Formalize data contracts, storage paradigms, and network protocols prior to component topology:

1. **Entity-Relationship Data Modeling**:
   - Identify primary entities, attributes, and relationships (1:1, 1:N, N:M).
   - Establish primary keys, foreign keys, partition keys, and query indexes.
2. **Database Paradigm Selection & Technical Justification**:
   - **Relational SQL (PostgreSQL/MySQL)**: Structured relational entities, ACID transactional consistency, complex joins (e.g. Booking.com reservations, Spotify artist/album catalog).
   - **NoSQL Document / Wide-Column (Cassandra/DynamoDB/ScyllaDB)**: Massive write throughput, time-series data, high horizontal scale (e.g. WhatsApp message mailboxes, Spotify track playback analytics).
   - **In-Memory Key-Value (Redis/Memcached)**: Ephemeral routing tables, session state, distributed locks (Redlock), and caching layers.
   - **Object / Blob Storage (S3/GCS)**: Static media assets, raw audio segments (Spotify), and user attachments.
3. **API Contract & Protocol Specification**:
   - Define exact API endpoints, HTTP methods, payload schemas, and response codes.
   - Select protocol based on access pattern: REST for stateless CRUD, gRPC for inter-service RPC, WebSocket/TCP for persistent bi-directional streams (WhatsApp).

> **Completion criterion**: Entity schemas defined, database paradigms technically justified, API contracts drafted, and protocol selections aligned with SLAs.

---

## 3. High-Level Architecture Design (15–20 min)

Construct the end-to-end component topology and trace primary read and write data flows:

1. **Ingress & Edge Routing Layer**:
   - DNS routing, Anycast IP, and Global CDN edge caching for static assets and media chunks (e.g. Cloudflare, Fastly).
   - API Gateway / Reverse Proxy (Envoy, Nginx) handling TLS termination, rate limiting, authentication, and request routing.
2. **Core Domain Microservices Tier**:
   - Decompose monolithic domains into single-responsibility stateless services (e.g. Search Service, Booking Service, Audio Ingestion Service, Connection Manager).
   - Ensure services scale horizontally behind load balancers.
3. **Data & Storage Tiering**:
   - Connect domain services to primary databases, read replicas, and caching clusters.
   - Integrate asynchronous message brokers (Kafka, RabbitMQ, SQS) to decouple write-heavy ingestion from downstream analytics and notifications.
4. **End-to-End Data Flow Trace**:
   - Walk through the step-by-step **Read Flow** from client request through CDN, Cache, and Read Replica.
   - Walk through the step-by-step **Write Flow** from client submission through Gateway, Service, Lock Manager, Primary Database, and Message Queue.

> **Completion criterion**: Comprehensive architecture topology mapped with clear ingress, microservices, caches, and end-to-end read/write data flows.

---

## 4. Scalability, Failure Modes & Reliability Deep Dive (10–15 min)

Stress-test the architecture against production scale, concurrency bottlenecks, and single points of failure:

1. **Single Point of Failure (SPOF) Identification & Elimination**:
   - Audit every component: *"What happens if this database, gateway, or cache fails?"*
   - Implement multi-AZ and multi-region active-passive or active-active redundancy with automated failover.
2. **Horizontal Scaling & Data Partitioning (Sharding)**:
   - Formulate sharding strategy: Range-based, Hash-based, or Consistent Hashing (Virtual Nodes).
   - Resolve rebalancing costs, cross-shard joins, and hot-shard / celebrity keys (e.g. Spotify viral song, WhatsApp popular group).
3. **Concurrency Control & Race Condition Prevention**:
   - **Optimistic Locking**: Version column checks (`WHERE version = :expected`) for low-contention environments.
   - **Pessimistic Locking / Distributed Leases**: Redis Redlock or ZooKeeper mutexes with short TTLs (10–15 min) to prevent double bookings in reservation systems.
4. **Caching Strategy & Stampede Protection**:
   - Strategy: Cache-Aside (Lazy Loading), Write-Through, or Write-Behind.
   - Invalidation & Eviction: TTL expiration, LRU/LFU policy, and distributed mutexes/probabilistic early expiration (XFetch) to prevent cache stampedes.
5. **Resilience & Fault Tolerance**:
   - Circuit breakers, exponential backoff with jitter, dead-letter queues (DLQ), and graceful degradation.

> **Completion criterion**: Single points of failure eliminated, sharding keys selected, concurrency locks verified, and caching stampede defenses established.

---

## 5. Trade-off Reflection & Extensions (5 min)

Conduct an objective architectural post-mortem and propose production refinements:

1. **Explicit Architectural Trade-offs**:
   - Articulate compromises made: *"We chose Cassandra over PostgreSQL for message history to optimize write throughput at the expense of complex cross-entity transactional joins."*
   - Evaluate CAP theorem trade-offs: Consistency vs Availability during network partitions.
2. **Alternative Approaches Evaluated**:
   - Compare rejected alternatives: Explain why WebSockets were selected over HTTP long-polling, or why Redis Redlock was chosen over pure SQL row locks.
3. **Production Extensions & Day-2 Operations**:
   - Observability: Distributed tracing (OpenTelemetry), metrics (Prometheus), structured logging.
   - Multi-region deployment, disaster recovery RTO/RPO targets, and cost optimization.

> **Completion criterion**: Architectural trade-offs explicitly documented, alternative designs contrasted, and operational scaling roadmap finalized.

---

## The 5 Senior Engineering Evaluation Dimensions

In production audits and senior/staff interviews, candidates and systems are graded across five dimensions:

| Dimension | Weight | Senior / Staff Evaluation Criteria |
|---|---|---|
| **1. Communication & Collaboration** | 20% | Treats the reviewer/interviewer as a peer colleague; asks clarifying questions upfront; validates assumptions incrementally; balances speaking with listening. |
| **2. Structured Decomposition** | 20% | Outlines the 5-step roadmap; deconstructs ambiguous problem spaces into crisp functional blocks; maintains structured progression without erratic jumps. |
| **3. Technical Judgment** | 25% | Selects databases, protocols, and architectural tiers strictly based on requirements and access patterns; justifies trade-offs; rejects buzzwords without merit. |
| **4. Practical Depth** | 25% | Proactively anticipates production failure modes, concurrency race conditions, network partitions, cache stampedes, and failover scenarios. |
| **5. Time Management & Pacing** | 10% | Actively manages pacing across the 45–60 minute session; aligns early on deep-dive focus areas; drives the discussion to a conclusive wrap-up. |

---

## Canonical Production Case Studies

### 1. Spotify (Audio Streaming Platform)
- **Audio Delivery:** S3 / Blob Storage + Global CDN with HTTP Range Requests (`Range: bytes=0-1048575`) and pre-buffering.
- **Metadata Management:** PostgreSQL for artist/album/track catalog + Redis cluster for user playlists and recommendations.
- **Audio Transcoding:** Asynchronous message queue (Kafka) triggering worker nodes for multi-bitrate AAC/OGG encoding.
- **Scale:** 500M+ users, > 95% CDN cache hit ratio, read:write ratio 50:1.

### 2. Booking.com (Hotel Reservation & Inventory System)
- **Zero-Double-Booking Guarantee:** 2-phase reservation state machine (`Pending` $\rightarrow$ `Reserved` $\rightarrow$ `Confirmed` $\rightarrow$ `Expired`/`Cancelled`).
- **Concurrency Control:** Short-lived distributed lease (Redis Redlock with 10–15 min TTL) + Optimistic locking on room inventory (`version` column).
- **Search & Filtering:** CQRS architecture with Elasticsearch/OpenSearch read cluster decoupled from transactional booking database.
- **Scale:** 1.1B annual reservations, 500M monthly web visits, read:write ratio 100:1.

### 3. WhatsApp (Global Real-Time Messaging)
- **Connection Management:** Stateful WebSocket / TCP gateways managing millions of persistent connections per cluster.
- **Session Registry:** Ephemeral Redis distributed routing table mapping User IDs to active Gateway instances with heartbeat monitoring.
- **Message Storage:** Transient mailbox queues (Cassandra / ScyllaDB) with automatic message purge upon client delivery ACK.
- **E2EE Security:** Signal Protocol double ratchet algorithm; public identity keys hosted on key server; private keys never leave local client devices.

---

## The Three Foundational Pillars

### 1. The Visual Brief
Every system design engagement renders a self-contained HTML visual brief at `%TEMP%\system-design-brief-<timestamp>.html` featuring Mermaid sequence and topology diagrams, capacity calculations, and 5-dimension scorecard evaluations.

### 2. Mandatory Checkpoint Gate
When designing complex multi-tier platforms or auditing enterprise architectures, the architect presents an `implementation_plan.md` artifact with `RequestFeedback: true`. STOP and await explicit user approval before generating infrastructure code or deep-module models.

### 3. Explicit Anti-Patterns
Rigid boundaries prevent superficial whiteboard drawing, buzzword inflation, and ungrounded architecture sprawl.

---

## Anti-Patterns

- **Premature Architecture Drawing** — Jumping directly into drawing boxes and database schemas before clarifying requirements and agreeing on scope boundaries.
- **Buzzword-Driven Tool Selection** — Defaulting to trendy technologies (Kafka, GraphQL, Cassandra, Microservices) without concrete requirement or throughput justification.
- **Monologue or Deafening Silence** — Talking non-stop without inviting feedback, or staying completely silent while diagramming without explaining thought processes.
- **Ignoring Production Failure Modes** — Assuming 100% happy-path uptime; failing to analyze what happens when Redis nodes crash, databases hit IOPS caps, or network partitions occur.
- **Unbudgeted Scope Blowout** — Attempting to design the entire universe of features in a single session rather than locking in 3 to 5 core functional flows.
- **Untracked Time Allocation** — Spending 35 minutes on high-level box drawing, leaving zero time for scaling bottlenecks, concurrency locks, or trade-off analysis.
