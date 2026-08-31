# Sandbox Hook Write-Deny Security Boundary

## Context
When agents run terminal commands, build scripts, or arbitrary code inside a workspace, a compromised prompt injection or malicious subprocess could attempt to overwrite hook configuration files (e.g. `~/.grok/hooks.json`, `.grok/hooks.json`, `.agents/rules/`), disabling safety gates, prompt block decisions, or audit logging.

## Distilled Learning
Implement automatic write-deny enforcement for all hook definition sources within the sandbox profile resolver:
- **Write-Denied, Read-Allowed**: Hook sources are marked as readable (so the host can parse and execute them) but strictly write-denied in the kernel sandbox capability set (`CapabilitySet` via `nono` or OS ACLs).
- **Profile-Level Automatic Resolution**: Regardless of whether a profile is `workspace`, `devbox`, or custom, `profile_hook_write_deny` queries active global and project-level hook locations and injects them into the deny set.
- **Kernel-Enforced System Calls**: Any attempt by a child process or tool to write, truncate, delete, or rename hook configuration files fails at the OS kernel boundary with an immediate `EPERM`/permission error.

## Triggers & Seam Choices
- **Trigger**: Launching untrusted tools, bash execution, compiler runners, or sandboxed external plugins.
- **Seam Choice**: Inject within sandbox profile resolution (`harness.plugins.sandbox` or `xai-grok-sandbox`) before launching subprocess transports.
