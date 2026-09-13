# Interactive Tool Approval Middleware & Security Sandboxing

## Context
Autonomous agents executing terminal commands and modifying files can inadvertently trigger destructive commands (e.g. `rm -rf`, `git reset --hard`, unredacted secrets in curl).

## Distilled Learning
Implement a two-stage interactive tool approval middleware:
- Intercept tool calls prior to execution in the agent step loop.
- Evaluate command against an explicit risk taxonomy: Read-Only (auto-approve), Standard Mutation (auto-approve with git checkpoint), Dangerous/Destructive (require interactive confirmation).
- Pattern match commands using regex rules (e.g. block destructive git flags, external network curls with sensitive tokens).
- Maintain an in-memory session whitelist so that repetitive benign commands (e.g. `npm test`, `pytest`) can be approved once per session.

## Triggers & Seam Choices
- **Trigger**: Shell execution (`run_command`), file write tools, and git credential injection.
- **Seam Choice**: Integrate in `harness.agent.step_engine` (Rule 8 & 15) inside context transaction boundaries.
