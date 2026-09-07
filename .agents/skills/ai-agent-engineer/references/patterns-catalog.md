# Appendix: The 60 Canonical Architectural Patterns Catalog

Distilled from Vahe Aslanyan's (*The AI Agent Engineer's Guide: 60 Patterns for Building Autonomous Systems*, LUNARTECH).

---

## Capability 1: Perception (Patterns 1–7)
*Turning raw signals into typed, structured percepts.*

1. **Multimodal Grounding**: Aligns linguistic references to visual/audio referents.
2. **Document Layout**: Turns complex documents (PDFs, scans) into typed hierarchical region trees.
3. **Temporal Sensor-Fusion**: Aligns asynchronous data streams onto a single coherent timeline.
4. **Anomaly-Spotter**: Surfaces statistically and contextually significant deviations from expected patterns.
5. **Visual Question Decomposition**: Breaks compound multimodal queries into focused visual sub-queries.
6. **Ambient Context**: Passively integrates background environmental signals without explicit user query.
7. **Schema-Inference**: Discovers and validates the structural schema of an unknown or dynamic data source.

---

## Capability 2: Reasoning (Patterns 8–15)
*Inferring logically and counterfactually beyond the given data.*

8. **Chain-of-Thought Auditor**: Verifies each premise, mathematical calculation, and logical step in a reasoning trace.
9. **Counterfactual Reasoner**: Runs speculative "what-if" rollouts against current state before action execution.
10. **Analogical Mapping**: Discovers structural and relational parallels to solved historical cases.
11. **Constraint-Satisfaction**: Formulates domain constraints into a formal solver (SMT/SAT) to bound feasible choices.
12. **Causal Graph Builder**: Induces causal DAG structure to distinguish correlation from intervention effects.
13. **Symbolic-Neural Bridge**: Translates ambiguous natural language into formal mathematical expressions and back.
14. **Probabilistic Belief Updater**: Maintains and updates Bayesian posterior belief distributions as new evidence arrives.
15. **Self-Consistency Voter**: Samples $N$ parallel reasoning chains and aggregates the final decision via consensus/majority.

---

## Capability 3: Planning (Patterns 16–22)
*Translating goals into bounded, sequenced execution graphs.*

16. **Hierarchical Decomposer**: Recursively decomposes high-level goals into directed acyclic subgoal trees.
17. **ReAct Loop**: Interleaves reasoning, action invocation, and observation evaluation with strict step bounds.
18. **Tree-of-Thought Explorer**: Evaluates, branches, and prunes a search tree of plan candidates using value heuristics.
19. **Plan-Then-Execute**: Generates complete upfront plan for human/system inspection before triggering monitored execution.
20. **Adaptive Replanner**: Continuously monitors execution progress and re-plans dynamically upon stagnation or deviation.
21. **Resource-Aware Scheduler**: Constructs plans optimized under strict compute, latency, token, and monetary budgets.
22. **Backward Goal-Regression**: Plans backward from the desired goal state to discover prerequisite enabling states.

---

## Capability 4: Memory (Patterns 23–29)
*Persistence, recall, and context management across time.*

23. **Episodic Buffer**: Stores time- and actor-indexed chronological events and execution trajectories.
24. **Semantic Memory Curator**: Distills discrete episodic interactions into consolidated, permanent factual knowledge.
25. **Working-Memory Manager**: Dynamically constructs, prunes, and reshapes prompt context per execution step.
26. **Forgetting-Policy**: Systematically prunes obsolete or low-utility memories via decay functions.
27. **Memory-of-Self**: Maintains an explicit, calibrated self-model of agent competencies, failure modes, and boundaries.
28. **Vector-Store Curator**: Continually cleans, re-indexes, and deduplicates semantic embedding indices.
29. **Persistent Identity**: Resolves user and agent persona identities consistently across multi-tenant surfaces.

---

## Capability 5: Tool Use (Patterns 30–37)
*Executing actions in the external digital environment.*

30. **Tool Selector**: Performs semantic retrieval across extensive tool registries to prevent prompt bloat ($> 20$ tools).
31. **API-Schema Adapter**: Dynamically synthesizes callable agent tools from OpenAPI specifications at runtime.
32. **Code-Execution Sandbox**: Executes model-generated code in isolated, sandboxed environments with strict timeouts.
33. **Shell-Operator**: Drives command-line interfaces with strict safety filters, parameter validation, and rollback.
34. **Browser-Driver**: Navigates web applications using DOM trees, accessibility trees, and visual coordinates.
35. **DB Query Synthesizer**: Translates natural language into SQL queries with read-only transaction wrappers.
36. **File-System Curator**: Maintains, modifies, and navigates project filesystem trees safely with atomic diffs.
37. **Side-Effect Auditor**: Records every external mutation into an append-only log with automated transactional rollback.

---

## Capability 6: Coordination (Patterns 38–45)
*Orchestrating multi-agent collaboration and human governance.*

38. **Router/Dispatcher**: Directs incoming requests to specialized expert agents based on intent analysis.
39. **Debate Moderator**: Orchestrates structured dialectical debates between competing reasoners to expose fallacies.
40. **Consensus-Builder**: Synthesizes heterogeneous agent recommendations using formal voting or aggregation rules.
41. **Pipeline Orchestrator**: Chains specialized agents into deterministic producer-consumer processing pipelines.
42. **Human-in-the-Loop Liaison**: Integrates structured human review, escalation modals, and approval checkpoints.
43. **Negotiation**: Conducts multi-party bargaining between autonomous agents based on utility curves.
44. **Auctioneer**: Uses market-based bidding mechanisms to allocate computational tasks among worker agents.
45. **Supervisor-Worker**: Manages, distributes, and aggregates tasks across a dynamic pool of parallel worker agents.

---

## Capability 7: Learning (Patterns 46–52)
*Improving agent performance and strategy through experience.*

46. **Feedback Loop**: Collects explicit user corrections and implicitly incorporates them into preference weights.
47. **Reflection**: Exercises autonomous self-critique against explicit quality rubrics prior to delivering output.
48. **Skill-Library Builder**: Modularizes verified execution trajectories into parameterized, reusable agent skills.
49. **Curriculum Designer**: Sequences training and operational tasks from simple to complex to accelerate proficiency.
50. **Few-Shot Prompt Tuner**: Dynamically retrieves the most relevant few-shot exemplars tailored to each prompt.
51. **Distillation**: Compresses high-cost multi-agent trajectories or frontier reasoning traces into smaller models.
52. **Active Learner**: Detects high-uncertainty edge cases and requests targeted human annotations.

---

## Capability 8: Alignment (Patterns 53–60)
*Enforcing safety, reliability, and human corrigibility by design.*

53. **Constitution-Bound**: Enforces structural rule validation on every candidate action before execution.
54. **Refusal Calibrator**: Produces polite, precise refusals without sycophancy or false-positive over-blocking.
55. **Provenance Tracker**: Attaches verified citation chains and isnad lineages to every factual claim.
56. **Red-Team Auditor**: Continuously executes automated adversarial attacks to uncover latent security vulnerabilities.
57. **Privacy-Preserving**: Enforces de-identification, anonymization, and minimization across trust boundaries.
58. **Explainer**: Emits truthful, post-hoc rationales detailing which factors drove an agent's decision.
59. **Drift Detector**: Monitors input queries and agent outputs for distributional drift away from benchmark distributions.
60. **Off-Switch-Compatible**: Provides an instantaneous, sub-second operator kill-switch with clean state preservation.
