# Differential Terminal Rendering & Synchronized Output Protocol for Agent TUIs

## Architectural Summary
`@moonshot-ai/pi-tui` provides flicker-free terminal UI rendering by coupling synchronized output protocol (CSI 2026) with 3-strategy differential line rendering.

## Operational Guidelines
1. **Synchronized Output:** Bracket all frame updates with `\x1b[?2026h` (enter synchronized update) and `\x1b[?2026l` (render synchronized update).
2. **Virtual Terminal Diffing:** Maintain shadow buffer state to send delta line rewrites rather than full-screen clears.
3. **Alt-Screen Isolation:** Use separate alternate screen buffers for full-screen modals, search prompts, and interactive diff viewers.
