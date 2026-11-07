# Argon briefs — 2026-11-05

Two jobs for Gemini Argon, in order. The user picked "both, audit first" on 2026-11-05.

Context: the user's Gemini Argon compute cap is at 53% remaining, resetting about 10:20 EST 2026-11-06. By the user's settled workflow, Argon plans and judges (frontier work), a fast model executes, and the independent check is never dropped — the assistant checks Argon's output afterwards. These briefs are the frontier-only work. Do not spend Argon on execution, on the vault-stats one-line fix, on the 22-item lint cleanup, or on version-bump trials; those are fast-model work. Gephi still needs a human desktop session and no model helps there.

Repo: SpectreDeath/Brain-Harness, main `57f4642` at the time of writing. Re-verify every claim against the head you are working from; do not carry forward old numbers.

## Brief 1 — Audit the 23 emergent macro-capabilities (send first)

`reports/` holds a skill-graph cluster analysis (140 skills, 20 clusters). `cluster_analysis_data.json` lists 23 "emergent macro-capabilities" — the user created these with the skill-creation workflow; the report's word "Discovered" is wrong, and nothing has ever executed one.

Job:

1. Audit all 23: does each `recommended_pipeline` name real skills, do consecutive steps have real graph edges between them (REQUIRES/dependency) or is the order arbitrary, and is the claimed outcome actually achievable by those skills?
2. Rank them by plausibility and testability, flagging any untestable as written.
3. Define "works" operationally and write a trial spec for the top-ranked one: exact steps, inputs, and what evidence counts as pass/fail.

Rules: cite a file path or skill name for every claim; assert no execution results, nothing has run.

Output: ranked table + trial spec.

## Brief 2 — Fresh analysis + new plan on the standing gaps (send after the audit)

Job: fresh analysis of current head plus a new comprehensive plan doc, same pattern as the Oct 25 / Oct 31 / Nov 3 rounds.

Start from the Nov 1 ranked gaps and re-verify each one against current head — do not carry forward old numbers, several may already be closed by the Nov 3 Big Fix (0950), its follow-up (13/13), and the portability fixes (14/14):

1. Gephi never actually opened — confirm it stays unticked/blocked on a human desktop session, no headless substitute.
2. Dock enforcement is string-pattern filtering with `shell=True`, not a sandbox, approval digest-only, dock tools unverified against ToolRegistry, generic dock has no SHA drift protection.
3. Joint-query KI side hand-rolled, not the real KI service.
4. No lifecycle transition on disk yet — check whether this is still data (nothing meeting the retrieval bar) rather than code.
5. Drift gate vs canonical counts — recheck the numbers at this head, they have moved since Nov 1.
6. Hyperframes manifest invalid JSON (stray character after the closing brace).
7. Vault items missing `status` and the forge flow that re-creates the gap.
8. `integrated-toolkits.md` REA row — verify whether still wrong.
9. Plugin-integration and REA plans were ~85–90% landed with the gap mostly paperwork — reconcile checkbox state against code.

Also fold in the soft §12 leftovers: version record (pydantic/ruff/mypy behind upstream), the git-service decision (is checkpointing dock-only by design?), floating plugin requirements, no dependabot.

Evidence rule: tick or assert nothing without commit+test, dated output, or a written decision.

Output: ranked findings with file-level evidence, then the plan doc.
