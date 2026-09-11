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
