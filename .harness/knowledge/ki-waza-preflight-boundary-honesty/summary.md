# Waza: Static Preflight Boundary Honesty vs Preventive Runtime Enforcement

## Key Invariant
- **No False Static Security Proof (`internal/preflight/boundary.go#L11-L43`)**:
  - `boundary.post_run`: Marks referenced boundary graders `Unresolved` because post-run observation does not prevent runtime side effects.
  - `boundary.requested_policy`: Marks `.agent.md` frontmatter `tools` (`requested-allowlist` or `requested-deny-all`) `Unresolved` until actual runtime policy denials and resulting-state evidence are inspected.
