# Knowledge Item: Senior Software System Design Architecture

## Epistemic Distillation

### 1. Paradigm: Thinking Process Over Memorized Architectures
The fundamental differentiator between junior/mid-level engineers and senior/staff engineers in system design is the **nature of evaluation**:
- In coding interviews (e.g. LeetCode), problems have explicit inputs, outputs, and deterministic unit tests.
- In system design, requirements are intentionally ambiguous, and **there is no single right answer**.
- Interviewers and architecture review boards evaluate candidates across **five distinct dimensions**:
  1. **Communication & Collaboration (20%)**: Treating reviewers as peer colleagues; verifying requirements upfront; validating assumptions incrementally; avoiding monologues or prolonged silence.
  2. **Structured Decomposition (20%)**: Establishing a clear 5-step roadmap; decomposing vague requirements into bounded functional blocks; maintaining structured progression without erratic jumps.
  3. **Technical Judgment (25%)**: Selecting storage paradigms, network protocols, and architectural tiers strictly based on access patterns and SLAs; rejecting buzzwords without concrete justification.
  4. **Practical Depth (25%)**: Proactively spotting production failure modes, concurrency race conditions, network partitions, cache stampedes, and single points of failure (SPOFs).
  5. **Time Management & Pacing (10%)**: Actively pacing across 45–60 minutes; aligning early on deep-dive focus areas; ensuring the design reaches a conclusive architectural wrap-up.

---

### 2. The 5-Step System Design Progression

```
[1. Requirements & Scope Lock] ──► [2. Data & API Modeling] ──► [3. High-Level Architecture]
  (5–10 min)                         (15–20 min)                    (15–20 min)
                                                                           │
                                                                           ▼
[5. Trade-offs & Reflection] ◄── [4. Scale & Failure Modes Deep Dive] ◄────┘
  (5 min)                          (10–15 min)
```

1. **Stage 1: Requirements Clarification & Scope Lock (5–10 min)**:
   - Identify non-negotiable core user flows: *"What functionalities, if removed, mean this system ceases to be itself?"*
   - Establish non-functional SLAs: Latency bounds (p99 read/write), Availability vs Consistency (CAP priority), and durability.
   - Enforce explicit boundaries: Catalog what is **In-Scope** versus **Out-of-Scope**.
2. **Stage 2: Data & API Modeling (15–20 min)**:
   - Formalize entity-relationship models, primary/partition keys, and query indexes.
   - Select storage paradigms: Relational SQL for ACID transactions; NoSQL wide-column for massive write scale; In-Memory Key-Value for sessions and distributed locks; Object Storage for media.
   - Define API contracts and choose protocols: REST for stateless CRUD, gRPC for inter-service RPC, WebSocket/TCP for persistent bi-directional streams.
3. **Stage 3: High-Level Architecture (15–20 min)**:
   - Ingress layer: DNS Anycast, global CDN edge caching, and API Gateway (rate limiting, auth, TLS termination).
   - Core domain microservices: Stateless compute scaling horizontally behind load balancers.
   - Data tiering: Primary databases, read replicas, caching clusters (Redis), and asynchronous message queues (Kafka, RabbitMQ).
   - End-to-end data flow walkthrough for primary read and write paths.
4. **Stage 4: Scale, Failure Modes & Reliability (10–15 min)**:
   - Single Point of Failure (SPOF) elimination: Multi-AZ/multi-region active-passive or active-active failover.
   - Horizontal sharding: Range vs Hash vs Consistent Hashing with virtual nodes; handling celebrity keys.
   - Concurrency control: Optimistic locking (versioning) vs Distributed leases (Redis Redlock).
   - Cache protection: Cache-Aside strategy; mitigating cache stampedes via distributed mutexes or probabilistic early expiration.
5. **Stage 5: Trade-offs & Extension (5 min)**:
   - Explicit architectural trade-offs: Consistency vs Availability compromises documented.
   - Justify rejected alternatives; outline operational monitoring and day-2 scalability.

