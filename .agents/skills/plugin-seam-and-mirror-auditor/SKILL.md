---
name: plugin-seam-and-mirror-auditor
description: >-
  Audit, stress-test, and auto-synchronize plugin codebases across IoC DAG
  topology, adversarial parameter fuzzing, and AST documentation mirroring on
  any target directory. Do not use for generic prose copyediting or
  unstructured markdown note-taking.
---

# Plugin Seam & Mirror Auditor

A specialized operational skill and CLI suite for auditing IoC service dependency DAGs, detecting async runtime deadlocks via adversarial parameter fuzzing, verifying documentation-to-code AST mirroring, and auto-fixing documentation and manifest drift across arbitrary target directories.

## Overview

When authoring or modifying Harness plugins, architectural seams frequently degrade:
1. **Dependency Drift**: Circular IoC registrations or dangling `ServiceKey[T]` requirements that crash kernel lifecycle startup.
2. **Event Loop & Timeout Deadlocks**: Entrypoints that call `asyncio.run()` inside running event loops, or execute unpruned subprocesses exceeding bounded budgets.
3. **Documentation Drift**: README tools tables that omit active entrypoints, or list out-of-date parameter names that fail model tool-calling.

This skill packages an autonomous 5-phase audit and auto-fix pipeline that can be pointed at **any directory** (single plugin, category group, or entire repository) to ensure 100% architectural integrity and zero documentation drift.

## Dependencies

- [adversarial-agent-verifier](../adversarial-agent-verifier/SKILL.md): For DAG seam analysis and inspect-before-edit protocols.
- [repo-doc-synchronizer](../repo-doc-synchronizer/SKILL.md): For Diátaxis documentation taxonomy and documentation drift verification.
- [agent-skill-sdlc](../agent-skill-sdlc/SKILL.md): For two-phase validation pipelines and zero-fork operational budgets.

Companion quick-reference card: [CARD.md](CARD.md)  
JSON Schema reference: [references/audit_schema.json](references/audit_schema.json)

## Quick Start

Execute a full audit with automatic remediation on any target directory:

```bash
# Point at any single plugin
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py all --target-dir plugins/integration_and_io/chatbotx

# Point at a domain category
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py all --target-dir plugins/data_engineering

# Run on the whole plugins directory with JSON report output
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py all --target-dir plugins --output audit_report.json
```

## Utility Scripts

The companion CLI script [`scripts/plugin_auditor.py`](scripts/plugin_auditor.py) provides 5 dedicated subcommands:

### 1. `dag` — IoC Dependency Graph Audit
Analyzes service registrations (`provides`) and service resolutions (`requires`).
```bash
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py dag --target-dir plugins/
```
- Traverses all discovered manifests.
- Detects circular dependencies using Tarjan / DFS cycle detection.
- Flags unprovided or dangling `ServiceKey` requirements.

### 2. `fuzz` — Adversarial Parameter Fuzzing
Subjects every exposed function to 4 distinct parameter matrices with async timeout bounds (default: 5.0s):
```bash
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py fuzz --target-dir plugins/software_engineering/test_runner --timeout 5.0
```
- **`empty`**: Zero-argument invocation (`fn()`).
- **`null_none`**: Passes `None` to every parameter.
- **`type_confusion`**: Passes integer literals (`42`) into expected strings/collections.
- **`boundary_injection`**: Traversal paths (`../../etc/passwd\x00\n🔥`) and Unicode symbols.
- Identifies unhandled exceptions, event loop crashes (`asyncio.run()`), and thread deadlocks.

### 3. `mirror` — Documentation-to-Code AST Mirroring
Parses `main.py` via Python's `ast` module and inspects companion `plugin.json` and `README.md`:
```bash
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py mirror --target-dir plugins/agent_orchestration
```
- Flags entrypoints present in code but missing from `README.md` tools tables.
- Validates that documented parameter lists mirror actual AST argument names.
- Verifies syntax validity of all embedded Python code blocks in markdown.

### 4. `sync` — Auto-Fix & Synchronization Engine
Automatically repairs discovered documentation and manifest drift in place:
```bash
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py sync --target-dir plugins/
```
- Scaffolds missing Diátaxis `README.md` files with complete metadata and tool tables.
- Rewrites `## Tools & Entrypoints` markdown tables to mirror exact AST code parameters.
- Populates `entrypoints` in `plugin.json` if initially unconfigured.

