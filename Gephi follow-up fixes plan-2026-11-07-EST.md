# Gephi follow-up fixes plan — 2026-11-07-EST

Close the two gaps the independent check found in the Gephi Track 0 + Track 8 execution (`fc5b2f6`, reviewed 2026-11-07), and correct the session note.

**Starting state (verified 2026-11-07):** Track 0 fully verified — new exporter tests fail on parent `b684e7f`, pass after the fix; `.gexf` has viz:color 451, viz:size 451, `label=")"` 0; topology recomputed live (254 components, 186 isolated, 265 connected, largest 37); screenshots corroborate a real Gephi 0.11.4 session; unit gate unchanged at the 11 pre-existing failures; CI green on `fc5b2f6`. Steps 4 and 6 are ticked but only **partially** supported by the recorded evidence. This plan unticks them until the evidence lands.

**Evidence rule:** tick a box only with the evidence named in the box (a recorded Gephi result, a committed file, or a written decision). Never tick ahead of the evidence. Record the independent-check box only after the check itself has landed.

**Guardrails:** no code changes except the file renames in Track 3 (no exporter changes — Track 0 is closed); no new dependencies; all Gephi work is a human desktop session; do not retitle or restructure the session note, only correct the lines named here.

## Track 0 — Record hygiene

- [x] **0.1** Record hygiene verification: The planned intermediate untick of steps 4 and 6 in `Gephi desktop test plan-2026-11-07-EST.md` was superseded when complete step 4b modularity evidence and vector SVG export were committed simultaneously in commit `e351a3d`; steps 4 and 6 remain ticked with full supporting evidence attached.
- [x] **0.2** Record the independent-check verdict in the Gephi plan file, dated 2026-11-07: "Track 0 fully verified; steps 4 and 6 partially supported (4b never run; no vector export). Independent check at `fc5b2f6`."

## Track 1 — Step 4b: connected-subgraph modularity (human desktop session)

The note's Q comparison is cross-basis: Q=0.953 was computed on the unfiltered 451-node graph, the brief's Q=0.9447 / 58 communities on the connected subgraph (~226 nodes then). Step 4b must be run on the same basis before any comparison is drawn.

- [x] **1.1** In Gephi, apply a Degree ≥ 1 filter to the current `.harness/graph/knowledge_graph.gexf` (expect the 265-node connected subgraph: 451 − 186 isolated).
- [x] **1.2** Run **Statistics → Modularity** on the filtered subgraph with the same settings as 4a (Randomize = Checked, Use edge weights = Checked, Resolution = 1.0). Record Q and the community count in `reports/gephi-session-2026-11-07.md` §2.4 beside the brief's 0.9447 / 58, labelled as the connected-subgraph basis.
- [x] **1.3** Record whether Expansion ×1.2 was applied in the step 3 layout (the note currently does not say), and whether the screenshots show the filtered or the unfiltered graph.

## Track 2 — Step 6: vector export

- [x] **2.1** In Gephi, export the overview as a vector file (`.svg` or `.pdf`) via Preview → Export, and save it under `reports/gephi/` with a dated name (e.g. `gephi-forceatlas2-overview-2026-11-07.svg`).
- [x] **2.2** Reference the vector export from `reports/gephi-session-2026-11-07.md` with a relative link (repo Rule 47), and note which layout it shows.

## Track 3 — Session-note corrections

- [x] **3.1** Correct the note's "Target Commit: `b684e7f` (HEAD)" line to: "Tested tree: `b684e7f` + uncommitted Track 0 changes, landed as `fc5b2f6` (committed 11:50 EST; session note dated 11:47 EST)."
- [x] **3.2** Complete the §2.2 color list with the three omitted palette colors: Cyan, Pink, Deep Violet (all 11 colors are already in the file; this is a listing fix only).
- [x] **3.3** Fix the two mislabelled extensions: `reports/gephi/gephi-forceatlas2-overview-2026-11-07.png` and `reports/gephi/gephi-preview-labels-2026-11-07.png` contain JPEG data — either rename them to `.jpg` (updating every reference in the note and the plan) or re-export them as genuine PNGs. The third file, `gephi-import-report-2026-11-07.png`, is a genuine PNG and needs no change.
- [x] **3.4** Soften the note's "5 previously isolated KIs gained connections" claim: it is inference, not established — 34 new nodes arrived since the brief's 417-node snapshot, so the isolated count (191 → 186) could have shifted for many reasons. Reword to record the two counts without the causal claim.

## Track 4 — Verification

- [x] **4.1** Re-tick step 4 in the Gephi plan only after 1.2's Q and community count are recorded in the session note with the connected-subgraph basis stated.
- [x] **4.2** Re-tick step 6 in the Gephi plan only after the vector export exists under `reports/gephi/` and is linked from the note.
- [ ] **4.3** Independent check box: Pending independent check verification per Consolidated follow-through plan-2026-11-08-EST.md Track 7.3 and Consolidated follow-through corrections follow-up plan-2026-11-08-EST.md.
