from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.mark.unit
def test_garf_skill_metadata_and_hygiene() -> None:
    """Verify SKILL.md adheres to Rule 44 (100-350 chars description, negative boundaries) and Rule 37."""
    skill_md = Path(".agents/skills/garf-reporting-architect/SKILL.md")
    assert skill_md.exists()

    content = skill_md.read_text(encoding="utf-8")

    # Frontmatter description check (Rule 44: 100-350 chars)
    import re

    desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    assert desc_match is not None
    desc = desc_match.group(1).strip()
    assert 100 <= len(desc) <= 350, f"Description length {len(desc)} outside [100, 350]"
    assert "Do not use for" in desc

    # Anti-patterns check (Rule 37)
    assert "## Anti-Patterns" in content
    assert re.search(r"-\s+\*\*[A-Za-z\s\-]+\*\*\s+—\s+", content) is not None


@pytest.mark.unit
def test_garf_card_ascii_borders_and_headers() -> None:
    """Verify CARD.md uses single-pipe borders and exact SKILL header (Rule 37)."""
    card_md = Path(".agents/skills/garf-reporting-architect/CARD.md")
    assert card_md.exists()

    content = card_md.read_text(encoding="utf-8")
    assert "SKILL: garf-reporting-architect" in content
    assert "│" in content
    assert "║" not in content  # Prohibited double-pipe border


@pytest.mark.unit
def test_garf_cli_seams() -> None:
    """Verify headless Click CLI subcommands (parse, simulate, export, workflow)."""
    import importlib.util

    cli_path = Path(".agents/skills/garf-reporting-architect/scripts/garf_cli.py")
    spec = importlib.util.spec_from_file_location("garf_cli", str(cli_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    runner = CliRunner()

    # Test parse command
    res_parse = runner.invoke(
        module.cli,
        [
            "parse",
            "-q",
            "SELECT id, metrics.clicks AS clicks FROM campaign",
            "--json-out",
        ],
    )
    assert res_parse.exit_code == 0
    assert '"resource_name": "campaign"' in res_parse.output
    assert '"clicks"' in res_parse.output

    # Test simulate command
    res_sim = runner.invoke(
        module.cli,
        [
            "simulate",
            "-q",
            "SELECT id, name FROM ad_group",
            "--rows",
            "3",
            "--json-out",
        ],
    )
    assert res_sim.exit_code == 0
    assert '"ad_group_name_1"' in res_sim.output


@pytest.mark.unit
def test_harness_garf_command_group() -> None:
    """Verify harness garf Click command group and all headless subcommands."""
    import tempfile

    import yaml

    from harness.cli import main
    from harness.commands.garf import garf_group

    runner = CliRunner()

    # Test group mounting in main CLI
    res_help = runner.invoke(main, ["garf", "--help"])
    assert res_help.exit_code == 0
    assert "Google Garf Declarative SQL Reporting" in res_help.output

    # Test alias mounting
    res_alias = runner.invoke(main, ["garf-reporting", "--help"])
    assert res_alias.exit_code == 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)

        # 1. Parse with --query-file (-f)
        qfile = tmp_p / "query.sql"
        qfile.write_text(
            "SELECT campaign.id AS id, metrics.cost_micros / 1000000 AS cost FROM campaign LIMIT 5",
            encoding="utf-8",
        )
        res_parse = runner.invoke(garf_group, ["parse", "-f", str(qfile), "--json-out"])
        assert res_parse.exit_code == 0
        assert '"resource_name": "campaign"' in res_parse.output
        assert '"cost"' in res_parse.output

        # 2. Simulate with --query-file (-f)
        res_sim = runner.invoke(
            garf_group, ["simulate", "-f", str(qfile), "-r", "2", "--json-out"]
        )
        assert res_sim.exit_code == 0
        assert len(_parse_json_list(res_sim.output)) == 2

        # 3. Export with --dest-type json
        out_json = tmp_p / "out.json"
        res_exp = runner.invoke(
            garf_group,
            [
                "export",
                "-f",
                str(qfile),
                "-t",
                "json",
                "-p",
                str(out_json),
                "-r",
                "3",
                "--json-out",
            ],
        )
        assert res_exp.exit_code == 0
        assert out_json.exists()

        # 4. Workflow execution with YAML config and dynamic params
        cfg_path = tmp_p / "workflow.yaml"
        staging_db = str(tmp_p / "staging.db")
        final_csv = str(tmp_p / "final.csv")
        workflow_data = {
            "steps": [
                {
                    "step_id": "extract",
                    "step_type": "query",
                    "query_path": str(qfile),
                    "writer_type": "sqlite",
                    "destination": staging_db,
                },
                {
                    "step_id": "export_csv",
                    "step_type": "writer",
                    "writer_type": "csv",
                    "destination": final_csv,
                    "query_path": staging_db,
                    "depends_on": ["extract"],
                },
            ]
        }
        cfg_path.write_text(yaml.safe_dump(workflow_data), encoding="utf-8")

        res_wf = runner.invoke(
            garf_group,
            ["workflow", "-c", str(cfg_path), "-p", "env=prod", "--json-out"],
        )
        assert res_wf.exit_code == 0
        assert '"status": "ok"' in res_wf.output
        assert Path(final_csv).exists()


def _parse_json_list(output: str) -> list[dict]:
    import json

    return json.loads(output)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_garf_command_registry() -> None:
    """Verify CommandRegistry registers and dispatches garf commands."""
    from harness.commands import CommandRegistry

    assert CommandRegistry.get("garf.parse") is not None
    assert CommandRegistry.get("garf.simulate") is not None
    assert CommandRegistry.get("garf.export") is not None
    assert CommandRegistry.get("garf.workflow") is not None

    res = await CommandRegistry.dispatch(
        "garf.parse", query="SELECT id, metrics.clicks AS clicks FROM campaign"
    )
    assert res["resource_name"] == "campaign"
    assert "clicks" in res["column_names"]

    sim_res = await CommandRegistry.dispatch(
        "garf.simulate",
        query="SELECT id, metrics.clicks AS clicks FROM campaign",
        rows=2,
    )
    assert len(sim_res) == 2
