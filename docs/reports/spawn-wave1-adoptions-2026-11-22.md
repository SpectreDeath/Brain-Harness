# Wave 1 Spawn Adoption & Provenance Evidence — 2026-11-22 EST

- **Generated (UTC):** `2026-11-22T17:14:28Z`
- **Decision Policy (`4.1`, 2026-11-22):** `"4.1: commit adoption evidence only — do not adopt the KIs into live .harness/knowledge."`
- **Live Knowledge Vault Status:** `.harness/knowledge/` remains untouched at `382` KIs (`test_readme_and_manual_knowledge_item_count_matches_live` passes).
- **External Source Repo (`harness-repo-distiller`):** `https://github.com/forrestchang/andrej-karpathy-skills.git` at commit `2c606141936f1eeef17fa3043a72095b4765b9c2` (local mirror `D:\GitHub\cloned\andrej-karpathy-skills`).

## Spawned Harness Digests (Reproducible `docs_sha256` Verified)

| Harness | Spawn ID | Tree SHA-256 | Docs SHA-256 | Local Shelf Output |
|---|---|---|---|---|
| `harness-repo-distiller` | `spawn_harness-repo-distiller_ba7f71b5` | `fc0353cfca8c5005ee02879d8274a45eeea0f5488d5914f82da0b187243dd264` | `400797e1b062b4350c1f6062df6524abb766795c5f919f90d6d02563f5db236a` | child shelf: "sources/raw/karpathy_claude.txt", "concepts/karpathy-behavioral-rules.md", "concepts/_index.md" (1 note, icm quotes 2 of 2) |
| `harness-security-forensics` | `spawn_harness-security-forensics_6af6d2c7` | `c8efd2fd24acb50e0682b5f133dbdae9d0a65a0d7a5f393939cac80365b94baa` | `f97d1efdc2bfa0567ddde57cfac49c572ccafdea831a0a698b75daddb3caa964` | child shelf: "records/finding-001.md", "records/_index.md" (1 note, harness mantis audit dock safety.py 0 findings) |
| `harness-arch-modernizer` | `spawn_harness-arch-modernizer_8ce8b20e` | `19c78f42140739fa58f281abdd809421b7973334d72278c57cfdec437cc764b2` | `c38e2f1bb7299ce0911e3334410b748e0d59592c9eb5c017f459132f2a72490d` | child shelf: "objects/spawner-blueprints.md", "processes/spawn-materialize-flow.md", index files (2 notes, 16 spawner modules) |
| `harness-context-economizer` | `spawn_harness-context-economizer_2ab8fab4` | `88b61b6a0564615537ccda3c3e2308f8d753d1fa84af0da9225fdb5d91c11339` | `b63eb2031d9b52e7b58a4fc332a90cf7fdde2591adfd360acfabe6c72dcbe401` | child shelf: "teams/spawner-context-boundary.md", "teams/_index.md" (2 notes, harness context lint PASS) |

## Merge-Back Proposals & Decisions (Sandbox Parent Store)

| Proposal ID | Spawn ID | Task ID | Kind | Status | KI ID | Reviewer | Note / Reason |
|---|---|---|---|---|---|---|---|
| `prop_distill-karpathy-1_214b16a9` | `spawn_harness-repo-distiller_ba7f71b5` | `distill-karpathy-1` | `ki` | `adopted` | `ki-distill-karpathy-minimalism` | `operator-sandbox` | Verified against raw karpathy_claude quote check. |
| `prop_distill-karpathy-2_a9f2e525` | `spawn_harness-repo-distiller_ba7f71b5` | `distill-karpathy-2` | `ki` | `rejected` | `ki-spawn-knowledge_distillation-distill-karpathy-2` | `operator-sandbox` | Violates Rule: preserve unrelated docstrings; failed evidentiary review. |
| `prop_mantis-safety-audit-1_09bcc64c` | `spawn_harness-security-forensics_6af6d2c7` | `mantis-safety-audit-1` | `ki` | `adopted` | `ki-sec-dock-safety-baseline` | `operator-sandbox` | Clean AST triage record and indexed shelf. |
| `prop_mantis-safety-audit-2_34321887` | `spawn_harness-security-forensics_6af6d2c7` | `mantis-safety-audit-2` | `config` | `rejected` | `ki-spawn-security_and_forensics-mantis-safety-audit-2` | `operator-sandbox` | Weakening env scrubbing violates dock boundary policy. |
| `prop_arch-map-spawner-1_c868eb56` | `spawn_harness-arch-modernizer_8ce8b20e` | `arch-map-spawner-1` | `ki` | `adopted` | `ki-arch-service-layer-graph-seam` | `operator-sandbox` | Confirmed against layer boundary AST test. |
| `prop_arch-map-spawner-2_d0e36648` | `spawn_harness-arch-modernizer_8ce8b20e` | `arch-map-spawner-2` | `ki` | `rejected` | `ki-spawn-architecture-arch-map-spawner-2` | `operator-sandbox` | Lazy upward imports still fail AST layer boundary checks. |
| `prop_econ-audit-1_b8ff8e4b` | `spawn_harness-context-economizer_2ab8fab4` | `econ-audit-1` | `ki` | `adopted` | `ki-econ-trimmed-domain-catalog` | `operator-sandbox` | Backed by empirical Tier-1 measurements. |
| `prop_econ-audit-2_e8cb41d2` | `spawn_harness-context-economizer_2ab8fab4` | `econ-audit-2` | `ki` | `rejected` | `ki-spawn-context_engineering-econ-audit-2` | `operator-sandbox` | Rule 44 requires explicit Do-not-use boundaries in 100-350 char descriptions. |

