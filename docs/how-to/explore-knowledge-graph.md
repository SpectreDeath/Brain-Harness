# How-To: Explore and Analyze the Brain Harness Knowledge Graph

This guide explains how to interact with, query, and visualize the Brain Harness Knowledge Vault (`.harness/knowledge/`) across desktop graph tools, an interactive standalone HTML brief, the Control Room UI, and the headless CLI / MCP seams.

---

## 1. Overview and Architecture

The Brain Harness Knowledge Vault consists of dual-file directories (`metadata.json` + `summary.md`) governed by Rule 40. The Knowledge Graph derivation engine unifies these records into an interconnected entity graph with heterogeneous nodes (`ki`, `skill`, `plugin`, `path`, `source`) and typed relationship edges.

### Asserted vs. Derived Edge Semantics

Every edge in the knowledge graph explicitly indicates whether it is asserted or derived:
- **Asserted Edges (`derived: false`, `confidence: 1.0`)**: Solid lines. Created through verified operational transitions—such as `became_skill` (linking a KI to an agent skill), `became_plugin` (linking to a plugin), `references_code` (linking to repository source files), or `supersedes` / `contradicts` (epistemic lifecycle resolutions).
- **Derived Edges (`derived: true`, `confidence: 0.80`)**: Dashed lines. Mechanically inferred by the derivation engine based on shared high-signal domain tags and common taxonomy domains (`TaxonomyDomain`). Mega-tags (`endogenous_memory`, `self_reflection`) appearing on >15% of items are capped from generating spurious edges.

---

## 2. Four Interaction Modes

### Mode 1: Standalone Interactive HTML Brief

Export a self-contained, zero-dependency HTML canvas graph view that works in any modern browser without a Node or build environment:

```bash
# Export and open in default browser
harness knowledge export --format html --open

# Export to a custom path
harness knowledge export --format html --out outputs/knowledge_graph.html
```

**Features**:
- Interactive HTML5 Canvas force-directed graph with pan, zoom, drag, and click selection.
- Controls ribbon: search by title/tag, filter by `TaxonomyDomain` or `node_kind`, toggle derived edges, and confidence threshold slider.
- Timeline scrubber: interactive slider and play/pause button filtering nodes by `created_at` timestamp.
- Inspector drawer displaying Isnad claims, incident edges, retrieval count, and metadata.
- Domain summary Mermaid flowchart TD showing inter-domain connection density.

---

### Mode 2: Desktop Graph Analyzers (Gephi, Cytoscape, yEd)

Export to open standard graph exchange formats:

```bash
# Export standard GEXF for Gephi
harness knowledge export --format gexf --out outputs/knowledge_graph.gexf

# Export dynamic GEXF with temporal attributes for Gephi timeline animation
harness knowledge export --format gexf --dynamic --out outputs/dynamic_graph.gexf

# Export GraphML for Cytoscape or yEd
harness knowledge export --format graphml --out outputs/knowledge_graph.graphml

# Export idempotent Cypher batch script for Neo4j
harness knowledge export --format cypher --out outputs/knowledge_graph.cypher
```

#### 4-Step Gephi Quickstart:
1. **Open**: In Gephi, choose **File → Open** and select `outputs/knowledge_graph.gexf` (Graph Type: Directed).
2. **Layout**: Under **Layout**, select **ForceAtlas2** (set *Scaling* to `2.0`, enable *Prevent Overlap*, click **Run** then **Stop** once stabilized).
3. **Partition Coloring**: Under **Appearance → Nodes → Partition**, choose `domain` and click **Apply** to color nodes by their taxonomy domain.
4. **Timeline Filtering**: Enable the **Timeline** bar at the bottom to animate graph formation across weeks and reflection cycles.

---

### Mode 3: Headless CLI & MCP Queries

Inspect graph topology, component statistics, and shortest paths directly from your terminal or external MCP client:

```bash
# Display full graph census metrics
harness knowledge stats [--json]

# Inspect node neighborhood (adjacent KIs, skills, code paths)
harness knowledge neighbors <node_id> [--depth 1..4] [--exclude-derived]

# Find cycle-safe BFS shortest path between two entities (Rule 55: zero synthetic paths)
harness knowledge path <from_id> <to_id> [--max-depth 6] [--directed]

# Query topic neighborhood (matched KIs, linked skills, referenced code)
harness knowledge topic <topic_keyword>

# List upstream dependents pointing to a specific KI or code path
harness knowledge dependents <node_id>

# Identify isolated KIs and triage missing tags or categories
harness knowledge orphans [--json]

# Audit and triage vault categories and tags
harness knowledge hygiene [--suggest-categories] [--suggest-tags] [--apply]

# Display data-driven temporal growth metrics and domain emergence order
harness knowledge timeline [--json]
```

#### Model Context Protocol (MCP) Parity:
External agent clients can inspect the knowledge graph via the registered MCP resources:
- `harness://knowledge/graph`: Returns JSON graph topology and summary census.
- `harness://knowledge/contradictions`: Returns detected contradictions and antinomies.

---

### Mode 4: Control Room UI

Launch the Harness Control Room dashboard to interact with the knowledge graph visually:

```bash
# Start the Control Room web server
harness ui
```

Navigate to **Knowledge Graph** in the sidebar:
- **Left Panel**: Render domain-clustered Mermaid diagrams or click to open the standalone HTML Canvas brief.
- **Right Panel (Inspector Drawer)**:
  - Search entities by title or tag.
  - Filter entities by `TaxonomyDomain`.
  - View connected edges, Isnad claim verifications, and retrieval rates.
  - Review the **Contradiction Review Queue** and resolve conflicts with one click (`Supersede`, `Conflict`, `Dismiss`).

---

## 3. Data Model Reference

### Node Attributes (`KnowledgeGraphNode`)
| Attribute | Type | Description |
|:---|:---|:---|
| `id` | `str` | Unique node identifier (e.g. `ki-cli-decomposition-pattern`) |
| `label` | `str` | Human-readable node title |
| `node_kind` | `str` | Entity type: `ki`, `skill`, `plugin`, `path`, `source` |
| `category` | `str` | Specific operational category |
| `domain` | `str` | High-level canonical `TaxonomyDomain` |
| `tags` | `list[str]` | List of domain and topic tags |
| `status` | `str` | Lifecycle status (`ACTIVE`, `PROMOTED`, `DEMOTED`, `SUPERSEDED`, `CHALLENGED`, `ARCHIVED`) |
| `retrieval_count` | `int` | Number of times retrieved in agent sessions |
| `success_count` | `int` | Number of successful task applications |
| `created_at` | `str` | ISO 8601 creation timestamp |
| `source_target` | `str` | Source repository origin or primary file path |

### Edge Attributes (`KnowledgeGraphEdge`)
| Attribute | Type | Description |
|:---|:---|:---|
| `source` | `str` | Source entity identifier |
| `target` | `str` | Target entity identifier |
| `target_kind` | `str` | Entity type of target (`ki`, `skill`, `plugin`, `path`, `source`) |
| `type` | `str` | Edge relationship type (`became_skill`, `became_plugin`, `references_code`, `same_domain`, `supersedes`, `contradicts`, `synthesizes`) |
| `derived` | `bool` | `true` for inferred edges; `false` for asserted edges |
| `confidence` | `float` | Edge confidence score (`0.0` - `1.0`) |
| `shared_tags` | `list[str]` | Tags shared between source and target |
| `description` | `str` | Human-readable relationship context |

