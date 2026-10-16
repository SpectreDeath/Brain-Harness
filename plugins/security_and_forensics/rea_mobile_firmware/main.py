"""REA Mobile & Firmware Forensics Plugin for Brain Harness.

Deepened architecture decomposing Android APK analysis (pure-Python DEX parsing),
ADB device communications, and Linux-isolated firmware carving into focused domain engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.rea_mobile_firmware import (
    REA_MOBILE_FIRMWARE_KEY,
    AdbClientReport,
    AdbListDevicesReport,
    AdbListPackagesReport,
    AdbPullPackageReport,
    AdbReadLogcatReport,
    AndroidClassSearchReport,
    AndroidTraceReferencesReport,
    ApkInspectReport,
    FirmwareExtractReport,
    FirmwareRegionsReport,
    JadxDecompileReport,
    ReaMobileFirmwareService,
)
from plugins.security_and_forensics.rea_mobile_firmware.engine import (
    AdbBridgeEngine,
    AndroidApkEngine,
    FirmwareCarvingEngine,
    MobileAnalysisSessionCache,
)

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# Deepened Domain Engine Coordinating Specialized Sub-Engines
# -----------------------------------------------------------------------------


class ReaMobileFirmwareEngine:
    """Coordinating domain facade delegating to specialized Android, ADB, and Firmware engines."""

    def __init__(
        self,
        jadx_path: str | None = None,
        adb_path: str | None = None,
        session_cache: MobileAnalysisSessionCache | None = None,
    ) -> None:
        self.session_cache = session_cache or MobileAnalysisSessionCache()
        self.android_engine = AndroidApkEngine(
            jadx_path=jadx_path, session_cache=self.session_cache
        )
        self.adb_engine = AdbBridgeEngine(adb_path=adb_path)
        self.firmware_engine = FirmwareCarvingEngine()

    @property
    def jadx_path(self) -> str | None:
        return self.android_engine.jadx_path

    @property
    def adb_path(self) -> str | None:
        return self.adb_engine.adb_path

    # --- Android APK Operations ---

    def apk_inspect(
        self,
        apk_path: str,
        decode_resources: bool = True,
    ) -> dict[str, Any]:
        """Inspect APK manifest, package identity, permissions, and resources."""
        return self.android_engine.apk_inspect(apk_path=apk_path, decode_resources=decode_resources)

    def jadx_decompile(
        self,
        apk_path: str,
        class_filter: str | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Decompile Dalvik bytecode into Java/Smali source trees via JADX."""
        return self.android_engine.jadx_decompile(
            apk_path=apk_path, class_filter=class_filter, output_dir=output_dir
        )

    def android_search_classes(
        self,
        apk_path: str,
        query: str,
    ) -> dict[str, Any]:
        """Search class names by case-sensitive substring."""
        return self.android_engine.search_classes(apk_path=apk_path, query=query)

    android_class_search = android_search_classes

    def android_trace_references(
        self,
        apk_path: str,
        class_name: str,
        method_name: str | None = None,
    ) -> dict[str, Any]:
        """Trace static incoming references to a class or unique method."""
        return self.android_engine.trace_references(
            apk_path=apk_path, class_name=class_name, method_name=method_name
        )

    # --- ADB Device Operations ---

    def adb_inspect_client(self) -> dict[str, Any]:
        """Report resolved adb binary path, version, and install source."""
        return self.adb_engine.inspect_client()

    def adb_list_devices(self) -> dict[str, Any]:
        """Enumerate attached devices and emulators."""
        return self.adb_engine.list_devices()

    def adb_list_packages(
        self,
        device_serial: str | None = None,
    ) -> dict[str, Any]:
        """List installed packages on target device with base APK paths."""
        return self.adb_engine.list_packages(device_serial=device_serial)

    def adb_pull_package(
        self,
        package_name: str,
        device_serial: str | None = None,
        destination: str = ".",
    ) -> dict[str, Any]:
        """Pull a device-installed APK to a local path."""
        return self.adb_engine.pull_package(
            package_name=package_name, device_serial=device_serial, destination=destination
        )

    def adb_read_logcat(
        self,
        device_serial: str | None = None,
        buffer: str = "main",
        filter_tag: str | None = None,
        max_lines: int = 500,
    ) -> dict[str, Any]:
        """Bounded adb logcat dump for a given buffer and optional tag filter."""
        return self.adb_engine.read_logcat(
            device_serial=device_serial, buffer=buffer, filter_tag=filter_tag, max_lines=max_lines
        )

    # --- Firmware Carving Operations ---

    def firmware_inspect_regions(
        self,
        firmware_path: str,
    ) -> dict[str, Any]:
        """Scan binary with Binwalk 3.1.0 for signature candidates (Linux-only)."""
        return self.firmware_engine.inspect_regions(firmware_path=firmware_path)

    def firmware_extract(
        self,
        firmware_path: str,
        destination_dir: str,
    ) -> dict[str, Any]:
        """Unpack embedded partitions via Unblob 26.6.4 (Linux-only)."""
        return self.firmware_engine.extract(
            firmware_path=firmware_path, destination_dir=destination_dir
        )


