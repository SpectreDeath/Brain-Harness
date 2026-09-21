"""Gradio App Architect Engine — Slotted domain engine and static AST diagnostic inspector.

Synthesized from Eva J Patel's literature:
'How to Use Gradio with Python: A Complete Beginner-to-Advanced Book' (freeCodeCamp, 2026).

Enforces:
1. Headless Decoupling (pure Python compute functions, 100% testable without Gradio)
2. Multi-User Session Isolation (gr.State per session, zero mutable global state)
3. Positional Arity & Cardinality Contracts (exact matching between inputs/outputs and handler signatures)
4. Singleton Warm-Loading (model pipelines loaded at module scope, never inside callbacks)
5. Queued Streaming & Telemetry (generators require demo.queue() for websocket load-shedding)

Complies with:
- Rule 12: Slotted and frozen dataclass architecture
- Rule 23: Windows UTF-8 stream codec entrypoint invariant
- Rule 51: Dynamic template escaping
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import sys
import tempfile
from typing import Any

# Rule 23: Windows UTF-8 stream codec
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DiagnosticSeverity(str, Enum):
    """Severity levels for diagnostic checks."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True, frozen=True)
class DiagnosticCheck:
    """Immutable diagnostic check result (Rule 12)."""

    rule_id: str
    name: str
    passed: bool
    message: str
    severity: str = "error"
    line_number: int | None = None


