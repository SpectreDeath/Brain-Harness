"""HTML visual review brief generator and interactive provider studio."""

from __future__ import annotations

import json
import os
import tempfile
import time

from harness.services.compute.providers import ProviderReasoningAdapter
from harness.services.compute.types import (
    AssessmentTrace,
    ComplexityVector,
    ComputeAssessment,
    ComputeEconomicsEstimator,
)


class ComputeVisualBriefGenerator:
    """Generates self-contained interactive dark-mode HTML briefs in %TEMP%."""

    @classmethod
    def render_to_temp(cls, assessment: ComputeAssessment, task_title: str = "Compute Assessment") -> str:
        """Render assessment to an HTML file in temp directory and return its path."""
        ts = int(time.time())
        temp_dir = tempfile.gettempdir()
        filename = f"compute-assessor-{ts}.html"
        filepath = os.path.join(temp_dir, filename)

        vector = assessment.vector or ComplexityVector(level=assessment.complexity)
        trace = assessment.trace or AssessmentTrace()
        econ = assessment.economics or ComputeEconomicsEstimator.estimate(
            assessment.recommended_model,
            assessment.thinking_level,
            assessment.budget_tokens,
        )

        alt_models_html = "".join(
            f'<span class="bg-[#21262d] text-gray-300 px-2 py-1 rounded text-xs border border-[#30363d]">{m}</span>'
            for m in assessment.alternative_models
        )

        high_factors_html = "".join(
            f'<li class="text-red-300 text-xs">• {f}</li>'
            for f in trace.high_factors
        ) or '<li class="text-gray-500 text-xs italic">No high complexity blockers detected</li>'

        low_factors_html = "".join(
            f'<li class="text-green-300 text-xs">• {f}</li>'
            for f in trace.low_factors
        ) or '<li class="text-gray-500 text-xs italic">Standard agentic baseline</li>'

        # Generate sample payloads for the interactive studio
        gemini_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("gemini-3.7-flash", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        claude_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("claude-3-7-sonnet", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        openai_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("o3-mini", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        deepseek_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("deepseek-r1", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        ollama_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("ollama/qwen2.5-coder:32b", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )

        badge_bg = (
            "bg-green-900/80 text-green-300 border-green-700"
            if assessment.complexity == "Low"
            else "bg-blue-900/80 text-blue-300 border-blue-700"
            if assessment.complexity == "Medium"
            else "bg-purple-900/80 text-purple-300 border-purple-700"
        )

        html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compute & Model Assessor Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#0d1117',
        primaryColor: '#1f6feb',
        primaryTextColor: '#c9d1d9',
        primaryBorderColor: '#30363d',
        lineColor: '#58a6ff'
      }}
    }});

    const providerPayloads = {{
      gemini: {json.dumps(gemini_payload)},
      claude: {json.dumps(claude_payload)},
      openai: {json.dumps(openai_payload)},
      deepseek: {json.dumps(deepseek_payload)},
      ollama: {json.dumps(ollama_payload)}
    }};

    function selectTab(provider) {{
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.remove('border-blue-500', 'text-blue-400', 'bg-[#21262d]');
        b.classList.add('text-gray-400');
      }});
      const activeBtn = document.getElementById('tab-' + provider);
      if (activeBtn) {{
        activeBtn.classList.add('border-blue-500', 'text-blue-400', 'bg-[#21262d]');
        activeBtn.classList.remove('text-gray-400');
      }}
      const codeBlock = document.getElementById('payload-code');
      if (codeBlock && providerPayloads[provider]) {{
        codeBlock.textContent = providerPayloads[provider];
      }}
    }}

    function copyPayload() {{
      const codeBlock = document.getElementById('payload-code');
      if (codeBlock) {{
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {{
          const toast = document.getElementById('copy-toast');
          if (toast) {{
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 2000);
          }}
        }});
      }}
    }}
  </script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] font-sans antialiased min-h-screen p-6 md:p-10">
  <div class="max-w-5xl mx-auto space-y-6">
    
    <header class="border-b border-[#30363d] pb-4 flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-mono bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded border border-blue-700/50">
            COMPUTE ROUTER
          </span>
          <span class="text-xs text-gray-400 font-mono">Stage 3 Visual Brief • Reactive IoC</span>
        </div>
        <h1 class="text-2xl font-bold text-white mt-1">{task_title}</h1>
        <p class="text-xs text-gray-400">Calibrated for Gemini 3.7 Flash, Claude 3.7 Sonnet, OpenAI o-series</p>
      </div>
      <div class="text-right">
        <span class="{badge_bg} text-xs px-3 py-1.5 rounded-full font-mono font-bold border">
          TIER: {assessment.complexity.upper()} ({assessment.model_tier.value})
        </span>
      </div>
    </header>

    <!-- Recommendation Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Primary Recommended Model</div>
        <div class="text-lg font-bold text-white mt-1 text-blue-400 font-mono">{assessment.recommended_model}</div>
        <div class="text-xs text-gray-400 mt-2">Thinking Budget: <span class="text-white font-mono font-semibold">{assessment.thinking_level.value.upper()} (~{assessment.budget_tokens:,} tokens)</span></div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Composite Score &amp; Profile</div>
        <div class="text-2xl font-extrabold text-white mt-1 text-purple-400 font-mono">{vector.composite_score:.2f} / 1.00</div>
        <div class="text-xs text-gray-400 mt-2">Profile: <span class="text-purple-300 font-mono">{trace.profile_used}</span> • Files: {trace.files_evaluated}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Token Economics &amp; Latency</div>
        <div class="text-lg font-bold text-white mt-1 text-green-400 font-mono">~${econ.estimated_query_cost_usd:.4f}</div>
        <div class="text-xs text-gray-400 mt-2">p50: <span class="text-gray-200">{econ.expected_latency_p50_seconds:.1f}s</span> • p95: <span class="text-gray-200">{econ.expected_latency_p95_seconds:.1f}s</span></div>
      </div>
    </div>

    <!-- Complexity Vector & Decision DAG -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Vector Breakdown -->
      <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl space-y-4">
        <h3 class="text-sm font-bold text-white">5-Dimensional Complexity Vector</h3>
        <div class="space-y-2.5 font-mono text-xs">
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Solution Ambiguity</span>
              <span class="font-bold text-blue-400">{vector.ambiguity_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.ambiguity_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Context &amp; DAG Span</span>
              <span class="font-bold text-blue-400">{vector.span_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.span_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Algorithmic Depth</span>
              <span class="font-bold text-blue-400">{vector.depth_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.depth_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Execution Rigor</span>
              <span class="font-bold text-blue-400">{vector.rigor_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.rigor_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Concurrency / Race Potential</span>
              <span class="font-bold text-blue-400">{vector.concurrency_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.concurrency_score * 100)}%"></div>
            </div>
          </div>
        </div>

        <div class="border-t border-[#30363d] pt-3">
          <div class="text-xs text-gray-400 font-semibold mb-1">Rationale:</div>
          <div class="text-xs text-gray-300 italic">{assessment.reasoning}</div>
        </div>
      </div>

      <!-- Decision DAG -->
      <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl">
        <h3 class="text-sm font-bold text-white mb-2">Routing Decision DAG</h3>
        <div class="mermaid">
graph TD
  Prompt["Task Prompt & Context"] --> Eval["DimensionalScorer (Composite: {vector.composite_score:.2f})"]
  Eval --> Decision{{"Tier: {assessment.complexity}"}}
  Decision -->|High| HighT["Gemini 3.7 Flash (Thinking: HIGH)<br/>Claude 3.7 Sonnet (>16k tok)"]
  Decision -->|Medium| MedT["Gemini 3.7 Flash (Thinking: MED)<br/>Claude 3.5 Sonnet / GPT-4o"]
  Decision -->|Low| LowT["Gemini 2.0 Flash (Thinking: OFF)<br/>GPT-4o-mini / Haiku"]
  
  style HighT fill:#28183d,stroke:#a371f7,stroke-width:1px,color:#fff
  style MedT fill:#092540,stroke:#58a6ff,stroke-width:1px,color:#fff
  style LowT fill:#0d3a1e,stroke:#238636,stroke-width:1px,color:#fff
        </div>
      </div>

    </div>

    <!-- Live Provider Payload Studio -->
    <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-bold text-white">Live Provider Payload Studio</h3>
          <span class="text-xs font-mono bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded border border-purple-700/50">
            Multi-Provider Ready
          </span>
        </div>
        <button onclick="copyPayload()" class="text-xs bg-[#21262d] hover:bg-[#30363d] text-gray-200 px-2.5 py-1 rounded border border-[#30363d] flex items-center gap-1 transition">
          <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
          Copy JSON
        </button>
      </div>

      <!-- Tab Buttons -->
      <div class="flex border-b border-[#30363d] gap-2 text-xs font-mono">
        <button id="tab-gemini" onclick="selectTab('gemini')" class="tab-btn px-3 py-1.5 border-b-2 border-blue-500 text-blue-400 font-bold bg-[#21262d] rounded-t">Google Gemini</button>
        <button id="tab-claude" onclick="selectTab('claude')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">Anthropic Claude</button>
        <button id="tab-openai" onclick="selectTab('openai')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">OpenAI o-Series</button>
        <button id="tab-deepseek" onclick="selectTab('deepseek')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">DeepSeek</button>
        <button id="tab-ollama" onclick="selectTab('ollama')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">Ollama / Local</button>
      </div>

      <!-- Code Box -->
      <div class="relative">
        <pre class="bg-[#0d1117] p-4 rounded-lg border border-[#30363d] text-xs font-mono text-gray-300 overflow-x-auto"><code id="payload-code">{gemini_payload}</code></pre>
        <div id="copy-toast" class="hidden absolute top-2 right-2 bg-green-900/90 text-green-300 border border-green-700 px-2 py-1 rounded text-xs font-mono">
          ✓ Copied to clipboard!
        </div>
      </div>
    </div>

    <!-- Factor Breakdown -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <h4 class="text-xs font-bold text-red-400 uppercase mb-2">High Complexity Indicators</h4>
        <ul class="space-y-1">
          {high_factors_html}
        </ul>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <h4 class="text-xs font-bold text-green-400 uppercase mb-2">Low Complexity Indicators</h4>
        <ul class="space-y-1">
          {low_factors_html}
        </ul>
      </div>
    </div>

    <footer class="border-t border-[#30363d] pt-4 text-xs text-gray-500 flex justify-between items-center font-mono">
      <div>Compute &amp; Model Assessor Engine • Brain Harness</div>
      <div>Generated at timestamp: {ts}</div>
    </footer>

  </div>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath
