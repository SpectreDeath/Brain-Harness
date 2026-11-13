# Waza: Deterministic Trajectory, Tool Constraint & Skill Invocation Graders

## Grader Families
1. **Action Sequence Grader**: Compares `Session.ToolsUsed` against `expected_actions` under `exact_match`, `in_order_match`, or `any_order_match`, outputting F1 alongside pass/fail.
2. **Tool Constraint Grader**: Validates at least one of `expect_tools`, `reject_tools`, or `allow_only` and compiles case-insensitive patterns (`tool`, `command_pattern`, `skill_pattern`, `path_pattern`).
3. **Skill Invocation Grader**: Checks actual `SkillInvocations` against `required_skills`, `forbidden_skills`, and `allow_extra` (default `true`).
