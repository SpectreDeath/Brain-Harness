import os
import tempfile
import time

temp_dir = tempfile.gettempdir()
report_path = os.path.join(temp_dir, "architecture-review-1787098294.html")

html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Review: Plugin Creator Subsystem — Brain Harness</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0f9ff',
              100: '#e0f2fe',
              400: '#38bdf8',
              500: '#0ea5e9',
              600: '#0284c7',
              900: '#0c4a6e',
            }
          }
        }
      }
    };
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
  </script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased p-8">
  <div class="max-w-6xl mx-auto space-y-8">
    
    <!-- Header -->
    <header class="border-b border-slate-800 pb-6 flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 text-xs font-semibold rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            Architecture Deepening Loop
          </span>
          <span class="text-xs text-slate-400">Brain Harness • Stage 3: Recommend</span>
        </div>
        <h1 class="text-3xl font-bold mt-2 text-white tracking-tight">Plugin Creator Seam Refactor & Deepening</h1>
        <p class="text-slate-400 mt-1">Deep-module analysis and architectural elevation of <code class="text-cyan-300">src/harness/creator/</code></p>
      </div>
      <div class="text-right text-xs text-slate-500">
        <div>Generated: August 2026</div>
        <div class="font-mono text-slate-400">v1.2.0-deepen</div>
      </div>
    </header>

    <!-- Executive Summary -->
    <section class="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <h2 class="text-xl font-semibold text-cyan-400 flex items-center gap-2">
        <span>Executive Summary & Friction Audit</span>
      </h2>
      <p class="text-slate-300 leading-relaxed">
        The <strong>Plugin Creator</strong> subsystem enables rapid, multi-language scaffolding, in-memory dynamic plugin synthesis, and static/runtime validation.
        However, an audit reveals four key architectural friction points where shallow wrappers and inflexible seams create cognitive overhead:
      </p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div class="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div class="text-amber-400 font-semibold text-sm mb-1">1. Shallow Trampoline in DynamicPluginBuilder</div>
          <p class="text-xs text-slate-400">
            <code class="text-slate-300">DynamicPluginBuilder</code> acts as a loose namespace of static methods that blindly delegate to scaffolders and validators without holding cohesive workspace state or providing bi-directional project export.
          </p>
        </div>
        <div class="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div class="text-amber-400 font-semibold text-sm mb-1">2. Rigid Scaffold Engine & Silent Archetype Seam</div>
          <p class="text-xs text-slate-400">
            <code class="text-slate-300">PluginScaffoldEngine.scaffold()</code> returns a raw <code class="text-slate-300">Path</code> without a rich <code class="text-slate-300">ScaffoldResult</code>. Archetypes cannot emit auxiliary files (Dockerfiles, READMEs, MCP configs) or execute automated post-generation checks.
          </p>
        </div>
        <div class="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div class="text-amber-400 font-semibold text-sm mb-1">3. Halting Validation Pipeline without Auto-Fix Seam</div>
          <p class="text-xs text-slate-400">
            <code class="text-slate-300">ValidationPipeline</code> aborts on the first rule failure, hiding independent diagnostics. It lacks severity grading (<code class="text-slate-300">INFO/WARN/ERROR/CRITICAL</code>) and automated remediation (<code class="text-slate-300">ValidationFixer</code>).
          </p>
        </div>
        <div class="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div class="text-amber-400 font-semibold text-sm mb-1">4. Disconnected Dynamic Synthesis & Project Export</div>
          <p class="text-xs text-slate-400">
            In-memory plugins (<code class="text-slate-300">DynamicPythonPlugin</code>) generated from callables or code strings cannot inspect full AST parameter schemas, hot-reload, or export themselves to disk as scaffolded packages.
          </p>
        </div>
      </div>
    </section>

    <!-- Topology Diagrams -->
    <section class="space-y-6">
      <h2 class="text-xl font-semibold text-slate-200">Architecture Topology Comparison</h2>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Before -->
        <div class="bg-slate-900 border border-red-500/20 rounded-xl p-5 shadow-lg">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-red-400 text-sm flex items-center gap-2">
              <span>Current (Shallow Delegation & Fragmented Seams)</span>
            </h3>
            <span class="px-2 py-0.5 text-xs bg-red-950 text-red-400 border border-red-800 rounded">Legacy</span>
          </div>
          <div class="mermaid">
