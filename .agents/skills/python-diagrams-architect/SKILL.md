---
name: python-diagrams-architect
description: Architect, generate, validate, and lint production system architecture and cloud infrastructure diagrams in Python using Diagrams-as-Code. Do not use for manual drag-and-drop canvas editing or non-Python diagram tools.
---

# Python Diagrams Architect: Diagrams-as-Code for System Design

`python-diagrams-architect` is the production skill that architects, generates, lints, and verifies cloud system design diagrams using Python code and the Mingrammer `diagrams` library backed by Graphviz.

Rather than relying on manual, drag-and-drop canvas tools that suffer from **Manual Canvas Drift** and disconnect documentation from codebase commits, this skill models system architectures as declarative, version-controlled Python programs that can be automatically verified and rendered in CI/CD pipelines.

Every diagramming session executes this five-stage progression:

```
[1. Requirements & Topology Scoping] ──► [2. Cluster & Hierarchy Partitioning] ──► [3. Node Instantiation & Batching]
                                                                                               │
                                                                                               ▼
[5. Validation, Graphviz Compilation & CI] ◄── [4. Data Flow & Typed Edge Construction] ◄──────┘
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and invariants checklist.
Consult `/system-design-architect` for capacity estimation, `/cloud-infrastructure-architect` for container governance, and `/developer-docs-architect` for documentation taxonomy.

---

## 1. Requirements & Topology Scoping

Analyze architectural requirements and establish global diagram canvas boundaries:

1. **Ingest Architectural Specification**:
   - Identify system components: client applications, entry points, compute tiers, message brokers, caching layers, databases, and third-party integrations.
   - Determine flow directionality: Left-to-Right (`LR`, default for web apps and ingestion pipelines) or Top-to-Bottom (`TB`, common for hierarchical trees).
2. **Provider & Ecosystem Mapping**:
   - Select cloud providers and icon sets:
     - AWS: `from diagrams.aws.compute import EC2`, `from diagrams.aws.database import RDS`
     - GCP: `from diagrams.gcp.compute import GCE`, `from diagrams.gcp.database import SQL`
     - Azure: `from diagrams.azure.compute import VM`, `from diagrams.azure.database import SQLDatabases`
     - Kubernetes: `from diagrams.k8s.compute import Pod`, `from diagrams.k8s.network import Ingress`
     - On-Premises: `from diagrams.onprem.client import User`, `from diagrams.onprem.database import PostgreSQL`
3. **Establish Global Diagram Context**:
   - Define canvas filename, output format (`png`, `jpg`, `svg`, `pdf`), and headless display flag (`show=False` for CI/CD environments).

> **Completion criterion**: Architecture boundary defined with explicit canvas direction (`LR`/`TB`), output filename, and target cloud providers selected.

---

## 2. Cluster & Hierarchy Partitioning

Group related infrastructure into semantic isolation boundaries using context-managed clusters:

1. **Identify Architectural Scopes**:
   - Availability Zones and Regions (e.g., `Cluster("us-east-1a")`, `Cluster("Production VPC")`).
   - Architectural Tiers (e.g., `Cluster("Web Tier")`, `Cluster("Application Tier")`, `Cluster("Database Tier")`).
   - Microservice Boundaries (e.g., `Cluster("Auth Service")`, `Cluster("Billing Pipeline")`).
2. **Enforce Cluster Nesting Rules**:
   - Nest clusters cleanly by indenting `with Cluster("Child"):` inside `with Cluster("Parent"):`.
   - Keep cluster nesting to $\le 3$ levels to prevent Graphviz layout engine blowout and visual illegibility.
3. **Partition Persistent Storage**:
   - Always isolate stateful stores (PostgreSQL, Redis, S3, DynamoDB) into dedicated database or storage clusters separate from ephemeral stateless compute.

> **Completion criterion**: Architectural tiers and VPC/region boundaries partitioned into semantic `Cluster` blocks with zero un-clustered orphan nodes.

---

## 3. Node Instantiation & Batch Grouping

Instantiate individual infrastructure components and leverage list grouping for horizontal scalability:

1. **Instantiate Explicit Nodes**:
   - Create nodes with semantic, lowercase, hyphen-separated labels: `api_server = EC2("api-server-01")`.
   - Maintain explicit variable references for all nodes that require incoming or outgoing connections.
2. **Batch Horizontally Scaled Nodes**:
   - When modeling multiple identical instances (web servers, worker pods, database replicas), group them inside a Python list rather than defining individual point-to-point connections:
     ```python
     web_servers = [
         EC2("web-01"),
         EC2("web-02"),
         EC2("web-03"),
     ]
     ```
3. **Prevent Label Collision**:
   - Ensure node labels are unique within their immediate cluster context to eliminate Graphviz node identifier collisions.

> **Completion criterion**: All infrastructure components declared with valid provider classes and horizontally scaled components batched in Python lists.

---

## 4. Data Flow & Typed Edge Construction

Wire communication channels using directional operators and annotated edge protocols:

1. **Select Flow Direction Operators**:
   - `>>` : Forward data flow (e.g., client requests, pipeline ingestion).
   - `<<` : Reverse data flow (e.g., polling consumers, reverse proxies).
   - `-`  : Undirected or symmetric connections (e.g., primary-replica replication, cluster peering).
2. **Execute Fan-Out and Fan-In Pipelines**:
   - Connect upstream load balancers directly to batched node lists:
     ```python
     load_balancer >> web_servers >> database
     ```
   - This expands deterministically into fan-out and fan-in edge topologies without code repetition.
3. **Annotate Inter-Tier Protocols with `Edge`**:
   - When crossing network or security boundaries, annotate the connection using `Edge`:
     ```python
     api >> Edge(label="gRPC (mutual TLS)", color="darkgreen", style="bold") >> auth_service
     worker >> Edge(label="SQL queries", color="firebrick", style="dashed") >> replica_db
     ```
   - Supported styles: `"solid"`, `"dashed"`, `"dotted"`, `"bold"`.

> **Completion criterion**: Data flow fully connected across all nodes with protocol labels, colors, and line styles specified on all cross-tier edges.

---

## 5. Validation, Graphviz Compilation & CI Verification

Lint the diagram source code, verify Graphviz binary availability, and render final artifacts:

1. **AST Code Linting**:
   - Verify that all imported node classes exist in their declared provider modules.
   - Detect dangling/orphan nodes that lack any incoming or outgoing edges.
   - Assert `show=False` is set to prevent blocking GUI window popups in headless environments.
2. **Graphviz System Verification**:
   - Verify that the Graphviz `dot` executable is present on `PATH` via `dot -V`.
   - If missing in CI, raise an actionable diagnostic message pointing to system package installation (`apt-get install graphviz` / `choco install graphviz`).
3. **Execute Headless Rendering**:
   - Compile the diagram script: `python diagram.py`.
   - Verify output artifact exists, is non-zero in size, and matches the requested format (`.png` / `.svg`).

> **Completion criterion**: Diagram AST passes all lint checks, executes cleanly against Graphviz, and renders verified visual artifact.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every diagramming and architecture generation run must generate an interactive HTML visual brief in `%TEMP%` displaying the pipeline DAG, architecture topology comparison (Manual Canvas vs DaC), diagnostic scorecards, and anti-pattern defense matrix.

### 2. The Mandatory Checkpoint Pillar
The agent must never generate diagram code or mutate documentation without first presenting `implementation_plan.md` with `RequestFeedback: true` detailing the target nodes, clusters, data flow, and file locations, and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns & Defenses
Rigid architectural boundaries prevent canvas drift, un-clustered flat layouts, redundant wiring spaghetti, and unlabeled mystery arrows.

---

## Anti-Patterns

- **Manual Canvas Drift** — Drawing architecture diagrams on manual web canvas tools (Draw.io, Lucidchart) that immediately drift out of sync with committed code.
- **Monolithic Flat Canvas** — Dumping dozens of disparate nodes into a single flat diagram without `Cluster` grouping, obscuring VPCs, tiers, and security boundaries.
- **Redundant Point-to-Point Wiring** — Manually connecting repeated identical nodes one by one (`lb >> s1; lb >> s2; lb >> s3`) instead of leveraging Python list batching (`lb >> [s1, s2, s3]`).
- **Unstyled Mystery Arrows** — Using uniform, unlabeled solid black arrows for heterogeneous protocol flows, making sync HTTP, async queues, and database replication indistinguishable.
- **Blocking GUI Execution in Headless CI** — Omitting `show=False` in `Diagram()`, causing headless CI runners and background agent proactors to hang indefinitely waiting for an image viewer window to close.
