# Technical Reference: Google Integration Plugins Suite

Comprehensive reference specification for all 7 plugins, typed ServiceKeys, and exported tools.

---

## 1. `plugin.google_adk_runtime`
- **Category**: `agent_orchestration`
- **ServiceKey**: `service.google_adk_runtime` (`ServiceKey[GoogleAdkRuntimeService]`)
- **Isolation**: `IsolationMode.SUBPROCESS` (Rule 5 & Rule 7)

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `adk_run_agent` | `agent_name: str`, `prompt: str`, `session_id: str`, `model: str` | `object` | Run agent workflow with session state tracking |
| `adk_list_sessions` | `limit: int = 20` | `object` | List active sessions and metadata |
| `adk_rewind_session` | `session_id: str`, `checkpoint_index: int` | `object` | Rewind session to previous checkpoint |
| `adk_register_skill` | `skill_name: str`, `description: str`, `prompt_template: str` | `object` | Register dynamic prompt or tool capability |

---

## 2. `plugin.google_adk_optimizer`
- **Category**: `agent_orchestration`
- **ServiceKey**: `service.google_adk_optimizer` (`ServiceKey[GoogleAdkOptimizerService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `adk_gepa_optimize_prompt` | `system_prompt: str`, `train_examples: list`, `iterations: int`, `metric: str` | `object` | Execute Generative Prompt Optimization |
| `adk_evaluate_agent` | `agent_name: str`, `scenario_ids: list`, `judge_model: str` | `object` | Run scenario benchmark evaluations |
| `adk_score_metrics` | `trajectory: list`, `rubrics: list` | `object` | Score multi-turn agent execution rubrics |

---

## 3. `plugin.google_adk_docs_navigator`
- **Category**: `developer_tooling`
- **ServiceKey**: `service.google_adk_docs_navigator` (`ServiceKey[GoogleAdkDocsNavigatorService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `adk_docs_search` | `query: str`, `category: str`, `limit: int` | `object` | Search ADK docs and architecture guides |
| `adk_get_api_reference` | `symbol_name: str`, `language: str` | `object` | Fetch code signature (Py/TS/Go/Kotlin) |
| `adk_fetch_llms_txt` | `topic: str`, `full_content: bool` | `object` | Stream LLM-optimized documentation sections |

---

## 4. `plugin.google_adk_web_bridge`
- **Category**: `developer_tooling`
- **ServiceKey**: `service.google_adk_web_bridge` (`ServiceKey[GoogleAdkWebBridgeService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `adk_web_status` | `project_dir: str` | `object` | Inspect Angular ADK web console state |
| `adk_web_export_graph` | `nodes: list`, `edges: list`, `format: str` | `object` | Export DAG to A2UI or ngx-vflow format |
| `adk_web_start_dev_server` | `port: int`, `poll_interval: int` | `object` | Launch local dev server (Rule 14 cleanup) |

---

## 5. `plugin.google_styleguide_auditor`
- **Category**: `software_engineering`
- **ServiceKey**: `service.google_styleguide_auditor` (`ServiceKey[GoogleStyleguideAuditorService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `styleguide_audit_file` | `file_path: str`, `language: str` | `object` | Audit source file against Google style rules |
| `styleguide_get_rule` | `language: str`, `topic: str` | `object` | Query rule rationales and conventions |
| `styleguide_generate_linter_config` | `tool_name: str`, `target_dir: str` | `object` | Emit .pylintrc or style configuration |

---

## 6. `plugin.google_tunix_posttraining`
- **Category**: `machine_learning`
- **ServiceKey**: `service.google_tunix_posttraining` (`ServiceKey[GoogleTunixPosttrainingService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `tunix_inspect_config` | `pipeline_type: str`, `model_name: str`, `learning_rate: float`, `batch_size: int` | `object` | Validate JAX training configurations |
| `tunix_launch_grpo` | `config_dict: dict`, `dry_run: bool`, `num_steps: int` | `object` | Launch or simulate GRPO training step |
| `tunix_launch_peft` | `config_dict: dict`, `lora_rank: int`, `dry_run: bool` | `object` | Configure and run LoRA fine-tuning |
| `tunix_compute_math_reward` | `completion: str`, `ground_truth: str`, `format_check: bool` | `object` | Compute mathematical reward score |

---

## 7. `plugin.perfetto_trace_processor`
- **Category**: `software_engineering`
- **ServiceKey**: `service.perfetto_trace_processor` (`ServiceKey[PerfettoTraceProcessorService]`)
- **Isolation**: `IsolationMode.SUBPROCESS`

### Exported Tools
| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `perfetto_load_trace` | `trace_path: str`, `verbose: bool` | `object` | Ingest trace file into schema tables |
| `perfetto_query_sql` | `trace_id: str`, `sql_query: str` | `object` | Execute SQL query against trace tables |
| `perfetto_compute_metrics` | `trace_id: str`, `metrics_list: list` | `object` | Compute CPU scheduling & thread metrics |
| `perfetto_export_flamegraph` | `trace_id: str`, `focus_thread: str` | `object` | Generate execution flame graph tree |
