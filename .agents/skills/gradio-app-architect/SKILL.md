---
name: gradio-app-architect
description: Architect, build, debug, and deploy production-grade Gradio web applications and AI interfaces using clean logic-interface separation, reactive Blocks event graphs, session state isolation, multimodal pipelines, and queued streaming. Do not use for non-Python web stacks or full-stack React/Node applications.
---

# Gradio App Architect: Production AI Interface Engineering

The `gradio-app-architect` skill provides the definitive engineering methodology for architecting, building, optimizing, and deploying production-grade interactive web applications and AI agent interfaces in Python using Gradio.

Synthesized from Eva J Patel's literature (*How to Use Gradio with Python: A Complete Beginner-to-Advanced Book*, freeCodeCamp, 2026), this skill eliminates brittle prototype-to-production failures—such as multi-user global state corruption, GPU VRAM thrashing from model reloading, and unqueued server freezing—by enforcing a rigorous **3-layer decoupled architecture**, reactive event graph synthesis, isolated session state, streaming generators, and hardened deployment standards.

```
[1. Decoupled Logic & Contracts] -> [2. Reactive Layout Topology] -> [3. Session State & Event Mesh] -> [4. Streaming & Media Pipelines] -> [5. Production Guardrails & Deployment]
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and verification checklist.
Consult [ai-file-analysis-agent](../ai-file-analysis-agent/SKILL.md) for document ingestion and [crafting-skills](../crafting-skills/SKILL.md) for skill craft standards.

---

## 1. Decoupled Logic & Signature Contract Definition

Ensure absolute separation between Python computation/inference logic and user interface bindings. Core functions must remain testable independently of Gradio.

1. **Author Pure Python Logic Units**:
   - Keep business logic, ML inference, data transformations, and external API requests inside standalone Python functions.
   - Prohibit importing `gradio` or calling UI helper objects (`gr.update()`) within the core logic layer.
   - Assert standalone testability: the function must execute successfully in headless `pytest` suites using mock arguments without spinning up an event loop.
2. **Establish Positional Arity & Cardinality Contracts**:
   - Formulate strict input-output signatures:
     ```python
     def analyze_document(file_path: str, query: str, temperature: float) -> tuple[str, dict]:
         """Pure logic layer function."""
         ...
         return formatted_summary, metrics_dict
     ```
   - Ensure the number and positional order of arguments in the function signature strictly match the `inputs=[...]` list of Gradio components.
   - Ensure returned values match the `outputs=[...]` list (single output for a scalar return; tuple for multiple output components).

> **Completion criterion**: Core computation implemented as pure Python functions with 100% headless testability and exact positional input/output arity mapping.

---

## 2. Reactive Layout & Component Topology Synthesis

Select the appropriate architectural topology and construct a declarative, ergonomic layout hierarchy.

1. **Select Architectural Topology**:
   - **`gr.Interface`**: Use strictly for rapid 1-to-1 or N-to-N functional demonstrations where layout customization is unnecessary.
   - **`gr.ChatInterface`**: Use for standard conversational agents requiring pre-built chat history, text input, retry, undo, and clear actions.
   - **`gr.Blocks`**: Use for all production dashboards, multi-step agent workflows, multi-tab tools, and asymmetric layouts.
2. **Structure Declarative Container Hierarchy**:
   - Use semantic layout containers to organize screen real estate:
     - `gr.Row()`: Horizontal component alignment.
     - `gr.Column(scale=...)`: Responsive column partitioning (e.g. `scale=1` for controls sidebar, `scale=3` for primary visualization).
     - `gr.Tab("Tab Name")`: Multi-view categorization (e.g., "Document Query", "Raw Data", "Analytics").
     - `gr.Accordion("Advanced Settings", open=False)`: Collapsible configuration controls.
3. **Instantiate Typed Controls & Visualizers**:
   - Select explicit components matching domain data types: `gr.Textbox`, `gr.Number`, `gr.Slider`, `gr.Dropdown`, `gr.Checkbox`, `gr.Radio`, `gr.DataFrame`, `gr.Plot`, `gr.JSON`, `gr.Label`.

> **Completion criterion**: Declarative layout compiled within `gr.Blocks` using semantic rows, columns, and tabs, with all I/O components typed and bound.

---

## 3. Multi-User Session State Isolation & Event Mesh

Prevent cross-user data leakage and coordinate reactive interactions across components.

1. **Enforce Zero Global Variable State**:
   - Never use module-level global variables (`history = []`, `active_user = None`) to store session context. Global variables are shared across all concurrent browser sessions in the server process.
   - Declare isolated, per-session state within the `gr.Blocks` context:
     ```python
     with gr.Blocks() as demo:
         session_history = gr.State(initial_value=[])
         session_file_cache = gr.State(initial_value={})
     ```
2. **Wire Reactive Event Bindings**:
   - Bind event triggers: `.click()`, `.submit()`, `.change()`, `.upload()`, `.clear()`.
   - Pass state into the event handler via `inputs` and receive the updated state via `outputs`:
     ```python
     submit_btn.click(
         fn=process_message,
         inputs=[user_msg, session_history],
         outputs=[chat_display, session_history]
     )
     ```
3. **Execute Dynamic UI Mutations**:
   - When an event modifies a component's appearance, visibility, or options, return `gr.update(...)`:
     ```python
     def toggle_view(show_advanced: bool):
         return gr.update(visible=show_advanced)
     ```

> **Completion criterion**: All interactive events bound to handler functions, with per-session state strictly managed via `gr.State` and zero global variable pollution.

---

## 4. Streaming Generators & Multimodal Media Pipelines

Provide responsive user feedback for long-running workflows and safely process binary multimedia assets.

1. **Implement Real-Time Streaming with Python Generators**:
   - For LLM generation, document parsing, or batch calculations, implement functions as Python generators using `yield`:
     ```python
     def stream_llm_response(prompt: str, history: list):
         accumulated_text = ""
         for token in model_client.stream(prompt):
             accumulated_text += token
             yield accumulated_text
     ```
   - Each `yield` transmits an immediate websocket delta frame to the connected browser, eliminating perceived latency.
2. **Attach Real-Time Progress Telemetry**:
   - For multi-step pipeline execution, pass `progress=gr.Progress(track_tqdm=True)` into the event function to stream granular status banners.
3. **Harden Multimodal File & Media Ingestion**:
   - Use `gr.File` with explicit extension boundaries: `file_types=[".pdf", ".docx", ".csv", ".json"]`.
   - Treat uploaded filenames as untrusted input. Validate paths against directory traversal attacks (`Path(file.name).resolve()`).
   - For media workflows, bind `gr.Image`, `gr.Audio`, or `gr.Video` configuring appropriate runtime types (`type="pil"`, `type="numpy"`, or `type="filepath"`).

> **Completion criterion**: Streaming workflows implemented with `yield`, progress indicators bound, and file pipelines sanitized with explicit type whitelisting.

---

## 5. Production Guardrails, Performance & Deployment Hardening

Harden the application against concurrency crashes, latency spikes, and security vulnerabilities.

1. **Warm-Load Models at Module Initialization Scope**:
   - Heavy neural weights, tokenizers, pipelines, and database pools must be initialized once at the root module level.
   - Prohibit re-initializing models inside event callback functions, which causes catastrophic memory exhaustion and multi-second latency penalties.
2. **Configure Queued Concurrency**:
   - For streaming, multimodal workloads, or multi-user traffic, mandate Gradio's websocket queue:
     ```python
     demo.queue(
         default_concurrency_limit=5,
         max_size=50
     ).launch(server_name="0.0.0.0", server_port=7860)
     ```
   - Bounds concurrent GPU/CPU execution while holding pending users in an orderly FIFO queue.
3. **Graceful Error Toast Notifications**:
   - Trap expected domain exceptions and elevate user-facing feedback via `raise gr.Error("User-friendly explanation")` instead of letting raw Python tracebacks crash the UI.
4. **Environment Secret Hygiene & Space Deployment Schema**:
   - Inject all API tokens, database passwords, and environment keys via `os.getenv()`; never hardcode credentials.
   - Structure Hugging Face Spaces deployment assets:
     - `app.py`: Entrypoint launching the application.
     - `requirements.txt`: Pinned dependencies.
     - `README.md`: YAML frontmatter defining Space configuration (title, sdk, sdk_version, app_file).

> **Completion criterion**: Application warm-loads singletons, enables queued concurrency, handles errors via `gr.Error`, and satisfies deployment manifests.

---

## Diagnostic Coaching Rubrics

When reviewing or refactoring a Gradio application, evaluate against these five diagnostic criteria:

1. **The Headless Decoupling Test**:
   - *Question*: Can the core logic function execute inside `pytest` without importing `gradio`?
   - *Pass*: Pure function accepting primitives/paths and returning domain data.
   - *Fail*: Function references Gradio components or returns `gr.update` mixed with domain data.
2. **The Multi-User Concurrency Isolation Test**:
   - *Question*: If two users interact with the app in separate browser windows, do their inputs, histories, or settings cross-pollinate?
   - *Pass*: All session state is stored in `gr.State` instances.
   - *Fail*: State is stored in module-level global variables or class static attributes.
3. **The Positional Arity Contract Test**:
   - *Question*: Does the number and order of items in `inputs=[...]` match the handler's parameters, and does the return match `outputs=[...]`?
   - *Pass*: Exact 1:1 positional alignment.
   - *Fail*: Unpacking errors, missing tuple elements, or mismatched component count.
4. **The Singleton Warm-Load Test**:
   - *Question*: Are ML pipelines, heavy tokenizers, or database connections loaded inside event handlers?
   - *Pass*: Single startup load at module initialization.
   - *Fail*: Model reloaded on every button click or submit event.
5. **The Queue & Streaming Telemetry Test**:
   - *Question*: Does long-running inference block the server worker thread and lock out other users?
   - *Pass*: `demo.queue()` enabled with streaming generators (`yield`).
   - *Fail*: Monolithic synchronous `return` on an unqueued server.

---

---

## The Visual Brief Specification

When architecting complex Gradio applications, multi-tab dashboards, or refactoring existing interfaces:
1. **Target Path**: Render an interactive HTML Visual Brief to `%TEMP%\gradio-app-architect-<timestamp>.html`.
2. **Visual Assets**: Include Tailwind CSS and Mermaid.js diagrams illustrating the proposed interface layout topology, reactive event mesh, and data flow.
3. **Diagnostic Tables**: Embed the 5-point diagnostic scorecard, input/output cardinality table, and anti-pattern defense matrix.
4. **Delivery**: Verify file existence and deliver a clickable `file:///` link to the user.

