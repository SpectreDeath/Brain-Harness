# How-To: Unified Security & Forensics Workflow

This guide documents the unified composition of the Brain Harness security and forensics cluster across 6 specialized toolkits and execution stages.

---

## The Unified Security & Forensics Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                   6-STAGE SECURITY & FORENSICS PIPELINE                │
├─────────────────────────┬──────────────────────────┬───────────────────┤
│ Stage                   │ CLI Command Group        │ Companion Skill   │
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 1. Shift-Left Gate      │ harness pre-commit-security pre-commit-guard │
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 2. Source & History     │ harness mantis           │ mantis-review     │
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 3. Artifact Dissection  │ harness rea              │ rea-reverse-eng   │
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 4. Differential Audit   │ harness facet / rea diff │ differential-facet│
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 5. Evidence Closure     │ harness rol / rea learn  │ obligation-ledger │
├─────────────────────────┼──────────────────────────┼───────────────────┤
│ 6. Network Recon        │ harness network-forensics│ ethical-networking│
└─────────────────────────┴──────────────────────────┴───────────────────┘
```

---

## Step-by-Step Execution Sequence

### Stage 1: Shift-Left Pre-Commit Interception

Intercept secrets and static SAST anti-patterns before code leaves local working directories:

```bash
# Scan working changes for credential leaks or high-risk patterns
harness pre-commit-security check --json
```

### Stage 2: Autonomous Source & VCS History Review (`mantis`)

Analyze repository commit histories for churn hotspots, and audit source code syntax trees:

```bash
# Scan commit history for vulnerability fix hotspots
harness mantis history-scan . --max-commits 100 --json

# Run AST taint analysis on modified files
harness mantis audit src/harness/kernel/loader.py --json

# Deduplicate raw findings and filter false positives
harness mantis dedupe findings.json --json > deduped.json
harness mantis critic-filter deduped.json --json

# Evaluate CI blocking gate
harness mantis gate deduped.json --fail-on HIGH
```

### Stage 3: Binary & Managed Runtime Dissection (`rea`)

When analyzing compiled binaries, APKs, Electron bundles, or firmware:

```bash
# Auto-detect artifact kind and extract semantic signatures
harness rea inspect ./build/target_binary --json
harness rea signatures ./build/target_binary --json > signatures.json
```

### Stage 4: Multi-Provider Differential Comparison (`facet`)

Verify reverse-engineering observations across competing disassemblers or decompilers (e.g. Ghidra vs Hopper/IDA):

```bash
# Compare multi-provider observations with 3-valued availability semantics
harness rea diff ./build/target_binary --providers ghidra,ida --json
```

### Stage 5: Cryptographic Evidence Sealing (`rol`)

Seal findings into immutable `CanonicalEvidence` (`ev:<sha256>`) records, update obligation FSMs, and distill learned signatures into the Knowledge Vault:

```bash
# Seal canonical evidence into ledger
harness rol ingest --provider "mantis" --format "json" --file deduped.json

# Distill verified signatures into Knowledge Vault with Isnad lineage
harness rea learn ./build/target_binary
```

### Stage 6: Network Reconnaissance & Fault Isolation (`network-forensics`)

Dissect packet traces, inspect TLS certificates, and diagnose network boundaries:

```bash
# Diagnose 7-layer network fault chains
harness network-forensics diagnose-7layer --target api.internal.local --json

# Analyze traceroute hop latency
harness network-forensics traceroute ./captures/trace.txt --json-output
```

