"""Human-in-the-loop permission escalation and approval ledger plugin."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

# In-memory approval ledger state
_APPROVALS: dict[str, dict[str, Any]] = {}


def request_human_approval(
    action_name: str,
    risk_level: str = "high",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Register a pending human approval request."""
    req_id = f"appr_{uuid.uuid4().hex[:8]}"
    record = {
        "id": req_id,
        "action_name": action_name,
        "risk_level": risk_level.lower(),
        "status": "pending",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "details": details or {},
        "decision": None,
    }
    _APPROVALS[req_id] = record

    return {
        "status": "ok",
        "request_id": req_id,
        "approval_required": True,
        "risk_level": risk_level,
        "action_name": action_name,
        "record": record,
    }


def record_human_decision(
    request_id: str,
    approved: bool,
    reason: str = "",
) -> dict[str, Any]:
    """Record operator decision on an approval request."""
    record = _APPROVALS.get(request_id)
    if not record:
        return {"status": "error", "error": f"Approval request '{request_id}' not found."}

    record["status"] = "approved" if approved else "rejected"
    record["decision"] = {
        "approved": approved,
        "reason": reason,
        "decided_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    return {
        "status": "ok",
        "request_id": request_id,
        "final_status": record["status"],
        "approved": approved,
        "reason": reason,
    }


def list_pending_approvals() -> dict[str, Any]:
    """List all pending approval requests."""
    pending = [r for r in _APPROVALS.values() if r["status"] == "pending"]
    return {
        "status": "ok",
        "pending_count": len(pending),
        "pending_requests": pending,
    }
