# Semantic Kernel Orchestration Engine Plugin

Forged directly from upstream **Microsoft Semantic Kernel** (`D:\GitHub\cloned\semantic-kernel-main\semantic-kernel-main`).

## Overview

The `domain.semantic_kernel_engine` plugin integrates Microsoft Semantic Kernel's agent orchestration and prompt engine into Brain Harness with full `subprocess` sandbox isolation.

### Key Capabilities

1. **`orchestrate_group_chat`**: Multi-agent collaborative discussions with speaker strategy (round-robin, supervisor-directed), turn management, and termination detection.
2. **`execute_kernel_process`**: Step DAG state machine execution engine with conditional routing, data transformation, and state propagation.
3. **`render_semantic_prompt`**: Dynamic semantic prompt template compiler supporting Handlebars and Jinja2 syntax (`{{var}}`, `{{#if}}`).
4. **`search_semantic_memory`**: Volatile in-memory vector similarity search engine using tokenized cosine similarity scoring.
5. **`execute_openapi_plugin`**: OpenAPI 3.0 / Swagger specification executor with operation resolution, parameter validation, and URL construction.

## Isolation Mode

- **Mode**: `IsolationMode.SUBPROCESS`
- **Category**: `agent_orchestration`
- **Trust Level**: Trusted external archetype


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `orchestrate_group_chat` | `(agents, task, strategy, max_rounds, termination_keyword)` | Execute multi-agent collaborative discussions with speaker strategy, turn execution, and consensus/termination criteria |
| `execute_kernel_process` | `(process_name, steps, initial_state)` | Execute step DAG and state machine processes with conditional event routing, step transitions, and state propagation |
| `render_semantic_prompt` | `(template, variables, engine)` | Compile and render Handlebars or Jinja2 dynamic semantic prompt templates with nested variable substitution |
| `search_semantic_memory` | `(query, documents, limit, min_relevance)` | Run volatile vector similarity search against documents using cosine similarity scoring and relevance thresholding |
| `execute_openapi_plugin` | `(openapi_spec, operation_id, arguments)` | Parse OpenAPI 3.0 / Swagger specifications and execute REST operations with JSON Schema parameter validation |