---

### 3. Quantitative Capacity Estimation Calculus
Capacity estimation anchors architectural decisions in concrete physics:
- **Throughput Calculus**:
  $$\text{Daily Reads} = \text{DAU} \times \text{Reads/User/Day}$$
  $$\text{Avg Read QPS} = \frac{\text{Daily Reads}}{86,400}$$
  $$\text{Peak Read QPS} = \text{Avg Read QPS} \times \text{Peak Multiplier (typically } 2\times \text{ to } 5\times)$$
- **Storage Calculus**:
  $$\text{Daily Storage} = \text{Daily Writes} \times \text{Avg Write Payload Bytes}$$
  $$\text{5-Year Storage} = \text{Daily Storage} \times 365 \times 5$$
- **Network Bandwidth Calculus**:
  $$\text{Ingress Bandwidth (Mbps)} = \frac{\text{Avg Write QPS} \times \text{Write Payload Bytes} \times 8}{1,000,000}$$
  $$\text{Egress Bandwidth (Mbps)} = \frac{\text{Avg Read QPS} \times \text{Read Payload Bytes} \times 8}{1,000,000}$$

---

### 4. Canonical Production Case Studies

#### A. Booking.com (Hotel Reservation & Inventory System)
- **Zero-Double-Booking Guarantee**:
  - Two-phase reservation state machine: `Pending` $\rightarrow$ `Reserved` $\rightarrow$ `Confirmed` $\rightarrow$ `Expired`/`Cancelled`.
  - When a user selects a room, acquire a short-lived distributed lease in Redis (Redlock) with a 10–15 minute TTL.
  - On payment submission, execute an ACID transaction against PostgreSQL verifying the room inventory record using optimistic concurrency control:
    ```sql
    UPDATE room_inventory
    SET available_count = available_count - 1, version = version + 1
    WHERE room_type_id = :id AND date = :target_date AND version = :expected_version AND available_count > 0;
    ```
- **Search & Inventory Decoupling (CQRS)**:
  - Hotel browsing and filtering operates over an Elasticsearch/OpenSearch read cluster (eventually consistent).
  - Booking checkout operates directly over the transactional PostgreSQL ledger (strongly consistent).

#### B. WhatsApp (Global Real-Time Messaging)
- **Stateful Connection Gateways & Routing**:
  - Millions of concurrent mobile and desktop clients maintain persistent WebSocket / TCP connections to Gateway nodes.
  - An ephemeral Redis session cluster maintains a distributed lookup table mapping `user_id -> gateway_instance_id`.
  - When User A sends a message to User B, the message router queries Redis for User B's active gateway and dispatches the payload via internal RPC.
- **Transient Mailbox Storage**:
  - If User B is online, the message is pushed immediately over the WebSocket connection.
  - If User B is offline, the message is appended to a transient Cassandra / ScyllaDB mailbox queue.
  - Once User B receives the message and sends back a delivery ACK, the message is **permanently purged** from the server mailbox.
- **End-to-End Encryption (Signal Protocol)**:
  - Messages are encrypted on the sender's device and decrypted only on the recipient's device.
  - WhatsApp servers store public identity keys but have zero visibility into plaintext content.

#### C. Spotify (Audio Streaming Platform)
- **Audio Storage & CDN Chunking**:
  - Master audio files are ingested through an asynchronous transcoding pipeline (Kafka + worker pool) into multiple bitrates (96 kbps, 160 kbps, 320 kbps AAC/OGG) and split into numbered chunks.
  - Chunks reside in S3 Blob Storage and are aggressively cached across global edge CDNs (Cloudflare/Fastly).
  - Client players issue HTTP Range requests (`Range: bytes=0-1048575`), pre-buffering the first 30 seconds of tracks to achieve near-instantaneous playback start.
- **Metadata vs Media Tiering**:
  - Relational PostgreSQL manages artists, albums, tracks, and licensing constraints.
  - In-memory Redis clusters store user playlists, recently played tracks, and collaborative queue state.