### 5. `all` — Full 5-Phase End-to-End Pipeline
Executes DAG verification, AST mirroring, Auto-Fix remediation, and parameter fuzzing in sequence:
```bash
python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py all --target-dir plugins/ --output audit_summary.json
```

## Workflow

When verifying or onboarding plugins into the repository, follow this 4-step sequence:

```
Target Directory ──> [1. DAG Audit] ──> [2. AST Mirror Audit]
                            │                     │
                            v                     v
                     Cycle/Dangling?       Doc Drift Detected?
                            │                     │
                            │                     └──> [3. Auto-Fix Sync]
                            v                                 │
                     [4. Adversarial Fuzzing] <───────────────┘
                            │
                            v
                     Verified Plugin Seam
```

1. **Point the Auditor at the Target Directory**: Run `python .agents/skills/plugin-seam-and-mirror-auditor/scripts/plugin_auditor.py all --target-dir <path>`.
2. **Review Auto-Fix Actions**: Inspect the output log for any scaffolded READMEs or synchronized tool tables.
3. **Inspect Fuzzing Exceptions**: Review any unhandled runtime exceptions or timeouts surfaced during parameter injection. If a tool uses `asyncio.run()`, refactor to `async def` with `await`.
4. **Final Regression Test**: Execute targeted test suites via `pytest tests/test_plugin_<name>.py` to guarantee zero behavior regressions.

## Visual Brief Pillar

When completing comprehensive plugin audits, the auditor generates an interactive HTML visual brief alongside structured JSON findings:
- **Interactive HTML Dashboard**: Written to `%TEMP%/plugin-verification-matrix.html` or specified via `--html-matrix <path>`.
- **Status Badges & Metrics**: Renders real-time DOM status cards for DAG validity, mirror parity rate, safe fuzz executions, and exception counts.

## Mandatory Checkpoint Gates

Before committing plugin changes or finalizing verification, agents must assert the following gates:
1. **Gate 1 (DAG Zero-Cycle)**: Assert `cycles_detected == 0` and `dangling_requirements == 0`.
2. **Gate 2 (AST Mirror Parity)**: Assert 0 missing READMEs, 0 missing entrypoint table rows, and 0 parameter drift warnings.
3. **Gate 3 (Fuzz Boundedness)**: Assert 0 hang or deadlock timeouts (>5.0s) and 0 unhandled `asyncio.run()` loop collisions.
4. **Gate 4 (User Feedback & Approvals)**: When scaffolding new plugins or applying sweeping syncs, request user review via `RequestFeedback: true` in the artifact implementation plan.

## Anti-Patterns

- **Direct In-Process Asyncio Run** — Calling `asyncio.run()` inside tool functions causes fatal `RuntimeError` crashes when invoked inside async agent loops or test runners; always expose async entrypoints as `async def` with `await`.
- **Manual Table Drift** — Manually typing parameter lists into `README.md` leads to silent documentation rot; always derive documentation tables directly from Python AST signatures via `plugin_auditor.py sync`.
- **Unbounded Fuzzing Loops** — Executing parameter fuzzing without per-call timeouts causes worker threads to hang indefinitely on rogue subprocesses; always enforce bounded timeouts ($\le 5.0$s).
- **Hardcoded Path Assumptions** — Scanners assuming plugins only live in `plugins/<cat>/<name>/` fail on standalone repos or flat directories; always inspect directory contents dynamically.

## Common Mistakes

1. **Running inline `-c` strings on PowerShell**: Avoid invoking Python snippets through PowerShell `-c` strings due to quote escaping and UTF-16 corruptions. Always use the provided script CLI (`Rule 29`).
2. **Omitting Windows UTF-8 reconfigure**: Running CLI tools on Windows without `sys.stdout.reconfigure(encoding='utf-8')` causes `cp1252` encoding crashes when printing Unicode DAG symbols or fuzz payloads (`Rule 23`).
3. **Skipping AST validation after code changes**: Modifying function signatures in `main.py` without re-running `sync` leaves stale documentation tables in `README.md`.
