"""Documentation and schema drift verification gate for Knowledge Graph (Track 8)."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import re
import pytest

from harness.commands.reflection import knowledge_group
from harness.services.storage.vault_graph_models import KnowledgeGraphEdge, KnowledgeGraphNode


def test_documented_cli_commands_match_live_registry() -> None:
    doc_path = Path("docs/how-to/explore-knowledge-graph.md")
    assert doc_path.exists(), "docs/how-to/explore-knowledge-graph.md must exist"

    content = doc_path.read_text(encoding="utf-8")
    cli_ref_path = Path("docs/reference/cli.md")
    cli_ref_content = cli_ref_path.read_text(encoding="utf-8")

    live_commands = set(knowledge_group.commands.keys())

    # Find all 'harness knowledge <subcmd>' in the how-to doc
    matches = re.findall(r"harness knowledge ([a-z0-9_-]+)", content)
    doc_commands = set(matches)

    # All documented subcommands must exist in live Click registry
    for cmd in doc_commands:
        assert cmd in live_commands, f"Documented subcommand 'harness knowledge {cmd}' not found in live CLI registry"

    # Verify that major commands are covered in the doc
    core_commands = {
        "export", "stats", "neighbors", "path", "topic",
        "dependents", "orphans", "hygiene", "timeline",
    }
    assert core_commands.issubset(doc_commands), f"Missing core commands in documentation: {core_commands - doc_commands}"

    # Also verify in cli.md reference
    matches_ref = re.findall(r"harness knowledge ([a-z0-9_-]+)", cli_ref_content)
    ref_commands = set(matches_ref)
    assert core_commands.issubset(ref_commands)


def test_documented_node_and_edge_attributes_match_dataclass_fields() -> None:
    doc_path = Path("docs/how-to/explore-knowledge-graph.md")
    content = doc_path.read_text(encoding="utf-8")

    # Extract backticked attributes from markdown tables
    # Node attributes table
    node_fields = {f.name for f in fields(KnowledgeGraphNode)}
    edge_fields = {f.name for f in fields(KnowledgeGraphEdge)}

    # Verify all live dataclass fields appear in the how-to documentation
    for field_name in node_fields:
        assert f"`{field_name}`" in content, f"Node attribute '{field_name}' not documented in {doc_path}"

    for field_name in edge_fields:
        assert f"`{field_name}`" in content, f"Edge attribute '{field_name}' not documented in {doc_path}"


def test_rule_47_markdown_codeblock_isolation_and_link_hygiene() -> None:
    doc_path = Path("docs/how-to/explore-knowledge-graph.md")
    content = doc_path.read_text(encoding="utf-8")

    # Strip fenced codeblocks per Rule 47
    content_no_codeblocks = re.sub(r"```[\s\S]*?```", "", content)

    # Assert no invalid workspace-absolute file:/// URIs
    assert "file:///" not in content_no_codeblocks, "Rule 47 violation: workspace-absolute file:/// link found in docs"

    # Assert no unescaped dollar signs causing KaTeX math corruption in prose
    # (Literal dollar should not appear unescaped in text)
    assert not re.search(r"(?<!\\)\$(?!\$)", content_no_codeblocks)

