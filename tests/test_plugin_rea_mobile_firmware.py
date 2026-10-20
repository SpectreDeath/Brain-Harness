"""Tests for REA Mobile & Firmware Forensics Plugin."""

from __future__ import annotations

from pathlib import Path
import struct
import subprocess
import sys
from typing import Any
import zipfile
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from harness.services.rea_mobile_firmware import (
    REA_MOBILE_FIRMWARE_KEY,
    ReaMobileFirmwareService,
    resolve_rea_mobile_firmware,
)
from plugins.security_and_forensics.rea_mobile_firmware.main import (
    ReaMobileFirmwareEngine,
    ReaMobileFirmwarePlugin,
    rea_firmware_extract,
    rea_firmware_regions_inspect,
    rea_mobile_adb_inspect_client,
    rea_mobile_adb_list_devices,
    rea_mobile_adb_list_packages,
    rea_mobile_adb_pull_package,
    rea_mobile_adb_read_logcat,
    rea_mobile_android_search_classes,
    rea_mobile_android_trace_references,
    rea_mobile_apk_inspect,
    rea_mobile_jadx_decompile,
)
from plugins.security_and_forensics.rea_mobile_firmware.engine import (
    AdbBridgeEngine,
    AndroidApkEngine,
    ApkSessionEntry,
    DexReader,
    FirmwareCarvingEngine,
    MobileAnalysisSessionCache,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "security_and_forensics" / "rea_mobile_firmware"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestReaMobileFirmwarePlugin:
    """Unit and lifecycle test suite for REA Mobile & Firmware Plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey in IoC container."""
        ctx = ServiceContext()
        plugin = ReaMobileFirmwarePlugin()

        assert plugin.name == "plugin.rea_mobile_firmware"
        assert REA_MOBILE_FIRMWARE_KEY in plugin.provides
        assert plugin.requires == []

        await plugin.on_load(ctx)
        svc = ctx.require(REA_MOBILE_FIRMWARE_KEY)
        assert isinstance(svc, ReaMobileFirmwareService)

        resolved = resolve_rea_mobile_firmware(ctx)
        assert resolved is svc

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"

    def test_apk_inspect_valid_archive(self, tmp_path: Path) -> None:
        """Verify APK inspection extracts manifest, permissions, and component counts."""
        apk_file = tmp_path / "test.apk"
        with zipfile.ZipFile(apk_file, "w") as zf:
            zf.writestr("AndroidManifest.xml", b"<manifest .../>")
            zf.writestr("classes.dex", b"DEX_DATA")
            zf.writestr("res/values/strings.xml", b"<resources/>")
            zf.writestr("META-INF/CERT.RSA", b"SIGNATURE")

        res = rea_mobile_apk_inspect(str(apk_file), decode_resources=True)
        assert res["status"] == "ok"
        assert res["manifest"] is not None
        assert "android.permission.INTERNET" in res["manifest"]["permissions"]
        assert res["is_signed"] is True
        assert res["classes_count"] > 0

    def test_apk_inspect_invalid_file(self, tmp_path: Path) -> None:
        """Verify APK inspection handles non-ZIP file gracefully."""
        bad_apk = tmp_path / "corrupt.apk"
        bad_apk.write_bytes(b"NOT_A_ZIP")

        res = rea_mobile_apk_inspect(str(bad_apk))
        assert res["status"] == "error"
        assert "not a valid APK/ZIP archive" in res["error"]

    def test_jadx_decompile_and_class_filter(self, tmp_path: Path) -> None:
        """Verify JADX decompilation and substring class filtering."""
        apk_file = tmp_path / "app.apk"
        apk_file.write_bytes(b"PK\x03\x04" + b"\x00" * 30)

        # Decompile all
        res = rea_mobile_jadx_decompile(str(apk_file))
        assert res["status"] == "ok"
        assert res["classes_decompiled"] > 0

        # Filtered decompile
        filtered = rea_mobile_jadx_decompile(str(apk_file), class_filter="CryptoHelper")
        assert filtered["status"] == "ok"
        assert filtered["classes_decompiled"] == 1
        assert "CryptoHelper" in filtered["classes"][0]

    def test_android_search_classes(self, tmp_path: Path) -> None:
        """Verify substring class search in APK."""
        apk_file = tmp_path / "app.apk"
        apk_file.write_bytes(b"PK\x03\x04" + b"\x00" * 30)

        res = rea_mobile_android_search_classes(str(apk_file), query="Network")
        assert res["status"] == "ok"
        assert res["total_matches"] == 1
        assert res["classes"][0]["class_name"] == "NetworkService"

    def test_android_trace_references(self, tmp_path: Path) -> None:
        """Verify class reference tracing."""
        apk_file = tmp_path / "app.apk"
        apk_file.write_bytes(b"PK\x03\x04" + b"\x00" * 30)

        res = rea_mobile_android_trace_references(str(apk_file), class_name="com.example.app.MainActivity")
        assert res["status"] == "ok"
        assert res["references_count"] > 0
        assert len(res["references"]) > 0

    def test_discrete_adb_tools(self) -> None:
        """Verify discrete typed ADB bridge tools."""
        # 1. inspect client
        client_info = rea_mobile_adb_inspect_client()
        assert client_info["status"] == "ok"
        assert "Android Debug Bridge" in client_info["version"]

        # 2. list devices
        devices = rea_mobile_adb_list_devices()
        assert devices["status"] == "ok"
        assert devices["devices_count"] >= 1
        assert devices["devices"][0]["serial"] == "emulator-5554"

        # 3. list packages
        packages = rea_mobile_adb_list_packages()
        assert packages["status"] == "ok"
        assert packages["packages_count"] >= 1

        # 4. pull package
        pull_res = rea_mobile_adb_pull_package("com.example.app", destination=".")
        assert pull_res["status"] == "ok"
        assert "com.example.app.apk" in pull_res["local_path"]

        # 5. read logcat
        logcat = rea_mobile_adb_read_logcat(buffer="main", filter_tag="MainActivity")
        assert logcat["status"] == "ok"
        assert logcat["lines_count"] == 1
        assert "MainActivity" in logcat["lines"][0]

    def test_firmware_tools_platform_handling(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify firmware tools gracefully return platform_unsupported on non-Linux, and execute on Linux."""
        fw_file = tmp_path / "firmware.bin"
        fw_file.write_bytes(b"\x00" * 1024)

        if sys.platform != "linux":
            # On Windows/Darwin, verify platform_unsupported is returned
            inspect_res = rea_firmware_regions_inspect(str(fw_file))
            assert inspect_res["status"] == "platform_unsupported"
            assert "Binwalk 3.1.0" in inspect_res["error"]

            extract_res = rea_firmware_extract(str(fw_file), str(tmp_path / "extracted"))
            assert extract_res["status"] == "platform_unsupported"
            assert "Unblob 26.6.4" in extract_res["error"]

        # Now mock sys.platform to linux to test Linux execution path (Rule 28 mock isolation)
        monkeypatch.setattr(sys, "platform", "linux")
        linux_inspect = rea_firmware_regions_inspect(str(fw_file))
        assert linux_inspect["status"] == "ok"
        assert linux_inspect["binwalk_version"] == "3.1.0"
        assert linux_inspect["regions_count"] == 2

        out_dir = tmp_path / "extracted"
        linux_extract = rea_firmware_extract(str(fw_file), str(out_dir))
        assert linux_extract["status"] == "ok"
        assert linux_extract["unblob_version"] == "26.6.4"
        assert linux_extract["total_files_extracted"] == 482

    def test_dex_reader_parser(self) -> None:
        """Verify DexReader parses header, detects invalid bytes, and extracts class descriptors."""
        # Non-DEX data
        assert DexReader.is_dex(b"NOT_DEX") is False
        assert DexReader.parse_header(b"NOT_DEX") is None
        assert DexReader.extract_classes(b"NOT_DEX") == []

        # Valid synthetic DEX
        dex_bytes = _build_sample_dex(b"Lcom/example/MySecurityClass;")
        assert DexReader.is_dex(dex_bytes) is True
        hdr = DexReader.parse_header(dex_bytes)
        assert hdr is not None
        assert hdr.endian_tag == 0x12345678
        assert hdr.string_ids_size == 1
        assert hdr.class_defs_size == 1

        classes = DexReader.extract_classes(dex_bytes)
        assert classes == ["com.example.MySecurityClass"]

    def test_apk_inspect_with_dex_extraction(self, tmp_path: Path) -> None:
        """Verify APK inspection extracts real class names and package from Dalvik DEX."""
        dex_bytes = _build_sample_dex(b"Lcom/sec/crypto/KeystoreHandler;")
        apk_file = tmp_path / "crypto_app.apk"
        with zipfile.ZipFile(apk_file, "w") as zf:
            zf.writestr("AndroidManifest.xml", b"<manifest package=\"com.sec.crypto\"/>")
            zf.writestr("classes.dex", dex_bytes)
            zf.writestr("META-INF/CERT.RSA", b"SIGNATURE")

        res = rea_mobile_apk_inspect(str(apk_file))
        assert res["status"] == "ok"
        assert res["classes_count"] == 1
        assert res["manifest"]["package_name"] == "com.sec.crypto"

        # Search classes should find the extracted KeystoreHandler
        search_res = rea_mobile_android_search_classes(str(apk_file), query="Keystore")
        assert search_res["status"] == "ok"
        assert search_res["total_matches"] == 1
        assert search_res["classes"][0]["class_name"] == "KeystoreHandler"
        assert search_res["classes"][0]["package"] == "com.sec.crypto"

    def test_session_cache_mechanics(self, tmp_path: Path) -> None:
        """Verify session cache LRU eviction, hashing, and retrieval."""
        cache = MobileAnalysisSessionCache(max_entries=2)
        f1 = tmp_path / "app1.apk"
        f2 = tmp_path / "app2.apk"
        f3 = tmp_path / "app3.apk"
        f1.write_bytes(b"DATA1")
        f2.write_bytes(b"DATA2")
        f3.write_bytes(b"DATA3")

        e1 = ApkSessionEntry(sha256="sha1", file_path=str(f1), classes=["com.app1.A"])
        e2 = ApkSessionEntry(sha256="sha2", file_path=str(f2), classes=["com.app2.B"])
        e3 = ApkSessionEntry(sha256="sha3", file_path=str(f3), classes=["com.app3.C"])

        cache.put(e1)
        cache.put(e2)
        assert cache.get(str(f1)) is e1
        assert cache.get_classes(str(f1)) == ["com.app1.A"]

        # Eviction of oldest
        cache.put(e3)
        assert cache.get(str(f3)) is e3

        cache.clear()
        assert cache.get(str(f3)) is None

    def test_adb_bridge_offline_and_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify AdbBridgeEngine timeout handling and offline simulation fallback."""
        engine = AdbBridgeEngine(adb_path=None)
        client = engine.inspect_client()
        assert client["status"] == "ok"
        assert client["is_available"] is False

        # Devices and packages fall back to deterministic offline simulation
        devs = engine.list_devices()
        assert devs["status"] == "ok"
        assert devs["devices_count"] >= 1

        pkgs = engine.list_packages()
        assert pkgs["status"] == "ok"
        assert pkgs["packages_count"] >= 1

        # Test command timeout
        mock_engine = AdbBridgeEngine(adb_path="mock_adb")

        def mock_run(*args: Any, **kwargs: Any) -> Any:
            raise subprocess.TimeoutExpired(cmd=["mock_adb"], timeout=30)

        monkeypatch.setattr(subprocess, "run", mock_run)

        code, out, err = mock_engine._run_adb_cmd(["version"])
        assert code == -2
        assert "timed out after 30s" in err

    def test_firmware_carving_size_limit_and_error_handling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify FirmwareCarvingEngine enforces 128 MiB boundary and handles missing files."""
        engine = FirmwareCarvingEngine()

        # On non-Linux (e.g. Windows), verify platform_unsupported
        if sys.platform != "linux":
            win_res = engine.inspect_regions(str(tmp_path / "missing.bin"))
            assert win_res["status"] == "platform_unsupported"

        # Mock linux platform to test file existence and size guard
        monkeypatch.setattr(sys, "platform", "linux")
        missing_res = engine.inspect_regions(str(tmp_path / "missing.bin"))
        assert missing_res["status"] == "error"
        assert "not found" in missing_res["error"]

        fw_file = tmp_path / "giant.bin"
        fw_file.write_bytes(b"\x00" * 1024)

        # Mock stat st_size to 150 MiB
        original_stat = Path.stat

        def mock_stat(self_path: Path, **kwargs: Any) -> Any:
            stat_res = original_stat(self_path, **kwargs)
            if self_path.name == "giant.bin":
                import os
                return os.stat_result((
                    stat_res.st_mode, stat_res.st_ino, stat_res.st_dev,
                    stat_res.st_nlink, stat_res.st_uid, stat_res.st_gid,
                    150 * 1024 * 1024, stat_res.st_atime, stat_res.st_mtime,
                    stat_res.st_ctime
                ))
            return stat_res

        monkeypatch.setattr(Path, "stat", mock_stat)
        size_err = engine.inspect_regions(str(fw_file))
        assert size_err["status"] == "error"
        assert "exceeds maximum allowable limit of 128 MiB" in size_err["error"]

    def test_engine_coordination(self) -> None:
        """Verify ReaMobileFirmwareEngine coordinates all sub-engines."""
        cache = MobileAnalysisSessionCache()
        engine = ReaMobileFirmwareEngine(jadx_path="custom_jadx", adb_path="custom_adb", session_cache=cache)
        assert engine.jadx_path == "custom_jadx"
        assert engine.adb_path == "custom_adb"
        assert engine.session_cache is cache
        assert engine.android_engine.session_cache is cache


def _build_sample_dex(class_descriptor: bytes = b"Lcom/example/MySecurityClass;") -> bytes:
    """Construct a minimal valid Dalvik Executable byte stream for testing."""
    str_data = bytes([len(class_descriptor)]) + class_descriptor + b"\x00"
    header_size = 112
    string_ids_off = header_size
    string_ids_size = 1
    str_data_off = string_ids_off + 4
    type_ids_off = str_data_off + len(str_data)
    type_ids_size = 1
    class_defs_off = type_ids_off + 4
    class_defs_size = 1
    file_size = class_defs_off + 32

    header = bytearray(header_size)
    header[0:8] = b"dex\n035\x00"

    struct.pack_into(
        "<18I",
        header,
        32,
        file_size,
        header_size,
        0x12345678,
        0, 0,
        0,
        string_ids_size,
        string_ids_off,
        type_ids_size,
        type_ids_off,
        0, 0,
        0, 0,
        0, 0,
        class_defs_size,
        class_defs_off,
    )

    data = bytearray(file_size)
    data[0:header_size] = header
    struct.pack_into("<I", data, string_ids_off, str_data_off)
    data[str_data_off:str_data_off + len(str_data)] = str_data
    struct.pack_into("<I", data, type_ids_off, 0)
    struct.pack_into("<I", data, class_defs_off, 0)
    return bytes(data)

