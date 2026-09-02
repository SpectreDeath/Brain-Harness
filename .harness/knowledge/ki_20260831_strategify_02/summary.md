# Multi-Commodity Supply Chain Vulnerability & Shock Engine

## Metadata
- **KI ID**: `ki_20260831_strategify_02`
- **Source Target**: `D:\GitHub\projects\Strategify`
- **Format**: `python_simulation_harness`
- **Timestamp**: `2026-08-31T23:15:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: Multi-Commodity Supply Chain Vulnerability & Shock Engine

## Operational Summary
Geopolitical economic modeling requires multi-commodity tracking (oil, gas, semiconductors, grain, rare earths) coupled with structural network topology. Tracking trade flows on a directed NetworkX graph allows computing betweenness centrality to isolate critical maritime chokepoints (Bosphorus, Hormuz, Malacca, Suez). Shock injections (embargoes, port closures, sanctions) dynamically increase commodity stress and apply cumulative economic penalties on target agents with gradual recovery loops.

## Primary Lineage
- **Assertion**: SupplyChainEngine models multi-commodity flows across directed trade graphs, computes maritime chokepoint vulnerability via NetworkX betweenness centrality, and propagates dynamic economic penalties to StateActorAgents upon shock events.
  - `primary_code`: `strategify/economics/supply_chain.py#L1-L409` (Verified: True)
  - `primary_code`: `strategify/economics/econometrics.py#L1-L150` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/repo-reader-20260831-231500.html` (Verified: True)
