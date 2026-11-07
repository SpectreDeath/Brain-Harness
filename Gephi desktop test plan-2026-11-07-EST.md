# Gephi Desktop Test Plan (2026-11-07 EST)

## Goal

Run the Track 8 manual Gephi verification on the vault knowledge graph and record what Gephi actually shows, so Track 8 (standing-gaps plan 8.1 / follow-up plan 6.1) can be ticked with evidence — or the gap written down.

This is a human-GUI job. No headless script, agent check, or HTML export may tick Track 8.

## Starting facts (verified 2026-11-07 at BH HEAD `899d618`)

- File: `.harness/graph/knowledge_graph.gexf` — **451 nodes, 218 edges** (27 asserted, 191 derived), regenerated Nov 6. Node attributes carried in the file: `node_kind`, `category`, `domain`, `tags`, plus `retrieval_count` and degree.
- **The file carries no `viz:color` or `viz:size`** (0 of each in the file). Colors and sizes are applied inside Gephi, not read from the file — Track 8.1's "verify node colors (`viz:color`) and sizes (`viz:size`)" cannot pass literally as written; step 3 below applies them in Gephi instead, and the wording gap is a finding to record.
- Reference numbers to compare against: `docs/reference/knowledge-graph-visual-brief.md` §2 — Louvain **Q = 0.9447**, **58 communities**, 248 components, 191 isolated nodes, connected subgraph 226 nodes, largest component 34 nodes. Top communities there: Architecture Deepening (19 nodes), Multi-Agent Swarms (15), Google Repos Bridge (8), PyRIT Security (8).
- Styling guide in the brief §3: ForceAtlas2, size by Degree, color by `category` partition, edges by `edge_type`.

## Prerequisites

- Gephi 0.10+ open on the desktop; repo pulled to `899d618` (or later — record the head actually used).
- If the `.gexf` is stale relative to the vault, regenerate it with `harness knowledge export --format gexf --out .harness/graph/knowledge_graph.gexf`. Never hand-edit the file.

## Steps

- [ ] 1. Open `.harness/graph/knowledge_graph.gexf` in Gephi. Record the node/edge counts Gephi reports (expect 451 / 218).
- [ ] 2. Run ForceAtlas2 (Scaling = 2.0, Gravity = 1.0, Prevent Overlap = checked, Tolerance = 0.1) until settled. Then Expansion (x1.2) followed by Label Adjust.
- [ ] 3. Size nodes by Degree (min 6, max 24) and color by `category` partition, using the palette in the brief §3. Note the `viz:color` / `viz:size` wording gap (see starting facts).
- [ ] 4. Run Statistics → Modularity (Louvain, resolution 1.0, weighted edges). Record Q, the number of communities, and the sizes of the largest few. Compare with the brief's Q = 0.9447 / 58 communities / 248 components / 191 isolated nodes. Note any difference and the likely cause (graph version, resolution, weights).
- [ ] 5. Eyeball the biggest communities: do the top ones match the brief's §2 top-8 list? Note matches and surprises.
- [ ] 6. Export a dated screenshot (PNG) and, if it looks useful, an SVG/PDF. Save under `reports/gephi/` (or record the path chosen).
- [ ] 7. Write the findings into `reports/gephi-session-2026-11-07.md` (or append to the visual brief): head used, counts, layout settings, Q + communities, comparison with the brief, screenshot path, and anything that looked wrong (isolated-node clutter, unreadable labels, missing attributes).
- [ ] 8. Only then tick Track 8 (8.1) in `Standing gaps analysis and plan-2026-11-05-1755-EST.md` and Track 6.1 in `Post-execution audit and follow-up plan-2026-11-06-EST.md`, citing the session note and screenshot.

## If it fails

- If Gephi cannot open the file, record the exact error and stop. Do not substitute a headless render or the HTML export. That outcome is itself the finding — the `.gexf` export needs fixing.
- If the counts differ from 451 / 218, record both numbers and check whether the file is stale (regenerate and re-open).

## Evidence rule and guardrails

- Tick or assert nothing without the session note + screenshot.
- The Gephi session is read-only with respect to the repo: the only repo changes are the session note, the screenshot, and ticking the two boxes.
- No new third-party dependencies.
