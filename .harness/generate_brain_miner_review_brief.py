#!/usr/bin/env python3
"""Generate Architecture Deepening Review HTML Brief for brain-artifact-miner."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# UTF-8 stream codec invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

temp_dir = Path(os.environ.get("TEMP", r"C:\Users\spectre\AppData\Local\Temp"))
output_path = temp_dir / "architecture-review-20261003-brain-artifact-miner.html"

html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Deepening Review — brain-artifact-miner</title>
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

  <!-- Header Header -->
  <header class="glass-card rounded-2xl p-8 border-l-4 border-indigo-500">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Architecture Deepening Loop</span>
          <span class="text-slate-400 text-sm font-mono">Cycle 2026-10-03</span>
        </div>
        <h1 class="text-3xl md:text-4xl font-black text-white mt-2 tracking-tight">
          brain-artifact-miner <span class="text-indigo-400 text-2xl font-normal">Seam Elevation & Deepening</span>
        </h1>
        <p class="text-slate-400 mt-2 text-base max-w-3xl">
          Deepening evaluation for the filesystem-native workspace archaeology engine. Transforming standalone script utilities into a first-class micro-kernel IoC service, high-leverage dual-transcript random seek seam, and headless Click CLI introspection suite.
        </p>
      </div>
      <div class="flex flex-col items-end justify-center font-mono text-xs text-slate-400 space-y-1 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
        <div>Target: <span class="text-slate-200">.agents/skills/brain-artifact-miner/</span></div>
        <div>Standard: <span class="text-slate-200">AGENTS.md (Rule 49, 12, 10, 40)</span></div>
        <div>Status: <span class="text-emerald-400 font-bold">Stage 3: Recommend</span></div>
      </div>
    </div>
  </header>

  <!-- Seam Audit Metric Cards -->
  <section class="grid grid-cols-1 md:grid-cols-4 gap-5">
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Analyzed Friction Sites</div>
      <div class="text-3xl font-extrabold text-white mt-2">4 Sites</div>
      <div class="text-slate-500 text-xs mt-1">Script isolation, seek leakage, CLI gap, KV manual</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Candidate Recommendations</div>
      <div class="text-3xl font-extrabold text-indigo-400 mt-2">2 Strong / 2 Worth</div>
      <div class="text-slate-500 text-xs mt-1">High leverage & locality improvements</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">IoC Target Seam</div>
      <div class="text-3xl font-extrabold text-emerald-400 mt-2">Rule 49</div>
      <div class="text-slate-500 text-xs mt-1">Micro-kernel elevation & typed ServiceKey[T]</div>
    </div>
    <div class="glass-card rounded-xl p-6">
      <div class="text-slate-400 text-xs font-bold uppercase tracking-wider">Regression Guard</div>
      <div class="text-3xl font-extrabold text-amber-400 mt-2">100% Pass</div>
      <div class="text-slate-500 text-xs mt-1">7/7 unit & contract tests baseline passing</div>
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
        <p class="text-xs text-slate-400">Callers must fork out-of-process subprocesses or dynamically import files; low-level seek math is exposed to callers; dual-transcript dereferencing is unimplemented.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        Session["harness session / reflect"]
        CliUser["User Shell"]
    end

    subgraph ScriptLayer["Standalone Script (.agents/skills/brain-artifact-miner/)"]
        Script["brain_artifact_miner.py<br/>(Argparse CLI + functions)"]
        SeekMath["build_offset_index()<br/>(returns raw tuple offsets)"]
    end

    subgraph Filesystem["Filesystem & IDE Brain"]
        BrainDir["C:.../brain/&lt;cid&gt;/"]
        Transcript["transcript.jsonl<br/>(is_truncated: true)"]
        TranscriptFull["transcript_full.jsonl"]
    end

    Agent -.->|"Subprocess fork or spec_from_file"| Script
    Session -.->|"No IoC ServiceKey"| Script
    CliUser -->|"python scripts/brain_artifact_miner.py"| Script
    Script --> BrainDir
    Script --> SeekMath
    SeekMath -.->|"Leaky (offset, len) dict"| Agent
    Agent -.->|"Must manually seek & decode"| Transcript
    Agent -.->|"Must manually find & dereference"| TranscriptFull
          </pre>
        </div>
      </div>

      <!-- After Topology -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
          <h3 class="font-bold text-emerald-400 text-base">After: Deep Micro-Kernel Seam (High Leverage & Locality)</h3>
        </div>
        <p class="text-xs text-slate-400">Slotted domain engine in kernel services, typed IoC ServiceKey, auto-dereferencing random seek step extraction, domain plugin in memory_and_epistemics, and headless Click CLI.</p>
        <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs overflow-x-auto">
          <pre class="mermaid">
flowchart TD
    subgraph Callers["Callers & Agent Loops"]
        Agent["ReAct Agent Step"]
        Session["harness session / reflect"]
        ClickCLI["harness brain-miner ..."]
        ThinScript["brain_artifact_miner.py CLI"]
    end

    subgraph IoC["Micro-Kernel IoC Container (Rule 49)"]
        SKey["BRAIN_ARTIFACT_MINER_KEY<br/>ServiceKey[BrainArtifactMinerService]"]
        Plugin["BrainArtifactMinerPlugin<br/>(plugins/memory_and_epistemics/)"]
    end

    subgraph ServiceEngine["src/harness/services/brain_artifact_miner.py"]
        Service["BrainArtifactMinerService<br/>(@runtime_checkable Protocol)"]
        StepEngine["get_step(path, idx)<br/>(Auto O(1) Seek & Dereference)"]
        ScratchEngine["scan_scratch_tools()<br/>(AST Classification)"]
        TriageEngine["triage_task_logs()<br/>(Stderr Drainage)"]
        BriefEngine["generate_html_brief()"]
    end

    subgraph Storage["Brain Workspace Filesystem"]
        BrainStore["brain/&lt;cid&gt;/"]
        Transcripts["Dual Transcripts<br/>(compact + full)"]
    end

    Agent -->|"context.require(KEY)"| SKey
    Session -->|"context.require(KEY)"| SKey
    ClickCLI --> Service
    ThinScript -->|"Thin delegation"| Service
    SKey --- Plugin
    Plugin --> Service
    Service --> StepEngine
    Service --> ScratchEngine
    Service --> TriageEngine
    Service --> BriefEngine
    StepEngine --> Transcripts
    ScratchEngine --> BrainStore
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
          <h3 class="text-xl font-bold text-white">Candidate 1: Elevate Standalone Script to Micro-Kernel IoC Service & Domain-Partitioned Plugin</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 49, Rule 1, Rule 2, Rule 45</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 5/5</div>
          <div class="text-slate-300 mt-1">Consolidates domain logic (AST scan, task triage, offset caching, brief generation) in `src/harness/services/brain_artifact_miner.py`, cleanly co-located with kernel protocols.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">High ratio of hidden complexity to public surface. ReAct agents and kernel services resolve mining capabilities via `context.require(BRAIN_ARTIFACT_MINER_KEY)` without subprocess forks.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Enables direct in-memory unit tests, mock injection via IoC context, and verified contract assertions without filesystem path monkeypatching.</div>
        </div>
      </div>

      <div class="text-sm text-slate-300 space-y-2">
        <p><strong class="text-slate-200">Problem:</strong> Currently, `scripts/brain_artifact_miner.py` is an isolated script in `.agents/skills/brain-artifact-miner/`. It has no `ServiceKey[T]`, no entry in `src/harness/services/`, and no plugin in `plugins/memory_and_epistemics/`. Callers attempting to use its capabilities must fork subprocesses or import via dynamic `spec_from_file_location`, directly violating Rule 49.</p>
        <p><strong class="text-slate-200">Deepened Solution:</strong> Author `src/harness/services/brain_artifact_miner.py` with slotted frozen dataclasses, `@runtime_checkable class BrainArtifactMinerService(Protocol)`, default engine implementation `StandardBrainArtifactMinerService`, and typed `BRAIN_ARTIFACT_MINER_KEY`. Register `BrainArtifactMinerPlugin` in `plugins/memory_and_epistemics/brain_artifact_miner/main.py`. Refactor the standalone script to delegate cleanly to the engine.</p>
      </div>
    </div>

    <!-- Candidate 2 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-emerald-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-strong">Recommendation: Strong</span>
          <h3 class="text-xl font-bold text-white">Candidate 2: High-Leverage Dual-Transcript Truncation Dereferencing & O(1) Step Access</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">SKILL.md Stage 2 & AGENTS.md Rule 22, Rule 48</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 5/5</div>
          <div class="text-slate-300 mt-1">Offset cache and dual-transcript pairing logic live together in the service instance, avoiding ad-hoc seek implementations scattered across callers.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 5/5</div>
          <div class="text-slate-300 mt-1">A single method `get_step(transcript_path, step_index, dereference_truncated=True)` hides binary seek, length decoding, JSON deserialization, and truncation recovery.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Easily asserted with synthetic paired JSONL fixtures containing truncated and untruncated steps to verify sub-millisecond retrieval.</div>
        </div>
      </div>

      <div class="text-sm text-slate-300 space-y-2">
        <p><strong class="text-slate-200">Problem:</strong> `build_offset_index` returns a raw `dict[int, tuple[int, int]]`. Callers must manually open the binary file, seek to the offset, read bytes, decode UTF-8, and parse JSON. Furthermore, Stage 2 in `SKILL.md` explicitly calls for dereferencing `is_truncated: true` steps against `transcript_full.jsonl`, but no code currently implements this dereferencing logic.</p>
        <p><strong class="text-slate-200">Deepened Solution:</strong> Implement internal offset index caching and provide `get_step(path, step_index, dereference_truncated=True)` and `stream_steps(path, dereference_truncated=True)`. When a step in `transcript.jsonl` has `is_truncated: True`, the engine automatically retrieves the corresponding step from `transcript_full.jsonl` and merges untruncated model thoughts and tool arguments.</p>
      </div>
    </div>

    <!-- Candidate 3 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-blue-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-worth">Recommendation: Worth exploring</span>
          <h3 class="text-xl font-bold text-white">Candidate 3: Headless Click CLI Command Seam Consolidation</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">AGENTS.md Rule 6, Rule 10</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 4/5</div>
          <div class="text-slate-300 mt-1">Co-located in `src/harness/commands/brain_miner.py` and registered in `src/harness/cli.py` alongside other harness commands.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Exposes headless JSON and formatted console outputs for scanning scratch tools, triaging task logs, seeking steps, and generating briefs.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Testable via Click `CliRunner` with deterministic JSON assertions.</div>
        </div>
      </div>

      <div class="text-sm text-slate-300 space-y-2">
        <p><strong class="text-slate-200">Problem:</strong> Users and automated test harnesses have to know the path `.agents/skills/brain-artifact-miner/scripts/brain_artifact_miner.py` and invoke Python directly. This breaks the unified headless Click CLI introspection standard established by Rule 10.</p>
        <p><strong class="text-slate-200">Deepened Solution:</strong> Create `src/harness/commands/brain_miner.py` with `brain_miner_group` and register it in `src/harness/cli.py` with alias `brain-miner`, `miner`, and `artifact-miner`. Maintain the standalone script as a thin wrapper for backward compatibility.</p>
      </div>
    </div>

    <!-- Candidate 4 -->
    <div class="glass-card rounded-2xl p-6 border-l-4 border-blue-500 space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-semibold badge-worth">Recommendation: Worth exploring</span>
          <h3 class="text-xl font-bold text-white">Candidate 4: Canonical Knowledge Vault Dual-File Scaffolding & isnad Claim Seam</h3>
        </div>
        <span class="font-mono text-xs text-slate-400">SKILL.md Stage 4 & AGENTS.md Rule 40, Rule 41</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Locality Score: 4/5</div>
          <div class="text-slate-300 mt-1">Knowledge item schema generation encapsulated in the service, guaranteeing strict Rule 40 and 41 compliance.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Leverage Score: 4/5</div>
          <div class="text-slate-300 mt-1">Automatically generates `metadata.json` + `summary.md` with verified isnad provenance claims from mining discoveries.</div>
        </div>
        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
          <div class="text-slate-400 font-bold uppercase">Testability Score: 5/5</div>
          <div class="text-slate-300 mt-1">Directly assertable against `test_brain_artifact_miner.py:test_knowledge_vault_canonical_item`.</div>
        </div>
      </div>

      <div class="text-sm text-slate-300 space-y-2">
        <p><strong class="text-slate-200">Problem:</strong> Stage 4 mandates cognitive bifurcation into Knowledge Vault dual-file items. Currently, creating these items is completely manual, risking schema divergence or missing isnad lineage.</p>
        <p><strong class="text-slate-200">Deepened Solution:</strong> Provide `export_knowledge_item(output_dir, ki_id, title, category, summary, claims)` within the service engine, enforcing the canonical dual-file format programmatically.</p>
      </div>
    </div>
  </section>

  <!-- Top Recommendation & Execution Strategy -->
  <section class="glass-card rounded-2xl p-8 border-l-4 border-indigo-500 space-y-4">
    <div class="flex items-center gap-3">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Actionable Strategy</span>
      <h2 class="text-2xl font-bold text-white tracking-tight">Top Recommendation: Unified Seam Elevation (Candidates 1 + 2 + 3)</h2>
    </div>
    <div class="text-slate-300 text-sm leading-relaxed space-y-3">
      <p>
        The primary architectural bottleneck of <code>brain-artifact-miner</code> is that its high-value intelligence (AST classification, task log stderr drainage, and binary offset math) is trapped inside an un-elevated skill script. By elevating this engine into the micro-kernel IoC service tier:
      </p>
      <ol class="list-decimal list-inside space-y-2 text-slate-300">
        <li><strong class="text-white">Implement Kernel Service (Candidate 1 & 2):</strong> Create <code>src/harness/services/brain_artifact_miner.py</code> with slotted/frozen dataclasses, <code>BrainArtifactMinerService</code> Protocol, <code>StandardBrainArtifactMinerService</code>, <code>BRAIN_ARTIFACT_MINER_KEY</code>, and the high-leverage <code>get_step()</code> auto-dereferencing random seek seam.</li>
        <li><strong class="text-white">Register IoC Plugin:</strong> Create <code>plugins/memory_and_epistemics/brain_artifact_miner/main.py</code> exporting module singleton <code>plugin = BrainArtifactMinerPlugin()</code> and <code>plugin.json</code>.</li>
        <li><strong class="text-white">Expose Headless Click CLI (Candidate 3):</strong> Add <code>src/harness/commands/brain_miner.py</code> with <code>scan</code>, <code>triage</code>, <code>step</code>, and <code>brief</code> subcommands, registering them cleanly in <code>src/harness/cli.py</code>.</li>
        <li><strong class="text-white">Thin Wrapper Delegation & Zero Regression:</strong> Refactor <code>.agents/skills/brain-artifact-miner/scripts/brain_artifact_miner.py</code> to import from <code>harness.services.brain_artifact_miner</code> while preserving all existing function signatures and immutability assertions in <code>tests/test_brain_artifact_miner.py</code>.</li>
      </ol>
      <div class="bg-indigo-950/40 p-4 rounded-xl border border-indigo-800/40 mt-4">
        <p class="text-xs text-indigo-300 font-mono">
          <strong>Next Stage:</strong> Stage 4 (Plan) — An implementation plan artifact <code>implementation_plan.md</code> has been formulated with <code>RequestFeedback: true</code> awaiting human confirmation before executing any code modifications.
        </p>
      </div>
    </div>
  </section>

</body>
</html>
"""

output_path.write_text(html_content, encoding="utf-8")
print(f"Architecture review HTML brief successfully generated at: {output_path}")
