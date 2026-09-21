# Knowledge Item: Shift-Left Pre-Commit Security & Dual-Gate Defense

## Epistemic Distillation

### 1. Paradigm Shift: Shift-Left Feedback Loops
Security reviews and vulnerability discoveries are most effective and least expensive when developers receive immediate feedback while code is active in their working memory. Waiting for pull request reviews, remote CI pipeline runs, or periodic penetration tests creates substantial context switching, re-work, and release delays.
- **Pre-Commit Principle**: Intercept insecure code patterns and secrets on developer workstations at the moment of `git commit`.
- **Latency Invariant**: Local pre-commit hooks must complete in under 3 seconds to avoid developer friction and hook bypasses. Local hooks must inspect only *staged* files (`pass_filenames: true`), leaving full-repository scans to remote CI pipelines.

### 2. Multi-Engine Division of Labor: SAST vs Secret Detection
A frequent engineering anti-pattern is conflating code linters with credential scanners. They address fundamentally distinct threat models:
- **DevSkim CLI (Microsoft CST)**: AST and lexical pattern analysis. Flags weak cryptography (MD5, SHA1), risky system calls, unvalidated deserialization, SQL/command injections, and insecure TLS configurations. DevSkim is *not* designed for secret scanning; its credential rules rely on basic regexes targeting long, token-like values.
- **Gitleaks**: Dedicated secret scanner. Uses Shannon entropy calculations and high-precision credential regexes to detect API keys, private tokens, passwords, and connection strings that slip past linters.
- **Division of Labor Invariant**: Deploy DevSkim and Gitleaks side-by-side as distinct hooks within `.pre-commit-config.yaml`.

### 3. Execution Dispatcher & CLI Argument Bridging
`pre-commit` passes all staged files as trailing arguments to the configured hook entrypoint. However, the DevSkim CLI accepts only a single path after `-I` (`devskim analyze -I <path>`).
- Direct invocation (`devskim analyze -I`) breaks whenever a commit contains two or more staged files.
- **Dispatcher Pattern**: Provide a lightweight Python loop wrapper (`scripts/run-devskim.py`) that iterates over `sys.argv[1:]`, invokes `devskim analyze -I <file>` per file, aggregates exit codes via bitwise OR, and terminates with non-zero exit if any file fails.

### 4. Deliberate Synthetic Failure Verification
A silent security tool is dangerous because passing checks can mask broken installations, incorrect glob paths, or missing environment variables.
- **Invariant**: Always execute deliberate synthetic failure smoke tests before trusting a security hook:
  1. *Weak Cryptography Smoke Test*: Stage `crypto.createHash("md5")` &rarr; assert DevSkim blocks commit with Exit Code 1 (`DS126858: Weak Hash Algorithm`).
  2. *Secret Scanner Smoke Test*: Stage high-entropy dummy key (`const apiKey = "4f2a9c1e7b6d3a8f0c5e9b2d7a41c6";`) &rarr; assert Gitleaks blocks commit with Exit Code 1.
- **Safety Boundary**: Delete synthetic fixtures immediately after test execution. Never use real credentials or live keys for testing.

### 5. Progressive Triage & Suppression Hygiene
Introducing pre-commit security tooling to mature or legacy codebases often reveals dozens of existing violations. Paralyzing developer velocity by blocking all commits immediately leads to hook abandonment.
- **Legacy Baseline**: Run `pre-commit run --all-files` once to catalog pre-existing violations into a prioritized remediation backlog.
- **Surgical Inline Suppressions**: When a finding is confirmed to be an unexploitable or intentional pattern, suppress only that specific instance with an in-code comment documenting the rationale and reviewer sign-off.
- **Strict Prohibition**: Never use blanket directory exclusions (e.g. `exclude: src/.*` or `exclude: tests/.*`). Blanket exclusions create permanent organizational blind spots.

### 6. Dual-Gate CI Defense & SARIF Governance
Local developer workstation guardrails provide fast feedback, but they can be bypassed using `git commit --no-verify`, web-based GitHub edits, or detached branches.
- **Remote CI Parity**: Remote CI (GitHub Actions) must mirror all workstation security checks.
- **Full History Depth**: Configure `actions/checkout@v4` with `fetch-depth: 0` so that Gitleaks inspects every commit in the PR branch history rather than just the latest commit tip.
- **SARIF Integration**: Generate SARIF outputs (`devskim analyze -I . -f sarif -O devskim.sarif`) and upload them via `github/codeql-action/upload-sarif@v3`. This surfaces findings directly inside GitHub's Security tab for centralized governance and vulnerability tracking.