_GLOBAL_ENGINE = ReaMobileFirmwareEngine()


# -----------------------------------------------------------------------------
# Top-Level Entrypoint Tool Handlers Matching Manifest Signatures
# -----------------------------------------------------------------------------


def rea_mobile_apk_inspect(
    apk_path: str,
    decode_resources: bool = True,
) -> dict[str, Any]:
    """Inspect APK manifest, package identity, permissions, SDK levels, and component counts."""
    return _GLOBAL_ENGINE.apk_inspect(apk_path=apk_path, decode_resources=decode_resources)


def rea_mobile_jadx_decompile(
    apk_path: str,
    class_filter: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Decompile Dalvik bytecode into Java/Smali source trees via headless JADX."""
    return _GLOBAL_ENGINE.jadx_decompile(apk_path=apk_path, class_filter=class_filter, output_dir=output_dir)


def rea_mobile_android_search_classes(
    apk_path: str,
    query: str,
) -> dict[str, Any]:
    """Search decompiler class names by case-sensitive substring."""
    return _GLOBAL_ENGINE.android_search_classes(apk_path=apk_path, query=query)


def rea_mobile_android_trace_references(
    apk_path: str,
    class_name: str,
    method_name: str | None = None,
) -> dict[str, Any]:
    """Trace static incoming references to a class or unique method across the decompiled APK."""
    return _GLOBAL_ENGINE.android_trace_references(apk_path=apk_path, class_name=class_name, method_name=method_name)


def rea_mobile_adb_inspect_client() -> dict[str, Any]:
    """Report resolved adb binary path, version, and install source without contacting devices."""
    return _GLOBAL_ENGINE.adb_inspect_client()


def rea_mobile_adb_list_devices() -> dict[str, Any]:
    """Enumerate attached devices and emulators with state, model, and serial metadata."""
    return _GLOBAL_ENGINE.adb_list_devices()


def rea_mobile_adb_list_packages(
    device_serial: str | None = None,
) -> dict[str, Any]:
    """List installed packages on one device with base APK paths."""
    return _GLOBAL_ENGINE.adb_list_packages(device_serial=device_serial)


def rea_mobile_adb_pull_package(
    package_name: str,
    device_serial: str | None = None,
    destination: str = ".",
) -> dict[str, Any]:
    """Pull a device-installed APK to a local path."""
    return _GLOBAL_ENGINE.adb_pull_package(package_name=package_name, device_serial=device_serial, destination=destination)


def rea_mobile_adb_read_logcat(
    device_serial: str | None = None,
    buffer: str = "main",
    filter_tag: str | None = None,
    max_lines: int = 500,
) -> dict[str, Any]:
    """Bounded adb logcat dump for a given buffer and optional tag filter."""
    return _GLOBAL_ENGINE.adb_read_logcat(device_serial=device_serial, buffer=buffer, filter_tag=filter_tag, max_lines=max_lines)


def rea_firmware_regions_inspect(
    firmware_path: str,
) -> dict[str, Any]:
    """Scan binary with Binwalk 3.1.0 for signature candidates (Linux-only)."""
    return _GLOBAL_ENGINE.firmware_inspect_regions(firmware_path=firmware_path)


def rea_firmware_extract(
    firmware_path: str,
    destination_dir: str,
) -> dict[str, Any]:
    """Unpack embedded partitions via Unblob 26.6.4 into structured file trees (Linux-only)."""
    return _GLOBAL_ENGINE.firmware_extract(firmware_path=firmware_path, destination_dir=destination_dir)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------


class ReaMobileFirmwarePlugin(HarnessPlugin, ReaMobileFirmwareService):
    """Brain Harness Plugin providing Android mobile and firmware reverse engineering capabilities."""

    name = "plugin.rea_mobile_firmware"
    version = "1.0.0"
    description = (
        "REA Android APK static inspection, JADX decompilation, reference tracing, "
        "discrete ADB device bridging, and Linux Binwalk/Unblob firmware carving."
    )
    trusted = True

    def __init__(self, engine: ReaMobileFirmwareEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REA_MOBILE_FIRMWARE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REA_MOBILE_FIRMWARE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation Delegations
    # -------------------------------------------------------------------------

    def apk_inspect(
        self,
        apk_path: str,
        decode_resources: bool = True,
    ) -> dict[str, Any]:
        return self._engine.apk_inspect(apk_path=apk_path, decode_resources=decode_resources)

    def jadx_decompile(
        self,
        apk_path: str,
        class_filter: str | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.jadx_decompile(apk_path=apk_path, class_filter=class_filter, output_dir=output_dir)

    def android_class_search(
        self,
        apk_path: str,
        query: str,
    ) -> dict[str, Any]:
        return self._engine.android_search_classes(apk_path=apk_path, query=query)

    def android_search_classes(
        self,
        apk_path: str,
        query: str,
    ) -> dict[str, Any]:
        return self._engine.android_search_classes(apk_path=apk_path, query=query)

    def android_trace_references(
        self,
        apk_path: str,
        class_name: str,
        method_name: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.android_trace_references(apk_path=apk_path, class_name=class_name, method_name=method_name)

    def adb_inspect_client(self) -> dict[str, Any]:
        return self._engine.adb_inspect_client()

    def adb_list_devices(self) -> dict[str, Any]:
        return self._engine.adb_list_devices()

    def adb_list_packages(
        self,
        device_serial: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.adb_list_packages(device_serial=device_serial)

    def adb_pull_package(
        self,
        package_name: str,
        device_serial: str | None = None,
        destination: str = ".",
    ) -> dict[str, Any]:
        return self._engine.adb_pull_package(package_name=package_name, device_serial=device_serial, destination=destination)

    def adb_read_logcat(
        self,
        device_serial: str | None = None,
        buffer: str = "main",
        filter_tag: str | None = None,
        max_lines: int = 500,
    ) -> dict[str, Any]:
        return self._engine.adb_read_logcat(device_serial=device_serial, buffer=buffer, filter_tag=filter_tag, max_lines=max_lines)

    def firmware_inspect_regions(
        self,
        firmware_path: str,
    ) -> dict[str, Any]:
        return self._engine.firmware_inspect_regions(firmware_path=firmware_path)

    def firmware_extract(
        self,
        firmware_path: str,
        destination_dir: str,
    ) -> dict[str, Any]:
        return self._engine.firmware_extract(firmware_path=firmware_path, destination_dir=destination_dir)


plugin = ReaMobileFirmwarePlugin()
