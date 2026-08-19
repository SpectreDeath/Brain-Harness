"""Tests for artifact_generator plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.software_engineering.artifact_generator.main import (
    diagram_generate_mermaid,
    report_create_briefing,
    report_generate_html,
)


@pytest.mark.unit
class TestArtifactGeneratorPlugin:
    def test_diagram_generate_mermaid(self) -> None:
        nodes = [
            {"id": "A", "label": "Start", "shape": "round"},
            {"id": "B", "label": "Process", "shape": "rect"},
            {"id": "C", "label": "Done", "shape": "circle"},
        ]
        edges = [
            {"source": "A", "target": "B", "label": "triggers"},
            {"source": "B", "target": "C", "style": "thick"},
        ]

        res = diagram_generate_mermaid(nodes, edges, direction="LR")
        assert res["status"] == "ok"
        assert "graph LR" in res["mermaid"]
        assert 'A("Start")' in res["mermaid"]
        assert 'B["Process"]' in res["mermaid"]
        assert 'C(("Done"))' in res["mermaid"]
        assert 'A -->|"triggers"| B' in res["mermaid"]
        assert "B ==> C" in res["mermaid"]

    def test_report_generate_html(self, tmp_path: Path) -> None:
        sections = [
            {"title": "Overview", "type": "text", "content": "System operating smoothly."},
            {"title": "Code Sample", "type": "code", "content": "print('hello')"},
            {
                "title": "Performance Table",
                "type": "table",
                "data": [
                    {"Plugin": "filesystem_git", "Status": "Active", "Latency": "12ms"},
                    {"Plugin": "web_fetcher", "Status": "Active", "Latency": "45ms"},
                ],
            },
        ]
        out_file = tmp_path / "report.html"
        res = report_generate_html("Execution Report", sections, output_path=str(out_file))

        assert res["status"] == "ok"
        assert res["sections_count"] == 3
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "<title>Execution Report</title>" in content
        assert "Performance Table" in content
        assert "filesystem_git" in content

    def test_report_create_briefing(self, tmp_path: Path) -> None:
        out_md = tmp_path / "briefing.md"
        res = report_create_briefing(
            title="Q3 System Briefing",
            summary="All core services operational.",
            metrics={"Uptime": "99.99%", "Active Plugins": "8"},
            recommendations=["Expand MCP test suite", "Enable context compaction by default"],
            output_path=str(out_md),
        )

        assert res["status"] == "ok"
        assert out_md.exists()
        text = out_md.read_text(encoding="utf-8")
        assert "# Q3 System Briefing" in text
        assert "| Uptime | 99.99% |" in text
        assert "- Expand MCP test suite" in text
