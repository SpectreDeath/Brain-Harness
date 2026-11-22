# Wave 2 8-Point ICM Cold Walk Report — 2026-11-22 EST

- **Generated (UTC):** `2026-11-22T19:36:45Z`
- **Prime Commit:** `87a1a2b`
- **Scope (`0.1 (b)` decision):** Core 3 + `harness-memory-graph` materialized under `D:\GitHub\harnesses\`.
- **Verification Split:** Points `#2, #3, #4, #6, #7` are verified automatically by `harness spawn cold-walk`. Points `#1, #5, #8` combine automated structural prechecks with a qualitative cold-read assessment recorded explicitly as reader judgment (`agent-cold-reader: Gemini 4 Neon`; human user sign-off pending).

| Harness | ICM Form | AGENTS Lines / Est. Tok | Step Est. Tok (`<8000`) | Skill Catalog Savings | Auto `#2,#3,#4,#6,#7` | Reader `#1,#5,#8` | `IcmAuditor` | Broken Links | Drift |
|---|---|---:|---:|---:|---|---|---|---|---|
| `harness-reverse-engineering` | `pipeline` | `22L / ~347` | `~554` | 5 of 114 (95.1%) | `PASS` | precheck PASS; agent-read PASS (pending human sign-off) | 10/10 | `0` (`51` checked) | `False` |
| `harness-ontology-spider` | `system_map` | `22L / ~345` | `~223` | 5 of 114 (95.81%) | `PASS` | precheck PASS; agent-read PASS (pending human sign-off) | 10/10 | `0` (`49` checked) | `False` |
| `harness-knowledge-graph` | `knowledge_bundle` | `22L / ~350` | `~204` | 5 of 114 (95.31%) | `PASS` | precheck PASS; agent-read PASS (pending human sign-off) | 10/10 | `0` (`46` checked) | `False` |
| `harness-memory-graph` | `context_map` | `22L / ~342` | `~199` | 5 of 114 (95.34%) | `PASS` | precheck PASS; agent-read PASS (pending human sign-off) | 10/10 | `0` (`53` checked) | `False` |

## `harness-reverse-engineering` (`pipeline`)

| # | Point | Mode | Machine Output Status | Precheck | Detail | Qualitative Reader Judgment |
|---:|---|---|---|---|---|---|
| 1 | Where am I | `human_judgment` | `pending_human_judgment` | `True` | Precheck: AGENTS.md=22L (~347 est. tok), links README.md + CONTEXT.md; human judgment not yet supplied | PASS in 2 reads (AGENTS.md 22L + CONTEXT.md 23-27L) — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 2 | Exact Inputs | `automated` | `passed` | `True` | Verified 2 backticked input path(s) in CONTEXT.md | N/A (automated) |
| 3 | Pure Disk Status | `automated` | `passed` | `True` | Disk status indexes present (stages) and drift clean | N/A (automated) |
| 4 | No Content in Catalog | `automated` | `passed` | `True` | AGENTS.md=22L (~347 tok), CONTEXT.md=24L, payload_leak=False | N/A (automated) |
| 5 | Single Source of Truth | `human_judgment` | `pending_human_judgment` | `True` | Precheck: canonical files linked from AGENTS.md without broken cross-references; human judgment not yet supplied | PASS — root catalog links to canonical homes without duplicate prose — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 6 | Resolving Links | `automated` | `passed` | `True` | IcmVerifier links=51 broken=0; doc_bundle_valid=True | N/A (automated) |
| 7 | Token Budget Under 8k | `automated` | `passed` | `True` | Step contract est_tokens=554 (<8000); skills=5/114 (~411 vs ~8392 tok, 95.1% saved) | N/A (automated) |
| 8 | Broken Invariants Explained | `human_judgment` | `pending_human_judgment` | `True` | Precheck: IcmAuditor=10/10 invariants, warnings=0; human judgment not yet supplied | PASS — IcmAuditor 10 of 10 invariants clean, zero warnings — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |

## `harness-ontology-spider` (`system_map`)

