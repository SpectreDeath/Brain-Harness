# Brain Harness Architecture & Design Concepts

This document provides a deep architectural examination of the design principles, structural choices, and runtime mechanisms that govern Brain Harness.

---

## 1. Micro-Kernel & IoC Architecture

At the core of Brain Harness is a minimalist micro-kernel. The kernel provides only foundational primitives: dependency injection, lifecycle management, an immutable event bus, and storage interfaces.

### 1.1 Everything is a Plugin (Rule 1)
No business capabilities or domain tools are hardcoded into the kernel:
- **Separation of Concerns**: LLM providers, file editing tools, web browsers, and memory graphs all live in domain-partitioned plugins (`plugins/<category>/<name>`).
- **Clean Inversion of Control**: The kernel defines interfaces and hosts an IoC container (`ServiceContext`). Plugins register implementations into this container during the `LOADED` lifecycle phase.

### 1.2 Typed Service Keys (Rule 2)
To eliminate fragile string identifiers and avoid runtime resolution typos, all service discovery is mediated by `ServiceKey[T]`:

```python
# Declaration in harness.services
STORAGE_SERVICE_KEY = ServiceKey[StorageService]("core.storage")

# Resolution in consumer
storage = context.require(STORAGE_SERVICE_KEY)
```
Generic typing guarantees that IDEs and static type checkers know the exact interface of the returned service.

---

## 2. ReAct Agent Step Engine & Context Optimization

Autonomous agents run inside the `ReActAgentLoop` guided by `StepExecutionEngine`. Every step progresses through a resilient execution pipeline:

```
[Thought Formulation] ──► [In-Flight Tool Repair] ──► [Context Transaction]
                                                             │
                                                             ▼
[Pre-LLM AST Optimization] ◄── [In-Flight Linter Audit] ◄── [Tool Invocation]
```

### 2.1 Transactional Workspace Isolation (Rule 8)
Tool executions that mutate files operate within atomic context transactions:
- When a tool starts, `FilesystemGitService` establishes a clean checkpoint.
- If the tool completes successfully and passes in-flight syntax verification, the transaction commits.
- If the tool errors or raises an unhandled exception, `rollback_transaction()` restores the workspace to the exact previous checkpoint, preventing partial corruption.

### 2.2 In-Flight Self-Repair (Rule 16 & Rule 21)
Model outputs frequently suffer from small syntax flaws (unclosed brackets, markdown fences wrapping JSON, trailing commas). Rather than halting:
- The stream parser detects and auto-repairs JSON fences in-flight before execution.
- File-writing tools immediately execute `ArchLinterService.lint_file()`, embedding any syntax or bracket errors into the observation for immediate self-correction on the next step.

### 2.3 Pre-LLM Context Optimization (Rule 9)
Context windows are finite and expensive. Before dispatching history to the model:
- `UnifiedContextPipelineService` applies deterministic multi-pass pruning: whitespace normalization, progressive middle-out reduction of large tool outputs, and tabular truncation.
- `RepoMapService` dynamically computes a PageRanked AST graph of workspace symbols, injecting a concise code skeleton of relevant definitions into the system prompt.

---

## 3. Subprocess Sandboxing & IPC Transports

Running untrusted external code requires rigid process boundaries:
- **Isolated Subprocesses (Rule 5)**: External plugins run in isolated virtual environments managed by `SubprocessSandbox`. Communication occurs via line-buffered JSON-RPC 2.0 over standard OS pipes.
- **Lazy Venv Staging (Rule 7)**: Virtual environments are provisioned on demand upon the first tool call rather than during boot, ensuring near-instantaneous startup times.
- **Pipe Resource Disposal (Rule 14 & Rule 53)**: Transports spawn asynchronous tasks draining `stderr` into ring buffers, preventing OS pipe deadlocks. All streams are explicitly closed within `finally` blocks upon exit.

---

## 4. Knowledge Vault & Epistemic Provability

Agent memory must be truthful and resistant to hallucination:
- **The Isnad Provenance Protocol**: Every verified claim stored in the Knowledge Vault (`.harness/knowledge/<ki_id>/`) carries an unbroken chain-of-custody lineage pointing to a source commit, document offset, or tool event.
- **Canonical Dual-File Structure (Rule 40)**: Knowledge items are persisted strictly as directory pairs (`metadata.json` + `summary.md`).
- **Dual-Lens Cognitive Distillation (Rule 41)**: Analysis of raw materials is bifurcated into an epistemic introspection seam (grounding mental models in the vault) and a procedural skill synthesis seam (scaffolding executable agent skills).

---

## 5. Immutable Event Bus & Telemetry

Every transition in Brain Harness emits a structured event:
- **Append-Only Event Log (Rule 4)**: Events are immutable records. Once appended, events are never modified or purged.
- **Decoupled Telemetry Projection**: The `UIProjectionEngine` streams event logs across WebSockets to dashboards, CLI watch daemons, and external monitors without introducing blocking locks into the execution loop.

---

## 6. Dynamic Compute & Complexity Calibration

Task planning evaluates composite 5D complexity (Span, Depth, Concurrency, Rigor, Domain Heterogeneity):
- Low-complexity tasks utilize lightweight models (e.g. Gemini Flash) with reasoning off for sub-second responses.
- High-complexity tasks ($\ge 0.75$) automatically escalate to advanced models (e.g. Claude Sonnet / Opus) with reasoning budgets locked to High and subprocess timeouts expanded to 300s+.
