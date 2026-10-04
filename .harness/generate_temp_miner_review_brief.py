#!/usr/bin/env python3
"""Generate Architecture Deepening Review HTML Brief for temp-artifact-miner."""

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
output_path = temp_dir / "architecture-review-20261004-temp-artifact-miner.html"

html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Deepening Review — temp-artifact-miner</title>
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
          <span class="text-slate-400 text-sm font-mono">Cycle 2026-10-04</span>
        </div>
        <h1 class="text-3xl md:text-4xl font-black text-white mt-2 tracking-tight">
          temp-artifact-miner <span class="text-indigo-400 text-2xl font-normal">Seam Elevation & Deepening</span>
        </h1>
        <p class="text-slate-400 mt-2 text-base max-w-3xl">
          Deepening evaluation for the ephemeral runtime archaeology and visual architecture salvage engine. Elevating standalone script utilities into a first-class micro-kernel IoC service, strictly slotted/frozen models with immutable tuples, automated dual-lens cognitive bifurcation into Knowledge Vault and permanent docs, and headless Click CLI introspection.
        </p>
      </div>
      <div class="flex flex-col items-end justify-center font-mono text-xs text-slate-400 space-y-1 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
        <div>Target: <span class="text-slate-200">.agents/skills/temp-artifact-miner/</span></div>
        <div>Standards: <span class="text-slate-200">AGENTS.md (Rule 1, 2, 6, 10, 12, 18, 40, 41, 48, 49)</span></div>
        <div>Status: <span class="text-emerald-400 font-bold">Stage 3: Recommend</span></div>
      </div>
    </div>
  </header>

  <!-- Seam Audit Metric Cards -->
  <section class="grid grid-cols-1 md:grid-cols-4 gap-5">
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Analyzed Friction Sites</div>
      <div class="text-3xl font-extrabold text-white mt-2">4 Sites</div>
      <div class="text-slate-500 text-xs mt-1">Script isolation, collection mutability, bifurcation gap, CLI gap</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Candidate Recommendations</div>
      <div class="text-3xl font-extrabold text-indigo-400 mt-2">2 Strong / 2 Worth</div>
      <div class="text-slate-500 text-xs mt-1">High leverage & locality improvements</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">IoC Target Seam</div>
      <div class="text-3xl font-extrabold text-emerald-400 mt-2">Rule 49</div>
      <div class="text-slate-500 text-xs mt-1">TEMP_ARTIFACT_MINER_KEY typed protocol</div>
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
        <p class="text-xs text-slate-400">Isolated script using argparse; mutable inner lists/dicts in frozen classes; missing Knowledge Vault export and docs salvage; callers must fork out-of-process subprocesses or parse stdout; no IoC integration.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        SessionCmd["harness session / reflect"]
        CliUser["User Shell"]
    end

    subgraph ScriptLayer["Standalone Script (.agents/skills/temp-artifact-miner/)"]
        Script["scripts/temp_artifact_miner.py<br/>(Argparse CLI + standalone functions)"]
        MutableCollections["BriefCatalogItem / BriefCatalog<br/>(mutable list/dict inner fields)"]
        PrintMarkdown["generate_salvage_markdown()<br/>(stdout print only, no KV export)"]
    end

    subgraph Storage["Operating System Ephemeral Stores"]
        TempDir["%TEMP%/*.html<br/>(Visual Briefs)"]
        PytestSandboxes["pytest-of-spectre/pytest-*<br/>(Mock Fixtures)"]
    end

    Agent -.->|"Subprocess fork (slow, un-slotted)"| Script
    SessionCmd -.->|"No IoC ServiceKey available"| Script
    CliUser -->|"python scripts/temp_artifact_miner.py"| Script
    Script --> MutableCollections
    Script --> PrintMarkdown
    Script --> TempDir
    Script --> PytestSandboxes
    Script -.->|"Markdown text stdout"| Agent
          </pre>
        </div>
      </div>

      <!-- After Topology -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
          <h3 class="font-bold text-emerald-400 text-base">After: Deep Micro-Kernel Seam (High Leverage & Locality)</h3>
        </div>
        <p class="text-xs text-slate-400">Slotted and frozen domain models with immutable tuples, typed IoC ServiceKey, heavy topology bounding, automated dual-lens cognitive bifurcation into Knowledge Vault and docs, and headless Click CLI commands.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        SessionCmd["harness session / reflect"]
        ClickCLI["harness temp scan/sandbox/salvage/bifurcate"]
        ThinScript["scripts/temp_artifact_miner.py (Thin CLI)"]
    end

    subgraph IoC["Micro-Kernel IoC Container (Rule 49)"]
        SKey["TEMP_ARTIFACT_MINER_KEY<br/>ServiceKey[TempArtifactMinerService]"]
        Plugin["TempArtifactMinerPlugin<br/>(plugins/memory_and_epistemics/)"]
    end

    subgraph ServiceEngine["src/harness/services/temp_artifact_miner.py"]
        Service["TempArtifactMinerService<br/>(@runtime_checkable Protocol)"]
        Models["Slotted & Frozen Dataclasses (Rule 12)<br/>(BriefCatalogItem, SandboxReport, Bifurcation)"]
        BriefParser["HTML Brief & Mermaid Parser<br/>(Heavy Topology Bounding Rule 48)"]
        Bifurcation["Dual-Lens Cognitive Bifurcation<br/>(Vault KV Items + Docs Salvage)"]
    end

    subgraph Storage["Ephemeral & Persistent Storage"]
        TempDir["%TEMP%/*.html (Read-only)"]
        VaultDir[".harness/knowledge/<ki_id>/ (Dual-file)"]
        DocsDir["docs/architecture/ (Permanent SVGs & briefs)"]
    end

    Agent -->|"context.require(KEY)"| SKey
    SessionCmd -->|"context.require(KEY)"| SKey
    ClickCLI --> Service
    ThinScript -->|"Thin delegation"| Service
    SKey --- Plugin
    Plugin --> Service
    Service --> Models
    Service --> BriefParser
    Service --> Bifurcation
    BriefParser --> TempDir
    Bifurcation --> VaultDir
    Bifurcation --> DocsDir
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
          <div class="text-slate-300 mt-1">Consolidates domain logic (brief scan, heavy topology bounding, pytest sandbox triage, ring-buffer tailing) in `src/harness/services/temp_artifact_miner.py`, co-located with kernel protocols.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">High ratio of hidden complexity to public surface. ReAct agents and kernel services resolve mining capabilities via `context.require(TEMP_ARTIFACT_MINER_KEY)` without subprocess forks.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Verifiable in-memory via `pytest` without spawning external OS processes or parsing brittle JSON string outputs from stdout.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Currently, `temp_artifact_miner.py` is an isolated script in `.agents/skills/temp-artifact-miner/scripts/`. Other subsystems cannot invoke it in-memory. Callers must invoke `subprocess.run()`, introducing process spawn latency, pipe disposal hazards (Rule 14), and lack of type safety.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Define `TempArtifactMinerService` protocol and `TEMP_ARTIFACT_MINER_KEY = ServiceKey[TempArtifactMinerService]("temp_artifact_miner_service")`. Scaffolds `plugins/memory_and_epistemics/temp_artifact_miner/` with `plugin.json` and `main.py` exporting module singleton `plugin`. Thin script retains backward-compatible CLI dispatch.</p>
      </div>
    </div>

    <!-- Candidate 2 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-emerald-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-strong">Recommendation: Strong</span>
          <h3 class="text-xl font-bold text-white">Candidate 2: Slotted & Frozen Dataclass Architecture with Strict Immutable Tuples</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 12, Rule 43</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 5/5</div>
          <div class="text-slate-300 mt-1">All ephemeral entity structures encapsulate validation in `__post_init__` construction assertions rather than leaking validation logic to callers.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Replaces nested mutable lists (`list[str]`, `list[BriefCatalogItem]`) with immutable tuples (`tuple[str, ...]`), eliminating hash-dict allocation overhead and accidental in-place mutation.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Immutability directly assertable via `pytest.raises((AttributeError, TypeError))` on direct attribute mutation (Rule 43).</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> `BriefCatalogItem`, `BriefCatalog`, and `SandboxReport` use `slots=True, frozen=True`, but declare mutable fields (`mermaid_dags: list[str]`, `runs: list[SandboxFixture]`), which can be modified in-place by external callers, violating immutability invariants.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Enforce `tuple[str, ...]`, `tuple[BriefCatalogItem, ...]`, and `tuple[SandboxFixture, ...]` across all domain models, introducing `IsnadAttributionRecord` and `VisualSalvageReport`.</p>
      </div>
    </div>

    <!-- Candidate 3 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-blue-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-worth">Recommendation: Worth Exploring</span>
          <h3 class="text-xl font-bold text-white">Candidate 3: Automated Dual-Lens Cognitive Bifurcation & Documentation Salvage</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 40, Rule 41</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 4/5</div>
          <div class="text-slate-300 mt-1">Cognitive bifurcation logic lives in the service engine rather than fragmented in external scripts or manual markdown dumps.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">Converts ephemeral visual briefs and Mermaid diagrams in `%TEMP%` into canonical Knowledge Vault items (`metadata.json` + `summary.md`) with unbroken isnad claims (Rule 40, 41) and permanent documentation.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 4/5</div>
          <div class="text-slate-300 mt-1">Easily asserted via filesystem fixtures verifying dual-file creation and isnad schema conformance.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Currently, `temp_artifact_miner.py` only implements a markdown text string generator (`generate_salvage_markdown`). It has no mechanism to commit extracted decisions into the Knowledge Vault or salvage diagrams into repository documentation.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Implement `bifurcate_distillation(brief_name, ...)` and `export_knowledge_item(...)` producing canonical Knowledge Vault dual-files and permanent architecture docs.</p>
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
          <div class="text-slate-300 mt-1">Single-source Click command group co-located in `src/harness/commands/temp_miner.py`, registered in `src/harness/cli.py`.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Provides both human-readable tables and machine-parseable JSON streams across `harness temp scan`, `harness temp sandbox`, `harness temp tail`, `harness temp salvage`, and `harness temp bifurcate`.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Directly testable in CI via `click.testing.CliRunner` with deterministic exit codes and stdout validation.</div>
        </div>
      </div>

      <div class="text-xs text-slate-300 space-y-2 border-t border-slate-800/80 pt-3">
        <p><strong class="text-white">Friction Point:</strong> Temporary artifact mining commands cannot be executed via the standard `harness` CLI; automation must invoke python directly with script arguments.</p>
        <p><strong class="text-white">Deepened Seam:</strong> Add `temp_miner_group` under `harness.commands`, registering subcommands `scan`, `sandbox`, `tail`, `salvage`, `bifurcate`, with aliases `temp`, `temp-miner`, `ephemeral-miner`.</p>
      </div>
    </div>
  </section>

  <!-- Top Recommendation & Execution Roadmap -->
  <section class="glass-card rounded-2xl p-8 border-2 border-indigo-500/50 space-y-6">
    <div class="flex items-center gap-3">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-indigo-500 text-white">Stage 3 Synthesis</span>
      <h2 class="text-2xl font-bold text-white tracking-tight">Top Recommendation: Complete Tri-Store Archaeology Architecture</h2>
    </div>

    <div class="text-sm text-slate-300 leading-relaxed space-y-3">
      <p>
        We recommend consolidating Candidates 1 through 4 into an end-to-end deepening that completes the third pillar of the Brain Harness artifact archaeology triumvirate:
      </p>
      <ol class="list-decimal list-inside space-y-2 pl-2 text-slate-300">
        <li><strong>Phase 1: Slotted & Frozen Domain Engine & Protocol</strong> (<code class="text-indigo-300">src/harness/services/temp_artifact_miner.py</code>): Implement slotted/frozen models (<code class="text-indigo-300">BriefCatalogItem</code>, <code class="text-indigo-300">BriefCatalog</code>, <code class="text-indigo-300">SandboxFixture</code>, <code class="text-indigo-300">SandboxReport</code>, <code class="text-indigo-300">IsnadAttributionRecord</code>, <code class="text-indigo-300">VisualSalvageReport</code>, <code class="text-indigo-300">CognitiveBifurcationReport</code>), typed <code class="text-indigo-300">TempArtifactMinerService</code> protocol, and <code class="text-indigo-300">TEMP_ARTIFACT_MINER_KEY</code>.</li>
        <li><strong>Phase 2: Domain-Partitioned Plugin</strong> (<code class="text-indigo-300">plugins/memory_and_epistemics/temp_artifact_miner/</code>): Create <code class="text-indigo-300">plugin.json</code> and <code class="text-indigo-300">main.py</code> exporting instantiated singleton <code class="text-indigo-300">plugin</code> registering into the IoC container.</li>
        <li><strong>Phase 3: Dual-Lens Cognitive Bifurcation & Heavy Bounding Engine</strong>: Implement HTML brief parsing with heavy topology bounding (Rule 48), ring-buffer diagnostic tailing (Rule 53), and canonical dual-file Knowledge Vault item generation with isnad claim verification (Rule 40, 41).</li>
        <li><strong>Phase 4: Headless Click CLI & Backward-Compatible Script Delegation</strong>: Create Click command group in <code class="text-indigo-300">src/harness/commands/temp_miner.py</code>, register in <code class="text-indigo-300">src/harness/cli.py</code>, and refactor <code class="text-indigo-300">temp_artifact_miner.py</code> into a thin CLI wrapper delegating to the deep service engine.</li>
        <li><strong>Phase 5: Comprehensive Contract & Regression Tests</strong> (<code class="text-indigo-300">tests/test_temp_artifact_miner_deepening.py</code>): Verify service protocol conformance, IoC lifecycle, slotted/frozen immutability (Rule 43), heavy topology bounding, Knowledge Vault export, and Click CLI execution.</li>
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
    Harness Architecture Deepening Loop — Generated for temp-artifact-miner — 2026-10-04
  </footer>

</body>
</html>
"""

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(html_content, encoding="utf-8")
print(f"Generated review brief successfully at: {output_path}")
