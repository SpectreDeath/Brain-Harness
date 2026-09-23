# Skill Summary Card: `pi-coding-harness`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       pi-coding-harness                         │
│ Category:    agent_orchestration / coding-harness      │
│ Invocation:  /pi-coding-harness                        │
│ Trigger:     "build pi coding agent",                  │
│              "minimalist coding agent harness",        │
│              "branchable session tree DAG",            │
│              "repair tool call history",               │
│              "evaluate project trust security"         │
│ Version:     1.0.0                                     │
│ Provides:    "pi_harness_engine", "tau_bridge"         │
│ Requires:    "crafting-skills", "agent-skills-architect"│
├────────────────────────────────────────────────────────┤
│ Target:      Architect, construct, and evaluate        │
│              portable Pi-style coding agent harnesses  │
│              with session DAGs and trust perimeters.   │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Operational Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Architecture Decoupling** | Isolate streaming (`tau_ai`), loop (`tau_agent`), and frontend (`tau_coding`) | Three-tier architecture | Zero UI imports inside agent loop package |
| **2. Branchable Session DAG** | Model conversation history as directed acyclic graph entries | Session DAG entries | Linear ancestry path resolved for fork nodes |
| **3. Append-Only Journal** | Persist session entries into file-locked append-only JSONL files | Locked JSONL storage | Non-destructive writes surviving crashes |
| **4. In-Flight Tool Repair** | Normalize tool-call and tool-response pairs before model submission | Clean message list | 100% parity between tool IDs; zero 400 errors |
| **5. Trust & RPC Governance** | Evaluate workspace trust and expose headless JSON-RPC protocol | Security & RPC seam | Protected assets isolated; valid RPC envelopes |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\pi-coding-harness-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Three-tier architecture DAG & session tree diagrams -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit human approval before scaffolding harness code.
```

### 3. Explicit Anti-Patterns Box
- **Loop UI Coupling**: Importing terminal widgets or CLI prompts into core agent loop modules.
- **Destructive History Truncation**: Overwriting session files when rewinding instead of appending DAG nodes.
- **Unrepaired Tool Desync**: Passing unresponded tool calls to LLMs causing 400 Bad Request crashes.
- **Unverified Workspace Execution**: Running code in untrusted workspaces without evaluating trust boundaries.
- **Monolithic State Sprawl**: Storing state in mutable dictionaries instead of slotted frozen dataclasses.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Instructions state direct target actions instead of negative prohibitions.
- [ ] **Leading Words**: Employs compact domain vocabulary (*harness*, *session tree*, *journal*, *ancestry*, *repair*, *trust*).
- [ ] **Exhaustive Completion Criteria**: Every stage specifies unambiguous completion gates.
- [ ] **Modular Boundaries**: Clear separation between streaming, cognition, and frontend layers.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored with ASCII single-pipe metadata box.
- [ ] **Pre-Flight Validation**: Passes `SkillValidator.validate()` with zero errors or warnings.
