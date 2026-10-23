```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: python-diagrams-architect                                     │
│ SKILL: python-diagrams-architect                                     │
│ Category: visualization / architecture / system-design               │
│ Version: 1.0.0                                                       │
│ Invocation: /python-diagrams-architect                               │
│ Triggers: "python diagrams", "diagrams as code",                     │
│           "system design diagrams", "cloud architecture diagram",    │
│           "generate architecture diagram", "lint diagram script"     │
│ Requires: "system-design-architect", "cloud-infrastructure-architect",│
│           "data-topology-mapper", "developer-docs-architect"         │
│ Target: Declarative Python Diagrams-as-Code for System Design        │
└──────────────────────────────────────────────────────────────────────┘
```

# Python Diagrams Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Requirements & Topology** | Ingest architectural specs, select providers & configure global canvas direction | Diagram Specification & Canvas Scope | Boundary defined; direction (`LR`/`TB`) set; providers mapped |
| **Stage 2: Cluster Partitioning** | Group infrastructure into VPCs, regions, tiers & nested microservice scopes | Semantic Cluster Hierarchy | Semantic clusters declared; zero un-clustered orphan nodes |
| **Stage 3: Node Instantiation** | Instantiate typed cloud resources and batch homogeneous instances in lists | Provider Nodes & Batched Lists | Typed provider nodes created; batch lists formed for fan-out |
| **Stage 4: Edge Flow Construction** | Wire directional data flows (`>>`, `<<`, `-`) & annotate protocol edges | Annotated Data Flow Pipe Graph | Full graph connected; protocol edges labeled & styled |
| **Stage 5: Validation & Compilation** | Lint diagram script AST, verify Graphviz binary & render output artifacts | Compiled Image Artifact (PNG/SVG) | AST lint clean; Graphviz compiled; image artifact verified |

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every diagramming and architecture generation run must generate an interactive HTML visual brief in `%TEMP%` displaying the pipeline DAG, architecture topology comparison (Manual Canvas vs DaC), diagnostic scorecards, and anti-pattern defense matrix.

### 2. The Mandatory Checkpoint Pillar
The agent must never generate diagram code or mutate documentation without first presenting `implementation_plan.md` with `RequestFeedback: true` detailing the target nodes, clusters, data flow, and file locations, and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns & Defenses
Rigid architectural boundaries prevent canvas drift, un-clustered flat layouts, redundant wiring spaghetti, unlabeled mystery arrows, and hanging CI processes.

---

## Mandatory Invariants Checklist

- [ ] **Declarative Version-Controlled Code**: All production architecture diagrams must be specified as version-controlled code using declarative diagram scripts.
- [ ] **Semantic Cluster Grouping**: Multi-tier or distributed systems must group components into semantic `Cluster` contexts (e.g. Presentation, Application, Data).
- [ ] **Batch List Fan-Out/In**: Homogeneous worker, server, or pod groups must be batched using Python lists to construct clean fan-out and fan-in flows.
- [ ] **Explicit Protocol Edge Annotations**: Inter-tier connections across security or protocol boundaries must use explicit `Edge` annotations specifying label, color, or line style.
- [ ] **Headless CI Execution Invariant**: Diagrams compiled in headless environments or CI/CD pipelines must explicitly declare `show=False` in `Diagram()`.
- [ ] **Slotted & Frozen Dataclass Domain**: Domain models and diagram specification containers must declare `slots=True, frozen=True` (Rule 12).