graph TD
  CLI[CLI / UI Server] -->|scaffold_project| DPB[DynamicPluginBuilder<br/>(Static Trampoline)]
  CLI -->|validate| PV[PluginValidator]
  DPB -->|instantiates| PSE[PluginScaffoldEngine]
  DPB -->|calls| PIP[PluginIngestionPipeline]
  PSE -->|hardcoded steps| FS[(Filesystem Files)]
  PSE -->|only 4 fixed files| AR[ArchetypeRegistry]
  PV -->|stops on 1st error| VP[ValidationPipeline]
  DPB -.->|no export link| DPP[DynamicPythonPlugin<br/>(In-Memory Only)]
          </div>
        </div>

        <!-- After -->
        <div class="bg-slate-900 border border-emerald-500/30 rounded-xl p-5 shadow-lg">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-emerald-400 text-sm flex items-center gap-2">
              <span>Target (Deepened Seam, Rich Artifacts & Studio Engine)</span>
            </h3>
            <span class="px-2 py-0.5 text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 rounded">Deep Module</span>
          </div>
          <div class="mermaid">
graph TD
  CLI[CLI / UI / Agents] -->|Authoritative Seam| CS[CreatorStudio & Workspace]
  CS --> PSE[Deep PluginScaffoldEngine]
  CS --> DPP[DynamicPythonPlugin + AST Extractor]
  CS --> PV[Multi-Diagnostic PluginValidator]
  
  PSE -->|Emits| SR[ScaffoldResult (Manifest, Files, Hashes, Report)]
  PSE -->|Extensible Generator| AR[ArchetypeRegistry (Auxiliary Files, Templates)]
  PV -->|Comprehensive Check| VP[Non-Halting ValidationPipeline + Severities]
  PV -->|Auto-Remediation| VF[ValidationFixer / Remediation Engine]
  DPP -->|Bidirectional Export| PSE
          </div>
        </div>
      </div>
    </section>

    <!-- Candidate Recommendations -->
    <section class="space-y-4">
      <h2 class="text-xl font-semibold text-slate-200">Deepening Candidate Assessments</h2>
      
      <div class="grid grid-cols-1 gap-4">
        <!-- Candidate 1 -->
        <div class="bg-slate-900 border border-slate-800 hover:border-slate-700 transition rounded-xl p-6">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Strong
              </span>
              <h3 class="text-lg font-semibold text-white">1. Deepen PluginScaffoldEngine with ScaffoldResult & Extensible Auxiliary Files</h3>
            </div>
            <div class="text-xs text-slate-400 font-mono">scaffold.py • archetypes.py</div>
          </div>
          <p class="text-sm text-slate-300 mb-3">
            Transform <code class="text-cyan-300">PluginScaffoldEngine</code> into an authoritative, multi-artifact builder returning a structured <code class="text-cyan-300">ScaffoldResult</code>. Extend <code class="text-cyan-300">PluginArchetype</code> with <code class="text-cyan-300">generate_extra_files(options)</code> and template customization hooks, enabling archetypes to generate Dockerfiles, READMEs, and MCP configuration schemas cleanly.
          </p>
          <div class="grid grid-cols-3 gap-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div><strong class="text-slate-400">Locality:</strong> Co-locates manifest, template file map, and generation telemetry.</div>
            <div><strong class="text-slate-400">Leverage:</strong> 1 call generates complete project + validates + returns full file inventory.</div>
            <div><strong class="text-slate-400">Testability:</strong> Zero IO-dependent mocking; pure filesystem verification.</div>
          </div>
        </div>

        <!-- Candidate 2 -->
        <div class="bg-slate-900 border border-slate-800 hover:border-slate-700 transition rounded-xl p-6">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Strong
              </span>
              <h3 class="text-lg font-semibold text-white">2. Multi-Diagnostic Validation Pipeline & Auto-Remediation Fixer</h3>
            </div>
            <div class="text-xs text-slate-400 font-mono">validator.py</div>
          </div>
          <p class="text-sm text-slate-300 mb-3">
            Upgrade <code class="text-cyan-300">PluginValidator</code> to run all non-dependent checks without halting prematurely on the first failure. Introduce <code class="text-cyan-300">RuleSeverity</code> (<code class="text-cyan-300">INFO, WARNING, ERROR, CRITICAL</code>), enhanced AST signature parameter validation, and an automated <code class="text-cyan-300">ValidationFixer</code> engine that can auto-repair missing entrypoint declarations and boilerplate.
          </p>
          <div class="grid grid-cols-3 gap-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div><strong class="text-slate-400">Locality:</strong> Diagnostic checking and repair logic live in the validation pipeline.</div>
            <div><strong class="text-slate-400">Leverage:</strong> Diagnoses complete list of issues and offers 1-click auto-repair.</div>
            <div><strong class="text-slate-400">Testability:</strong> Tested across invalid permutations and automated repair cycles.</div>
          </div>
        </div>

        <!-- Candidate 3 -->
        <div class="bg-slate-900 border border-slate-800 hover:border-slate-700 transition rounded-xl p-6">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Strong
              </span>
              <h3 class="text-lg font-semibold text-white">3. Deepen Dynamic Plugins with CreatorWorkspace, AST Schema Extraction & Project Export</h3>
            </div>
            <div class="text-xs text-slate-400 font-mono">dynamic.py • workspace.py</div>
          </div>
          <p class="text-sm text-slate-300 mb-3">
            Elevate <code class="text-cyan-300">DynamicPluginBuilder</code> and <code class="text-cyan-300">DynamicPythonPlugin</code> to extract full AST parameter schemas, support hot-reloading callables, and support direct bi-directional export to on-disk scaffolded projects (<code class="text-cyan-300">plugin.export_project(path)</code>).
          </p>
          <div class="grid grid-cols-3 gap-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div><strong class="text-slate-400">Locality:</strong> In-memory plugin lifecycle, AST schema generation, and disk export co-located.</div>
            <div><strong class="text-slate-400">Leverage:</strong> Allows live prototyping of tools with instant conversion into production plugins.</div>
            <div><strong class="text-slate-400">Testability:</strong> Fully unit testable without subprocess overhead.</div>
          </div>
        </div>

        <!-- Candidate 4 -->
        <div class="bg-slate-900 border border-slate-800 hover:border-slate-700 transition rounded-xl p-6">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="px-2.5 py-1 text-xs font-bold rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Worth exploring
              </span>
              <h3 class="text-lg font-semibold text-white">4. New Built-in Archetypes: AgenticWorkflow & Containerized</h3>
            </div>
            <div class="text-xs text-slate-400 font-mono">archetypes.py</div>
          </div>
          <p class="text-sm text-slate-300 mb-3">
            Add <code class="text-cyan-300">AgenticWorkflowArchetype</code> (generating supervisor/debater agent loops with session hooks) and <code class="text-cyan-300">ContainerArchetype</code> (generating Dockerfile, compose definitions, and container sandboxing configs).
          </p>
          <div class="grid grid-cols-3 gap-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div><strong class="text-slate-400">Locality:</strong> Archetype strategy pattern cleanly encapsulates preset templates.</div>
            <div><strong class="text-slate-400">Leverage:</strong> Expands scaffolding to complex multi-agent and containerized plugins.</div>
            <div><strong class="text-slate-400">Testability:</strong> Direct archetype output verification.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Top Recommendation -->
    <section class="bg-gradient-to-br from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-500/30 rounded-xl p-6 shadow-2xl">
      <div class="flex items-center gap-3 mb-3">
        <span class="px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full bg-cyan-500 text-slate-950">
          Top Recommendation
        </span>
        <h2 class="text-xl font-bold text-white">Holistic Creator Seam Deepening Loop</h2>
      </div>
      <p class="text-slate-300 leading-relaxed mb-4">
        Execute a unified deepening across <code class="text-cyan-300">src/harness/creator/</code> in three synchronized layers:
      </p>
      <ol class="list-decimal list-inside space-y-2 text-sm text-slate-300">
        <li><strong>Scaffolding Seam:</strong> Implement <code class="text-cyan-200">ScaffoldResult</code>, extensible auxiliary file generation in <code class="text-cyan-200">PluginArchetype</code>, and template overlay support in <code class="text-cyan-200">PluginScaffoldEngine</code>.</li>
        <li><strong>Validation & Remediation Seam:</strong> Implement <code class="text-cyan-200">RuleSeverity</code>, comprehensive non-halting pipeline execution, AST signature matching, and <code class="text-cyan-200">ValidationFixer</code> auto-remediation.</li>
        <li><strong>Dynamic & Workspace Seam:</strong> Deepen <code class="text-cyan-200">DynamicPythonPlugin</code> with AST schema inference, <code class="text-cyan-200">export_project()</code>, and add rich new archetypes (<code class="text-cyan-200">AgenticWorkflowArchetype</code> and <code class="text-cyan-200">ContainerArchetype</code>).</li>
      </ol>
      <div class="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div>Preserves 100% backward compatibility for all CLI, UI, and test consumers.</div>
        <div class="text-cyan-400 font-semibold">Ready for Implementation Plan</div>
      </div>
    </section>

  </div>
</body>
</html>
"""

with open(report_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Report written to: {report_path}")
