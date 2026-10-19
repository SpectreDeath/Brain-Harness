---
name: ai-red-teaming-architect
description: Execute automated GenAI adversarial red-teaming, jailbreak audits, and vulnerability scorecards using Microsoft PyRIT patterns with subprocess isolation. Do not use for unauthorized external network attacks or generic penetration testing.
---

# AI Red-Teaming Architect

The AI Red-Teaming Architect governs adversarial evaluation of LLM agent loops, system prompts, and tool interfaces using Microsoft PyRIT (Python Risk Identification Tool) methodologies. It tests model boundaries against multi-turn jailbreaks, prompt injection, and tool hijacking within sandboxed subprocess environments.

## Operational Workflow

1. **Target Specification**: Select and configure evaluation targets (`agent_loop`, `system_prompt`, `tool_interface`, `mcp_endpoint`).
2. **Attack Vector Configuration**: Formulate structured attack vectors selecting techniques (`crescendo`, `roleplay_jailbreak`, `encoding_fuzz`, `tool_hijack`) and intensity level (1–5).
3. **Subprocess Isolation**: Dispatch adversarial probes via lazy virtual environment execution with standard stream drainage and loopback preservation.
4. **Vulnerability Scorecarding**: Generate objective scorecards measuring attack success rate (ASR), leaked tokens, boundary bypasses, and security recommendations.

## Anti-Patterns

- **Unauthenticated API Fuzzing** — Sending adversarial payloads directly to live external production APIs without sandboxed harness boundaries.
- **In-Process Dependency Pollution** — Installing heavy red-teaming frameworks directly into core micro-kernel environments rather than lazy subprocess venvs.
- **Unchecked Tool Side-Effects** — Executing adversarial payloads against unmocked file write or shell execution tools.

## Diagnostic Verification

Verify red-teaming scans using `harness.services.pyrit_scanner.DefaultPyritScannerService` or the CLI plugin tools `redteam_fuzz_prompt` and `redteam_jailbreak_audit`.
