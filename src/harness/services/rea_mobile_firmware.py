"""REA Mobile & Firmware Forensics Service Protocol, models, and ServiceKey.

Elevates Android APK inspection, JADX decompilation, reference tracing,
ADB device bridging (discrete typed endpoints), and Binwalk/Unblob firmware carving
into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) Android, Apktool, ADB, and Firmware modules.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey


# -----------------------------------------------------------------------------
# Typed Domain Models & Response Envelopes
# -----------------------------------------------------------------------------


class ReaReportBase(BaseModel):
    """Base model with dictionary-style backward compatibility."""

    def __getitem__(self, key: str) -> Any:
        try:
            val = getattr(self, key)
            return val
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class ApkManifestInfo(ReaReportBase):
    """Information extracted from AndroidManifest.xml."""

    package_name: str = ""
    version_code: int = 0
    version_name: str = ""
    min_sdk: int = 21
    target_sdk: int = 34
    permissions: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    receivers: list[str] = Field(default_factory=list)


class ApkInspectReport(ReaReportBase):
    """Result envelope for Android APK static inspection."""

    status: str = "ok"
    apk_path: str
    manifest: ApkManifestInfo | None = None
    classes_count: int = 0
    resources_count: int = 0
    is_signed: bool = True
    error: str | None = None


class JadxDecompileReport(ReaReportBase):
    """Result envelope for JADX headless decompilation."""

    status: str = "ok"
    apk_path: str
    output_dir: str = ""
    classes_decompiled: int = 0
    errors_count: int = 0
    classes: list[str] = Field(default_factory=list)
    error: str | None = None


class AndroidClassMatch(ReaReportBase):
    """Matching class in APK search."""

    class_name: str
    package: str = ""
    methods_count: int = 0


class AndroidClassSearchReport(ReaReportBase):
    """Result envelope for APK class search."""

    status: str = "ok"
    apk_path: str
    query: str
    total_matches: int = 0
    classes: list[AndroidClassMatch] = Field(default_factory=list)
    error: str | None = None


class ReferenceSource(ReaReportBase):
    """Source referencing a target class or method."""

    calling_class: str
    calling_method: str = ""
    instruction_offset: int = 0


class AndroidTraceReferencesReport(ReaReportBase):
    """Result envelope for static reference tracing."""

    status: str = "ok"
    apk_path: str
    target_class: str
    target_method: str | None = None
    references_count: int = 0
    references: list[ReferenceSource] = Field(default_factory=list)
    error: str | None = None


class AdbClientReport(ReaReportBase):
    """Result envelope for ADB client binary inspection."""

    status: str = "ok"
    adb_path: str = ""
    version: str = ""
    is_available: bool = True
    error: str | None = None


class AdbDeviceEntry(ReaReportBase):
    """Entry describing an attached Android device."""

    serial: str
    state: str = "device"  # device, offline, unauthorized, recovery
    model: str = ""
    product: str = ""
    transport_id: str = ""


class AdbListDevicesReport(ReaReportBase):
    """Result envelope for ADB device listing."""

    status: str = "ok"
    devices_count: int = 0
    devices: list[AdbDeviceEntry] = Field(default_factory=list)
    error: str | None = None


class AdbListPackagesReport(ReaReportBase):
    """Result envelope for ADB package listing."""

    status: str = "ok"
    device_serial: str | None = None
    packages_count: int = 0
    packages: list[dict[str, str]] = Field(default_factory=list)  # {"package": name, "path": apk_path}
    error: str | None = None


class AdbPullPackageReport(ReaReportBase):
    """Result envelope for pulling an APK via ADB."""

    status: str = "ok"
    package_name: str
    device_serial: str | None = None
    local_path: str = ""
    bytes_transferred: int = 0
    error: str | None = None


class AdbReadLogcatReport(ReaReportBase):
    """Result envelope for reading logcat via ADB."""

    status: str = "ok"
    device_serial: str | None = None
    buffer: str = "main"
    filter_tag: str | None = None
    lines_count: int = 0
    lines: list[str] = Field(default_factory=list)
    error: str | None = None


class FirmwareRegion(ReaReportBase):
    """Identified region in firmware binary."""

    offset: int
    length: int = 0
    description: str
    confidence: float = 1.0


class FirmwareRegionsReport(ReaReportBase):
    """Result envelope for Binwalk 3.1.0 firmware signature scan."""

    status: str = "ok"
    firmware_path: str
    binwalk_version: str = "3.1.0"
    regions_count: int = 0
    regions: list[FirmwareRegion] = Field(default_factory=list)
    error: str | None = None


class ExtractedPartition(ReaReportBase):
    """Extracted filesystem partition or component."""

    filesystem_type: str  # squashfs, cramfs, jffs2, uboot
    offset: int
    destination: str
    extracted_files_count: int = 0


class FirmwareExtractReport(ReaReportBase):
    """Result envelope for Unblob 26.6.4 firmware unpacking."""

    status: str = "ok"
    firmware_path: str
    destination_dir: str
    unblob_version: str = "26.6.4"
    partitions: list[ExtractedPartition] = Field(default_factory=list)
    total_files_extracted: int = 0
    error: str | None = None


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Service Protocol & Key
# -----------------------------------------------------------------------------


@runtime_checkable
class ReaMobileFirmwareService(Protocol):
    """Protocol for Android mobile and firmware reverse engineering operations."""

    def apk_inspect(
        self,
        apk_path: str,
        decode_resources: bool = True,
    ) -> ApkInspectReport | dict[str, Any]:
        """Inspect APK manifest, permissions, SDK levels, and resources."""
        ...

    def jadx_decompile(
        self,
        apk_path: str,
        class_filter: str | None = None,
        output_dir: str | None = None,
    ) -> JadxDecompileReport | dict[str, Any]:
        """Decompile Dalvik bytecode into Java/Smali source trees via JADX."""
        ...

    def android_class_search(
        self,
        apk_path: str,
        query: str,
    ) -> AndroidClassSearchReport | dict[str, Any]:
        """Search decompiler class names by substring."""
        ...

    def android_trace_references(
        self,
        apk_path: str,
        class_name: str,
        method_name: str | None = None,
    ) -> AndroidTraceReferencesReport | dict[str, Any]:
        """Trace static incoming references to a class or method across the APK."""
        ...

    def adb_inspect_client(self) -> AdbClientReport | dict[str, Any]:
        """Report resolved adb binary path, version, and install source without contacting devices."""
        ...

    def adb_list_devices(self) -> AdbListDevicesReport | dict[str, Any]:
        """Enumerate attached devices and emulators."""
        ...

    def adb_list_packages(
        self,
        device_serial: str | None = None,
    ) -> AdbListPackagesReport | dict[str, Any]:
        """List installed packages and their base APK paths on a device."""
        ...

    def adb_pull_package(
        self,
        package_name: str,
        device_serial: str | None = None,
        destination: str = ".",
    ) -> AdbPullPackageReport | dict[str, Any]:
        """Pull a device-installed APK to a local path."""
        ...

    def adb_read_logcat(
        self,
        device_serial: str | None = None,
        buffer: str = "main",
        filter_tag: str | None = None,
        max_lines: int = 500,
    ) -> AdbReadLogcatReport | dict[str, Any]:
        """Bounded adb logcat dump for a given buffer and optional tag filter."""
        ...

    def firmware_inspect_regions(
        self,
        firmware_path: str,
    ) -> FirmwareRegionsReport | dict[str, Any]:
        """Scan binary with Binwalk 3.1.0 for signature candidates (Linux-only)."""
        ...

    def firmware_extract(
        self,
        firmware_path: str,
        destination_dir: str,
    ) -> FirmwareExtractReport | dict[str, Any]:
        """Unpack embedded partitions via Unblob 26.6.4 into structured trees (Linux-only)."""
        ...


REA_MOBILE_FIRMWARE_KEY: ServiceKey[ReaMobileFirmwareService] = ServiceKey(
    "service.rea_mobile_firmware"
)


def resolve_rea_mobile_firmware(ctx: ServiceContext) -> ReaMobileFirmwareService | None:
    """Resolve ReaMobileFirmwareService from context if registered."""
    return ctx.optional(REA_MOBILE_FIRMWARE_KEY)
