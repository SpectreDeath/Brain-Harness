# Security & Forensics Domain Architecture

The Security & Forensics domain governs threat modeling, vulnerability detection, structured log pattern extraction, port auditing, and execution trajectory verification.

---

## Domain Scope & Boundaries

This domain enforces security boundaries, secret protection, and post-execution forensic audits:
- **In Scope**: Pre-commit SAST scanning (DevSkim), Git credential safety, packet capture dissection, TCP port analysis, and execution trajectory verification.
- **Out of Scope**: Destructive penetration exploits, unauthorized network attacks, or unauthenticated Wi-Fi cracking.

---

## Ubiquitous Language & Core Terminology

- **Threat Modeler**: A structured risk assessment pipeline that enumerates system attack surfaces and formulates defensive mitigation trees using STRIDE. (*Avoid*: Risk analyzer, security checker)
- **Security Scanner**: An automated audit tool that scans codebases for hardcoded credentials, known dependency vulnerabilities, and unsafe syscalls. (*Avoid*: Vulnerability finder, secret detector)
- **Trajectory Auditor**: An epistemic verification engine that replays agent execution steps to assert that no safety invariants or file boundaries were violated. (*Avoid*: Action logger, history checker, trace viewer)
- **Log Forensics**: A pattern extraction parser that isolates anomalies, stack traces, and failure cascades across high-volume log streams. (*Avoid*: Log searcher, grep tool)

---

## Architectural Invariants & Patterns

- **Secure Credential Injection (Rule 15)**: Authenticated operations never use shell variable interpolation; credentials use isolated runner scripts, standard input pipes, or custom git helpers.
- **Forensic Extension Mock Isolation (Rule 28)**: Security and forensic extensions must provide self-contained contract verification tests using mocked DAL/Nexus adapters before integration.
- **Pre-Commit Interception Left-Shift**: Security verification runs pre-commit via Git hooks before pull requests to prevent credential leaks and high-severity SAST warnings.

---

## Co-Located Plugins & Micro-Kernel Services

- **Pre-Commit Security Guard Service**: [`src/harness/services/pre_commit_security_guard.py`](../../../src/harness/services/pre_commit_security_guard.py) providing `PRE_COMMIT_SECURITY_GUARD_KEY`.
- **Network Forensics Service**: [`src/harness/services/network_forensics.py`](../../../src/harness/services/network_forensics.py) providing `NETWORK_FORENSICS_SERVICE_KEY`.
- **Arch Linter Service**: [`src/harness/services/arch_linter.py`](../../../src/harness/services/arch_linter.py) providing `ARCH_LINTER_KEY`.

---

## Associated Agent Skills

- [`pre-commit-security-guard`](../../../.agents/skills/pre-commit-security-guard/SKILL.md): Intercepts vulnerabilities and secrets before PRs using Git hooks and DevSkim.
- [`ethical-hacker-networking`](../../../.agents/skills/ethical-hacker-networking/SKILL.md): Executes protocol-level packet capture dissection and port evaluation.
- [`git-guardrails-claude-code`](file:///C:/Users/spectre/.gemini/config/plugins/pocock-skills/skills/git-guardrails-claude-code/SKILL.md): Blocks destructive git operations before execution.
