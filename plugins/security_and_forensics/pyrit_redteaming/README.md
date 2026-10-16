# PyRIT AI Red Teaming & Harm Evaluation Plugin

Forged directly from upstream **Microsoft PyRIT** (`D:\GitHub\cloned\PyRIT-main\PyRIT-main`).

## Overview

The `domain.pyrit_redteaming` plugin integrates Microsoft PyRIT's AI red teaming engine into Brain Harness with full `subprocess` sandbox isolation.

### Key Capabilities

1. **`orchestrate_crescendo_attack`**: Multi-turn conversational attack simulator executing crescendo progression to test safety boundaries incrementally.
2. **`apply_prompt_converters`**: Obfuscation and encoding converters (Base64, ROT13, Leetspeak, Unicode confusables, string joining, PigLatin translation).
3. **`score_risk_and_harm`**: Multi-category safety evaluation engine evaluating toxicity, PII leaks, violence, and jailbreak probability.
4. **`generate_jailbreak_tree`**: Tree-of-Attacks-with-Pruning (TAP) attack graph generator synthesizing structured nodes and Mermaid visualization.
5. **`audit_attack_trajectory`**: Multi-turn conversation auditor computing cumulative risk and flagging policy violations.

## Isolation Mode

- **Mode**: `IsolationMode.SUBPROCESS`
- **Category**: `security_and_forensics`
- **Trust Level**: Trusted external archetype


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `orchestrate_crescendo_attack` | `(objective, max_turns, adversarial_personas, temperature)` | Execute multi-turn crescendo red-teaming dialogue simulating incremental boundary testing |
| `apply_prompt_converters` | `(prompt, converters, converter_args)` | Apply adversarial obfuscation, encoding, and character perturbation converters to a prompt |
| `score_risk_and_harm` | `(prompt, response, harm_categories, scorer_type)` | Evaluate safety violations, toxicity, hate, violence, PII leak, and jailbreak success probability |
| `generate_jailbreak_tree` | `(target_system, attack_goal, branching_factor, max_depth)` | Construct Tree-of-Attacks-with-Pruning (TAP) exploration graph with Mermaid diagram synthesis |
| `audit_attack_trajectory` | `(conversation_id, trace_events)` | Audit multi-turn red teaming conversation logs, calculating cumulative risk exposure and policy violations |
