# Evidence Tri-State & Capture-Proof Ref Identity Resolution

## Context
Extracted during automated repository triad ingestion from `D:\GitHub\cloned\agent-desktop`.

## Distilled Learning
Operating system accessibility trees exhibit partial reads, timing glitches, and identical twins. agent-desktop resolves this by enforcing a non-collapsing Evidence Tri-State (Known, Absent, Unknown) and whole-window CaptureProof. When an element is captured, its uniqueness is verified across the window under a 16 field-mask bucket index. If unread_bits exist (a property timed out or failed to read), uniqueness is withheld, preventing false-positive ref actions and eliminating non-deterministic click delivery.

## Triggers & Seam Choices
- **Trigger**: Desktop GUI automation, native accessibility tree walks, ref resolution, or agent ReAct tool retry decisions.
- **Seam Choice**: Integration via Brain Harness IoC container (`AGENT_DESKTOP_KEY`), `agent-desktop-operator` skill, and `plugin.agent_desktop`.
