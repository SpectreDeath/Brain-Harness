# Layered Zero-Fork Skill Configuration & AST Security Scoring Engine

**ID:** `ki_self_20260905_07`  
**Category:** `system_architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `.agents/skills/agent-skill-sdlc/scripts/resolve_config.py#L48-L100`, `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py#L182-L310`, `.agents/skills/agent-skill-sdlc/config.default.yaml`, `.agents/skills/agent-skill-sdlc/references/security-and-skillspector.md`, `scratch/test_skillspector_adversarial.py`

## Executive Summary
Deploying autonomous agent skills into production requires solving two opposing tensions:
1. **Configurability Without Forking**: Upstream skills require site-specific adaptations (custom line budgets, extra commit types, additional tool clients). Modifying upstream skill files creates fragmented, unmaintainable forks.
2. **Deterministic Unattended Security**: Community skills run arbitrary scripts. Leaving security verification as prose in documentation exposes the host to supply-chain tampering and dangerous operations.

## Architectural Solutions & Invariants

### 1. 3-Tier Layered Configuration Precedence
- **Tier 1 (Project Override)**: `<project_root>/.agents/skills.config.yaml`
- **Tier 2 (Skill Default)**: `<skill_dir>/config.default.yaml`
- **Tier 3 (Hardcoded Base)**: In-code conservative fallback dictionary.
- **Additive Lists Pattern**: Overrides targeting collections use the `extra_*` prefix (e.g. `extra_supported_clients`, `extra_allowed_types`) to append items without discarding base values.
- **Config-Driven Tool Seam**: Validation and execution engines dynamically invoke `resolve_for_skill(skill_dir)`, eliminating manual CLI flag dispatch.

### 2. SkillSpector 70-Pattern AST Security Scanner
- Evaluates script syntax trees across four weighted risk dimensions:
  1. **Dangerous System Calls (30% weight)**: `eval()`, `exec()`, `os.system()`, `subprocess` with `shell=True`, `ctypes`.
  2. **Network & Exfiltration (30% weight)**: Raw sockets, unauthorized outbound HTTP POST/PUT dispatches.
  3. **Filesystem Mutation (20% weight)**: Destructive root or home directory deletions (`rm -rf /`).
  4. **Environment & Credentials (20% weight)**: Direct reads of sensitive tokens (`AWS_SECRET_ACCESS_KEY`, `*_KEY`, `*_TOKEN`).
- Calculates an aggregate $0 - 100$ score and enforces risk bands:
  - `SAFE` ($\le 20$): Automatic clearance.
  - `CAUTION` ($21 - 50$): Manual approval gate required.
  - `HIGH` ($51 - 80$): Prohibited in production.
  - `CRITICAL` ($81 - 100$): Immediate quarantine.
