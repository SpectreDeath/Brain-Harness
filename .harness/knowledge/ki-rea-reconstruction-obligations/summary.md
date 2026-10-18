# Reconstruction Obligation Ledgers & Canonical Evidence Records

## Epistemic Lineage & Provenance Snapshot

- **Primary Source Codebase**: `D:\GitHub\cloned\rea-main` (`morluto/rea`)
- **Verified Commit**: `701695139490777ece7a3ccb8508b6215a11c0fe`
- **Source Modules**: `src/domain/evidence.ts`, `src/domain/reconstructionObligationLedgerSchemas.ts`, `docs/reconstruction-obligation-ledgers.md`, `docs/tool-design.md`

---

## 1. Ground-Truth Mental Models

1. **Content-Addressed Immutable Evidence**:
   Tool outputs in reverse engineering are volatile and polyglot (disassembly, AST trees, deobfuscation maps, debugger memory dumps). Canonicalizing every observation into a deterministic SHA-256 digest (`ev:<sha256>`) establishes an immutable, auditable chain-of-custody. Evidence records never mutate once written.

2. **Reconstruction Obligations as Behavioral Contracts**:
   Reverse engineering complex software without formal obligations inevitably leads to incomplete reconstructions or untested assumptions. An obligation models a specific behavioral surface across 10 architectural layers (`cli`, `protocol`, `electron`, `persistence`, `process`, `runtime`, `packaging`, `native-abi`, `application`, `other`).

3. **8-State FSM Dispositions**:
   Surfaces advance through an explicit state machine:
   `unowned` $\rightarrow$ `characterized` $\rightarrow$ `implemented` $\rightarrow$ `verified`
   with side-branches for `contradicted`, `blocked`, `out-of-scope`, and `unknown`.

4. **Cryptographic Proof of Reconstruction Closure**:
   Closure is not declared by narrative consensus. It is a cryptographic assertion: the hash over all sorted obligations in the ledger where `unowned == 0` and `contradicted == 0`.

---

## 2. Decision Heuristics & Behavioral Rules

- **The Facet Availability Rule**: When comparing two decompilers or analyzing partial static analysis, never equate an unobserved dimension with an empty set. Always emit explicit availability maps (`{ available: false, reason: "..." }`).
- **Contradiction Quarantine**: When static decompilation and dynamic debugger trace disagree on a procedure's control flow or return value, immediately quarantine the obligation in `contradicted` state. Never silently overwrite or average conflicting evidence.
- **Strict Implementation Attribution**: Every obligation in `implemented` state must carry both `owner_path` and `owner_sha256` to ensure that code refactors or deletions immediately flag stale obligations.

---

## 3. Anti-Pattern Defenses

- **Facet Conflation**: Treating absent facets as empty sets. *Defense*: Hard-fail comparisons unless both sides provide explicit coverage or `available: false`.
- **Premature Closure**: Declaring reconstruction finished while behavioral surfaces remain unowned or contradicted. *Defense*: Deterministic verification failure (`is_closed == False`) when active unowned or contradicted obligations exist.
- **Speculative Registration**: Creating obligations without grounding them in empirical evidence. *Defense*: Mandatory transition gate requiring $\ge 1$ evidence ID for `characterized` disposition.
- **Non-Deterministic Evidence Hashing**: Producing fluctuating SHA-256 digests due to unformatted JSON key ordering. *Defense*: Canonical JSON serialization sorting keys alphabetically with compact token separators.

---

## 4. Cross-References & Ecosystem Lineage

- Skill: `reconstruction-obligation-ledger` (`.agents/skills/reconstruction-obligation-ledger/`)
- Plugin: `plugin.reconstruction_obligation_ledger` (`plugins/security_and_forensics/reconstruction_obligation_ledger/`)
- Related Skills:
  - `adversarial-agent-verifier`
  - `epistemic-isnad-audit`
  - `deep-skill-forge`
