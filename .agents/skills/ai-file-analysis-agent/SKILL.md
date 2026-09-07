---
name: ai-file-analysis-agent
description: "Design, configure, ground, and verify production-grade AI file analysis agents using direct file APIs, negative constraint prompts, and robust conversational loops. Use when building document-analyzing assistants, selecting between direct upload vs RAG, grounding LLM outputs to prevent hallucinations, or hardening file agents against malformed documents and prompt injection."
---

# AI File Analysis Agent

`ai-file-analysis-agent` is a deep-module agent skill for engineering, deploying, and verifying document-grounded AI file analysis assistants. Distilled from Eva J Patel's curriculum, it equips agents with architectural decision rules for Direct File API versus Chunked RAG, prompt grounding guardrails that eliminate hallucinations, and resilient conversational loops.

See [CARD.md](CARD.md) for companion quick reference cards, CLI commands, and stage matrices.

---

## Core Operational Pillars

Every document analysis engagement enforces three architectural pillars:

1. **The Visual Brief** — Interactive HTML briefs generated in `%TEMP%/ai-file-analysis-agent-<timestamp>.html` with live Mermaid.js pipeline routing topologies, 10-point grounding audits, and context decision matrices.
2. **The Mandatory Checkpoint** — Human-in-the-loop validation via `implementation_plan.md` with `RequestFeedback: true`. The agent must halt and await user confirmation before modifying file agent configurations or dispatching live batch API calls.
3. **Behavioral Boundaries & Anti-Patterns** — Rigid negative guardrails that reject ungrounded prose, untethered pre-training speculations, unvalidated file types, and silent interactive inputs.

---

## Authoritative Tooling & Execution Seams

The skill provides deterministic, non-interactive execution engines in `scripts/`:

- `python scripts/file_agent_cli.py validate-file <path> [--json]`: Non-interactive file validation checking path existence, extension whitelist, and size thresholds.
- `python scripts/file_agent_cli.py assemble-prompt [--role <role>] [--json]`: Assembles authoritative system instructions via `GroundingCatalog` with 10 grounding rules and specialized role addenda.
- `python scripts/file_agent_cli.py dry-run --file <path> --question "<q>" [--role <role>]`: Prepares staged session payload via `FileAnalysisEngine.prepare_session` without external network calls.
- `python scripts/file_agent_cli.py audit-response --text "<text>" [--file <path>] [--json]`: Audits model output against the 10 Negative Grounding Constraints via `GroundingAuditor`, scoring compliance and detecting inference tags.

Consult co-located architectural reference guides in `references/`:
- If choosing between full document streaming and vector retrieval, consult [`direct-api-vs-rag-guide.md`](references/direct-api-vs-rag-guide.md) for architectural trade-offs, latency budgets, and file size limits.
- If designing specialized agent personas or strict anti-hallucination instructions, consult [`grounding-and-role-catalog.md`](references/grounding-and-role-catalog.md) for the 10 Negative Grounding Constraints and 4 domain profiles.

---

## Execution Stages

### Stage 1: Pre-flight Ingestion & Boundary Validation

Verify and sanitize input file paths before touching external API endpoints or allocating memory.

#### Procedure
1. Verify target file existence and ensure the path resolves to a regular filesystem file.
2. Filter the file extension against the configured whitelist (`.pdf`, `.docx`, `.csv`, `.txt`). Reject unsupported formats immediately with clear guidance.
3. Check file size against the direct upload threshold (`max_direct_file_bytes = 50 MB`).
4. Sanitize path references to prevent directory traversal or terminal injection.
5. Invoke `python scripts/file_agent_cli.py validate-file <path>` to confirm validation status.

> **Completion Gate**: `Input file existence, extension whitelist, and size bounds verified`

---

### Stage 2: Context Architecture & Retrieval Triage

Evaluate document size and query characteristics to select between Direct File API Upload and Chunked Vector RAG per `direct-api-vs-rag-guide.md`.

