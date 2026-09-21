# Responsible AI Prototyping & Web App Governance

**ID:** `ki-responsible-ai-prototyping`
**Source:** *"How to Use Lovable Responsibly"* by Eva J Patel (*freeCodeCamp.org*, September 18, 2026)

## Summary
AI-powered app generation engines (such as Lovable, v0, Bolt, Cursor, Replit Agent) dramatically accelerate application prototyping from natural language specifications. However, unchecked generation introduces structural failure modes: client-side security illusions, bloated dependency trees, unvalidated inputs, data leaks, and dark patterns.

This knowledge item records the ground-truth heuristics, test contracts, and mental models synthesized from Eva J Patel's literature:

1. **Data Minimization & Blast Radius Principle**: Never add data fields out of speculative optimism. For every field or table, evaluate necessity and compromise blast radius. Strip unnecessary PII before schema generation.
2. **Responsible Prompting Contract**: Embed negative constraints, security requirements (server-side authz, input sanitization), accessibility (WCAG AA contrast, keyboard navigation), and post-generation transparency contracts (file changes, stored data, external dependencies, residual risks) directly into prompts.
3. **Bipartite Authentication vs. Authorization**: Authentication answers *"Who are you?"*; authorization answers *"What are you allowed to do?"*. Hiding UI navigation or action buttons is not security. Server-side queries and mutations must enforce permissions. All prototypes must pass 5 negative test cases (logged-out access, role escalation, horizontal IDOR, missing tokens, and back-button cache leakage).
4. **Dependency Pruning ("Digital Souvenirs")**: AI generation frequently imports heavy packages for trivial UI features. Maintainers must interrogate each dependency and favor native browser standards.
5. **Operational Honesty & The Golden Rule**: Always review AI-generated software from the perspective of an affected human user. Accurately designate prototypes as experimental ("Prototype" / "Demo") until full formal security, privacy, and error handling audits are completed.
