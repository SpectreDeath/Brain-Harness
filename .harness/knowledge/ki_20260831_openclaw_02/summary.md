# Trusted Gateway Control Plane & Deterministic Sandboxed Execution

## Context
When an AI assistant operates simultaneously across interactive web dashboards, TUIs, CLI invocations, mobile companion apps, and public chat channels (Telegram, WhatsApp, Slack, Discord), direct execution of agent actions risks catastrophic compromise if inbound channel prompts contain prompt injection or malicious command payloads.

## Distilled Learning
Enforce a three-tier execution hierarchy:
1. **Unified WebSocket RPC Control Plane**:
   - All clients and channel adapters connect as clients to a local or remote Gateway via typed WebSocket JSON-RPC.
   - Device pairing and cryptographic secret references ensure only authenticated channels can initiate agent sessions.
2. **Deterministic Execution Approvals**:
   - High-risk operations (terminal execution, filesystem mutation outside workspace, network access) generate explicit approval requests.
   - Approvals are validated through protocol guards (`validateApprovalGetResult`, `validateApprovalResolveResult`) before execution proceeds.
3. **Subprocess / Container Sandboxing**:
   - Host runs the Gateway and ReAct loop, but foreign plugin tools execute inside sandboxed runner environments with strict network policy gates (`packages/net-policy`).

## Triggers & Seam Choices
- **Trigger**: Multi-channel message ingress, remote agent deployment, or untrusted external plugin execution.
- **Seam Choice**: Register `OpenClawGatewayService` (`service.openclaw.gateway`) as a bridge client connecting Harness agents to external gateways.
