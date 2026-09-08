## CHANGELOG Absence

### Discovery
Brain Harness has no CHANGELOG.md or machine-parseable release notes.
All architectural evolution is encoded only in git log (46 commits), AGENTS.md
(44 rules), and the .harness/knowledge/ KI vault.

### Risk
- Difficult for new contributors to understand breaking changes
- AI agents summarizing the codebase cannot query version history efficiently
- Rule progression has no timestamped changelog entry

### Recommendation
1. Adopt Conventional Commits (already ~90% compliant) consistently
2. Add CHANGELOG.md maintained by git-cliff or equivalent automated tool
3. Tag semantic versions at major architectural milestones
   (e.g., v0.1.0 at initial scaffold, v0.2.0 at cycle 10 arch deepening)
