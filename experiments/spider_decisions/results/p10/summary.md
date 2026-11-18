# Phase 10 — Skill Routing Evaluation Summary (`route_intent` vs Spider vs Hybrid)

Evaluated **20** task intents across **114** `.agents/skills/` targets and **377** vault KIs.

## Hit@1 and Hit@3 Comparison

| Method | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % |
|---|---:|---:|---:|---:|
| Baseline (`route_intent`) | 19/20 | 95.0% | 19/20 | 95.0% |
| Spider-assisted (vault tags + edges) | 2/20 | 10.0% | 4/20 | 20.0% |
| Hybrid (baseline top-3 re-ranked) | 13/20 | 65.0% | 19/20 | 95.0% |
| Hybrid Union (baseline ∪ spider top-3) | 8/20 | 40.0% | 11/20 | 55.0% |

## Unique Wins
- **Baseline `@1` only (missed by Spider `@1`):** `[1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 20]`
- **Spider `@1` only (missed by Baseline `@1`):** `[]`
- **Hybrid Union `@3` gains over Baseline `@3`:** `[]`

## Per-Task Outcomes

| # | Expected | Baseline Top-1 | Spider Top-1 | Hybrid Top-1 | Union Top-1 | B@3 | S@3 | H@3 | U@3 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `deep-repo-auditor` | `deep-repo-auditor` | `architecture-deepening-workflow` | `deep-repo-auditor` | `architecture-deepening-workflow` | True | False | True | False |
| 2 | `ontology-spider` | `research` | `ai-agent-engineer` | `research` | `ai-agent-engineer` | False | False | False | False |
| 3 | `rea-reverse-engineering` | `rea-reverse-engineering` | `ai-agent-engineer` | `rea-reverse-engineering` | `rea-reverse-engineering` | True | False | True | True |
| 4 | `epistemic-isnad-audit` | `epistemic-isnad-audit` | `graphiti-zep-memory-governor` | `epistemic-memory-lifecycle` | `epistemic-memory-lifecycle` | True | False | True | False |
| 5 | `ai-red-teaming-architect` | `ai-red-teaming-architect` | `plugin-seam-and-mirror-auditor` | `ai-red-teaming-architect` | `ai-red-teaming-architect` | True | False | True | True |
| 6 | `mantis-security-review` | `mantis-security-review` | `ai-agent-engineer` | `mantis-security-review` | `ai-agent-engineer` | True | False | True | True |
| 7 | `monolith-decomposition-engine` | `monolith-decomposition-engine` | `graphiti-zep-memory-governor` | `python-dataclass-architect` | `epistemic-memory-lifecycle` | True | False | True | False |
| 8 | `headroom-context-optimizer` | `headroom-context-optimizer` | `ai-agent-engineer` | `headroom-context-optimizer` | `ai-agent-engineer` | True | False | True | True |
| 9 | `prompt-pruning-architect` | `prompt-pruning-architect` | `ai-agent-engineer` | `prompt-pruning-architect` | `ai-agent-engineer` | True | False | True | True |
| 10 | `game-theoretic-swarm-deliberator` | `game-theoretic-swarm-deliberator` | `ai-agent-engineer` | `orca-orchestrator` | `ai-agent-engineer` | True | False | True | False |
| 11 | `ebbinghaus-memory-governor` | `ebbinghaus-memory-governor` | `epistemic-memory-lifecycle` | `ebbinghaus-memory-governor` | `ebbinghaus-memory-governor` | True | True | True | True |
| 12 | `uncertainty-aware-ai-architect` | `uncertainty-aware-ai-architect` | `architecture-deepening-workflow` | `agent-harness-architect` | `architecture-deepening-workflow` | True | False | True | False |
| 13 | `deepselect-topk-optimizer` | `deepselect-topk-optimizer` | `headroom-context-optimizer` | `deepselect-topk-optimizer` | `deepselect-topk-optimizer` | True | True | True | True |
| 14 | `youtube-transcript-fetcher` | `youtube-transcript-fetcher` | `epistemic-memory-lifecycle` | `youtube-transcript-fetcher` | `youtube-transcript-fetcher` | True | False | True | True |
| 15 | `bigquery-augmented-analytics` | `bigquery-augmented-analytics` | `ai-native-harness-engineer` | `bigquery-augmented-analytics` | `bigquery-augmented-analytics` | True | False | True | True |
| 16 | `geospatial-disaster-simulation` | `geospatial-disaster-simulation` | `geospatial-disaster-simulation` | `geospatial-disaster-simulation` | `geospatial-disaster-simulation` | True | True | True | True |
| 17 | `gradio-app-architect` | `gradio-app-architect` | `ai-agent-engineer` | `gemini-vercel-streaming-chatbot` | `ai-agent-engineer` | True | False | True | False |
| 18 | `pre-commit-security-guard` | `pre-commit-security-guard` | `pre-commit-security-guard` | `pre-commit-security-guard` | `pre-commit-security-guard` | True | True | True | True |
| 19 | `brain-artifact-miner` | `brain-artifact-miner` | `agent-skills-architect` | `brain-artifact-miner` | `agent-skill-sdlc` | True | False | True | False |
| 20 | `recursive-harness-refiner` | `recursive-harness-refiner` | `ai-agent-engineer` | `ai-agent-engineer` | `ai-agent-engineer` | True | False | True | False |
