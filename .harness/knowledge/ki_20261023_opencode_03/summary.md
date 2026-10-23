# Persistent PTY Multiplexing Daemon for Long-Running Agents

## Context
When coding agents execute interactive commands, build processes, or background test watchers, standard subprocess execution pipes stdout directly to the active client session. If the user closes their terminal or reconnects, child processes receive SIGHUP or orphaned pipe errors, destroying in-progress work.

## Distilled Learning
Decouple pseudo-terminal (PTY) lifecycle from the user interface:
- Host a persistent PTY daemon (`packages/core/src/persistent-pty`) inside the background server process (`opencode service`).
- Connect terminals via persistent PTY sessions with circular ring-buffer histories and session UUIDs.
- Clients attach as non-exclusive stream observers: disconnecting from the TUI or web interface leaves the background compilation or test runner uninterrupted.
- Re-attaching to a session immediately replays recent terminal state from the buffer.

## Triggers & Seam Choices
- **Trigger**: Agents executing long-running builds, dev servers, or background tasks across transient UI sessions.
- **Seam Choice**: Isolate process execution into a headless daemon service with WebSocket stream subscriptions rather than in-process direct shell invocation.
