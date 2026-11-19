# Phase 3 — Vault Category to Repo Domain-Class Mapping Review

Please review or edit the `FINAL_DOMAIN_CLASS` column below (or confirm ``ok`` / ``proceed``).

## Repo `domain_class` Distribution (5 Snapshots)

| Repo `domain_class` | Unit Count |
|---|---:|
| `general_ml_project` | 274 |
| `vision_and_3d_project` | 160 |
| `nlp_and_llm_project` | 155 |
| `rl_and_control_project` | 58 |
| `optimization_and_compression_project` | 48 |
| `privacy_fairness_safety_project` | 42 |
| `science_and_bio_project` | 24 |
| `speech_and_audio_project` | 13 |
| `graph_and_program_project` | 7 |
| `systems_and_runtime_project` | 7 |
| `agent_orchestration_project` | 6 |

## Draft Mapping (`vault_category` -> `domain_class`)

| # | Vault `category` | KI Count | Draft `domain_class` | Notes | FINAL_DOMAIN_CLASS |
|---:|---|---:|---|---|---|
| 1 | `agent_orchestration` | 117 | `agent_orchestration_project` |  | `agent_orchestration_project` |
| 2 | `memory_and_epistemics` | 36 | `unmapped` |  | `unmapped` |
| 3 | `security_and_forensics` | 35 | `privacy_fairness_safety_project` |  | `privacy_fairness_safety_project` |
| 4 | `developer_experience` | 31 | `unmapped` |  | `unmapped` |
| 5 | `software_engineering` | 23 | `unmapped` |  | `unmapped` |
| 6 | `data_engineering` | 21 | `conditional:optimization_and_compression_project` | tag-split opt=1, unmapped=22 | `conditional:optimization_and_compression_project` |
| 7 | `developer_experience/architecture` | 19 | `unmapped` |  | `unmapped` |
| 8 | `infrastructure_and_runtime` | 17 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 9 | `machine_learning` | 6 | `general_ml_project` |  | `general_ml_project` |
| 10 | `developer_experience/testing` | 5 | `unmapped` |  | `unmapped` |
| 11 | `integration_and_io` | 5 | `unmapped` |  | `unmapped` |
| 12 | `scientific_computing/geospatial` | 5 | `unmapped` |  | `unmapped` |
| 13 | `context_engineering` | 4 | `unmapped` |  | `unmapped` |
| 14 | `developer_tooling` | 4 | `unmapped` |  | `unmapped` |
| 15 | `scientific_computing` | 4 | `unmapped` |  | `unmapped` |
| 16 | `agent_orchestration/skills` | 3 | `agent_orchestration_project` |  | `agent_orchestration_project` |
| 17 | `developer_experience/software_engineering` | 3 | `unmapped` |  | `unmapped` |
| 18 | `security_and_forensics/sandboxing` | 3 | `privacy_fairness_safety_project` |  | `privacy_fairness_safety_project` |
| 19 | `context_engineering/architecture` | 2 | `unmapped` |  | `unmapped` |
| 20 | `data_engineering/modeling` | 2 | `conditional:optimization_and_compression_project` | tag-split opt=1, unmapped=22 | `conditional:optimization_and_compression_project` |
| 21 | `developer_experience/documentation` | 2 | `unmapped` |  | `unmapped` |
| 22 | `developer_experience/tooling` | 2 | `unmapped` |  | `unmapped` |
| 23 | `infrastructure_and_runtime/integration` | 2 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 24 | `infrastructure_and_runtime/kernel` | 2 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 25 | `infrastructure_and_runtime/sandbox` | 2 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 26 | `memory_and_epistemics/reflection` | 2 | `unmapped` |  | `unmapped` |
| 27 | `security_and_forensics/reverse_engineering` | 2 | `privacy_fairness_safety_project` |  | `privacy_fairness_safety_project` |
| 28 | `agent_orchestration/recursive_refinement` | 1 | `agent_orchestration_project` |  | `agent_orchestration_project` |
| 29 | `agent_orchestration/tooling` | 1 | `agent_orchestration_project` |  | `agent_orchestration_project` |
| 30 | `architecture` | 1 | `unmapped` |  | `unmapped` |
| 31 | `context_engineering/templates` | 1 | `unmapped` |  | `unmapped` |
| 32 | `data_structures` | 1 | `unmapped` |  | `unmapped` |
| 33 | `developer_experience/skills` | 1 | `unmapped` |  | `unmapped` |
| 34 | `developer_experience/ui` | 1 | `unmapped` |  | `unmapped` |
| 35 | `developer_experience/velocity` | 1 | `unmapped` |  | `unmapped` |
| 36 | `developer_experience/visualization` | 1 | `unmapped` |  | `unmapped` |
| 37 | `governance` | 1 | `unmapped` |  | `unmapped` |
| 38 | `infrastructure_and_runtime/cloud` | 1 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 39 | `infrastructure_and_runtime/platform` | 1 | `systems_and_runtime_project` |  | `systems_and_runtime_project` |
| 40 | `memory_and_epistemics/integration` | 1 | `unmapped` |  | `unmapped` |
| 41 | `nlp_and_llm` | 1 | `nlp_and_llm_project` |  | `nlp_and_llm_project` |
| 42 | `performance` | 1 | `unmapped` |  | `unmapped` |
| 43 | `scientific_computing/machine_learning` | 1 | `general_ml_project` |  | `general_ml_project` |
| 44 | `security_and_forensics/auditing` | 1 | `privacy_fairness_safety_project` |  | `privacy_fairness_safety_project` |
| 45 | `testing` | 1 | `unmapped` |  | `unmapped` |
| 46 | `optimization_and_compression` | 1 | `optimization_and_compression_project` | Added in Phase 6 (approved at Checkpoint 6.2) | `optimization_and_compression_project` |
| 47 | `rl_and_control` | 1 | `rl_and_control_project` | Added in Phase 6 (approved at Checkpoint 6.2) | `rl_and_control_project` |
| 48 | `vision_and_3d` | 1 | `vision_and_3d_project` | Added in Phase 6 (approved at Checkpoint 6.2) | `vision_and_3d_project` |