---

## Mandatory Checkpoint Gate

Before authoring code or executing major interface refactors:
1. **Present Implementation Plan**: Author a comprehensive plan artifact detailing target component topology, state models, streaming generators, and deployment targets.
2. **Set Feedback Header**: Set `RequestFeedback: true` in artifact metadata.
3. **Human Sign-Off Invariant**: STOP and wait for explicit human review and confirmation before writing application files or modifying production Spaces.

---

## Anti-Patterns

- **Global State Pollution** — Storing conversation history, counters, or user session data in module-level global variables, triggering race conditions and cross-user data leakage.
- **Per-Request Model Reloading** — Instantiating pipelines or loading neural network weights inside event callback functions, creating massive latency spikes and GPU OOM crashes.
- **Tightly Coupled UI Logic** — Embedding Gradio components or UI formatting logic directly inside core calculation and inference functions, destroying automated testability.
- **Blocking Unqueued Workflows** — Executing long-duration inference, batch file transformations, or streaming operations without `demo.queue()`, locking the server worker thread and dropping concurrent requests.
- **Raw Exception Leakage** — Allowing uncaught Python exceptions to crash the UI or expose internal paths, rather than catching expected failures and raising informative `gr.Error` alerts.
- **Hardcoded Secrets & Path Traversal** — Hardcoding API keys in source code or blindly passing user-uploaded file paths into shell commands or filesystem writes without sanitization.