| # | Point | Mode | Machine Output Status | Precheck | Detail | Qualitative Reader Judgment |
|---:|---|---|---|---|---|---|
| 1 | Where am I | `human_judgment` | `pending_human_judgment` | `True` | Precheck: AGENTS.md=22L (~345 est. tok), links README.md + CONTEXT.md; human judgment not yet supplied | PASS in 2 reads (AGENTS.md 22L + CONTEXT.md 23-27L) — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 2 | Exact Inputs | `automated` | `passed` | `True` | Verified 3 backticked input path(s) in CONTEXT.md | N/A (automated) |
| 3 | Pure Disk Status | `automated` | `passed` | `True` | Disk status indexes present (objects/_index.md, processes/_index.md) and drift clean | N/A (automated) |
| 4 | No Content in Catalog | `automated` | `passed` | `True` | AGENTS.md=22L (~345 tok), CONTEXT.md=24L, payload_leak=False | N/A (automated) |
| 5 | Single Source of Truth | `human_judgment` | `pending_human_judgment` | `True` | Precheck: canonical files linked from AGENTS.md without broken cross-references; human judgment not yet supplied | PASS — root catalog links to canonical homes without duplicate prose — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 6 | Resolving Links | `automated` | `passed` | `True` | IcmVerifier links=49 broken=0; doc_bundle_valid=True | N/A (automated) |
| 7 | Token Budget Under 8k | `automated` | `passed` | `True` | Step contract est_tokens=223 (<8000); skills=5/114 (~352 vs ~8392 tok, 95.81% saved) | N/A (automated) |
| 8 | Broken Invariants Explained | `human_judgment` | `pending_human_judgment` | `True` | Precheck: IcmAuditor=10/10 invariants, warnings=0; human judgment not yet supplied | PASS — IcmAuditor 10 of 10 invariants clean, zero warnings — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |

## `harness-knowledge-graph` (`knowledge_bundle`)

| # | Point | Mode | Machine Output Status | Precheck | Detail | Qualitative Reader Judgment |
|---:|---|---|---|---|---|---|
| 1 | Where am I | `human_judgment` | `pending_human_judgment` | `True` | Precheck: AGENTS.md=22L (~350 est. tok), links README.md + CONTEXT.md; human judgment not yet supplied | PASS in 2 reads (AGENTS.md 22L + CONTEXT.md 23-27L) — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 2 | Exact Inputs | `automated` | `passed` | `True` | Verified 2 backticked input path(s) in CONTEXT.md | N/A (automated) |
| 3 | Pure Disk Status | `automated` | `passed` | `True` | Disk status indexes present (concepts/_index.md) and drift clean | N/A (automated) |
| 4 | No Content in Catalog | `automated` | `passed` | `True` | AGENTS.md=22L (~350 tok), CONTEXT.md=23L, payload_leak=False | N/A (automated) |
| 5 | Single Source of Truth | `human_judgment` | `pending_human_judgment` | `True` | Precheck: canonical files linked from AGENTS.md without broken cross-references; human judgment not yet supplied | PASS — root catalog links to canonical homes without duplicate prose — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 6 | Resolving Links | `automated` | `passed` | `True` | IcmVerifier links=46 broken=0; doc_bundle_valid=True | N/A (automated) |
| 7 | Token Budget Under 8k | `automated` | `passed` | `True` | Step contract est_tokens=204 (<8000); skills=5/114 (~394 vs ~8392 tok, 95.31% saved) | N/A (automated) |
| 8 | Broken Invariants Explained | `human_judgment` | `pending_human_judgment` | `True` | Precheck: IcmAuditor=10/10 invariants, warnings=0; human judgment not yet supplied | PASS — IcmAuditor 10 of 10 invariants clean, zero warnings — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |

## `harness-memory-graph` (`context_map`)

| # | Point | Mode | Machine Output Status | Precheck | Detail | Qualitative Reader Judgment |
|---:|---|---|---|---|---|---|
| 1 | Where am I | `human_judgment` | `pending_human_judgment` | `True` | Precheck: AGENTS.md=22L (~342 est. tok), links README.md + CONTEXT.md; human judgment not yet supplied | PASS in 2 reads (AGENTS.md 22L + CONTEXT.md 23-27L) — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 2 | Exact Inputs | `automated` | `passed` | `True` | Verified 2 backticked input path(s) in CONTEXT.md | N/A (automated) |
| 3 | Pure Disk Status | `automated` | `passed` | `True` | Disk status indexes present (teams/_index.md) and drift clean | N/A (automated) |
| 4 | No Content in Catalog | `automated` | `passed` | `True` | AGENTS.md=22L (~342 tok), CONTEXT.md=27L, payload_leak=False | N/A (automated) |
| 5 | Single Source of Truth | `human_judgment` | `pending_human_judgment` | `True` | Precheck: canonical files linked from AGENTS.md without broken cross-references; human judgment not yet supplied | PASS — root catalog links to canonical homes without duplicate prose — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
| 6 | Resolving Links | `automated` | `passed` | `True` | IcmVerifier links=53 broken=0; doc_bundle_valid=True | N/A (automated) |
| 7 | Token Budget Under 8k | `automated` | `passed` | `True` | Step contract est_tokens=199 (<8000); skills=5/114 (~391 vs ~8392 tok, 95.34% saved) | N/A (automated) |
| 8 | Broken Invariants Explained | `human_judgment` | `pending_human_judgment` | `True` | Precheck: IcmAuditor=10/10 invariants, warnings=0; human judgment not yet supplied | PASS — IcmAuditor 10 of 10 invariants clean, zero warnings — reader: agent (Gemini 4 Neon, 2026-11-22); pending user sign-off. |
