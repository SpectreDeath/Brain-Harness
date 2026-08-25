"""Tests for artifact_generator plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.artifact_generator import (
    ARTIFACT_GENERATOR_KEY,
    ArtifactGeneratorService,
    BriefingResult,
    HtmlReportResult,
    MermaidResult,
)
from plugins.software_engineering.artifact_generator.main import (
    ArtifactGeneratorPlugin,
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

    @pytest.mark.asyncio
    async def test_artifact_generator_plugin_ioc_lifecycle(self, tmp_path: Path) -> None:
        plugin = ArtifactGeneratorPlugin()
        assert plugin.name == "plugin.artifact_generator"
        assert ARTIFACT_GENERATOR_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(ARTIFACT_GENERATOR_KEY)
        assert isinstance(service, ArtifactGeneratorService)

        m_res = service.generate_mermaid([{"id": "N1", "label": "Node1"}], [])
        assert isinstance(m_res, MermaidResult)
        assert m_res.status == "ok"
        assert "graph TD" in m_res.mermaid

        h_out = tmp_path / "ioc_report.html"
        h_res = service.generate_html_report("IoC Report", [{"title": "T1", "content": "C1"}], output_path=str(h_out))
        assert isinstance(h_res, HtmlReportResult)
        assert h_res.status == "ok"
        assert h_out.exists()

        b_out = tmp_path / "ioc_brief.md"
        b_res = service.create_briefing("IoC Brief", "Summary text", output_path=str(b_out))
        assert isinstance(b_res, BriefingResult)
        assert b_res.status == "ok"
        assert b_out.exists()

        await plugin.on_disable()
        await plugin.on_unload()
