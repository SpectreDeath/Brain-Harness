# Mantis Security Review Plugin (`plugin.mantis_security_review`)

## Overview
`plugin.mantis_security_review` integrates Google's Mantis autonomous security review and triage capabilities into the Brain Harness IoC container. It provides automated VCS history vulnerability extraction, directory architecture mapping, defensive review planning, deep-dive static AST code audits, multi-pass deduplication ladders, false-positive elimination gates, production viability filtering, multi-stage exploit chaining, and executive report compilation.

## Service Key
- **Key**: `service.mantis_security_review`
- **Type**: `ServiceKey[MantisSecurityReviewService]`

## Exported Tools
- `mantis_history_scan`: Mine Git history for prior security patches and vulnerability commit trajectories.
- `mantis_directory_summary`: Produce hierarchical directory maps highlighting security assets.
- `mantis_plan_review`: Formulate targeted review roadmaps targeting high-risk CWEs.
- `mantis_research_audit`: Deep-dive static source code audit detecting code execution, command injection, hardcoded secrets, and SQL flaws.
- `mantis_dedupe_ladder`: Multi-pass syntactic and AST signature deduplication ladder.
- `mantis_review_gate`: Independent validation gate verifying findings against actual source context.
- `mantis_critic_filter`: Assess production viability, dropping assertion traps and debug-only flaws.
- `mantis_chain_exploits`: Link individual vulnerabilities into compound exploit chains.
- `mantis_calibrate_risk`: Calculate multi-axis CVSS/CWE risk ratings based on asset criticality.
- `mantis_generate_report`: Compile executive stakeholder review packets.

## Storage Contract (Open Knowledge Format v0.2)
Includes SQLite persistence schema for findings, OKF v0.2 concept notes, and execution logs using deterministic stable signature hashing (`compute_stable_signature`).


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `mantis_history_scan` | `(repo_path, max_commits, pattern_filter)` | Mine VCS repository history for historical vulnerabilities, security fix patterns, and commit trajectories |
| `mantis_directory_summary` | `(dir_path, recursive)` | Generate hierarchical security-focused directory map and asset overview |
| `mantis_plan_review` | `(threat_model, target_paths, focus_cwe)` | Formulate targeted defensive security review plan from threat model and codebase boundaries |
| `mantis_research_audit` | `(target_file, code_content, focus_cwe)` | Deep-dive static analysis audit of target source code for vulnerability patterns |
| `mantis_dedupe_ladder` | `(findings, mode)` | Consolidate raw security findings through multi-pass syntactic, AST, and semantic deduplication |
| `mantis_review_gate` | `(finding, source_content, strictness)` | Independent validation gate evaluating findings against source semantics to eliminate false positives |
| `mantis_critic_filter` | `(finding, check_release_assertions)` | Assess production viability of findings, filtering out debug-only features and assertion traps |
| `mantis_chain_exploits` | `(findings, target_objective)` | Analyze individual security findings to construct multi-stage compound exploit chains |
| `mantis_calibrate_risk` | `(findings, asset_criticality)` | Calculate multi-axis risk ratings based on threat intel, impact, criticality, and exploitability |
| `mantis_generate_report` | `(findings, exploit_chains, executive_summary)` | Compile stakeholder-facing security review packet from confirmed findings and exploit chains |
