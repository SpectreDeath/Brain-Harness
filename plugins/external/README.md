# 🌐 External Plugins & Sandboxed Ecosystem Bridges

Subprocess-sandboxed external community plugins, third-party agent skills, and isolated Python virtual environment execution boundaries.

---

## Category Architecture

Plugins within `external` adhere to the single-responsibility domain partitioning invariant (Rule 18). Each capability is encapsulated in a dedicated directory with independent manifests, isolation boundaries, and typed `ServiceKey[T]` declarations.

```mermaid
flowchart TD
    subgraph CategoryDomain ["External Plugins & Sandboxed Ecosystem Bridges"]
        CategoryHub["plugins/external/"]
        PluginsList["1 Domain Plugins"]
    end
    KernelCore[Brain Harness Kernel] -->|Topological Discovery| CategoryHub
    CategoryHub -->|Instantiates| PluginsList
```

---

## Member Plugins Catalog

| Plugin | Isolation | Provided Services | Summary |
|---|---|---|---|
| [Pocock-skills-main](Pocock-skills-main/README.md) | `subprocess` | None | Pinned v1.2.3 (`2181519d`). Matt Pocock's agent skills for real engineering — grilling, spec/ticket flows, TDD, code review, domain modelling. |

---

## Vendored Upstream Update Procedure

Vendored external snapshots maintain a co-located `.version_pin` recording upstream repository provenance, Git commit hash, and semantic release tag.

To update a vendored snapshot to a newer upstream release:
```bash
# Ingest upstream release and re-sandbox
harness ingest https://github.com/mattpocock/skills --ref v1.3.0 --force
```

---

## Invariants & Execution Boundaries

1. Domain Partitioning (Rule 18): Plugins in `external` do not mix cross-domain concerns.
2. Typed Service Registration (Rule 2): All services register using typed `ServiceKey[T]` contracts.
3. Subprocess Isolation (Rule 5 & 7): Untrusted and heavy external dependencies execute in isolated subprocess sandboxes with lazy venv provisioning.
4. Zero-Fork Config (Rule 44): Baseline operational budgets reside in co-located `config.default.yaml`.
5. Version Pinning: All vendored external snapshots must carry a `.version_pin` and declared `source_commit`.

