# Agent Harness Architect Plugin

`plugin.agent_harness_architect` is an in-process, trusted agent orchestration plugin elevating the `agent-harness-architect` skill into an authoritative micro-kernel IoC service.

## Architecture

- **IoC Service Key**: `AGENT_HARNESS_ARCHITECT_SERVICE_KEY` (`service.agent_harness_architect`)
- **Protocol**: `AgentHarnessArchitectService`
- **Category**: `agent_orchestration`
- **Isolation**: `in_process`

## Tool Entrypoints

1. `harness_audit(target)`: Run 5-part architecture and 4-layer stack boundary audit.
2. `harness_score(config_path)`: Evaluate 4 reliability mechanisms across Level 0 to Level 2.
3. `harness_classify_bet(bottleneck)`: Classify team bottleneck to one of four architectural bets (`dsh`, `claude-code`, `hermes`, `pi`).
4. `harness_visual_brief(target, output_path)`: Generate interactive HTML review report with Mermaid diagrams.
