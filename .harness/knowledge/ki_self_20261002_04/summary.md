# Continuous Reflection Daemon, JUnit Test Trajectory Harvesting & CI Distillation

## Problem
In continuous AI development workflows:
1. Every time test suites fail or recover in CI or developer workstations, rich failure traces, exception logs, and timing anomalies evaporate once the runner process exits.
2. Agents starting fresh sessions have no endogenous memory of what tests recently broke or what patterns caused regressions, leading to repeated cycles of trial and error.

## Solution
1. **JUnit Trajectory Harvester (`TestExecutionPatternExtractor`)**:
   - Ingests standard JUnit XML reports (e.g. generated via `pytest --junitxml=report.xml`).
   - Parses `<testsuite>`, `<testcase>`, `<failure>`, and `<error>` nodes, extracting test names, failure messages, and stack traces into structured telemetry.
2. **Continuous Background Daemon (`ReflectionDaemonWorker`)**:
   - Operates as a background asyncio service or headless CLI daemon (`harness reflect --daemon --interval 300`).
   - Periodically scans `%TEMP%` for HTML visual briefs and test reports, distilling high-confidence heuristics into Knowledge Items.
3. **CI Pipeline Integration**:
   - The GitHub Actions workflow (`.github/workflows/ci.yml`) runs `harness reflect --test-report test-report.xml` immediately following test runs to commit verified execution memories directly into the repository.

## Operational Guideline
- Always output JUnit XML in CI test steps (`--junitxml=test-report.xml`).
- Wire the reflection daemon into long-running agent workflows or CI runs.
- Distinguish flaky timeout errors from persistent assertion bugs during failure extraction.

## Provenance
- Source code: `src/harness/creator/reflection.py`, `src/harness/services/reflection_worker.py`, `src/harness/commands/reflection.py`
- Test contract: `tests/test_reflection_daemon.py`
- Commit: `c3bfffebc5749c6aab51f19004b595d1b552c90c`
