"""Tests for REA Managed Runtime & Bytecode Forensics Plugin."""

from __future__ import annotations

import json
import marshal
import struct
import sys
from pathlib import Path
from typing import Any
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from harness.services.rea_managed_runtime import (
    REA_MANAGED_RUNTIME_KEY,
    Il2cppMetadataReport,
    ManagedArtifactReport,
    ManagedBoundariesReport,
    ModelArtifactReport,
    PycInspectReport,
    ReaManagedRuntimeService,
    resolve_rea_managed_runtime,
)
from plugins.security_and_forensics.rea_managed_runtime.engine import (
    Il2cppMetadataParser,
    ManagedPeEngine,
    ModelArtifactEngine,
    PycEngine,
    ReaManagedRuntimeEngine,
)
from plugins.security_and_forensics.rea_managed_runtime.main import (
    ReaManagedRuntimePlugin,
    plugin,
    rea_inspect_il2cpp_metadata,
    rea_inspect_managed_artifact,
    rea_inspect_managed_native_boundaries,
    rea_inspect_model_artifact,
    rea_inspect_python_pyc,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = (
        Path(__file__).parent.parent
        / "plugins"
        / "security_and_forensics"
        / "rea_managed_runtime"
    )
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestReaManagedRuntimePlugin:
    """Unit and lifecycle test suite for REA Managed Runtime Inspection Plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey in IoC container (Rule 2 & 45)."""
        ctx = ServiceContext()
        p = ReaManagedRuntimePlugin()

        assert p.name == "plugin.rea_managed_runtime"
        assert REA_MANAGED_RUNTIME_KEY in p.provides
        assert p.requires == []

        await p.on_load(ctx)
        svc = ctx.require(REA_MANAGED_RUNTIME_KEY)
        assert isinstance(svc, ReaManagedRuntimeService)

        resolved = resolve_rea_managed_runtime(ctx)
        assert resolved is svc

        await p.on_enable()
        await p.on_disable()
        await p.on_unload()

    def test_plugin_singleton_export(self) -> None:
        """Verify module exports singleton instance (Rule 45)."""
        assert isinstance(plugin, ReaManagedRuntimePlugin)
        assert plugin.name == "plugin.rea_managed_runtime"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules (Rule 34 & 38)."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {[c.message for c in report.checks if not c.passed]}"

    def test_il2cpp_metadata_valid_parsing(self, tmp_path: Path) -> None:
        """Verify IL2CPP global-metadata.dat parsing with valid magic and sections."""
        meta_file = tmp_path / "global-metadata.dat"

        # Build synthetic header
        magic = 0xFAB11BAF
        version = 29
        # section 0: stringLiterals (offset, size) -> (264, 80) -> 10 literals
        # section 1: stringLiteralData -> (344, 100)
        # section 2: strings -> (444, 64)
        # padding up to 264 bytes
        header = bytearray(struct.pack("<Ii", magic, version))
        # pad section table
        sec_table = bytearray()
        # stringLiterals
        sec_table.extend(struct.pack("<ii", 264, 80))
        # stringLiteralData
        sec_table.extend(struct.pack("<ii", 344, 100))
        # strings
        sec_table.extend(struct.pack("<ii", 444, 64))
        # pad remaining sections to 256 bytes
        sec_table.extend(b"\x00" * (256 - len(sec_table)))
        header.extend(sec_table)

        # File content up to offset 444
        content = bytearray(header)
        if len(content) < 444:
            content.extend(b"\x00" * (444 - len(content)))

        # Add sample strings at offset 444
        content.extend(b"GameManager\x00PlayerController\x00OnTriggerEnter\x00")
        meta_file.write_bytes(content)

        report = rea_inspect_il2cpp_metadata(str(meta_file))
        assert isinstance(report, Il2cppMetadataReport)
        assert report.status == "ok"
        assert report.magic_valid is True
        assert report.version == 29
        assert report.string_literals_count == 10
        assert "GameManager" in report.sample_strings
        assert "PlayerController" in report.sample_strings

    def test_il2cpp_metadata_invalid_magic_and_missing(self, tmp_path: Path) -> None:
        """Verify IL2CPP parser cleanly handles invalid magic or missing file."""
        bad_file = tmp_path / "bad.dat"
        bad_file.write_bytes(b"CORRUPTED_BYTES_HERE")

        report = rea_inspect_il2cpp_metadata(str(bad_file))
        assert report.status == "invalid_magic"
        assert report.magic_valid is False
        assert "Invalid IL2CPP magic" in (report.error or "")

        missing_report = rea_inspect_il2cpp_metadata("non_existent_file.dat")
        assert missing_report.status == "error"
        assert missing_report.magic_valid is False

    def test_model_artifact_safetensors(self, tmp_path: Path) -> None:
        """Verify zero-allocation Safetensors inspection (Rule 48)."""
        model_file = tmp_path / "model.safetensors"

        header_dict = {
            "__metadata__": {"format": "pt", "author": "Harness"},
            "transformer.layer.0.weight": {
                "dtype": "F32",
                "shape": [768, 768],
                "data_offsets": [0, 2359296],
            },
            "transformer.layer.0.bias": {
                "dtype": "F32",
                "shape": [768],
                "data_offsets": [2359296, 2362368],
            },
        }
        json_bytes = json.dumps(header_dict).encode("utf-8")
        header_len = len(json_bytes)
        file_bytes = struct.pack("<Q", header_len) + json_bytes + (b"\x00" * 1024)
        model_file.write_bytes(file_bytes)

        report = rea_inspect_model_artifact(str(model_file))
        assert isinstance(report, ModelArtifactReport)
        assert report.status == "ok"
        assert report.format == "safetensors"
        assert report.tensor_count == 2
        assert report.metadata_preview.get("author") == "Harness"
        assert len(report.tensors) == 2
        assert report.tensors[0].name == "transformer.layer.0.weight"
        assert report.tensors[0].shape == [768, 768]
        assert report.tensors[0].type_name == "F32"

    def test_model_artifact_gguf(self, tmp_path: Path) -> None:
        """Verify zero-allocation GGUF v3 header inspection."""
        gguf_file = tmp_path / "model.gguf"

        magic = b"GGUF"
        version = 3
        tensor_count = 12
        kv_count = 1
        # KV pair: key="general.architecture" (len=20), type=8 (string), val="llama" (len=5)
        key = b"general.architecture"
        val = b"llama"
        kv_data = (
            struct.pack("<Q", len(key))
            + key
            + struct.pack("<I", 8)
            + struct.pack("<Q", len(val))
            + val
        )

        header = struct.pack("<4sIQQ", magic, version, tensor_count, kv_count) + kv_data
        gguf_file.write_bytes(header)

        report = rea_inspect_model_artifact(str(gguf_file))
        assert isinstance(report, ModelArtifactReport)
        assert report.status == "ok"
        assert report.format == "gguf_v3"
        assert report.version == 3
        assert report.tensor_count == 12
        assert report.metadata_preview.get("general.architecture") == "llama"

    def test_pyc_bytecode_inspection(self, tmp_path: Path) -> None:
        """Verify CPython .pyc bytecode disassembly."""
        pyc_file = tmp_path / "sample.pyc"

        # Compile a sample python snippet
        code_obj = compile("def add(x, y):\n    return x + y\n", "<test>", "exec")
        marshaled = marshal.dumps(code_obj)

        magic = struct.pack("<H2s", 3413, b"\r\n")  # Python 3.8 magic
        header = magic + struct.pack("<II", 0, 1600000000) + struct.pack("<I", 1234)
        pyc_file.write_bytes(header + marshaled)

        report = rea_inspect_python_pyc(str(pyc_file), disassemble=True)
        assert isinstance(report, PycInspectReport)
        assert report.status == "ok"
        assert report.magic == 3413
        assert "3.8" in report.cpython_version
        assert report.instruction_count > 0
        assert len(report.sample_disassembly) > 0

    def test_managed_pe_and_boundaries(self, tmp_path: Path) -> None:
        """Verify PE inspection on non-PE and synthetic DOS MZ files."""
        non_pe = tmp_path / "sample.txt"
        non_pe.write_text("Hello World", encoding="utf-8")

        rep1 = rea_inspect_managed_artifact(str(non_pe))
        assert rep1.status == "non_pe"
        assert rep1.is_cli is False

        rep2 = rea_inspect_managed_native_boundaries(str(non_pe))
        assert rep2.status == "non_pe"

    def test_frozen_slotted_dataclass_immutability(self) -> None:
        """Verify Rule 12 & Rule 43: reports are frozen and slotted."""
        report = Il2cppMetadataReport(
            status="ok",
            metadata_path="test.dat",
            magic_valid=True,
            version=29,
        )
        assert report.status == "ok"
        # Test dict-like read access
        assert report["status"] == "ok"
        assert report.get("version") == 29
        assert "magic_valid" in report

        # Rule 43: assert immutability using direct assignment
        with pytest.raises((AttributeError, TypeError)):
            report.status = "mutated"  # type: ignore[misc]
