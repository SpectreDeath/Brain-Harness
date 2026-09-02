# Unattended Background Cron Scheduler & Incident Classification

**ID:** `ki_hermes_004`  
**Category:** `agent_orchestration`  
**Origin:** `NousResearch/hermes-agent`  
**Source Provenance:** `cron/scheduler.py`, `cron/jobs.py`, `cron/lifecycle_guard.py`

## Executive Summary
Natural language cron scheduler running unattended background workflows with incident error tracking, blueprint catalog management, and multi-channel notification dispatch.

## Architectural Invariants
1. All extracted tool patterns must map to deterministic parameter schemas.
2. Verified provenance links must cite exact source file locations.
3. State modifications must integrate into the IoC container via typed `ServiceKey[T]`.
