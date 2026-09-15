# Claude Code Bridge Plugin

A sandboxed Harness plugin providing pre-tool bash command guardrails and prompt compaction derived from Anthropic's Claude Code CLI.

## Capabilities
- **Bash Guardrails**: Evaluates shell commands before execution against destructive patterns (`git push --force`, `git reset --hard`, recursive deletions).
- **Prompt Compaction**: Progressive middle-out line folding and deduplication to bound prompt context bloat.

## Service Key
- `service.claude_code_bridge` (`CLAUDE_CODE_BRIDGE_KEY`)
