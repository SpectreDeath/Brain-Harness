"""Tests for Domain 1: Log Forensics plugin."""

from __future__ import annotations

import pytest

from plugins.log_forensics.main import (
    build_incident_timeline,
    detect_log_anomalies,
    parse_log_stream,
)


@pytest.mark.unit
class TestLogForensicsPlugin:
    def test_parse_jsonl_and_syslog(self) -> None:
        raw_logs = (
            '{"timestamp": "2026-08-14T20:00:00Z", "user": "alice", "msg": "login success"}\n'
            '{"timestamp": "2026-08-14T20:01:00Z", "user": "admin", "msg": "failed password"}\n'
        )
        res = parse_log_stream(raw_logs)
        assert res["status"] == "ok"
        assert res["parsed_events_count"] == 2

    def test_detect_anomalies_brute_force(self) -> None:
        events = [
            {"line_number": 1, "user": "root", "message": "Failed password for root from 192.168.1.50"},
            {"line_number": 2, "user": "root", "message": "Failed password for root from 192.168.1.50"},
            {"line_number": 3, "user": "root", "message": "Failed password for root from 192.168.1.50"},
            {"line_number": 4, "user": "admin", "message": "sudo su executed"},
        ]
        res = detect_log_anomalies(events)
        assert res["status"] == "ok"
        assert res["suspicious"] is True
        types = [a["type"] for a in res["anomalies"]]
        assert "Potential Brute Force" in types
        assert "Privilege Escalation" in types

    def test_build_incident_timeline(self) -> None:
        events = [
            {"timestamp": "2026-08-14T10:00:00Z", "line_number": 1, "message": "Scan started"},
            {"timestamp": "2026-08-14T10:05:00Z", "line_number": 2, "message": "Alert triggered"},
        ]
        res = build_incident_timeline(events)
        assert res["status"] == "ok"
        assert res["timeline_events_count"] == 2
