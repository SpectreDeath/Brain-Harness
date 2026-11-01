# Reconstruction Obligation Ledger Plugin

`plugin.reconstruction_obligation_ledger` provides cryptographic evidence sealing (`ev:<sha256>`), 8-state disposition FSMs, and reconstruction obligation verification across the 10 REA architectural layers.

## Capabilities

- **Evidence Ingestion:** Mints canonical immutable `CanonicalEvidence` records from multi-provider dissection outputs.
- **Obligation Lifecycle:** Tracks reverse-engineering reconstruction obligations across 8 disposition states (`unowned`, `claimed`, `in_progress`, `review`, `closed`, `waived`, `superseded`, `rejected`).
- **Cryptographic Closure:** Generates verifiable `ReconstructionProof` certificates asserting closure completeness.
- **Micro-Kernel Seam:** Registers `service.reconstruction_obligation` (`ReconstructionObligationService`) into the IoC container.

## Documentation & Unified Workflows

- **REA Toolkit Guide:** See [Use REA Toolkit](../../../docs/how-to/use-rea-toolkit.md) for unified `harness rea learn` and `harness rea learned` workflows.
- **Companion Skill:** [.agents/skills/reconstruction-obligation-ledger](../../../.agents/skills/reconstruction-obligation-ledger/SKILL.md).
- **CLI Commands:** `harness rol ingest`, `harness rol obligation`, `harness rol verify`, `harness rol export`.

