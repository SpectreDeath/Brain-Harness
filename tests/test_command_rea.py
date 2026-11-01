"""Tests for the Click CLI command group `harness rea`."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.commands.rea import rea_group


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_wasm(tmp_path: Path) -> Path:
    p = tmp_path / "sample.wasm"
    p.write_bytes(b"\x00asm\x01\x00\x00\x00\x01\x04\x01\x60\x00\x00")
    return p


def test_rea_list_command(runner: CliRunner) -> None:
    """harness rea list prints 28 tools organized by category."""
    result = runner.invoke(rea_group, ["list"])
    assert result.exit_code == 0
    assert "REA Reverse-Engineering Toolkit" in result.output
    assert "rea.native.elf_layout" in result.output
    assert "rea.managed.inspect_artifact" in result.output
    assert "rea.js.recover_sources" in result.output
    assert "rea.mobile.apk_inspect" in result.output


def test_rea_providers_command(runner: CliRunner) -> None:
    """harness rea providers prints status of the 4 domain plugins."""
    result = runner.invoke(rea_group, ["providers"])
    assert result.exit_code == 0
    assert "REA EXTERNAL PROVIDERS" in result.output
    assert "plugin.rea_native" in result.output
    assert "plugin.rea_mobile_firmware" in result.output
    assert "plugin.rea_javascript" in result.output


def test_rea_inspect_command(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea inspect inspects a binary target and prints table and json."""
    # Text output
    result = runner.invoke(rea_group, ["inspect", str(sample_wasm)])
    assert result.exit_code == 0
    assert "REA DISSECTION ENVELOPE" in result.output
    assert "wasm" in result.output

    # JSON output
    json_result = runner.invoke(rea_group, ["inspect", str(sample_wasm), "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert data["artifact"]["detected_kind"] == "wasm"
    assert data["provider"]["plugin"] == "plugin.rea_native"


def test_rea_signatures_command(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea signatures extracts semantic signatures."""
    result = runner.invoke(rea_group, ["signatures", str(sample_wasm)])
    assert result.exit_code == 0
    assert "Signatures" in result.output


def test_rea_devices_command(runner: CliRunner) -> None:
    """harness rea devices queries adb client status without raising."""
    result = runner.invoke(rea_group, ["devices"])
    assert result.exit_code == 0
    assert "ADB Client Status" in result.output


def test_rea_decompile_command(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea decompile dispatches decompilation request."""
    result = runner.invoke(rea_group, ["decompile", str(sample_wasm), "--symbols", "main"])
    assert result.exit_code == 0
    assert "REA DECOMPILATION" in result.output


def test_rea_callgraph_command(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea callgraph traverses function call graphs."""
    result = runner.invoke(rea_group, ["callgraph", str(sample_wasm), "--entry", "main", "--depth", "2"])
    assert result.exit_code == 0
    assert "Call Graph Traversal" in result.output


def test_rea_diff_command(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea diff executes multi-provider differential comparison."""
    result = runner.invoke(rea_group, ["diff", str(sample_wasm), "--providers", "ghidra,hopper"])
    assert result.exit_code == 0
    assert "REA MULTI-PROVIDER DIFFERENTIAL REPORT" in result.output


def test_rea_learn_command_dry_run(runner: CliRunner, sample_wasm: Path) -> None:
    """harness rea learn with --dry-run synthesizes Knowledge Item without writing."""
    result = runner.invoke(rea_group, ["learn", str(sample_wasm), "--dry-run", "--tag", "test_tag"])
    assert result.exit_code == 0
    assert "REA KNOWLEDGE DISTILLATION COMPLETE" in result.output
    assert "Knowledge Item ID" in result.output


def test_rea_learned_command(runner: CliRunner) -> None:
    """harness rea learned lists Knowledge Items stored in vault."""
    result = runner.invoke(rea_group, ["learned"])
    assert result.exit_code == 0
    assert "Knowledge Items" in result.output
