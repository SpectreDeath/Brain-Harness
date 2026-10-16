# Google ADK Optimizer Plugin

Prompt optimization and agent evaluation harness.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `adk_gepa_optimize_prompt` | `(system_prompt, train_examples, iterations, metric)` | Run Generative Prompt Optimization (GEPA) to iteratively improve agent prompts against reference metrics |
| `adk_evaluate_agent` | `(agent_name, scenario_ids, judge_model)` | Evaluate agent execution against benchmark conversation scenarios |
| `adk_score_metrics` | `(trajectory, rubrics)` | Score agent execution trajectories across multi-dimensional quality rubrics |