## Adopted KI Payloads (Archived Evidence Only; Not in Live Vault)

### `ki-arch-service-layer-graph-seam`

#### `metadata.json`

```json
{
  "id": "ki-arch-service-layer-graph-seam",
  "title": "Spawn Learning: architecture (arch-map-spawner-1)",
  "summary": "when adding service-to-service graph calls under src/harness/services/ -> call get_default_skill_registry directly inside services rather than harness.commands wrappers",
  "domain": "architecture",
  "status": "adopted",
  "tags": [
    "spawn",
    "architecture"
  ],
  "created_at": "2026-11-21T23:01:14.120541+00:00",
  "updated_at": "2026-11-21T23:01:14.120541+00:00",
  "source_spawn_id": "spawn_harness-arch-modernizer_8ce8b20e",
  "source_proposal_id": "prop_arch-map-spawner-1_c868eb56",
  "task_id": "arch-map-spawner-1",
  "isnad_claim": {
    "cue": "when adding service-to-service graph calls under src/harness/services/",
    "lesson": "call get_default_skill_registry directly inside services rather than harness.commands wrappers",
    "evidence": "verified via test_services_never_imports_commands_or_creator; mapped 16 spawner modules cleanly"
  }
}
```

#### `summary.md`

```markdown
# Spawn Learning: architecture (arch-map-spawner-1)

- **KI ID**: `ki-arch-service-layer-graph-seam`
- **Domain**: `architecture`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-arch-modernizer_8ce8b20e` (`arch-map-spawner-1`)
- **Proposal ID**: `prop_arch-map-spawner-1_c868eb56`

## Transferable Claim
- **Cue**: when adding service-to-service graph calls under src/harness/services/
- **Lesson**: call get_default_skill_registry directly inside services rather than harness.commands wrappers
- **Evidence**: verified via test_services_never_imports_commands_or_creator; mapped 16 spawner modules cleanly

## Rationale
Enforces strict layered dependency directionality without circular imports.
```

### `ki-distill-karpathy-minimalism`

#### `metadata.json`

```json
{
  "id": "ki-distill-karpathy-minimalism",
  "title": "Spawn Learning: knowledge_distillation (distill-karpathy-1)",
  "summary": "when scaffolding single-use agent helpers -> keep implementations minimal and speculative-free unless multiple reuse seams exist",
  "domain": "knowledge_distillation",
  "status": "adopted",
  "tags": [
    "spawn",
    "knowledge_distillation"
  ],
  "created_at": "2026-11-21T22:21:45.097454+00:00",
  "updated_at": "2026-11-21T22:21:45.097454+00:00",
  "source_spawn_id": "spawn_harness-repo-distiller_ba7f71b5",
  "source_proposal_id": "prop_distill-karpathy-1_214b16a9",
  "task_id": "distill-karpathy-1",
  "isnad_claim": {
    "cue": "when scaffolding single-use agent helpers",
    "lesson": "keep implementations minimal and speculative-free unless multiple reuse seams exist",
    "evidence": "inspected andrej-karpathy-skills (9 files, tier=Medium); icm quotes verified=2/2"
  }
}
```

#### `summary.md`

```markdown
# Spawn Learning: knowledge_distillation (distill-karpathy-1)

