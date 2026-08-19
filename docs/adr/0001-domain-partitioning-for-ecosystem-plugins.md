# ADR 0001: Domain Partitioning for Ecosystem Plugins

- **Status**: ACCEPTED
- **Date**: 2026-08-19
- **Deciders**: Brain Harness Core Architecture Team

---

## Context & Problem Statement

The Brain Harness project initially accumulated 34 diverse plugins (ranging from Kubernetes manifest validators and network packet auditors to Z3 symbolic solvers and statistical tabular profilers) within a flat `plugins/` directory.

Shipping all 34 plugins inside the core repository created several architectural problems:
1. It violated the core principle that **Harness is a blank cognitive canvas**, where the harness reflects the user's brain rather than a fixed bundle of opinions.
2. It blurred domain boundaries between autonomous agent coordination, data engineering, infrastructure operations, and cybersecurity forensics.
3. It burdened the core repository with unrelated domain dependencies and test suites.

## Decision

We have partitioned the 34 plugins into seven cohesive **Bounded Domains** documented in [CONTEXT-MAP.md](../../CONTEXT-MAP.md):

1. **Agent Orchestration** (`agent_supervisor`, `agent_debater`, `evaluator_critic`, `task_planner`, `human_in_the_loop`)
2. **Memory & Epistemics** (`skill_knowledge_graph`, `vector_index`, `embedding_cluster`, `context_compactor`, `prompt_benchmark`)
3. **Data Engineering** (`dataset_profiler`, `data_transformer`, `database_sql`, `synthetic_generator`)
4. **Software Engineering** (`refactor_engine`, `arch_linter`, `code_runner`, `filesystem_git`, `migration_assistant`, `artifact_generator`)
5. **Security & Forensics** (`security_scanner`, `threat_modeler`, `log_forensics`, `network_forensics`, `trajectory_auditor`)
6. **Infrastructure & Cloud** (`docker_container`, `k8s_manifest`, `terraform_iac`, `ci_pipeline`)
7. **Integration & I/O** (`web_fetcher`, `api_openapi`, `notification_webhook`, `symbolic_solver`)

The core Git repository tracks only the Harness Micro-Kernel, Ingestion Pipeline, Agent Skills, and Services. Domain plugins are maintained as independent packages/branches to be ingested on demand.

## Consequences

### Positive
- **Clean Cognitive Model**: Users and agents can navigate plugins through a strict ubiquitous language per domain.
- **Independent Evolution**: Domains can be versioned, branched, and published independently without polluting the core micro-kernel.
- **Zero Kernel Coupling**: No domain-specific logic leaks into the core runtime.

### Negative / Trade-offs
- Requires maintaining the `CONTEXT-MAP.md` and domain glossaries when new plugins are added.
