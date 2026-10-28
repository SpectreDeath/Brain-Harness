# PyRIT AI Red Teaming & Harm Evaluation Plugin

Provides automated adversarial evaluations for AI agent loops, prompts, and tool interfaces using Microsoft PyRIT patterns with subprocess virtual environment isolation.

## Overview

The `domain.pyrit_red_teaming` plugin integrates Microsoft PyRIT's AI red teaming engine into Brain Harness with full `subprocess` sandbox isolation and typed IoC registration (`PYRIT_SCANNER_SERVICE_KEY`).

### Key Capabilities

1. **`orchestrate_crescendo_attack`**: Multi-turn conversational attack simulator executing crescendo progression to test safety boundaries incrementally.
2. **`apply_prompt_converters`**: Obfuscation and encoding converters (Base64, ROT13, Leetspeak, Unicode confusables, string joining, PigLatin translation).
3. **`score_risk_and_harm`**: Multi-category safety evaluation engine evaluating toxicity, PII leaks, violence, and jailbreak probability.
4. **`generate_jailbreak_tree`**: Tree-of-Attacks-with-Pruning (TAP) attack graph generator synthesizing structured nodes and Mermaid visualization.
5. **`audit_attack_trajectory`**: Multi-turn conversation auditor computing cumulative risk and flagging policy violations.

## Service Key & Isolation

- **Service Key**: `PYRIT_SCANNER_SERVICE_KEY` (`service.pyrit_scanner`)
- **Isolation Mode**: `IsolationMode.SUBPROCESS`
- **Category**: `security_and_forensics`
- **Trust Level**: Trusted external archetype

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `redteam_fuzz_prompt` | `(prompt, intensity=3)` | Fuzz prompt with adversarial mutations to detect leakage |
| `redteam_jailbreak_audit` | `(target_type='agent_loop', technique='crescendo')` | Execute structured jailbreak evaluation |
| `redteam_tool_tampering_check` | `(tool_name, payload)` | Check whether untrusted tool outputs can hijack agent execution flow |
| `redteam_scorecard_report` | `(session_id='default')` | Generate risk classification and vulnerability scorecard from recent scan |
| `orchestrate_crescendo_attack` | `(objective, max_turns, adversarial_personas, temperature)` | Execute multi-turn crescendo red-teaming dialogue |
| `apply_prompt_converters` | `(prompt, converters, converter_args)` | Apply adversarial obfuscation, encoding, and character perturbation converters |
| `score_risk_and_harm` | `(prompt, response, harm_categories, scorer_type)` | Evaluate safety violations, toxicity, hate, violence, PII leak, and jailbreak probability |
| `generate_jailbreak_tree` | `(target_system, attack_goal, branching_factor, max_depth)` | Construct Tree-of-Attacks-with-Pruning (TAP) exploration graph |
| `audit_attack_trajectory` | `(conversation_id, trace_events)` | Audit multi-turn red teaming conversation logs, calculating cumulative risk |
