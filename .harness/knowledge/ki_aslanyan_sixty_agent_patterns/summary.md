# The Eight Capabilities & Sixty Architectural Agent Patterns

**ID:** `ki_aslanyan_sixty_agent_patterns`  
**Category:** `agent_orchestration`  
**Origin:** *The AI Agent Engineer's Guide: 60 Patterns for Building Autonomous Systems* (Vahe Aslanyan, LUNARTECH)  
**Provenance Lineage:** Part II & Appendix A/B, freeCodeCamp, 2026.

## Executive Summary
Autonomous agents are not monolithic entities; they are compositions of capabilities. Vahe Aslanyan codifies 60 canonical architectural patterns partitioned across eight fundamental cognitive and system capabilities: Perception, Reasoning, Planning, Memory, Tool Use, Coordination, Learning, and Alignment.

### Capability Taxonomy & Pattern Catalog
1. **Perception (Patterns 1–7)**: Translates unstructured signals into structured percepts.
   - *Patterns*: Multimodal Grounding (1), Document Layout (2), Temporal Sensor-Fusion (3), Anomaly-Spotter (4), Visual Question Decomposition (5), Ambient Context (6), Schema-Inference (7).
2. **Reasoning (Patterns 8–15)**: Deductive, counterfactual, and probabilistic inference beyond given observations.
   - *Patterns*: Chain-of-Thought Auditor (8), Counterfactual Reasoner (9), Analogical Mapping (10), Constraint-Satisfaction (11), Causal Graph Builder (12), Symbolic-Neural Bridge (13), Probabilistic Belief Updater (14), Self-Consistency Voter (15).
3. **Planning (Patterns 16–22)**: Decomposes goals into bounded, executable operational sequences.
   - *Patterns*: Hierarchical Decomposer (16), ReAct Loop (17), Tree-of-Thought Explorer (18), Plan-Then-Execute (19), Adaptive Replanner (20), Resource-Aware Scheduler (21), Backward Goal-Regression (22).
4. **Memory (Patterns 23–29)**: Persistence across time, context reshaping, and decay.
   - *Patterns*: Episodic Buffer (23), Semantic Memory Curator (24), Working-Memory Manager (25), Forgetting-Policy (26), Memory-of-Self (27), Vector-Store Curator (28), Persistent Identity (29).
5. **Tool Use (Patterns 30–37)**: Interacting with external environments and digital artifacts.
   - *Patterns*: Tool Selector (30), API-Schema Adapter (31), Code-Execution Sandbox (32), Shell-Operator (33), Browser-Driver (34), DB Query Synthesizer (35), File-System Curator (36), Side-Effect Auditor (37).
6. **Coordination (Patterns 38–45)**: Multi-agent synchronization and human governance.
   - *Patterns*: Router/Dispatcher (38), Debate Moderator (39), Consensus-Builder (40), Pipeline Orchestrator (41), Human-in-the-Loop Liaison (42), Negotiation (43), Auctioneer (44), Supervisor-Worker (45).
7. **Learning (Patterns 46–52)**: Performance optimization through feedback and trajectory distillation.
   - *Patterns*: Feedback Loop (46), Reflection (47), Skill-Library Builder (48), Curriculum Designer (49), Few-Shot Prompt Tuner (50), Distillation (51), Active Learner (52).
8. **Alignment (Patterns 53–60)**: Safety, constitutional rule checking, provenance, and corrigibility.
   - *Patterns*: Constitution-Bound (53), Refusal Calibrator (54), Provenance Tracker (55), Red-Team Auditor (56), Privacy-Preserving (57), Explainer (58), Drift Detector (59), Off-Switch-Compatible (60).

## Architectural Invariants & Rules
1. **Capability Contract Invariant**: Every scoped agent must declare a 1-page capability contract table defining exactly which patterns it employs across each of the 8 capabilities.
2. **Multi-Agent Skepticism**: Multi-agent coordination patterns (38–45) must never be selected unless empirical benchmarks demonstrate that a single well-prompted agent is insufficient.
