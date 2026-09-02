# Pre-Commit Verification Evidence Tracking & Stop Interceptors

**ID:** `ki_hermes_003`  
**Category:** `agent_orchestration`  
**Origin:** `NousResearch/hermes-agent`  
**Source Provenance:** `agent/verification_evidence.py`, `agent/verification_stop.py`, `agent/verify_hooks.py`

## Executive Summary
Dynamic tracking of shell verification commands and file mutations, intercepting agent turn completion with synthetic corrective guidance if code was modified without test verification.

## Architectural Invariants
1. All extracted tool patterns must map to deterministic parameter schemas.
2. Verified provenance links must cite exact source file locations.
3. State modifications must integrate into the IoC container via typed `ServiceKey[T]`.