#### Procedure
1. If the document is $\le 50$ MB and represents a discrete analytical artifact (report, contract, paper, dataset), route to **Direct File API**.
2. If the document exceeds context bounds or requires multi-document semantic retrieval across a large corpus, route to **Chunked RAG**.
3. When using Direct File API, upload the document once using `client.files.create(file=file, purpose="user_data")` and retain the resulting `file_id`.
4. Avoid redundant uploads across conversational follow-ups by binding the stored `file_id` to subsequent turn messages.

> **Completion Gate**: `Direct File API vs Chunked RAG context architecture selected`

---

### Stage 3: Grounded Instructions & Role Specialization

Assemble system instructions embedding the 10 Negative Grounding Constraints and domain-specific role configurations from `grounding-and-role-catalog.md`.

#### Procedure
1. Inject the 10 negative grounding constraints into the system instruction block:
   - Primary source invariant, direct answers, zero fabrication.
   - Explicit admission when information is missing: *"The provided file does not contain enough information to answer this question."*
   - Distinction between methods, results, and conclusions for analytical queries.
   - Requirement to prefix deductive leaps with `[INFERENCE]`.
2. Append specialized domain profiles when requested:
   - `research`: Isolates hypotheses, empirical findings, and author conclusions.
   - `legal`: Analyzes contractual terms, liabilities, and termination clauses.
   - `resume`: Extracts verified technical capabilities and career achievements.
   - `tabular`: Audits schemas, null distributions, and numeric metrics.
3. Validate assembled prompt via `python scripts/file_agent_cli.py assemble-prompt --role <role>`.

> **Completion Gate**: `Grounded system instructions assembled with negative constraints and role profile`

---

### Stage 4: Conversational State Loop & Fault Tolerance

Implement the interaction engine with defensive exception shielding and session state management.

#### Procedure
1. Enforce turn-level input sanitization: strip whitespace and ignore empty prompts.
2. Implement explicit termination triggers (`exit`, `quit`) that cleanly release held file handles.
3. Shield API dispatch calls inside structured `try/except` blocks to intercept rate limits, timeout exceptions, and API transport errors.
4. Render output streaming or clean markdown responses with formatted headings and bullet points.
5. In automated environments, use `python scripts/file_agent_cli.py dry-run` to verify structured input formatting.
6. Verify model response adherence against the 10 negative grounding constraints using `GroundingAuditor.audit` or `python scripts/file_agent_cli.py audit-response`.

> **Completion Gate**: `Conversational turn loop implemented with defensive input and error shielding`

---

### Stage 5: Security Hardening & PII Quarantine

Apply zero-trust security practices across credentials, document storage, and instruction hierarchies.

#### Procedure
1. Secure credential injection: Load API keys strictly from environment variables (`OPENAI_API_KEY`). Never hardcode secrets in source or commit `.env` files.
2. Defense against document prompt injection: Frame file content strictly as data payloads (`input_file`), isolating it from administrative system instructions.
3. PII and sensitive data handling: Sanitize temporary file caches and delete ephemeral uploads on session exit.
4. Verify non-interactive execution: Ensure all production scripts execute without hanging on interactive standard input.

> **Completion Gate**: `Environment key isolation verified and document injection defense enforced`

---

## Anti-Patterns

- **Premature File Upload** — Uploading documents to external APIs before validating file existence, size thresholds, and extension whitelists, leading to wasted bandwidth and unhandled API errors.
- **Hallucinatory Context Filling** — Allowing the agent to speculate or answer questions from general pre-training weights when the uploaded file lacks supporting evidence, rather than stating context absence.
- **Redundant Per-Turn Upload** — Re-uploading the same file on every conversational query instead of caching and referencing the persistent `file_id` across session turns.
- **Unbounded Extension Ingestion** — Accepting arbitrary file extensions (`.exe`, `.bin`, `.py`) without validation, exposing the system to binary corruption or execution exploits.
- **Hardcoded Secret Ingestion** — Embedding API credentials directly into Python scripts or commit history instead of injecting via environment variables.
- **Interactive Hanging Script** — Invoking `input()` or blocking stdin prompts inside automated pipelines, causing headless execution runners to freeze indefinitely.
