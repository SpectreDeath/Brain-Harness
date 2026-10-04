#!/usr/bin/env python3
"""Generate Architecture Deepening Review HTML Brief for conversation-trajectory-miner."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# UTF-8 stream codec invariant (Rule 23, Rule 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

temp_dir = Path(os.environ.get("TEMP", r"C:\Users\spectre\AppData\Local\Temp"))
output_path = temp_dir / "architecture-review-20261003-conversation-trajectory-miner.html"

html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Deepening Review — conversation-trajectory-miner</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0f172a',
        primaryColor: '#6366f1',
        primaryBorderColor: '#818cf8',
        lineColor: '#94a3b8',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a'
      }
    });
  </script>
  <style>
    body {
      background-color: #0b0f19;
      color: #f1f5f9;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .glass-card {
      background: rgba(17, 24, 39, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
    }
    .badge-strong {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .badge-worth {
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(96, 165, 250, 0.3);
    }
    .badge-speculative {
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(251, 191, 36, 0.3);
    }
  </style>
</head>
<body class="p-6 md:p-12 max-w-7xl mx-auto space-y-10">

  <!-- Header Section -->
  <header class="glass-card rounded-2xl p-8 border-l-4 border-indigo-500">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Architecture Deepening Loop</span>
          <span class="text-slate-400 text-sm font-mono">Cycle 2026-10-03</span>
        </div>
        <h1 class="text-3xl md:text-4xl font-black text-white mt-2 tracking-tight">
          conversation-trajectory-miner <span class="text-indigo-400 text-2xl font-normal">Seam Elevation & Deepening</span>
        </h1>
        <p class="text-slate-400 mt-2 text-base max-w-3xl">
          Deepening evaluation for the autobiographical execution trajectory and memory archaeology engine. Elevating standalone script utilities into a first-class micro-kernel IoC service, slotted/frozen domain models, failure cluster & retry loop archaeology, dual-lens cognitive bifurcation, and headless Click CLI introspection.
        </p>
      </div>
      <div class="flex flex-col items-end justify-center font-mono text-xs text-slate-400 space-y-1 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
        <div>Target: <span class="text-slate-200">.agents/skills/conversation-trajectory-miner/</span></div>
        <div>Standards: <span class="text-slate-200">AGENTS.md (Rule 1, 2, 6, 10, 12, 22, 40, 41, 48, 49)</span></div>
        <div>Status: <span class="text-emerald-400 font-bold">Stage 3: Recommend</span></div>
      </div>
    </div>
  </header>

  <!-- Seam Audit Metric Cards -->
  <section class="grid grid-cols-1 md:grid-cols-4 gap-5">
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Analyzed Friction Sites</div>
      <div class="text-3xl font-extrabold text-white mt-2">4 Sites</div>
      <div class="text-slate-500 text-xs mt-1">Script isolation, mutable dataclasses, coarse errors, CLI gap</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Candidate Recommendations</div>
      <div class="text-3xl font-extrabold text-indigo-400 mt-2">2 Strong / 2 Worth</div>
      <div class="text-slate-500 text-xs mt-1">High leverage & locality improvements</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">IoC Target Seam</div>
      <div class="text-3xl font-extrabold text-emerald-400 mt-2">Rule 49</div>
      <div class="text-slate-500 text-xs mt-1">CONVERSATION_TRAJECTORY_MINER_KEY typed protocol</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Target Domain Plugin</div>
      <div class="text-3xl font-extrabold text-amber-400 mt-2">Rule 18 / 45</div>
      <div class="text-slate-500 text-xs mt-1">plugins/memory_and_epistemics/ co-location</div>
    </div>
  </section>

  <!-- Architectural Topology: Before vs After -->
  <section class="glass-card rounded-2xl p-8 space-y-6">
    <div class="flex items-center justify-between border-b border-slate-800 pb-4">
      <div>
        <h2 class="text-2xl font-bold text-white tracking-tight">Architectural Topology: Shallow vs. Deepened</h2>
        <p class="text-slate-400 text-sm mt-1">Comparison of caller friction, boundary leakage, and IoC resolution.</p>
      </div>
      <span class="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-3 py-1 rounded border border-indigo-800/50">Mermaid Visualization</span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Before Topology -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-rose-500"></span>
          <h3 class="font-bold text-rose-400 text-base">Before: Shallow Standalone Script (Friction & Leakage)</h3>
        </div>
        <p class="text-xs text-slate-400">Isolated script using argparse; mutable dataclasses; coarse status error counts; regex prompt slicing; callers must fork out-of-process subprocesses or parse stdout; no IoC integration.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        SessionCmd["harness session / reflect"]
        CliUser["User Shell"]
    end

    subgraph ScriptLayer["Standalone Script (.agents/skills/conversation-trajectory-miner/)"]
        Script["scripts/trajectory_miner.py<br/>(Argparse CLI + mutable classes)"]
        MutableDC["StepRecord / ConversationManifest<br/>(slots=True, NOT frozen)"]
        CoarseErrors["Crude SQL status count<br/>(No failure cluster analysis)"]
    end

    subgraph Storage["IDE Multi-Store Storage"]
        ConvDB["conversations/*.db<br/>(SQLite WAL)"]
        ProtobufBlob["step_payload bytes<br/>(raw regex slicing)"]
    end

    Agent -.->|"Subprocess fork (slow, brittle)"| Script
    SessionCmd -.->|"No IoC ServiceKey available"| Script
    CliUser -->|"python scripts/trajectory_miner.py"| Script
    Script --> MutableDC
    Script --> CoarseErrors
    Script --> ConvDB
    ConvDB --> ProtobufBlob
    Script -.->|"Untyped dict stdout"| Agent
          </pre>
        </div>
      </div>

      <!-- After Topology -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
          <h3 class="font-bold text-emerald-400 text-base">After: Deep Micro-Kernel Seam (High Leverage & Locality)</h3>
        </div>
        <p class="text-xs text-slate-400">Slotted and frozen domain models, typed IoC ServiceKey, failure cluster & retry loop archaeology, dual-lens cognitive bifurcation, domain plugin, and headless Click CLI commands.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        SessionCmd["harness session / reflect"]
        ClickCLI["harness trajectory scan/friction/export"]
        ThinScript["scripts/trajectory_miner.py (Thin CLI)"]
    end

    subgraph IoC["Micro-Kernel IoC Container (Rule 49)"]
        SKey["CONVERSATION_TRAJECTORY_MINER_KEY<br/>ServiceKey[ConversationTrajectoryMinerService]"]
        Plugin["ConversationTrajectoryMinerPlugin<br/>(plugins/memory_and_epistemics/)"]
    end

    subgraph ServiceEngine["src/harness/services/conversation_trajectory_miner.py"]
        Service["ConversationTrajectoryMinerService<br/>(@runtime_checkable Protocol)"]
        Models["Slotted & Frozen Dataclasses (Rule 12)<br/>(Manifest, Step, Friction, Cluster)"]
        Archaeology["Friction Archaeology Engine<br/>(Retry Loops & Failure Clusters)"]
        Bifurcation["Dual-Lens Cognitive Bifurcation<br/>(Vault KV Items + Skill Scaffolds)"]
    end

    subgraph Storage["IDE Multi-Store Storage"]
        ConvDB["conversations/*.db (RO URI mode)"]
        VaultDir[".harness/knowledge/<ki_id>/ (Dual-file)"]
    end

    Agent -->|"context.require(KEY)"| SKey
    SessionCmd -->|"context.require(KEY)"| SKey
    ClickCLI --> Service
    ThinScript -->|"Thin delegation"| Service
    SKey --- Plugin
    Plugin --> Service
    Service --> Models
    Service --> Archaeology
    Service --> Bifurcation
    Archaeology --> ConvDB
    Bifurcation --> VaultDir
          </pre>
        </div>
      </div>
    </div>
  </section>

  <!-- Deep Seam Audit: Detailed Candidates -->
  <section class="space-y-6">
    <div class="border-b border-slate-800 pb-4">
      <h2 class="text-2xl font-bold text-white tracking-tight">Evaluated Architecture Candidates</h2>
      <p class="text-slate-400 text-sm mt-1">Multi-axis assessment across Locality, Leverage, and Testability.</p>
    </div>

    <!-- Candidate 1 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-emerald-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-strong">Recommendation: Strong</span>
          <h3 class="text-xl font-bold text-white">Candidate 1: Elevate Standalone CLI Script to Typed Micro-Kernel IoC Service & Domain-Partitioned Plugin</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 49, Rule 1, Rule 2, Rule 45</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 5/5</div>
          <div class="text-slate-300 mt-1">Consolidates domain logic (safe connection, step unpacking, corpus scanning, friction scorecard) in `src/harness/services/conversation_trajectory_miner.py`, co-located with kernel protocols.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">High ratio of hidden complexity to public surface. ReAct agents and kernel services resolve mining capabilities via `context.require(CONVERSATION_TRAJECTORY_MINER_KEY)` without subprocess forks.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Verifiable in-memory via `pytest` without spawning external OS processes or parsing brittle JSON string outputs from stdout.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Currently, `trajectory_miner.py` is an isolated script in `.agents/skills/conversation-trajectory-miner/scripts/`. Other subsystems cannot invoke it in-memory. Callers must invoke `subprocess.run()`, introducing process spawn latency, pipe disposal hazards (Rule 14), and lack of type safety.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Define `ConversationTrajectoryMinerService` protocol and `CONVERSATION_TRAJECTORY_MINER_KEY = ServiceKey[ConversationTrajectoryMinerService]("conversation_trajectory_miner_service")`. Scaffolds `plugins/memory_and_epistemics/conversation_trajectory_miner/` with `plugin.json` and `main.py` exporting module singleton `plugin`. Thin script retains backward-compatible CLI dispatch.</p>
      </div>
    </div>

    <!-- Candidate 2 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-emerald-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-strong">Recommendation: Strong</span>
          <h3 class="text-xl font-bold text-white">Candidate 2: Slotted & Frozen Dataclass Architecture with Immutability Guarantees</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 12, Rule 43</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 5/5</div>
          <div class="text-slate-300 mt-1">All trajectory entities encapsulate their own validation in `__post_init__` construction assertions rather than leaking validation logic to callers.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Drastically reduces per-record memory footprint across large sessions with thousands of steps, eliminating hash-dict allocation overhead.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Immutability directly assertable via `pytest.raises((AttributeError, TypeError))` on direct attribute mutation (Rule 43).</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> `StepRecord` and `ConversationManifest` currently use `slots=True`, but omit `frozen=True`. They lack `__post_init__` checks and rely on mutable dict collections (`dict[str, int]`) that can be mutated in-place by callers, risking silent state corruption.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Introduce slotted and frozen dataclasses: `TrajectoryStepRecord`, `ConversationManifest`, `FailureCluster`, `FrictionScorecard`, and `CognitiveBifurcationReport`. Enforce tuple conversions and immutable value semantics.</p>
      </div>
    </div>

    <!-- Candidate 3 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-blue-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-worth">Recommendation: Worth Exploring</span>
          <h3 class="text-xl font-bold text-white">Candidate 3: Deep Friction Archaeology & Error Loop Isolation Engine</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 22, Rule 40, Rule 41</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 4/5</div>
          <div class="text-slate-300 mt-1">Friction pattern detection, retry cascade grouping, and dual-lens bifurcation live inside the service engine rather than fragmented in external scripts.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">Converts raw SQL error counts into semantic failure clusters (e.g. repeated tool retry sequences, exception classes) and automatically generates dual-file Knowledge Vault items with isnad claims (Rule 40, 41).</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 4/5</div>
          <div class="text-slate-300 mt-1">Easily verified using synthetic SQLite trajectory fixtures containing known error and retry patterns.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Currently, error analysis is just `SELECT COUNT(*) FROM steps WHERE status IN (6, 7)...`. It does not detect retry loops, tool call failures, or resolution diffs. It completely lacks the Dual-Lens Cognitive Bifurcation promised in SKILL.md Section 4.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Implement `mine_failure_clusters(cid)` and `bifurcate_distillation(cid, ...)` producing canonical Knowledge Vault artifacts (`metadata.json` + `summary.md`) with unbroken isnad provenance chains.</p>
      </div>
    </div>

    <!-- Candidate 4 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-blue-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-worth">Recommendation: Worth Exploring</span>
          <h3 class="text-xl font-bold text-white">Candidate 4: Headless Click CLI Introspection Seam & Command Consolidation</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 6, Rule 10, Rule 23</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 4/5</div>
          <div class="text-slate-300 mt-1">Single-source Click command group co-located in `src/harness/commands/trajectory_miner.py`, registered in `src/harness/cli.py`.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Provides both human-readable tables and machine-parseable JSON streams across `harness trajectory scan`, `harness trajectory friction`, and `harness trajectory inspect`.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Directly testable in CI via `click.testing.CliRunner` with deterministic exit codes and stdout validation.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Trajectory mining commands cannot be executed via the standard `harness` CLI; users and automation must know the path to `.agents/skills/conversation-trajectory-miner/scripts/trajectory_miner.py` and invoke python directly with non-standard flags.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Add `trajectory_miner_group` under `harness.commands`, registering subcommands `scan`, `friction`, `inspect`, and `export`, with aliases `trajectory`, `trajectory-miner`, `conversation-miner`.</p>
      </div>
    </div>
  </section>

  <!-- Top Recommendation & Execution Roadmap -->
  <section class="glass-card rounded-2xl p-8 border-2 border-indigo-500/50 space-y-6">
    <div class="flex items-center gap-3">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-indigo-500 text-white">Stage 3 Synthesis</span>
      <h2 class="text-2xl font-bold text-white tracking-tight">Top Recommendation: Comprehensive Seam Elevation & Deepening</h2>
    </div>

    <div class="text-sm text-slate-300 leading-relaxed space-y-3">
      <p>
        We recommend executing an end-to-end deepening that consolidates Candidates 1 through 4 into a single, high-leverage architectural elevation:
      </p>
      <ol class="list-decimal list-inside space-y-2 pl-2 text-slate-300">
        <li><strong>Phase 1: Slotted & Frozen Domain Engine & Protocol</strong> (<code class="text-indigo-300">src/harness/services/conversation_trajectory_miner.py</code>): Implement slotted/frozen models (<code class="text-indigo-300">TrajectoryStepRecord</code>, <code class="text-indigo-300">ConversationManifest</code>, <code class="text-indigo-300">FailureCluster</code>, <code class="text-indigo-300">FrictionScorecard</code>, <code class="text-indigo-300">CognitiveBifurcationReport</code>), typed <code class="text-indigo-300">ConversationTrajectoryMinerService</code> protocol, and <code class="text-indigo-300">CONVERSATION_TRAJECTORY_MINER_KEY</code>.</li>
        <li><strong>Phase 2: Domain-Partitioned Plugin</strong> (<code class="text-indigo-300">plugins/memory_and_epistemics/conversation_trajectory_miner/</code>): Create <code class="text-indigo-300">plugin.json</code> and <code class="text-indigo-300">main.py</code> exporting instantiated singleton <code class="text-indigo-300">plugin</code> registering into the IoC container.</li>
        <li><strong>Phase 3: Deep Friction Archaeology & Dual-Lens Bifurcation</strong>: Implement failure cluster extraction, retry cascade detection, and canonical dual-file Knowledge Vault item generation with isnad claim verification.</li>
        <li><strong>Phase 4: Headless Click CLI & Backward-Compatible Script Delegation</strong>: Create Click command group in <code class="text-indigo-300">src/harness/commands/trajectory_miner.py</code>, register in <code class="text-indigo-300">src/harness/cli.py</code>, and refactor <code class="text-indigo-300">trajectory_miner.py</code> into a thin CLI wrapper delegating to the deep service engine.</li>
        <li><strong>Phase 5: Comprehensive Contract & Regression Tests</strong> (<code class="text-indigo-300">tests/test_conversation_trajectory_miner_deepening.py</code>): Verify service protocol conformance, IoC lifecycle, slotted/frozen immutability (Rule 43), friction archaeology, Knowledge Vault export, and Click CLI execution.</li>
      </ol>
    </div>

    <div class="p-4 rounded-xl bg-slate-900/90 border border-indigo-500/30 flex items-center justify-between">
      <div class="text-xs text-slate-300">
        <span class="text-indigo-400 font-bold">Passing Gate:</span> All unit and contract tests pass with 100% green status; zero breaking changes to existing CLI flags or skill workflows.
      </div>
      <span class="text-xs font-mono text-emerald-400 bg-emerald-950/60 px-3 py-1 rounded border border-emerald-800/40">Ready for Plan Approval</span>
    </div>
  </section>

  <!-- Footer -->
  <footer class="text-center text-xs text-slate-500 border-t border-slate-900 pt-6">
    Harness Architecture Deepening Loop — Generated for conversation-trajectory-miner — 2026-10-03
  </footer>

</body>
</html>
"""

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(html_content, encoding="utf-8")
print(f"Generated review brief successfully at: {output_path}")