- **KI ID**: `ki-distill-karpathy-minimalism`
- **Domain**: `knowledge_distillation`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-repo-distiller_ba7f71b5` (`distill-karpathy-1`)
- **Proposal ID**: `prop_distill-karpathy-1_214b16a9`

## Transferable Claim
- **Cue**: when scaffolding single-use agent helpers
- **Lesson**: keep implementations minimal and speculative-free unless multiple reuse seams exist
- **Evidence**: inspected andrej-karpathy-skills (9 files, tier=Medium); icm quotes verified=2/2

## Rationale
Prevents single-use abstraction bloat across domain harnesses.
```

### `ki-econ-trimmed-domain-catalog`

#### `metadata.json`

```json
{
  "id": "ki-econ-trimmed-domain-catalog",
  "title": "Spawn Learning: context_engineering (econ-audit-1)",
  "summary": "when optimizing agent prompt catalog overhead -> replace 114-skill workspace catalogs with 5-skill graph-selected domain harnesses (~94.8-95.6% catalog reduction)",
  "domain": "context_engineering",
  "status": "adopted",
  "tags": [
    "spawn",
    "context_engineering"
  ],
  "created_at": "2026-11-21T23:01:32.825562+00:00",
  "updated_at": "2026-11-21T23:01:32.825562+00:00",
  "source_spawn_id": "spawn_harness-context-economizer_2ab8fab4",
  "source_proposal_id": "prop_econ-audit-1_b8ff8e4b",
  "task_id": "econ-audit-1",
  "isnad_claim": {
    "cue": "when optimizing agent prompt catalog overhead",
    "lesson": "replace 114-skill workspace catalogs with 5-skill graph-selected domain harnesses (~94.8-95.6% catalog reduction)",
    "evidence": "measured across 4 Tier-1 spawned harnesses; harness context lint passed cleanly ([PASS] Context files healthy across 3 checks at: .)"
  }
}
```

#### `summary.md`

```markdown
# Spawn Learning: context_engineering (econ-audit-1)

- **KI ID**: `ki-econ-trimmed-domain-catalog`
- **Domain**: `context_engineering`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-context-economizer_2ab8fab4` (`econ-audit-1`)
- **Proposal ID**: `prop_econ-audit-1_b8ff8e4b`

## Transferable Claim
- **Cue**: when optimizing agent prompt catalog overhead
- **Lesson**: replace 114-skill workspace catalogs with 5-skill graph-selected domain harnesses (~94.8-95.6% catalog reduction)
- **Evidence**: measured across 4 Tier-1 spawned harnesses; harness context lint passed cleanly ([PASS] Context files healthy across 3 checks at: .)

## Rationale
Prevents unused skill descriptions from consuming per-turn token budget.
```

### `ki-sec-dock-safety-baseline`

#### `metadata.json`

```json
{
  "id": "ki-sec-dock-safety-baseline",
  "title": "Spawn Learning: security_and_forensics (mantis-safety-audit-1)",
  "summary": "when auditing dock execution safety guards -> enforce boundary path and env-scrub checks cleanly before shell=True dispatch",
  "domain": "security_and_forensics",
  "status": "adopted",
  "tags": [
    "spawn",
    "security_and_forensics"
  ],
  "created_at": "2026-11-21T22:22:03.799561+00:00",
  "updated_at": "2026-11-21T22:22:03.799561+00:00",
  "source_spawn_id": "spawn_harness-security-forensics_6af6d2c7",
  "source_proposal_id": "prop_mantis-safety-audit-1_09bcc64c",
  "task_id": "mantis-safety-audit-1",
  "isnad_claim": {
    "cue": "when auditing dock execution safety guards",
    "lesson": "enforce boundary path and env-scrub checks cleanly before shell=True dispatch",
    "evidence": "harness mantis audit on src/harness/services/dock/safety.py (0 AST findings); recorded in records/finding-001.md"
  }
}
```

#### `summary.md`

```markdown
# Spawn Learning: security_and_forensics (mantis-safety-audit-1)

- **KI ID**: `ki-sec-dock-safety-baseline`
- **Domain**: `security_and_forensics`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-security-forensics_6af6d2c7` (`mantis-safety-audit-1`)
- **Proposal ID**: `prop_mantis-safety-audit-1_09bcc64c`

## Transferable Claim
- **Cue**: when auditing dock execution safety guards
- **Lesson**: enforce boundary path and env-scrub checks cleanly before shell=True dispatch
- **Evidence**: harness mantis audit on src/harness/services/dock/safety.py (0 AST findings); recorded in records/finding-001.md

## Rationale
Establishes repeatable AST security audit baseline as indexed record.
```
