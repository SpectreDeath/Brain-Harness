---
name: repo-reader
description: Introspect, reflect on, and extract architectural patterns, commit trajectories, and engineering heuristics from an attached local or remote Git repository. Use when the user asks to read a repository, connect a repo, introspect a codebase, analyze commit evolution, learn from a peer repo, or run the repository introspection loop.
---

# Repo Reader: Codebase Introspection & Repository Distillation Engine

`repo-reader` is the repository-level cognitive introspection engine for Brain Harness. Operating atop `plugin.brain_bridge`, it mounts local Git repositories or remote GitHub/GitLab repositories to analyze multi-language codebases, architectural seams, and historical Git commit trajectories—distilling them into grounded, decision-ready Knowledge Items (KIs).

Every repository reflection session follows a five-stage progression:

```
[1. Attach & Detect] → [2. 4-Axis Repo Matrix] → [3. Visual Repository Brief] → [4. Synthesis Checkpoint] → [5. KI Extraction & Lineage Commit]
```

See [CARD.md](CARD.md) for the companion summary card, 4-axis repository prompt matrix, and invariants.
Consult `/crafting-skills` for skill craft standards, `/mind-reader` for foreign brain introspection, and `/epistemic-isnad-audit` for chain-of-custody provenance rules.

---

## 1. Attach & Format Detection

Mount the target repository using the `plugin.brain_bridge` entrypoint:

1. **Invoke `brain_attach`**:
   - `folder_path`: Target directory path or remote Git URL (e.g. `https://github.com/org/repo.git`).
   - `alias`: Descriptive mnemonic identifier (e.g., `upstream_repo`, `fastapi_core`).
   - `read_commits`: `true` to extract Git commit history into cognitive trajectory chunks.
   - `max_commits`: `50` to `100` commits.
   - `attach_mode`: `"lens"` (read-only ephemeral introspection).
2. **Handle Boundary & Archive Snapshots**:
   - **External Workspace Paths**: If the target directory is outside the IDE workspace root and direct file tools return permission errors, use shell inspection commands (`run_command` with PowerShell/bash) anchored in the host workspace.
   - **Nested Root & Non-Git Snapshots**: Detect if the repository is an unzipped archive snapshot without `.git` or contains a single nested subdirectory root. If `.git` is absent, gracefully pivot Axis 2 from Git commit trajectories to release notes, changelogs, and manifest evolution.
3. **Verify Format Signature & Manifests**:
   Confirm format signature (`git_repository`, `harness_instance`, `ide_memo`) and note detected languages and packaging manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, etc.).
4. **Log Mount Volume**:
   Confirm total chunks, code chunks, git commit trajectory chunks, detected branch, and vocabulary index size.

> **Completion criterion**: Target repository mounted with `status: "ok"`, languages identified, and commit trajectories recorded.

---

## 2. 4-Axis Repository Introspection Matrix

Execute four structured queries via `brain_query` across the mounted repository to interrogate its structural and historical surface:

