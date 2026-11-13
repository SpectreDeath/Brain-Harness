# Bot HQ: In-Band MCP Tool Approval Gate

## Protocol
1. **Read-Only Fast Path**: Read-only tools execute immediately without human interruption.
2. **Blocking Write Gate**: Write/mutating tools post an interactive approval card into the conversation and suspend the MCP call until the user chooses `Allow`, `Always allow` (persisting a per-tool policy), or `Don't allow` (returning a refusal instructing the agent not to retry).
3. **Supersession**: A new user message or timeout closes the card and returns `skipped`.
