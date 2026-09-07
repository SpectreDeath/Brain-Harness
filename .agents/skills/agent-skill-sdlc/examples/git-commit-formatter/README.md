# Example: Configurable Git Commit Formatter (Zero-Fork Architecture)

This case study demonstrates Obum's **Layered Configuration Pattern**, showing how a development team customized a shared, upstream Git commit formatter skill without creating a fragmented fork.

---

## The Problem: The Forking Trap

A team adopted an upstream community skill: `.agents/skills/git-commit-formatter/`.
The upstream skill enforced strict Conventional Commits with standard types:
```yaml
# config.default.yaml (Upstream)
allowed_types:
  - feat
  - fix
  - docs
  - style
  - refactor
  - test
  - chore
max_subject_length: 50
require_scope: false
```

The team needed two modifications for their micro-frontend repository:
1. Allow custom commit types: `feat-ui` and `experiment`.
2. Expand `max_subject_length` to `72` characters.

**The Anti-Pattern**: Forking the skill repository or directly editing `config.default.yaml`. When upstream released bug fixes or security patches, the team was stranded with merge conflicts.

---

## The Solution: Project-Level Override (`.agents/skills.config.yaml`)

Instead of modifying the skill directory, the team created a project-level configuration file in their repository root:

```yaml
# .agents/skills.config.yaml (Project Root)
git-commit-formatter:
  max_subject_length: 72
  extra_allowed_types:
    - feat-ui
    - experiment
```

Notice the use of the `extra_*` additive prefix:
- Standard `allowed_types` are retained.
- Custom types are cleanly appended.
- Scalar settings (`max_subject_length`) are cleanly overridden.

---

## Runtime Execution & Resolution Trace

When the agent invokes the commit formatting workflow, it runs `resolve_config.py`:

```bash
$ python scripts/resolve_config.py git-commit-formatter --print-sources
```

### Resolution Output:
```text
=== Resolved Configuration for 'git-commit-formatter' ===
  allowed_types: ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'feat-ui', 'experiment']  [project override (skills.config.yaml) (additive via extra_allowed_types)]
  max_subject_length: 72  [project override (skills.config.yaml)]
  require_scope: False  [skill default (config.default.yaml)]
```

### Result:
- Zero files in `.agents/skills/git-commit-formatter/` were touched.
- Upstream updates can be pulled at any time with `git merge` or submodule updates.
- The project enforces custom team conventions deterministically.
