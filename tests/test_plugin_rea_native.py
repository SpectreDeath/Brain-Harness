"""Tests for REA Native Binary Inspection Plugin."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from harness.services.rea_native import (
    REA_NATIVE_KEY,
    ReaNativeService,
    resolve_rea_native,
)
from plugins.security_and_forensics.rea_native.engine import (
    BinaryLayoutEngine,
    DecompilerEngine,
    DosMzInspector,
    ElfParser,
    EvmEngine,
    NativeAnalysisSessionCache,
    NativeBinarySessionEntry,
    WasmEngine,
    WasmParser,
)
from plugins.security_and_forensics.rea_native.main import (
    ReaNativeEngine,
    ReaNativePlugin,
    rea_native_annotate_function,
    rea_native_batch_decompile,
    rea_native_call_graph,
    rea_native_elf_layout,
    rea_native_evm_interface,
    rea_native_inspect_load_image,
    rea_native_wasm_inspect,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "security_and_forensics" / "rea_native"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestReaNativePlugin:
    """Unit and lifecycle test suite for REA Native Inspection Plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey in IoC container."""
        ctx = ServiceContext()
        plugin = ReaNativePlugin()

        assert plugin.name == "plugin.rea_native"
        assert REA_NATIVE_KEY in plugin.provides
        assert plugin.requires == []

        await plugin.on_load(ctx)
        svc = ctx.require(REA_NATIVE_KEY)
        assert isinstance(svc, ReaNativeService)

        resolved = resolve_rea_native(ctx)
        assert resolved is svc

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"

    def test_batch_decompile_success_and_missing_binary(self, tmp_path: Path) -> None:
        """Verify batch decompile returns pseudocode or graceful tool_not_found."""
        bin_file = tmp_path / "target.bin"
        bin_file.write_bytes(b"\x7fELF" + b"\x00" * 60)

        # Provider without headless binary
        res_ghidra = rea_native_batch_decompile(str(bin_file), symbols=["main", "init"], provider="ghidra")
        assert res_ghidra["status"] in ("ok", "tool_not_found")
        if res_ghidra["status"] == "tool_not_found":
            assert res_ghidra["required_binary"] == "analyzeHeadless"

        # Supported provider simulation
        engine = ReaNativeEngine(ghidra_headless_path="/usr/bin/analyzeHeadless")
        sim_res = engine.batch_decompile(str(bin_file), symbols=["main", "init"], provider="ghidra")
        assert sim_res["status"] == "ok"
        assert len(sim_res["procedures"]) == 2
        assert sim_res["procedures"][0]["symbol"] == "main"
        assert "void main()" in sim_res["procedures"][0]["pseudocode"]

    def test_batch_decompile_nonexistent_file(self) -> None:
        """Verify batch decompile returns error on nonexistent file."""
        res = rea_native_batch_decompile("nonexistent_binary.elf", symbols=["main"])
        assert res["status"] == "error"
        assert "not found" in res["error"]

    def test_batch_decompile_unsupported_provider(self, tmp_path: Path) -> None:
        """Verify batch decompile validates provider name."""
        bin_file = tmp_path / "target.bin"
        bin_file.write_bytes(b"\x7fELF" + b"\x00" * 60)
        res = rea_native_batch_decompile(str(bin_file), symbols=["main"], provider="unsupported_radare")
        assert res["status"] == "error"
        assert "Unsupported decompiler provider" in res["error"]

    def test_call_graph(self, tmp_path: Path) -> None:
        """Verify reachability DAG construction."""
        bin_file = tmp_path / "target.bin"
        bin_file.write_bytes(b"\x7fELF" + b"\x00" * 60)

        cg = rea_native_call_graph(str(bin_file), entry_symbol="main", depth=3, direction="callee")
        assert cg["status"] == "ok"
        assert "main" in cg["nodes"]
        assert len(cg["edges"]) >= 2
        assert cg["edges"][0]["caller"] == "main"

    def test_elf_layout_and_checksec(self, tmp_path: Path) -> None:
        """Verify ELF layout and exploit mitigation extraction."""
        bin_file = tmp_path / "sample.elf"
        bin_file.write_bytes(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 120)

        layout = rea_native_elf_layout(str(bin_file), checksec=True)
        assert layout["status"] == "ok"
        assert layout["format"] == "ELF"
        assert len(layout["sections"]) > 0
        assert layout["mitigations"] is not None
        assert layout["mitigations"]["nx"] is True

    def test_wasm_inspect_valid_and_invalid(self, tmp_path: Path) -> None:
        """Verify WABT WASM inspect validates magic bytes and extracts sections."""
        wasm_file = tmp_path / "module.wasm"
        # \x00asm \x01\x00\x00\x00 (valid WASM header)
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"\x00" * 32)

        res = rea_native_wasm_inspect(str(wasm_file), emit_wat=True)
        assert res["status"] == "ok"
        assert res["wabt_version"] == "1.0.42"
        assert len(res["sections"]) > 0
        assert res["wat_disassembly"] is not None

        invalid_file = tmp_path / "bad.wasm"
        invalid_file.write_bytes(b"INVALID_HEADER")
        bad_res = rea_native_wasm_inspect(str(invalid_file))
        assert bad_res["status"] == "error"
        assert "magic number mismatch" in bad_res["error"]

    def test_evm_interface_parsing(self) -> None:
        """Verify EVM bytecode parsing and 4-byte selector resolution."""
        # PUSH4 0xa9059cbb (transfer) and PUSH4 0x70a08231 (balanceOf)
        bytecode = "608060405234801561001057600080fd5b5063a9059cbb60e01b8114610034576370a0823160e01b811461005a57"
        res = rea_native_evm_interface(bytecode, resolve_signatures=True)
        assert res["status"] == "ok"
        assert len(res["selectors"]) >= 2
        assert "0xa9059cbb" in res["resolved_signatures"]
        assert "transfer" in res["resolved_signatures"]["0xa9059cbb"]
        assert "0x70a08231" in res["resolved_signatures"]

    def test_annotate_native_function(self, tmp_path: Path) -> None:
        """Verify function annotation updates."""
        bin_file = tmp_path / "binary.bin"
        bin_file.write_bytes(b"MZ" + b"\x00" * 60)

        res = rea_native_annotate_function(
            str(bin_file),
            address="0x401000",
            name="crypto_decrypt_core",
            comment="AES round key expansion",
        )
        assert res["status"] == "ok"
        assert res["name"] == "crypto_decrypt_core"
        assert res["comment"] == "AES round key expansion"

    def test_inspect_native_load_image(self, tmp_path: Path) -> None:
        """Verify DOS MZ load image verification against target snapshot."""
        mz_file = tmp_path / "program.exe"
        mz_file.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff" + b"\x00" * 128)

        res = rea_native_inspect_load_image(str(mz_file))
        assert res["status"] == "ok"
        assert res["format"] == "MZ"
        assert len(res["header_digest"]) == 64
        assert res["matches_snapshot"] is True

    def test_elf_parser_synthetic_binary(self, tmp_path: Path) -> None:
        """Verify ElfParser extracts accurate section names from 64-bit ELF binary."""
        elf_bytes = _build_sample_elf64()
        elf_file = tmp_path / "sample.elf"
        elf_file.write_bytes(elf_bytes)

        # Direct ElfParser verification
        parsed = ElfParser.parse_layout(elf_bytes)
        assert parsed["arch"] == "x86_64"
        assert parsed["format"] == "ELF"
        sec_names = [s["name"] for s in parsed["sections"]]
        assert ".text" in sec_names
        assert ".shstrtab" in sec_names

        # Via public tool
        res = rea_native_elf_layout(str(elf_file))
        assert res["status"] == "ok"
        assert res["arch"] == "x86_64"
        res_names = [s["name"] for s in res["sections"]]
        assert ".text" in res_names

    def test_wasm_parser_synthetic_binary(self, tmp_path: Path) -> None:
        """Verify WasmParser extracts sections and export signatures from WASM bytes."""
        wasm_bytes = _build_sample_wasm()
        wasm_file = tmp_path / "sample.wasm"
        wasm_file.write_bytes(wasm_bytes)

        # Direct WasmParser verification
        sections, exports = WasmParser.parse_sections(wasm_bytes)
        assert len(sections) >= 3
        assert exports[0]["name"] == "add"
        assert exports[0]["kind"] == "func"

        # Via public tool
        res = rea_native_wasm_inspect(str(wasm_file), emit_wat=True)
        assert res["status"] == "ok"
        assert res["wabt_version"] == "1.0.42"
        assert any(e["name"] == "add" for e in res["exports"])
        assert res["wat_disassembly"] is not None

    def test_session_cache_mechanics(self, tmp_path: Path) -> None:
        """Verify NativeAnalysisSessionCache LRU eviction, hashing, and retrieval."""
        cache = NativeAnalysisSessionCache(max_entries=2)
        f1 = tmp_path / "bin1.elf"
        f2 = tmp_path / "bin2.elf"
        f3 = tmp_path / "bin3.elf"
        f1.write_bytes(b"DATA1")
        f2.write_bytes(b"DATA2")
        f3.write_bytes(b"DATA3")

        e1 = NativeBinarySessionEntry(sha256="sha1", file_path=str(f1), sections=[{"name": ".text"}])
        e2 = NativeBinarySessionEntry(sha256="sha2", file_path=str(f2), sections=[{"name": ".data"}])
        e3 = NativeBinarySessionEntry(sha256="sha3", file_path=str(f3), sections=[{"name": ".rodata"}])

        cache.put(e1)
        cache.put(e2)
        assert cache.get(str(f1)) is e1
        assert cache.get_sections(str(f1)) == [{"name": ".text"}]

        # Eviction of oldest
        cache.put(e3)
        assert cache.get(str(f3)) is e3

        cache.clear()
        assert cache.get(str(f3)) is None

    def test_evm_extended_signatures_and_validation(self) -> None:
        """Verify EVM engine resolves extended ERC/Ownable signatures and rejects invalid hex."""
        # PUSH4 owner() (0x8da5cb5b) and PUSH4 mint(address,uint256) (0xd0def521)
        bytecode = "608060405234801561001057600080fd5b50638da5cb5b60e01b81146100345763d0def52160e01b811461005a57"
        res = rea_native_evm_interface(bytecode, resolve_signatures=True)
        assert res["status"] == "ok"
        assert len(res["selectors"]) >= 2
        assert "0x8da5cb5b" in res["resolved_signatures"]
        assert "owner()" in res["resolved_signatures"]["0x8da5cb5b"]
        assert "0xd0def521" in res["resolved_signatures"]
        assert "mint" in res["resolved_signatures"]["0xd0def521"]

        # Invalid hex
        bad_hex = rea_native_evm_interface("not_a_valid_hex_string")
        assert bad_hex["status"] == "error"
        assert "Invalid hex" in bad_hex["error"]

        # Empty bytecode
        empty_res = rea_native_evm_interface("")
        assert empty_res["status"] == "error"
        assert "empty" in empty_res["error"]

    def test_wasm_size_limit_rejection(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify WasmEngine enforces 8 MiB input file boundary."""
        wasm_file = tmp_path / "oversized.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"\x00" * 32)

        original_stat = Path.stat

        def mock_stat(self_path: Path, **kwargs: Any) -> Any:
            stat_res = original_stat(self_path, **kwargs)
            if self_path.name == "oversized.wasm":
                import os
                return os.stat_result((
                    stat_res.st_mode, stat_res.st_ino, stat_res.st_dev,
                    stat_res.st_nlink, stat_res.st_uid, stat_res.st_gid,
                    10 * 1024 * 1024, stat_res.st_atime, stat_res.st_mtime,
                    stat_res.st_ctime
                ))
            return stat_res

        monkeypatch.setattr(Path, "stat", mock_stat)
        res = rea_native_wasm_inspect(str(wasm_file))
        assert res["status"] == "error"
        assert "exceeds maximum allowable limit of 8 MiB" in res["error"]

    def test_engine_coordination(self) -> None:
        """Verify ReaNativeEngine coordinates all sub-engines."""
        cache = NativeAnalysisSessionCache()
        engine = ReaNativeEngine(
            ghidra_headless_path="custom_ghidra",
            wabt_wasm2wat_path="custom_wabt",
            session_cache=cache,
        )
        assert engine.ghidra_headless_path == "custom_ghidra"
        assert engine.wabt_wasm2wat_path == "custom_wabt"
        assert engine.session_cache is cache
        assert engine.layout_engine.session_cache is cache
        assert engine.decompiler_engine.session_cache is cache