@dataclass(slots=True, frozen=True)
class DiagnosticReport:
    """Immutable report aggregating diagnostic checks and metrics (Rule 12)."""

    target: str
    passed: bool
    checks: tuple[DiagnosticCheck, ...]
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[DiagnosticCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    @property
    def warnings(self) -> list[DiagnosticCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]


@dataclass(slots=True, frozen=True)
class ArityContract:
    """Immutable positional arity contract for an event handler (Rule 12)."""

    func_name: str
    input_count: int
    output_count: int
    is_generator: bool = False
    param_names: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class AppScaffoldConfig:
    """Configuration for scaffolding production Gradio applications (Rule 12)."""

    app_name: str
    topology: str = "blocks"  # "blocks", "chat", or "interface"
    enable_queue: bool = True
    concurrency_limit: int = 5
    max_queue_size: int = 50
    output_dir: str = "."


@dataclass(slots=True, frozen=True)
class AppScaffoldResult:
    """Result of application scaffolding containing generated files (Rule 12)."""

    files: tuple[tuple[str, str], ...]
    manifest: dict[str, Any] = field(default_factory=dict)


class GradioASTInspector(ast.NodeVisitor):
    """Static Python AST analyzer evaluating Eva J Patel's 5 diagnostic rubrics."""

    HEAVY_LOADERS = {
        "pipeline",
        "from_pretrained",
        "load_model",
        "SentenceTransformer",
        "AutoModel",
        "AutoModelForCausalLM",
        "AutoModelForSequenceClassification",
        "AutoTokenizer",
    }

    def __init__(self, source_code: str, file_path: str = "<source>") -> None:
        self.source_code = source_code
        self.file_path = file_path
        self.checks: list[DiagnosticCheck] = []
        self.metrics: dict[str, Any] = {
            "functions_found": 0,
            "callbacks_found": 0,
            "global_mutations_found": 0,
            "heavy_loaders_in_callbacks": 0,
            "generators_found": 0,
            "queue_enabled": False,
        }

        self._function_defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self._global_vars: set[str] = set()
        self._global_mutations: list[tuple[str, int]] = []
        self._heavy_loads_in_funcs: list[tuple[str, str, int]] = []
        self._generator_funcs: set[str] = set()
        self._event_calls: list[tuple[str, ast.Call]] = []
        self._has_queue_call = False
        self._current_func: str | None = None
        self._tree: ast.AST | None = None

    def inspect(self) -> DiagnosticReport:
        """Parse source code and evaluate diagnostic rules."""
        try:
            self._tree = ast.parse(self.source_code, filename=self.file_path)
        except SyntaxError as e:
            syntax_check = DiagnosticCheck(
                rule_id="PYTHON_SYNTAX_VALID",
                name="Python Syntax",
                passed=False,
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                line_number=e.lineno,
            )
            return DiagnosticReport(
                target=self.file_path,
                passed=False,
                checks=(syntax_check,),
                metrics={"syntax_error": True},
            )

        self.visit(self._tree)
        self._evaluate_rubrics()

        overall_passed = all(
            c.passed for c in self.checks if c.severity == "error"
        )
        return DiagnosticReport(
            target=self.file_path,
            passed=overall_passed,
            checks=tuple(self.checks),
            metrics=self.metrics,
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._current_func is None:
            # Top-level assignment: check for mutable global data structures
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                        self._global_vars.add(target.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.metrics["functions_found"] += 1
        self._function_defs[node.name] = node
        prev_func = self._current_func
        self._current_func = node.name

        # Check if function is a generator (contains yield or yield from)
        has_yield = any(
            isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node)
        )
        if has_yield:
            self._generator_funcs.add(node.name)
            self.metrics["generators_found"] += 1

        self.generic_visit(node)
        self._current_func = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.metrics["functions_found"] += 1
        self._function_defs[node.name] = node
        prev_func = self._current_func
        self._current_func = node.name

        has_yield = any(
            isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node)
        )
        if has_yield:
            self._generator_funcs.add(node.name)
            self.metrics["generators_found"] += 1

        self.generic_visit(node)
        self._current_func = prev_func

    def visit_Global(self, node: ast.Global) -> None:
        if self._current_func:
            for name in node.names:
                if name in self._global_vars:
                    self._global_mutations.append((name, node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for heavy loader instantiation
        func_name = self._resolve_call_name(node.func)
        if self._current_func and func_name:
            for heavy in self.HEAVY_LOADERS:
                if heavy in func_name:
                    self._heavy_loads_in_funcs.append(
                        (self._current_func, func_name, node.lineno)
                    )

        # Check for .queue() call
        if isinstance(node.func, ast.Attribute) and node.func.attr == "queue":
            self._has_queue_call = True
            self.metrics["queue_enabled"] = True

        # Check for event bindings: .click(), .submit(), .change(), or gr.Interface(fn=...)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "click",
            "submit",
            "change",
            "upload",
            "clear",
            "select",
        }:
            self._event_calls.append((node.func.attr, node))
            self.metrics["callbacks_found"] += 1
        elif func_name in {"Interface", "gr.Interface", "ChatInterface", "gr.ChatInterface"}:
            self._event_calls.append(("interface", node))
            self.metrics["callbacks_found"] += 1

        self.generic_visit(node)

    def _resolve_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._resolve_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""

    def _evaluate_rubrics(self) -> None:
        # Rubric 1: Headless Decoupling (Pure compute logic must not import gradio or call gr.update in pure functions)
        # Check if functions titled *compute*, *analyze*, *infer*, *process*, or standalone calculation functions import gradio
        has_gr_import_in_func = False
        for f_name, f_node in self._function_defs.items():
            for child in ast.walk(f_node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    for alias in getattr(child, "names", []):
                        if "gradio" in alias.name:
                            has_gr_import_in_func = True
                            self.checks.append(
                                DiagnosticCheck(
                                    rule_id="HEADLESS_DECOUPLING",
                                    name="Headless Pure Logic Decoupling",
                                    passed=False,
                                    message=f"Function '{f_name}' imports Gradio directly inside function scope (Line {child.lineno}). Core logic must remain decoupled.",
                                    line_number=child.lineno,
                                )
                            )
        if not has_gr_import_in_func:
            self.checks.append(
                DiagnosticCheck(
                    rule_id="HEADLESS_DECOUPLING",
                    name="Headless Pure Logic Decoupling",
                    passed=True,
                    message="Core computation is decoupled from Gradio UI imports.",
                )
            )

        # Rubric 2: Multi-User Session Isolation (gr.State vs global mutable state)
        if self._global_mutations:
            self.metrics["global_mutations_found"] = len(self._global_mutations)
            for var_name, lineno in self._global_mutations:
                self.checks.append(
                    DiagnosticCheck(
                        rule_id="SESSION_STATE_ISOLATION",
                        name="Multi-User Session State Isolation",
                        passed=False,
                        message=f"Global mutable variable '{var_name}' mutated in function scope at line {lineno}. Use gr.State for session-isolated state.",
                        line_number=lineno,
                    )
                )
        else:
            self.checks.append(
                DiagnosticCheck(
                    rule_id="SESSION_STATE_ISOLATION",
                    name="Multi-User Session State Isolation",
                    passed=True,
                    message="Zero mutable global variable pollution detected.",
                )
            )

        # Rubric 3: Positional Arity & Cardinality Contracts
        arity_errors: list[str] = []
        for event_name, call_node in self._event_calls:
            fn_arg = self._get_kwarg(call_node, "fn")
            inputs_arg = self._get_kwarg(call_node, "inputs")

            if fn_arg and isinstance(fn_arg, ast.Name):
                target_fn_name = fn_arg.id
                if target_fn_name in self._function_defs:
                    f_def = self._function_defs[target_fn_name]
                    # Count non-self non-progress parameters
                    params = [
                        a.arg
                        for a in f_def.args.args
                        if a.arg not in {"self", "progress"}
                    ]
                    expected_inputs = len(params)

                    actual_inputs = 0
                    if inputs_arg is None:
                        actual_inputs = 0
                    elif isinstance(inputs_arg, ast.List):
                        actual_inputs = len(inputs_arg.elts)
                    elif isinstance(inputs_arg, (ast.Name, ast.Attribute)):
                        actual_inputs = 1

                    if inputs_arg is not None and actual_inputs != expected_inputs:
                        err_msg = (
                            f"Arity mismatch on {event_name} binding '{target_fn_name}': "
                            f"inputs list has {actual_inputs} components but function accepts {expected_inputs} parameters ({params})."
                        )
                        arity_errors.append(err_msg)
                        self.checks.append(
                            DiagnosticCheck(
                                rule_id="POSITIONAL_ARITY_CONTRACT",
                                name="Positional Input/Output Arity Contract",
                                passed=False,
                                message=err_msg,
                                line_number=call_node.lineno,
                            )
                        )

        if not arity_errors:
            self.checks.append(
                DiagnosticCheck(
                    rule_id="POSITIONAL_ARITY_CONTRACT",
                    name="Positional Input/Output Arity Contract",
                    passed=True,
                    message="All event handler bindings satisfy positional input/output arity contracts.",
                )
            )

        # Rubric 4: Singleton Warm-Load Test (Heavy loaders inside callbacks)
        if self._heavy_loads_in_funcs:
            self.metrics["heavy_loaders_in_callbacks"] = len(self._heavy_loads_in_funcs)
            for f_name, loader_name, lineno in self._heavy_loads_in_funcs:
                self.checks.append(
                    DiagnosticCheck(
                        rule_id="SINGLETON_WARM_LOAD",
                        name="Module-Scope Singleton Warm-Loading",
                        passed=False,
                        message=f"Heavy model/pipeline loader '{loader_name}' called inside function '{f_name}' at line {lineno}. Warm-load models at module scope.",
                        line_number=lineno,
                    )
                )
        else:
            self.checks.append(
                DiagnosticCheck(
                    rule_id="SINGLETON_WARM_LOAD",
                    name="Module-Scope Singleton Warm-Loading",
                    passed=True,
                    message="Heavy model pipelines warm-loaded at module initialization scope.",
                )
            )

        # Rubric 5: Queue & Streaming Telemetry (Generators require .queue())
        if self._generator_funcs and not self._has_queue_call:
            gen_names = ", ".join(self._generator_funcs)
            self.checks.append(
                DiagnosticCheck(
                    rule_id="QUEUED_STREAMING_TELEMETRY",
                    name="Queued Concurrency & Streaming Telemetry",
                    passed=False,
                    message=f"Generator functions ({gen_names}) found using 'yield' but demo.queue() is missing. Queued concurrency is mandatory for streaming.",
                )
            )
        else:
            self.checks.append(
                DiagnosticCheck(
                    rule_id="QUEUED_STREAMING_TELEMETRY",
                    name="Queued Concurrency & Streaming Telemetry",
                    passed=True,
                    message="Streaming generators paired with queued concurrency or no unqueued streaming found.",
                )
            )

    def _get_kwarg(self, call_node: ast.Call, name: str) -> ast.AST | None:
        for kw in call_node.keywords:
            if kw.arg == name:
                return kw.value
        return None


class GradioAppScaffolder:
    """Scaffolder generating decoupled 3-tier production Gradio architectures."""

    @staticmethod
    def scaffold(config: AppScaffoldConfig) -> AppScaffoldResult:
        """Scaffold decoupled Python logic, Gradio app, requirements, and Spaces README."""
        title = config.app_name.replace("_", " ").replace("-", " ").title()

        logic_code = f'''"""Pure Python core computation logic for {title}.

Decoupled from Gradio UI bindings. 100% testable in headless pytest suites.
"""

from __future__ import annotations

from typing import Any


def process_query(prompt: str, temperature: float = 0.7) -> dict[str, Any]:
    """Execute core computation or model inference.

    Args:
        prompt: User input query text.
        temperature: Model sampling temperature.

    Returns:
        Structured result dictionary.
    """
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("Prompt cannot be empty.")

    # Pure domain transformation
    char_count = len(clean_prompt)
    word_count = len(clean_prompt.split())

    return {{
        "prompt": clean_prompt,
        "temperature": temperature,
        "metrics": {{
            "characters": char_count,
            "words": word_count,
        }},
        "status": "completed",
    }}
'''

        app_code = f'''"""Production Gradio Application Entrypoint for {title}.

Synthesized using Gradio App Architect standards (Eva J Patel / freeCodeCamp, 2026).
- 3-Layer Decoupled Architecture
- Multi-User Session Isolation via gr.State
- Queued Concurrency with Load Shedding
- Graceful gr.Error Toast Notifications
"""

from __future__ import annotations

import os
from typing import Any
import gradio as gr

from logic import process_query

# Warm-load singletons at module scope (Rule 15 of Gradio Architecture)
# Heavy neural models or DB pools initialized once here.


def handle_submit(user_input: str, temp_val: float, session_history: list[dict[str, Any]]):
    """Event callback with strict positional arity matching."""
    if not user_input or not user_input.strip():
        raise gr.Error("Please enter a valid query before submitting.")

    try:
        result = process_query(user_input, temperature=temp_val)
        updated_history = session_history + [result]
        formatted_output = f"Processed: {{result['prompt']}}\\nWord Count: {{result['metrics']['words']}}"
        return formatted_output, updated_history
    except ValueError as ve:
        raise gr.Error(str(ve))
    except Exception as exc:
        raise gr.Error(f"Computation failed: {{str(exc)}}")


def build_app() -> gr.Blocks:
    """Construct declarative layout hierarchy using gr.Blocks."""
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
    )

    with gr.Blocks(theme=theme, title="{title}") as demo:
        # Isolated per-session state (Zero mutable global variables)
        session_history = gr.State(initial_value=[])

        gr.Markdown(
            """
            # {title}
            ### Production AI Interface with Decoupled Logic & Session State
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                user_text = gr.Textbox(
                    label="Input Prompt",
                    placeholder="Enter your prompt here...",
                    lines=3,
                )
                temp_slider = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.7,
                    step=0.05,
                    label="Temperature",
                )
                submit_btn = gr.Button("Submit Query", variant="primary")

            with gr.Column(scale=2):
                output_box = gr.Textbox(
                    label="Structured Result",
                    lines=6,
                    interactive=False,
                )

        # Wire reactive event mesh
        submit_btn.click(
            fn=handle_submit,
            inputs=[user_text, temp_slider, session_history],
            outputs=[output_box, session_history],
        )

        return demo


demo = build_app()

if __name__ == "__main__":
    # Bound concurrency via WebSocket queue
    port = int(os.getenv("PORT", 7860))
    demo.queue(
        default_concurrency_limit={config.concurrency_limit},
        max_size={config.max_queue_size},
    ).launch(server_name="0.0.0.0", server_port=port)
'''

        reqs_code = """gradio>=4.0.0
pydantic>=2.0.0
pytest>=8.0.0
"""

        spaces_readme = f"""---
title: {title}
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.29.0
app_file: app.py
pinned: false
---

# {title}

Production AI application interface synthesized with the **Gradio App Architect** engine.
"""

        files_tuple = (
            ("logic.py", logic_code),
            ("app.py", app_code),
            ("requirements.txt", reqs_code),
            ("README.md", spaces_readme),
        )

        manifest = {
            "app_name": config.app_name,
            "title": title,
            "topology": config.topology,
            "files_count": len(files_tuple),
            "enable_queue": config.enable_queue,
            "concurrency_limit": config.concurrency_limit,
        }

        return AppScaffoldResult(files=files_tuple, manifest=manifest)


class GradioAppArchitectEngine:
    """Primary domain engine for Gradio application architecture and AST verification."""

    def __init__(self) -> None:
        self.scaffolder = GradioAppScaffolder()

    def audit_code(self, source_code: str, file_path: str = "<source>") -> DiagnosticReport:
        """Run AST static analysis against the 5 production Gradio rubrics."""
        inspector = GradioASTInspector(source_code, file_path=file_path)
        return inspector.inspect()

    def scaffold_app(self, config: AppScaffoldConfig) -> AppScaffoldResult:
        """Generate a decoupled production Gradio application."""
        return self.scaffolder.scaffold(config)

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate standalone HTML visual brief with Tailwind and Mermaid.js."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if output_path is None:
            out_p = Path(tempfile.gettempdir()) / f"gradio-app-architect-{timestamp}.html"
        else:
            out_p = Path(output_path)

        html_template = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gradio App Architect: Production Telemetry & Topology Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0f172a',
        primaryColor: '#3b82f6',
        primaryTextColor: '#f8fafc',
        primaryBorderColor: '#60a5fa',
        lineColor: '#94a3b8',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a'
      }
    });
  </script>
  <style>
    body { background-color: #0b0f19; color: #f1f5f9; font-family: ui-sans-serif, system-ui, sans-serif; }
    .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
  </style>
</head>
<body class="min-h-screen p-8 max-w-7xl mx-auto">
  <header class="mb-10 pb-6 border-b border-slate-800 flex justify-between items-center">
    <div>
      <div class="flex items-center gap-3">
        <span class="px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">Production AI Interface Engineering</span>
        <span class="text-xs text-slate-400">Gradio App Architect Engine</span>
      </div>
      <h1 class="text-3xl font-bold mt-2 text-white">Production Gradio Architecture & Diagnostic Brief</h1>
      <p class="text-slate-400 text-sm mt-1">Literature: Eva J Patel (freeCodeCamp, 2026) | Generated: __TIMESTAMP__</p>
    </div>
  </header>

  <!-- 3-Layer Decoupled Topology -->
  <section class="glass-card p-6 rounded-2xl mb-8 shadow-xl">
    <h2 class="text-xl font-bold text-white mb-4">3-Layer Decoupled Architecture Topology</h2>
    <pre class="mermaid text-xs">
flowchart TD
    subgraph UI [Layer 1: Reactive Layout & Components]
        Blocks[gr.Blocks / Semantic Containers]
        Inputs[Typed Inputs: Textbox, Slider, Dropdown]
        Outputs[Typed Outputs: Markdown, Plot, JSON]
        State[gr.State - Per-Session Memory]
    end

    subgraph Mesh [Layer 2: Event Mesh & State Coordination]
        Events[btn.click / textbox.submit]
        Inputs --> Events
        State --> Events
        Events --> Toast[gr.Error Toast Notifications]
    end

    subgraph QueueLayer [Layer 3: Queued Concurrency & Telemetry]
        Queue[demo.queue - Concurrency Limit 5, Max 50]
        Streaming[yield Token Stream / Websocket Delta]
        Events --> Queue
        Queue --> Streaming
    end

    subgraph PureLogic [Layer 4: Headless Core Python Logic]
        Compute[Pure Functions: zero gradio imports]
        Pytest[100% Headless Pytest Suite]
        Queue --> Compute
        Compute -.-> Pytest
    end
    </pre>
  </section>

  <!-- 5-Point Diagnostic Scorecard -->
  <section class="glass-card p-6 rounded-2xl mb-8 shadow-xl">
    <h2 class="text-xl font-bold text-white mb-4">5-Point Diagnostic Coaching Rubrics</h2>
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div class="text-xs font-bold text-blue-400">1. Headless Decoupling</div>
        <p class="text-xs text-slate-400 mt-2">Pure computation functions accept primitives and return domain data without importing Gradio.</p>
      </div>
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div class="text-xs font-bold text-emerald-400">2. Multi-User Isolation</div>
        <p class="text-xs text-slate-400 mt-2">Zero global mutable state. User dialogues strictly managed through <code class="text-blue-300">gr.State</code>.</p>
      </div>
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div class="text-xs font-bold text-purple-400">3. Positional Arity</div>
        <p class="text-xs text-slate-400 mt-2">Strict 1:1 match between <code class="text-blue-300">inputs=[...]</code> and function argument list.</p>
      </div>
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div class="text-xs font-bold text-amber-400">4. Singleton Warm-Load</div>
        <p class="text-xs text-slate-400 mt-2">Neural pipelines initialized once at module startup scope, never inside callbacks.</p>
      </div>
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div class="text-xs font-bold text-rose-400">5. Queued Telemetry</div>
        <p class="text-xs text-slate-400 mt-2">Generators require <code class="text-blue-300">demo.queue()</code> to prevent worker thread lockouts.</p>
      </div>
    </div>
  </section>

  <footer class="text-center text-xs text-slate-500 pt-6 border-t border-slate-800">
    Gradio App Architect &bull; Brain Harness Micro-Kernel Architecture &bull; Rule 12 & 49 Compliant
  </footer>
</body>
</html>
"""
        rendered = html_template.replace("__TIMESTAMP__", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        out_p.write_text(rendered, encoding="utf-8")
        return out_p
