# Web API Seam Decoupling via AnalysisRegistry & AgentStateAdapter

## Metadata
- **KI ID**: `ki_20260831_strategify_05`
- **Source Target**: `D:\GitHub\projects\Strategify`
- **Format**: `python_simulation_harness`
- **Timestamp**: `2026-08-31T23:15:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: Web API Seam Decoupling via AnalysisRegistry & AgentStateAdapter

## Operational Summary
Coupling simulation classes directly to web route endpoints produces brittle API contracts and serialization overhead. `AnalysisRegistry` maps query keys to isolated `BaseAnalysisHandler` instances (VAR, Granger causality, Louvain community detection, strategic risk assessment), while `AgentStateAdapter` standardizes agent state extraction and converts Shapely geometries into standard GeoJSON `FeatureCollection` dictionaries for React-Leaflet frontend rendering.

## Primary Lineage
- **Assertion**: AnalysisRegistry and AgentStateAdapter decouple FastAPI route handlers from simulation internals, providing O(1) analysis dispatch and zero-latency GeoJSON FeatureCollection serialization for React-Leaflet live visualization.
  - `primary_code`: `strategify/web/analysis_registry.py#L1-L136` (Verified: True)
  - `primary_code`: `strategify/web/agent_adapter.py#L1-L102` (Verified: True)
  - `primary_code`: `strategify/web/api.py#L1-L250` (Verified: True)
