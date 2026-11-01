---
name: rea-reverse-engineering
description: Dissect, route, and extract semantic signatures from native binaries, PE/.NET assemblies, Android APKs, JS bundles, WASM, EVM bytecode, and firmware using the unified REA toolkit. Do not use for live exploit execution, active network scanning, or generic source-code linting.
---

# REA Reverse-Engineering Toolkit

The **rea-reverse-engineering** skill provides a unified architectural gateway for software reverse engineering, binary layout inspection, decompiler orchestration, and semantic signature extraction across 13 artifact categories. It enforces strict 3-valued facet availability semantics and bridges observations directly into the Reconstruction Obligation Ledger and Knowledge Vault.

See [CARD.md](CARD.md) for the companion summary card, operational stages, and mandatory invariants checklist.
Consult [references/routing-matrix.md](references/routing-matrix.md) for the deterministic artifact-type routing rules and [references/facet-semantics.md](references/facet-semantics.md) for the 3-valued availability and absence claimability gates.

---

## 1. Trigger Bounds & Deflection

### Activation Triggers
- Reverse engineering or static inspection of native binaries (ELF, PE32, PE32+, Mach-O, DOS MZ/COM).
- Dissecting managed .NET PE/CLI assemblies, Unity IL2CPP binaries, or CPython `.pyc` bytecode.
- Inspecting Android APK containers, Dalvik DEX classes, or connected ADB devices.
- Unpacking Electron ASAR archives or deobfuscating JavaScript bundles.
- Disassembling WebAssembly (`.wasm`) or Ethereum Virtual Machine (`.evm`) bytecode.
- Carving embedded firmware images and filesystem partitions.
- Extracting semantic signatures for endogenous Knowledge Vault learning.

### Negative Deflection (When NOT to Use)
- **Do not use for live exploit execution or payload delivery** — Use sandboxed verification.
- **Do not use for active network vulnerability scanning** — Inspection is strictly passive and offline.
- **Do not use for generic line text diffing** — Use standard Git diff or `difflib`.
- **Do not use for multi-provider comparison without inspection** — Use [differential-facet-verifier](../differential-facet-verifier/SKILL.md).
- **Do not use for code obligation tracking without evidence** — Use [reconstruction-obligation-ledger](../reconstruction-obligation-ledger/SKILL.md).

---

## 2. Operational Progression (The Shu Stages)

| Stage | Name | Key Activity | Completion Gate |
|---|---|---|---|
| **1** | **Detect & Route** | Inspect magic bytes and container headers; resolve target to one of 13 artifact categories. | Artifact identity resolved with SHA-256 digest and valid kind. |
| **2** | **Dissect & Probe** | Dispatch inspection through specialized domain engines; enforce operational budgets and isolation. | Facets populated with explicit 3-valued availability status. |
| **3** | **Extract Signatures** | Distill semantic signatures (selectors, channels, P/Invoke, imports/exports) into normalized records. | Signatures extracted with deterministic canonical digests. |
| **4** | **Differential Audit** | If multiple providers are specified, execute differential comparison via [differential-facet-verifier](../differential-facet-verifier/SKILL.md). | DifferentialReport emitted with `rep:<sha256>` digest. |
| **5** | **Seal & Distill** | Mint `ev:<sha256>` evidence and distill signatures into dual-file Knowledge Vault items via [reconstruction-obligation-ledger](../reconstruction-obligation-ledger/SKILL.md). | Dual-file `.harness/knowledge/<ki_id>/` committed with Isnad. |

---

## 3. Diagnostic Coaching Scorecards

| Dimension | Pass Condition | Fail Symptom | Repair Action |
|---|---|---|---|
| **Facet Conflation Guard** | Empty facet has explicit `{ available: true }` | Missing/empty facet treated as 0 occurrences | Force `state: unknown`, attach non-empty reason |
| **Absence Claimability Guard** | `absence_claimable == True` before claiming absence | Absence claimed when `truncated == True` or coverage incomplete | Downgrade facet to `unknown` with limitation reason |
| **PE Disambiguation Guard** | Inspect Optional Header Directory #14 (CLR RVA) | Managed .NET routed to native decompiler or vice versa | Check CLR RVA > 0: if true, route to `rea_managed_runtime` |
| **Offline Execution Guard** | Target is never executed or contacted | Outbound socket connection or process spawn of target code | Enforce offline static inspection and passive observation only |
| **Secret Scrubbing Guard** | No sensitive tokens persisted to Knowledge Vault | Authorization headers or tokens written to `summary.md` | Redact credential strings prior to vault commit |

---

## 4. CLI Execution Seam

Execute via the unified `harness` CLI:

```bash
# Auto-detect artifact and print unified dissection envelope
harness rea inspect target_binary

# List all REA tools grouped by artifact category
harness rea list

# Probe external reverse-engineering binary availability
harness rea providers

# Extract semantic signatures layer only
harness rea signatures target_binary --json

# Multi-provider differential comparison
harness rea diff target_binary --providers ghidra,hopper

# Endogenous learning into Knowledge Vault and ROL ledger
harness rea learn target_binary --dry-run
```

Or execute via the co-located runner script:

```bash
python scripts/rea_toolkit_engine.py inspect target_binary
```

---

## Anti-Patterns

- **Target Code Execution** — Running or executing untrusted target binaries, `.dll`, or `.pyc` in-process during discovery or inspection.
- **Facet Conflation** — Conflating an unobserved or undeclared facet with zero occurrences (`[]`), creating false negative claims.
- **Premature Absence Claim** — Asserting that an entity is absent when operational budgets truncated traversal or decompiler output.
- **Provider Text False Contradiction** — Equating raw provider formatting syntax differences with genuine binary semantic divergence.
- **Secret Bleed into Vault** — Writing raw embedded API keys or session credentials into permanent Knowledge Vault items.

---

## 5. References & Sibling Skills

- Companion Summary Card: [CARD.md](CARD.md)
- Artifact Routing Matrix: [references/routing-matrix.md](references/routing-matrix.md)
- Facet Availability Semantics: [references/facet-semantics.md](references/facet-semantics.md)
- Multi-Provider Comparison: [differential-facet-verifier](../differential-facet-verifier/SKILL.md)
- Evidence & Obligation Ledger: [reconstruction-obligation-ledger](../reconstruction-obligation-ledger/SKILL.md)

