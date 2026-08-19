"""Log Forensics and SIEM stream analyzer plugin for Brain Harness."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

_SYSLOG_REGEX = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<process>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$"
)


def parse_log_stream(log_content: str, format_hint: str = "auto") -> dict[str, Any]:
    """Parse raw log lines into structured event dictionaries."""
    events: list[dict[str, Any]] = []
    lines = [line.strip() for line in log_content.splitlines() if line.strip()]

    for idx, line in enumerate(lines, start=1):
        parsed = False
        # Try JSONL
        if format_hint in ("auto", "jsonl") and line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    data.setdefault("line_number", idx)
                    events.append(data)
                    parsed = True
            except json.JSONDecodeError:
                pass

        if not parsed and format_hint in ("auto", "syslog"):
            match = _SYSLOG_REGEX.match(line)
            if match:
                ev = match.groupdict()
                ev["line_number"] = idx
                events.append(ev)
                parsed = True

        if not parsed:
            # Fallback raw line
            events.append({
                "line_number": idx,
                "message": line,
                "raw": True,
            })

    return {
        "status": "ok",
        "total_lines": len(lines),
        "parsed_events_count": len(events),
        "events": events,
    }


def detect_log_anomalies(log_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Inspect structured logs for attack patterns and anomalies."""
    anomalies: list[dict[str, Any]] = []
    ip_counter: Counter[str] = Counter()
    failed_auth_counter: Counter[str] = Counter()

    for ev in log_events:
        msg = str(ev.get("message", "")) + " " + str(ev.get("msg", ""))
        user = str(ev.get("user", ev.get("username", "unknown")))
        ip = str(ev.get("ip", ev.get("client_ip", "")))

        if ip:
            ip_counter[ip] += 1

        # Check failed logins
        if re.search(r"(?:failed password|authentication failure|invalid user|login failed)", msg, re.IGNORECASE):
            failed_auth_counter[user] += 1
            anomalies.append({
                "type": "Authentication Failure",
                "severity": "medium",
                "user": user,
                "line": ev.get("line_number"),
                "detail": msg[:150],
            })

        # Check privilege escalation
        if re.search(r"(?:sudo|root privilege|escalat)", msg, re.IGNORECASE):
            anomalies.append({
                "type": "Privilege Escalation",
                "severity": "high",
                "user": user,
                "line": ev.get("line_number"),
                "detail": msg[:150],
            })

        # Check SQL injection or path traversal strings in messages
        if re.search(r"(\.\./|UNION SELECT|1=1|/etc/passwd)", msg, re.IGNORECASE):
            anomalies.append({
                "type": "Web Attack Indicator",
                "severity": "critical",
                "line": ev.get("line_number"),
                "detail": msg[:150],
            })

    # Detect brute force (>= 3 failed logins for a single user)
    for usr, count in failed_auth_counter.items():
        if count >= 3:
            anomalies.append({
                "type": "Potential Brute Force",
                "severity": "critical",
                "user": usr,
                "attempts": count,
                "detail": f"User '{usr}' had {count} consecutive authentication failures.",
            })

    return {
        "status": "ok",
        "anomalies_detected": len(anomalies),
        "suspicious": len(anomalies) > 0,
        "anomalies": anomalies,
    }


def build_incident_timeline(log_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct an incident timeline from event logs."""
    timeline: list[dict[str, Any]] = []

    for ev in log_events:
        ts = ev.get("timestamp", ev.get("time", f"Line {ev.get('line_number', 0)}"))
        msg = ev.get("message", ev.get("msg", str(ev)))
        timeline.append({
            "timestamp": ts,
            "line": ev.get("line_number", 0),
            "event": str(msg)[:200],
        })

    return {
        "status": "ok",
        "timeline_events_count": len(timeline),
        "timeline": timeline,
    }
