# Open Knowledge Framework (OKF v0.2): Git-Native Agent Memory & Governance

## 1. Normative Concept Schema
OKF v0.2 models persistent cognitive memory as plain-text Markdown files with YAML frontmatter stored in a repository's `knowledge/` directory:
- **Mandatory Fields**: `id` (unique alphanumeric kebab-case string), `title` (human-readable), `type` (`decision`, `architecture`, `operational`, `concept`), `description` (1-2 sentence high-density summary).
- **Governance Invariants**: `governance` array specifying immutable boundaries, security gates, or architectural constraints.
- **Code Linkages**: `code_refs` array specifying file or directory paths that this concept explicitly governs.
- **Provenance & Verification**: `generated: {by, at}` and `verified: {by, at}` capturing actor identity and timestamp.
- **Relations**: Structured adjacency links (`relations: [{target, description}]`) avoiding unstructured prose link rot.

## 2. Git-Native Memory Economics
Unlike external vector databases (Pinecone, Qdrant, Milvus) that introduce persistent network latency, recurring embedding API billing, and out-of-sync state branches:
- OKF bundles reside directly in the workspace repository.
- Changes are tracked via standard `git diff`, `git blame`, and atomic commits.
- Branching, rebasing, and rollbacks apply to agent memory identically to application source code.
- Cold-start latency is zero: bundles load from disk into in-memory BM25 indexes in <5ms.

## 3. BM25 Lexical Ranking & Governance Boosting
Retrieval uses the Okapi BM25 algorithm ($k_1=1.2, b=0.75$) over inverted token indexes:
- **Term Weighting**: Token matches in `title` receive a 3.0× multiplier, `governance` and `id` receive 2.5×–3.0× multipliers, `description` receives 2.0×, and `body` receives 1.0×.
- **Governance Boosting**: Concepts whose `governance` constraints match query terms receive an additive score bonus, ensuring safety invariants outrank descriptive tutorials.
- **Path Scoping (`SearchForPath`)**: Directly matches a target file path against `code_refs` prefixes, returning all governing constraints in $O(N)$ comparisons without text search ambiguities.

## 4. Anti-Blanket Scan Protocol
Autonomous agents often succumb to context bloat by executing `list_dir` or recursive `grep` across memory folders. OKF enforces:
- **Progressive Disclosure**: `okf_search` defaults to `limit=3`, returning only IDs, titles, and 1-sentence summaries.
- **Deferred Body Loading**: Agents must inspect the 3 summaries before calling `okf_show` to pull full Markdown bodies into their prompt context.
- **Prompt Protection**: Prevents context blowout and preserves LLM reasoning budgets on large repositories.

## 5. Actor Trust Hierarchy & Anti-Self-Attestation
To prevent automated agent hallucinations from gaining unearned authority:
- **Actor Namespaces**: Actors are partitioned into `human:<username>`, `agent:<agent-name>`, and `org:<team-name>`.
- **Trust Ordering Invariant**: An agent actor (`agent:*`) may generate concepts, but CANNOT self-attest as a `human:` verifier.
- **Verification Gate**: `verified.by` may only claim human verification if explicitly authored or approved by a human operator. Self-attestation is flagged as a critical normative failure.

## 6. Cross-Platform Path Traversal Defenses
OKF bundles enforce filesystem isolation:
- **Boundary Verification (`ensureWithinRoot`)**: All file operations verify that `target.resolve().relative_to(root.resolve())` succeeds, rejecting `../` traversal escapes.
- **Backslash Normalization**: Windows backslashes (`\`) are normalized to forward slashes (`/`) across all `code_refs` and relative paths for cross-platform deterministic hashing.
- **Scalar Sanitization**: Scalar YAML fields (`id`, `title`, `type`, `description`) are stripped of unescaped newlines to prevent frontmatter delimiter injection attacks.

## 7. Upstream Windows MCP Test Finding
During the repository audit of Google `okf-agent-memory`:
- Core library `pkg/okf` passed 100% of 70+ test cases in 3.76s on Windows.
- CLI/MCP suite `cmd/okf` reported 2 failures (`TestMCPAdversarialSearchResourceLimits`, `TestMCPAdversarialIndirectPromptInjectionInputs`).
- **Root Cause Analysis**: The test authoring in `cmd/okf/mcp_test.go` concatenated unescaped Windows paths (`C:\Users\...`) directly into raw JSON-RPC string literals. Standard Go `json.Unmarshal` strictly rejects invalid escape sequences (e.g. `\U`). This is an authoring artifact in the test fixture, not an architectural defect in the OKF engine.
