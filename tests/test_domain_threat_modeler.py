"""Tests for Domain 1: Threat Modeler plugin."""

from __future__ import annotations

import pytest

from plugins.security_and_forensics.threat_modeler.main import (
    generate_attack_tree,
    map_mitre_attack,
    model_stride_threats,
)


@pytest.mark.unit
class TestThreatModelerPlugin:
    def test_model_stride_threats(self) -> None:
        components = [
            {"name": "Public API", "type": "web_service", "auth": False, "stores_data": False},
            {"name": "User DB", "type": "database", "auth": True, "stores_data": True},
        ]
        res = model_stride_threats(components)
        assert res["status"] == "ok"
        assert res["threats_count"] >= 5
        categories = {t["category"] for t in res["threats"]}
        assert "Spoofing" in categories
        assert "Information Disclosure" in categories

    def test_map_mitre_attack(self) -> None:
        techs = ["credential_dumping", "sql_injection", "unknown_custom_exploit"]
        res = map_mitre_attack(techs)
        assert res["status"] == "ok"
        assert res["mapped_count"] == 2
        assert res["unmapped_count"] == 1
        ids = [t["id"] for t in res["mapped_techniques"]]
        assert "T1003" in ids
        assert "T1190" in ids

    def test_generate_attack_tree(self) -> None:
        goal = "Access Cloud Secrets"
        vectors = ["Phishing credentials", "Exploit vulnerable API", "SSRF metadata service"]
        res = generate_attack_tree(goal, vectors)
        assert res["status"] == "ok"
        assert "graph TD" in res["mermaid"]
        assert "🎯 Goal: Access Cloud Secrets" in res["mermaid"]
