# Differential Facet Verifier Plugin

`plugin.differential_facet_verifier` provides three-valued observation comparison (`unchanged`, `changed`, `unknown`), facet availability tracking, and strict absence-claimability gating for reverse-engineering dossiers and multi-provider audits.

## Capabilities

- **3-Valued Facet Comparisons:** Compares observations across providers while strictly distinguishing between proved identity, detectable differences, and unobserved dimensions (`FacetAvailability.available == False`).
- **Absence-Claimability Gating:** Enforces that negative assertions (`state="absent"`) require complete non-truncated coverage declarations.
- **Micro-Kernel Seam:** Registers `service.differential_facet` (`DifferentialFacetService`) into the IoC container.

## Documentation & Unified Workflows

- **REA Toolkit Guide:** See [Use REA Toolkit](../../../docs/how-to/use-rea-toolkit.md) for unified `harness rea diff` workflows.
- **Companion Skill:** [.agents/skills/differential-facet-verifier](../../../.agents/skills/differential-facet-verifier/SKILL.md).
- **CLI Commands:** `harness facet compare`, `harness facet claim-absence`, `harness facet verify`, `harness facet export`.