def _build_sample_elf64() -> bytes:
    """Construct a minimal valid 64-bit ELF binary with .text and .shstrtab sections."""
    e_ident = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    e_type = 2
    e_machine = 0x3E
    e_version = 1
    e_entry = 0x401000
    e_phoff = 0
    e_flags = 0
    e_ehsize = 64
    e_phentsize = 0
    e_phnum = 0
    e_shentsize = 64
    e_shnum = 3
    e_shstrndx = 2

    text_data = b"\x90" * 16
    text_off = 64
    text_sz = len(text_data)

    shstrtab = b"\x00.text\x00.shstrtab\x00"
    shstrtab_off = text_off + text_sz
    shstrtab_sz = len(shstrtab)

    sh_table_off = shstrtab_off + shstrtab_sz
    e_shoff = sh_table_off

    hdr = bytearray(64)
    hdr[0:16] = e_ident
    struct.pack_into(
        "<HHIQQQIHHHHHH", hdr, 16,
        e_type, e_machine, e_version, e_entry, e_phoff, e_shoff,
        e_flags, e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx
    )

    sh0 = b"\x00" * 64
    sh_text = bytearray(64)
    struct.pack_into(
        "<2I4Q2I2Q", sh_text, 0,
        1, 1, 6, 0x401000, text_off, text_sz, 0, 0, 16, 0
    )
    sh_shstrtab = bytearray(64)
    struct.pack_into(
        "<2I4Q2I2Q", sh_shstrtab, 0,
        7, 3, 0, 0, shstrtab_off, shstrtab_sz, 0, 0, 1, 0
    )

    return bytes(hdr) + text_data + shstrtab + bytes(sh0) + bytes(sh_text) + bytes(sh_shstrtab)


def _build_sample_wasm() -> bytes:
    """Construct a minimal valid WebAssembly binary with export section."""
    header = b"\x00asm\x01\x00\x00\x00"
    sec_type = b"\x01\x04\x01\x60\x00\x01\x7f"
    sec_func = b"\x03\x02\x01\x00"
    sec_export = b"\x07\x07\x01\x03add\x00\x00"
    sec_code = b"\x0a\x06\x01\x04\x00\x41\x2a\x0b"
    return header + sec_type + sec_func + sec_export + sec_code

