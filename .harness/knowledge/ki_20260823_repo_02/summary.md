# Deterministic AST-Level Command Authorization via execpolicy

## Problem
Balancing usability and security in agent shell execution: prompting users for every command causes fatigue and reduces automation speed, but naive regex matching fails against shell metacharacters, subshells, aliases, or chained invocations (`&&`, `||`, `;`, `|`).

## Solution
Implement a dedicated execution policy engine (`execpolicy`) that:
1. Deconstructs command strings into AST tokens (`PatternToken`, `PrefixPattern`).
2. Evaluates prefix rules (`PrefixRule`) against exact argument boundaries.
3. Outputs structured decision states (`Decision::Allow`, `Decision::Prompt`, `Decision::Deny`, `Decision::Amend`).
4. Supports policy amendment (`blocking_append_allow_prefix_rule`) allowing users to permanently approve safe command families.

## Operational Guideline
- Never evaluate command authorization on raw unparsed strings.
- Tokenize and canonicalize commands before evaluation.
- Separate binary identification from argument pattern matching.

## Provenance
- Source repository: `D:/GitHub/cloned/codex-main/codex-main`
- Primary files: `codex-rs/execpolicy/src/lib.rs#L1-L33`, `codex-rs/execpolicy/src/rule.rs`, `codex-rs/execpolicy/src/policy.rs`
