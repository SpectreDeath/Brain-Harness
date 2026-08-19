# Quick Start Guide: `mattpocock-skills` (v1.2.3)

> Matt Pocock's agent skills for real engineering — grilling, spec/ticket flows, TDD, code review, domain modelling and more. Plug-and-play, not vibe coding.

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`ask-matt`**: Ask which skill or flow fits your situation. A router over the skills in this repo.
- **`code-review`**: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them 
- **`codebase-design`**: Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
- **`diagnosing-bugs`**: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
- **`domain-modeling`**: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
- **`grill-with-docs`**: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
- **`implement`**: Implement a piece of work based on a spec or set of tickets.
- **`improve-codebase-architecture`**: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('mattpocock-skills.ask-matt', {'task': '<task>', 'context': '<context>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider mattpocock-skills
harness plugin enable mattpocock-skills
```

## ⚡ Available Entrypoints & Skills
- **`ask-matt(task: string, context: string)`**
  Ask which skill or flow fits your situation. A router over the skills in this repo.
- **`code-review(task: string, context: string)`**
  Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them 
- **`codebase-design(task: string, context: string)`**
  Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
- **`diagnosing-bugs(task: string, context: string)`**
  Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
- **`domain-modeling(task: string, context: string)`**
  Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
- **`grill-with-docs(task: string, context: string)`**
  A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
- **`implement(task: string, context: string)`**
  Implement a piece of work based on a spec or set of tickets.
- **`improve-codebase-architecture(task: string, context: string)`**
  Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
- **`prototype(task: string, context: string)`**
  Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
- **`research(task: string, context: string)`**
  Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
- **`resolving-merge-conflicts(task: string, context: string)`**
  Use when you need to resolve an in-progress git merge/rebase conflict.
- **`setup-matt-pocock-skills(task: string, context: string)`**
  Configure this repo for the engineering skills — set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills.
- **`tdd(task: string, context: string)`**
  Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
- **`to-spec(task: string, context: string)`**
  Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
- **`to-tickets(task: string, context: string)`**
  Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker — edges as text in one file per ticket locally, or native blocking links on a real tracker.
- **`triage(task: string, context: string)`**
  Move issues and external PRs through a state machine of triage roles — categorise, verify, grill if needed, and write agent-ready briefs.
- **`wayfinder(task: string, context: string)`**
  Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
- **`wizard(task: string, context: string)`**
  Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or running a one-off migration or cutover. Don't invoke this for steps the agent can pe
- **`claude-handoff(task: string, context: string)`**
  Hand the current conversation off to a fresh background agent that picks up the work immediately.
- **`loop-me(task: string, context: string)`**
  Grill me about specs for the workflows I want to build, within this workspace.
- **`setup-ts-deep-modules(task: string, context: string)`**
  Wire dependency-cruiser into a TypeScript repo so each package is a deep module — implementation hidden in subfolders, reachable only through its entry-point files. User-invoked.
- **`writing-beats(task: string, context: string)`**
  Writing, exploit — assemble raw material into a journey of beats, grounding each term before a beat leans on it.
- **`writing-fragments(task: string, context: string)`**
  Writing, explore — mine raw fragments, no structure yet.
- **`writing-shape(task: string, context: string)`**
  Writing, exploit — shape raw material into an article, paragraph by paragraph.
- **`git-guardrails-claude-code(task: string, context: string)`**
  Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
- **`migrate-to-shoehorn(task: string, context: string)`**
  Migrate test files from `as` type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace `as` in tests, or needs partial test data.
- **`scaffold-exercises(task: string, context: string)`**
  Create exercise directory structures with sections, problems, solutions, and explainers that pass linting. Use when user wants to scaffold exercises, create exercise stubs, or set up a new course section.
- **`setup-pre-commit(task: string, context: string)`**
  Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.
- **`grill-me(task: string, context: string)`**
  A relentless interview to sharpen a plan or design.
- **`grilling(task: string, context: string)`**
  Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
- **`handoff(task: string, context: string)`**
  Compact the current conversation into a handoff document for another agent to pick up.
- **`teach(task: string, context: string)`**
  Teach the user a new skill or concept, within this workspace.
- **`to-questionnaire(task: string, context: string)`**
  Turn a decision you can't fully answer into a questionnaire for someone else to fill in.
- **`wait-what(task: string, context: string)`**
  Stop. That last message did not land — re-pitch it.
- **`writing-for-agents(task: string, context: string)`**
  Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.