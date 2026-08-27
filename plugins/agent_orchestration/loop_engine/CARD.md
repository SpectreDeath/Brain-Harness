# 🧠 Skill Summary Card: `loop_engine`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        loop_engine                               │
│ Category:    agent_orchestration                       │
│ Archetype:   agent_worker / service_provider           │
│ Isolation:   subprocess                                │
│ Status:      Verified & Sandboxed                      │
├────────────────────────────────────────────────────────┤
│ Target:      Goal-Directed DAG Controller & Recovery   │
└────────────────────────────────────────────────────────┘
```

## Tools
- `run_loop(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations)`: Goal-directed DAG controller.
- `validate_task_dag(tasks)`: DAG integrity and cycle detector.
- `benchmark_loop_vs_linear(num_scenarios, seed, max_iterations)`: Head-to-head resilience comparison.
- `create_scenario_graph(num_branches, tasks_per_branch, seed, failure_mix)`: Synthetic failure graph generator.
