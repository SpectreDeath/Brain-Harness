┌─────────────────────────────────────────────────────────────┐
│ SKILL: gradio-app-architect                                 │
├─────────────────────────────────────────────────────────────┤
│ DESCRIPTION: Production-grade Gradio web apps with decoupled│
│ logic, reactive Blocks, session state, & queued streaming   │
└─────────────────────────────────────────────────────────────┘

## Stage Progression Matrix

| Stage | Focus Area | Core Mechanism | Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Decoupled Logic** | Pure Python Logic | Pure compute functions, testable via headless pytest | 100% testable without Gradio, exact arity contract |
| **2. Layout Topology** | Container Mesh | `gr.Blocks`, `Row`, `Column`, `Tab`, `Accordion` | Declarative UI hierarchy with typed I/O components |
| **3. Session State** | Concurrency Mesh | `gr.State(initial_value)`, `.click()`, `.submit()` | Zero global variable state, isolated per session |
| **4. Streaming & Media** | Pipeline Processing | `yield` generators, `gr.Progress`, file validation | Real-time token streaming, path traversal defended |
| **5. Production Guardrails**| Performance & Deploy | Warm-start models, `demo.queue()`, `gr.Error` | Queued concurrency, zero hardcoded secrets |

---

## Three Pillars Cheat Sheet

### Pillar 1: Decoupled Logic & Session State Isolation
- **Decoupled Logic**: Keep compute and inference functions 100% pure; testable in pytest without Gradio imports.
- **Zero Global State**: Never use module-level variables (`history = []`) to store user dialogue or state.
- **The Invariant**: *"Always use `gr.State(initial_value)` inside Blocks and pass it explicitly through inputs and outputs."*

### Pillar 2: Reactive Topology & Streaming Pipelines
- **Topology Selection**: Use `gr.Blocks` for custom dashboards, `gr.ChatInterface` for conversational agents.
- **Streaming Generators**: Use Python `yield` to stream tokens or progressive updates across websockets.
- **Progress Telemetry**: Bind `gr.Progress(track_tqdm=True)` for multi-step execution feedback.
- **File Security**: Whitelist MIME types via `file_types=[...]` and resolve paths safely with `Path.resolve()`.

### Pillar 3: Production Guardrails & Space Deployment
- **Warm-Load Singletons**: Load ML models and pipelines once at module scope; never inside event handlers.
- **Queued Concurrency**: Always enable `demo.queue()` to protect server threads and shed excess load gracefully.
- **Graceful Error Handling**: Catch domain exceptions and raise `gr.Error("Clear explanation")`.
- **Deployment Manifests**: Standardize `app.py`, pinned `requirements.txt`, and `README.md` YAML frontmatter for Spaces.

---

## Verification Checklist

- [ ] Frontmatter description bounded between 100 and 350 characters with action verbs and negative boundary.
- [ ] Core Python functions decoupled from Gradio components and testable independently in headless pytest.
- [ ] Input and output arity contracts match handler function arguments and return types 1:1.
- [ ] Per-session user context managed strictly via `gr.State`, with zero mutable module-level globals.
- [ ] Reactive event bindings (`.click()`, `.submit()`, `.change()`) properly wire inputs, state, and outputs.
- [ ] Long-running or conversational tasks use `yield` generators for real-time streaming.
- [ ] File and media components enforce strict `file_types=[...]` boundaries and path sanitization.
- [ ] Heavy models and pipelines warm-loaded at module initialization scope, never inside event callbacks.
- [ ] Server enables `demo.queue()` with bounded concurrency limits for streaming and load shedding.
- [ ] Exceptions surfaced via user-friendly `gr.Error` toasts instead of unhandled raw stacktraces.
- [ ] Companion `CARD.md` utilizes single-pipe borders (`│`) and exact `SKILL:` header.
