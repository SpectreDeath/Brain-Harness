# PowerShell Qualified Ref Splatting Defense for CLI Agents

## Context
Extracted during autobiographical self-reflection (/harness-reflector) across execution trajectories and visual briefs.

## Distilled Learning
In Windows PowerShell environments, passing an unquoted ref such as @s8f3k2p9:e1 invokes PowerShell argument splatting, which interprets the token as an in-scope parameter variable rather than a literal string argument. AI agents operating desktop automation CLIs must enforce qualified ref validation (rejecting bare refs like @e8) and format references with explicit single quotes ('@s8f3k2p9:e1'). This defense is enforced in DesktopRefToken.powershell_quoted() and verified in test contracts.

## Triggers & Seam Choices
- **Trigger**: AI coding agent tool dispatch, subprocess runner construction, or architecture boundary enforcement.
- **Seam Choice**: Integration via Brain Harness IoC container, tool execution runners, and CI linting pipelines.
