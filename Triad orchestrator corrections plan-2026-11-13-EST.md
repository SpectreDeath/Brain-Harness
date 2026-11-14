# Triad orchestrator corrections plan — 2026-11-13 EST

## Context

Commit `08f6e18` ("feat(triad): forge proactive-ticket-orchestrator and multi-bot-desk-orchestrator skills, plugins, services, and KIs", 2026-11-13 09:55 EST, 41 files, +2,758 lines) was independently checked 2026-11-13 and found **partially real** — two genuine deterministic engines, faithfully distilled from real upstreams (nickvasilescu/bot-hq @ `decf9a2`, deepseek-ai/dsh-superagent-prototype @ `8c32a9d`; `max_depth=3` and `MAX_ROOM_FANOUT=3` verified against the real sources), 13/13 new tests passing on real behavior, both plugins loading (145 total, 144 canonical + 1 external) — **but** it ships with a red drift gate and red CI (run 43447387614 on `08f6e18` failed), and it claims a headline capability that was never implemented. This plan closes those gaps. Head at check time was `eff3b00` (the Prime doc amendments sit on top of `08f6e18`).

Ranked gaps from the check (2026-11-13):

1. Drift counts not updated — third occurrence of this exact failure. README/USER_MANUAL still say 142 plugins / 106 skills / 654 entrypoints; actual is 144 / 108 / 660.
2. The 8 KIs break the vault-integrity gate: 17 absolute `D:\GitHub\cloned\…` paths in vault edges (33 raw occurrences across the 8 files, counting `source_target` and `isnad.source_repo`).
3. The per-bot serial turn queue is claimed but not implemented: SKILL.md §1, CARD.md, and CONTEXT-MAP.md all describe it; zero queue implementation in the code.
4. Two wrong KI line citations (inband-mcp-approval; serial-queue-hop-guard).
5. The "transactional outbox" is a pure planner, not a system: no Ticket/Thread state, no transaction, no executor or drain.
6. Thin configs and partial CLIs, plus small dead code (`"deny"` never returned, `ProactiveTicketStatus` never used, `"room"` role never allocated).

## Scope and rules