```
┌─────────────────────────────────────────────────────────────┐
│               4-AXIS REPOSITORY INTROSPECTION               │
├──────────────────────────────┬──────────────────────────────┤
│ Axis 1: Architecture & Seams │ Axis 2: Commit Trajectories  │
│ - IoC / Service registry     │ - Historical bug fixes       │
│ - Module boundaries & layers │ - Refactor evolution & diffs │
├──────────────────────────────┼──────────────────────────────┤
│ Axis 3: Engineering Standards│ Axis 4: Delta Innovations    │
│ - Test patterns & fixtures   │ - Deep module designs        │
│ - Typing, linting, CI rules  │ - Novel algorithms & tooling │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Axis 1 (Architectural Topography & Seams)**:
   - Query: `"What are the core architecture patterns, IoC service keys, entrypoints, and module boundaries?"`
   - Purpose: Surface component relationships, dependency flow, and interface contracts.
2. **Axis 2 (Commit Evolution & Trajectories)**:
   - Query: `"What major refactors, breaking changes, or bug fixes occurred in recent commit history?"`
   - Purpose: Understand how the codebase evolved, what pitfalls were encountered, and how design decisions matured.
3. **Axis 3 (Engineering Conventions & Verification Standards)**:
   - Query: `"What testing frameworks, typing standards, CI workflows, and coding conventions are enforced?"`
   - Purpose: Identify testing hygiene, error handling conventions, and verification gates.
4. **Axis 4 (Delta Innovations & Reusable Assets)**:
   - Query: `"What unique algorithms, deep module implementations, or reusable abstractions exist in this repository?"`
   - Purpose: Extract reusable techniques, high-leverage primitives, and domain models.

> **Completion criterion**: 4 query result batches harvested, sorted by cosine relevance, with exact source file and commit hash citations.

### 2.1 Quantitative Scoring & Tiered Prioritization Matrix

When comparing foreign harnesses or evaluating candidate capabilities against Brain Harness, apply the objective scoring formula:

$$\text{Total Score} = \text{Usefulness} + (6 - \text{Difficulty}) + \text{Value} + \text{Architectural Fit}$$

*(Each scored 1–5; Difficulty is inverted so that easier adoptions score higher, Max: 20).*

Structure candidate features into a 3-Tier Roadmap:
- **Tier 1 (Immediate Quick Wins)**: Python-native, low-medium difficulty, direct service plugin fit (Weeks 1–2).
- **Tier 2 (Strategic Safety & Observability)**: Structural invariants, DAG execution graphs, permission policies, session replays.
- **Tier 3 (Horizon Bets)**: Alternative language runtimes, local model inference, peer-to-peer distributed meshes.

---

## 3. The Visual Repository Brief

Synthesize the harvested architectural and commit insights into an interactive, standalone HTML report:

1. **Output Location**: Write to `%TEMP%\repo-reader-<timestamp>.html` (Windows) or `/tmp/repo-reader-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Use Tailwind CSS and Mermaid.js via CDN in dark mode (`#0d1117`).
   - Include a Mermaid **Repository Architecture & Dependency DAG** showing core modules, bridges, and services.
   - Display a **Commit Evolution & Refactor Timeline** highlighting pivotal architectural transitions.
   - Provide a side-by-side matrix of **Architectural Strengths vs. Friction Areas**.
3. **Delivery**: Surface the absolute file path with clickable links to the user.

```html
<!-- Location: %TEMP%\repo-reader-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Repo Reader: Repository Introspection Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Repository Introspection Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Multi-Language Codebase Analysis & Commit Trajectory Distillation</p>
  </header>
  <!-- Mermaid DAG & 4-Axis Repository Analysis Grid -->
</body>
</html>
```

> **Completion criterion**: Standalone HTML brief generated in `%TEMP%` and delivered to user.

---

## 4. Synthesis Checkpoint

Present candidate architectural and engineering learnings to the user before committing persistent memory:

1. Formulate atomic candidate Knowledge Items (KIs) with:
   - **Title**: Actionable architecture pattern or engineering heuristic.
   - **Context**: Problem space, language/framework context, and trigger conditions.
   - **Distilled Learning**: Positive recommendation, seam choice, or mitigation strategy.
   - **Provenance Link**: Exact file path, line coordinates, and Git commit hash in the source repo.
2. Present candidate KIs via an interactive multi-select checkpoint (`ask_question`) or `RequestFeedback: true` proposal.
3. Await user confirmation on which items to retain, adjust, or discard before writing files.

> **Completion criterion**: User review checkpoint completed; approved items selected for commit.

---

## 5. KI Extraction & Lineage Commit

Persist approved learnings into the host repository's knowledge directory:

1. **Target Directory**: Write to `.harness/knowledge/<ki_id>/` on the host.
2. **Metadata Schema (`metadata.json`)**:
   ```json
   {
     "id": "ki_20260822_repo_01",
     "title": "Typed Service Key Registration in Plugin Systems",
     "source_target": "https://github.com/org/repo",
     "detected_format": "git_repository",
     "isnad": {
       "decision_id": "dec_20260822_repo_01",
       "claims": [
         {
           "assertion": "Typed ServiceKey[T] registration required for IoC containers",
           "lineage": [
             {"node_type": "primary_code", "uri": "src/kernel/context.py#L42-L68", "sha256_hash": "a1b2c3d4", "verified": true}
           ]
         }
       ],
       "status": "VERIFIED"
     },
     "tags": ["architecture", "ioc_container", "plugin_lifecycle"]
   }
   ```
3. **Artifact Summary**: Co-locate `summary.md` detailing the operational guideline and code examples.

> **Completion criterion**: Approved KIs written with unbroken Isnad provenance links and commit citations.

---

## Anti-Patterns

- **Surface Code Scanning** — Reading file listings without querying deep module implementations or commit evolution.
- **Disconnected Commit Analysis** — Inspecting commit messages without correlating them to modified code files.
- **Foreign Repository Mutation** — Attempting to write, commit, or alter files in the external mounted repository.
- **Unanchored Seam Extrapolations** — Speculating on architectural intent without citing source lines and commit diffs.
