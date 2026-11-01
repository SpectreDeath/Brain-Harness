# Elephant & Goldfish Bifurcated Cognitive Context Architecture

## Core Architectural Axiom
Unstructured, conversational AI code generation suffers from systemic **hallucination cascades** and **context pollution**. When a single LLM thread interviews the developer, drafts the specification, and generates code, the conversational session accumulates speculative hypotheses, conversational bias, and developer fatigue. The model validates its own faulty assumptions instead of detecting errors.

EGM solves this by bifurcating the agent architecture into two distinct, asymmetric cognitive contexts:

```
┌───────────────────────────────────────────────┐
│              THE ELEPHANT                     │
│  - Deep project context & system history      │
│  - User interviews, goals & trade-offs        │
│  - Iterative drafting of specifications       │
│  - Resolves findings and applies patches      │
└───────────────────────┬───────────────────────┘
                        │
       Target Document  │ (Zero chat history)
                        ▼
┌───────────────────────────────────────────────┐
│              THE GOLDFISH                     │
│  - Isolated, fresh-context subagent instances │
│  - Reads ONLY target doc & referenced code    │
│  - Antagonistic evaluation against rubrics    │
│  - Emits normalized blocker/major/nit reports │
└───────────────────────────────────────────────┘
```

## Foundational Mandates & Invariants
1. **Zero-Context Review Invariant**: A Goldfish reviewer must never inherit the parent agent's conversation history. If the harness cannot spawn isolated subagents, in-thread review is prohibited.
2. **Critique-First & Anti-Sycophancy Mandate**: Reviewers are forbidden from outputting flattery ("brilliant idea", "great design") or polite apologies. Subagents must lead directly with technical objections, missing edge cases, and failure modes.
3. **Artifact-First Handshake**: Review feedback is offloaded to markdown artifacts rather than dumped into the conversation window.
