"""Domain-partitioned service exports: _security_and_forensics."""
from __future__ import annotations

from harness.services.pre_commit_security_guard import (
    PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY,
    DualGateCheckData,
    PreCommitSecurityGuardService,
    SarifExportData,
    ScanReportData,
    SecurityFindingData,
    SmokeCheckData,
    SmokeReportData,
    SuppressionCheckData,
    SuppressionReportData,
)

from harness.services.network_forensics import (
    CleartextExposureData,
    DiagnosticChainReportData,
    HopAnalysisData,
    LayerDiagnosticData,
    NETWORK_FORENSICS_KEY,
    NetworkForensicsService,
    PortEvaluationData,
    PortReconReportData,
    SubnetGeometryData,
    TCPFlagAnalysisData,
    TracerouteReportData,
)

from harness.services.rea_native import (
    REA_NATIVE_KEY,
    BatchDecompileReport,
    CallGraphReport,
    ElfLayoutReport,
    EvmInterfaceReport,
    FunctionAnnotationReport,
    LoadImageReport,
    ReaNativeService,
    WasmInspectReport,
    resolve_rea_native,
)

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
    resolve_rea_mobile_firmware,
)

from harness.services.pyrit_scanner import (
    PYRIT_SCANNER_SERVICE_KEY,
    AttackVector,
    DefaultPyritScannerService,
    PyritScannerService,
    PyritSubprocessRunner,
    RedTeamTarget,
    VulnerabilityScorecard,
    resolve_pyrit_scanner,
)