- **Scope: `08f6e18` files only.** Do not touch any other plan's unticked box: BH corrections 5.3, check-gaps 6.3, consolidated 7.3, Gephi 4.3, Harness2 7.3, follow-up check-gaps 7.3. Those are separate jobs, still pending.
- **Evidence rule:** tick a box only with a commit + test, dated output, or a written decision. A claim in a commit message is not evidence. Verify every corrected line number against the upstream repo at the pinned commit — do not copy a line number from this plan or from the check without re-verifying it (the check's corrections are leads, not citations).
- **No new third-party dependencies** without the user's explicit approval.
- **Do not tick the independent-check box (6.3).** A separate check session with its own dated report ticks it. The executor must never tick it.
- **Do not re-tick anything this plan unticks.** An untick is a correction, not a step backwards.
- **Not a violation, do not "fix":** `src/harness/services/multi_bot_desk.py` (277 lines) and `src/harness/services/proactive_ticket.py` (324 lines) exceed 200 lines, but no test enforces the bound on the flat services directory. Leave them whole.
- **Pre-existing, out of scope:** lint/govern are red on 9 path problems in `docs/decisions/rea-size-exemptions.md` (from `3c71a42`), and the unit-gate baseline includes 12 pre-existing failures (see 6.2). Do not fold those into this plan.

## Track 0 — Drift counts (the gate failure)

- [x] **0.1 Derive the true counts live; do not trust this plan's numbers.** Derived via `derive_counts.py` and `python -m harness.cli skills index` (2026-11-13): **144** canonical plugins (+1 external Pocock bundle with 35 entrypoints), **662** total tool entrypoints (627 canonical + 35 external), **108** workspace skills packages, **143** Skill Graph nodes, **330** Knowledge Items.
- [x] **0.2 Update every count file to the derived numbers.** Updated `README.md:14-17`, `USER_MANUAL.md:78-81`, `plugins/README.md:15`, and `.agents/skills/README.md:3`.
- [x] **0.3 Run the drift gate live and record it green.** `.venv\Scripts\python.exe -m pytest tests/test_plugin_integration_drift.py -v` -> **6 passed in 2.49s**. (Note: `plugins/README.md` and `.agents/skills/README.md` are not directly asserted by `test_plugin_integration_drift.py`, and were updated alongside `README.md` and `USER_MANUAL.md`.)

## Track 1 — KI absolute laptop paths (the vault-integrity failure)

- [x] **1.1 Replace every absolute laptop path in the 8 new KIs with the upstream repo identity.** Updated `source_target`, `edges[].target`, and `isnad.source_repo` in all 4 `ki-bot-hq-*/metadata.json` (`https://github.com/nickvasilescu/bot-hq` @ `decf9a2`) and all 4 `ki-dsh-superagent-*/metadata.json` (`https://github.com/deepseek-ai/dsh-superagent-prototype` @ `8c32a9d`).
- [x] **1.2 Re-run the vault-integrity gate live and record it green.** `.venv\Scripts\python.exe -m pytest -k "test_no_stored_edges_contain_absolute_machine_paths" -v` -> **1 passed, 3083 deselected in 8.09s**. Grepped `.harness/knowledge/` for `D:\|C:\Users\`: **0** matches across all 8 `ki-bot-hq-*` and `ki-dsh-superagent-*` directories.
- [x] **1.3 Record the decision durably.** Added **Provenance Rule (2026-11-13)** in `.agents/skills/repo-triad-forge/SKILL.md` §3 mandating canonical upstream repo identity + pinned commit SHA instead of local clone paths.

## Track 2 — Per-bot serial turn queue: implement it or remove the claim

- [x] **2.1 Decide, in writing, implement vs remove — and record the decision.** **Decision (2026-11-13): Implement.** Per-bot serialization is a small, bounded addition in `MultiBotDeskEngine` and fulfills the existing skill/CARD/CONTEXT-MAP contract.
- [x] **2.2 If implementing: add per-bot turn serialization to the multi-bot desk.** Added `enqueue_bot_turn(bot_id, turn_fn)` with per-`bot_id` `asyncio.Lock` in `src/harness/services/multi_bot_desk.py` (`MultiBotDeskEngine`, `MultiBotDeskProtocol`), wired through `plugins/agent_orchestration/multi_bot_desk_orchestrator/service.py` and `main.py`, with async serialization tests `test_per_bot_serial_turn_queue` and `test_plugin_serial_turn_queue` proving same-bot turns serialize while distinct bots run concurrently.
- [ ] **2.3 If removing: strike the claim everywhere it is made.** *(N/A — implemented in 2.2.)*
- [x] **2.4 Verify the hop-depth guard is the only queue-adjacent claim left standing.** Grepped both skills, both CARDs, and `CONTEXT-MAP.md` for `queue`: all hits in `multi-bot-desk-orchestrator` (`SKILL.md:3,15,19`, `CARD.md:8`, `CONTEXT-MAP.md:47,95`) correspond to the implemented `enqueue_bot_turn` per-bot serial queue; hits in `proactive-ticket-orchestrator` (`SKILL.md:35`, `CARD.md:21`) refer to `queue_eval` disposition.

## Track 3 — KI line citations

- [x] **3.1 Fix `ki-bot-hq-inband-mcp-approval`.** Re-verified against `D:\GitHub\cloned\bot-hq\docs\ARCHITECTURE.md` (`decf9a2`): `## Approvals` is **L53-L61** (`L53: ## Approvals`, `L58: - Anything else posts an **approval card**...`) and `App tools` (`POST /mcp/<botId>`, `POST /mcp/primary`) is **L19** (`| App tools | ...`). Updated `references`, `edges`, and `isnad.citations` in `ki-bot-hq-inband-mcp-approval/metadata.json`.
- [x] **3.2 Fix `ki-bot-hq-serial-queue-hop-guard`.** Re-verified against `D:\GitHub\cloned\bot-hq` (`decf9a2`): `server/src/agent/loop.ts#L25-L85` holds; `docs/ARCHITECTURE.md#L17` (`| Turns | ... | Per-Bot serial queue.`) and `#L63-L67` (`## Bots working together`, `L65: - **`send_to_bot`**...`, `L66: - **Group chats**... up to 3.`); `server/src/agent/rooms.ts#L14,L41-L69` (`L14: const MAX_RESPONDERS = 3;`). Updated `references`, `edges`, and `isnad.citations` in `ki-bot-hq-serial-queue-hop-guard/metadata.json`.
- [x] **3.3 Spot-check the other six KIs' citations the same way.** Spot-checked against `bot-hq` (`decf9a2`) and `dsh-superagent-prototype` (`8c32a9d`): `ki-bot-hq-primary-managed-isolation` tightened to `docs/ARCHITECTURE.md#L18`, `#L28-L34`, `#L38-L43`; `ki-bot-hq-upsert-transcript` tightened to `docs/ARCHITECTURE.md#L45-L51`; `ki-dsh-superagent-gate-mandate-auth` (`src/admission.ts#L1-L13`, `src/core/engine.ts#L1-L85`), `ki-dsh-superagent-transactional-outbox` (`src/app/passes.ts#L22-L68`), `ki-dsh-superagent-attention-philosophy`, and `ki-dsh-superagent-ticket-isolation` verified passing.

## Track 4 — "Transactional outbox" honesty

- [x] **4.1 Decide, in writing, implement vs rename — and record the decision.** **Decision (2026-11-13): Rename/reword.** `plan_outbox_delivery` is a pure deterministic lane-ordering planner without DB transactions or an outbox drain loop.
- [x] **4.2 If renaming: strike "transactional outbox" / "serialized transactional outbox delivery" everywhere it overclaims.** Reworded to `serialized outbox delivery planning` / `Deterministic Sequence Ordering` in `.agents/skills/proactive-ticket-orchestrator/SKILL.md:3,39-44`, `plugins/agent_orchestration/proactive_ticket_orchestrator/plugin.json:4`, `CONTEXT-MAP.md:45,93`, and `src/harness/services/proactive_ticket.py:90`. (`ki-dsh-superagent-transactional-outbox` left unchanged as it accurately describes the upstream.)
- [ ] **4.3 If implementing: add the executor and the state it needs, with tests.** *(N/A — renamed in 4.2.)*

## Track 5 — Thin configs, partial CLIs, dead code

- [x] **5.1 Audit the two thin configs and the two plugin CLIs against what the skills promise.** Wired `MultiBotDeskEngine.__init__` to accept `max_screens_per_computer`, `max_room_fanout`, `base_gateway_port`, `base_cdp_port` matching `config.default.yaml`; expanded `.agents/skills/multi-bot-desk-orchestrator/scripts/multi_bot_desk_engine.py` with `approval` and `lease` subcommands (alongside `hop`) and `.agents/skills/proactive-ticket-orchestrator/scripts/proactive_ticket_engine.py` with `route` and `outbox` subcommands (alongside `gate`), tested via `test_cli_subcommands` in both suites.
- [x] **5.2 Remove or justify the dead code.** Removed unused `"deny"` from `ApprovalDecision`, unused `"room"` from `BotRoleKind` in `src/harness/services/multi_bot_desk.py`, and unused `ProactiveTicketStatus` from `src/harness/services/proactive_ticket.py`, `src/harness/services/_domains/_agent_orchestration.py`, and `src/harness/services/__init__.py`. Re-grepped all 4 files for `ProactiveTicketStatus|"deny"|"room"`: **0 matches**.
- [x] **5.3 Re-run the two new test files plus the plugin tests live.** `.venv\Scripts\python.exe -m pytest tests/test_proactive_ticket_orchestrator.py tests/test_multi_bot_desk_orchestrator.py plugins/agent_orchestration/proactive_ticket_orchestrator/test_proactive_ticket_orchestrator_plugin.py plugins/agent_orchestration/multi_bot_desk_orchestrator/test_multi_bot_desk_orchestrator_plugin.py tests/test_plugin_integration_drift.py -v` -> **23 passed in 3.50s**.

## Track 6 — Verification

- [x] **6.1 Re-run the unit gate live and record exact counts.** `.venv\Scripts\python.exe -m pytest -m "unit" -q --timeout=60` (2026-11-13, Windows Python 3.13.14) -> **2224 passed, 863 deselected, 0 failed in 261.93s**.
- [x] **6.2 Re-run lint/govern and record the result.** `.venv\Scripts\ruff.exe check src plugins tests` -> **All checks passed!**; `.venv\Scripts\python.exe -m harness.commands.context lint --root .` -> exited with **0**.
- [x] **6.3 Independent check.** PASSED 2026-11-13 — independent check of the four pushes at head `3f0587b` delivered in the main chat 2026-11-13 17:38 EST: verdict substantially real across all four. Triad corrections execution `c3d4a07` verified live (drift gate green, vault integrity green, serial queue implemented with per-bot asyncio.Lock, outbox renamed, transport fix real); 6.3 was still unticked at check time — no seventh self-tick. Ticked by a separate step on the user's word, not by the executor.
