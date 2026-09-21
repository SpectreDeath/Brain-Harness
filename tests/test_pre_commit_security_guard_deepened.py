"""Deepened architectural verification suite for Pre-Commit Security Guard.

Tests slotted domain models (Rule 12 & Rule 43), SAST & secret interception engines,
deliberate synthetic smoke gates, suppression hygiene, dual-gate CI parity, SARIF formatting,
IoC service resolution (Rule 49), PluginValidator sync (Rule 38), and Click CLI seams.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "pre-commit-security-guard" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pre_commit_security_engine import (
    PreCommitSecurityGuardEngine,
    ScanReport,
    SecurityFinding,
    SmokeCheckResult,
    calculate_shannon_entropy,
)

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.pre_commit_security_guard import (
    PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY,
    PreCommitSecurityGuardService,
)
from plugins.security_and_forensics.pre_commit_security_guard.main import (
    plugin,
)


@pytest.fixture
def engine() -> PreCommitSecurityGuardEngine:
    return PreCommitSecurityGuardEngine(use_native_devskim=False, use_native_gitleaks=False)


# -----------------------------------------------------------------------------
# 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

def test_frozen_dataclass_immutability() -> None:
    finding = SecurityFinding(
        rule_id="DS126858",
        name="Weak Hash",
        severity="critical",
        scanner="sast_devskim",
        file_path="src/auth.py",
        line_number=42,
    )

    with pytest.raises((AttributeError, TypeError)):
        finding.name = "Mutated Name"

    report = ScanReport(
        target="test_scan",
        passed=True,
        total_files_scanned=1,
        findings=(finding,),
    )
    with pytest.raises((AttributeError, TypeError)):
        report.passed = False

    smoke = SmokeCheckResult(
        fixture_name="test_fixture",
        hazard_type="insecure_crypto",
        expected_failure=True,
        detected=True,
        exit_code=1,
        matched_rule="DS126858",
        passed=True,
        diagnostic="Blocked",
    )
    with pytest.raises((AttributeError, TypeError)):
        smoke.exit_code = 0


# -----------------------------------------------------------------------------
# 2. SAST Vulnerability Detection
# -----------------------------------------------------------------------------

def test_sast_detects_insecure_md5_hash(engine: PreCommitSecurityGuardEngine) -> None:
    code = "import hashlib\ntoken = hashlib.md5(b'user_input').hexdigest()\n"
    findings = engine.scan_code(code, file_path="crypto.py")

    assert len(findings) >= 1
    assert any(f.rule_id == "DS126858" for f in findings)
    assert any(f.severity == "critical" for f in findings)


def test_sast_detects_insecure_des_cipher(engine: PreCommitSecurityGuardEngine) -> None:
    code = "from Crypto.Cipher import DES\ncipher = DES.new(key, DES.MODE_ECB)\n"
    findings = engine.scan_code(code, file_path="cipher.py")

    assert any(f.rule_id == "DS137138" for f in findings)


def test_sast_detects_command_injection_hazard(engine: PreCommitSecurityGuardEngine) -> None:
    code = "import subprocess\nsubprocess.run(user_arg, shell=True)\n"
    findings = engine.scan_code(code, file_path="runner.py")

    assert any(f.rule_id == "DS184626" for f in findings)


def test_sast_clean_code_passes(engine: PreCommitSecurityGuardEngine) -> None:
    code = "import hashlib\nh = hashlib.sha256(b'secure_data').hexdigest()\n"
    findings = engine.scan_code(code, file_path="clean.py")

    assert len(findings) == 0


# -----------------------------------------------------------------------------
# 3. Secret & Shannon Entropy Interception
# -----------------------------------------------------------------------------

def test_secret_detects_aws_key(engine: PreCommitSecurityGuardEngine) -> None:
    code = "AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE'\n"
    findings = engine.scan_code(code, file_path="aws.py")

    assert any(f.rule_id == "GL-AWS-KEY" for f in findings)


def test_secret_detects_github_pat(engine: PreCommitSecurityGuardEngine) -> None:
    code = "GH_TOKEN = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\n"
    findings = engine.scan_code(code, file_path="gh.py")

    assert any(f.rule_id == "GL-GITHUB-TOKEN" for f in findings)


def test_shannon_entropy_calculation() -> None:
    low_entropy = calculate_shannon_entropy("aaaaaaaaaaaaaaaaaaaa")
    assert low_entropy == 0.0

    high_entropy_hex = calculate_shannon_entropy("4f2a9c1e7b6d3a8f0c5e9b2d7a41c6e8d1a3b5c7")
    assert high_entropy_hex > 3.8


def test_secret_detects_high_entropy_string(engine: PreCommitSecurityGuardEngine) -> None:
    code = "raw_token = '4f2a9c1e7b6d3a8f0c5e9b2d7a41c6e8d1a3b5c7'\n"
    findings = engine.scan_code(code, file_path="token.py")

    assert any(f.scanner == "secret_gitleaks" for f in findings)


# -----------------------------------------------------------------------------
# 4. Deliberate Synthetic Failure Verification (Stage 3)
# -----------------------------------------------------------------------------

def test_deliberate_synthetic_smoke_tests_all_pass(engine: PreCommitSecurityGuardEngine) -> None:
    report = engine.run_synthetic_smoke_tests()

    assert report.passed is True
    assert report.fixtures_tested == 5
    for check in report.checks:
        assert check.detected is True
        assert check.exit_code == 1
        assert check.passed is True


# -----------------------------------------------------------------------------
# 5. Suppression Hygiene & Zero Blanket Exclusions (Stage 4)
# -----------------------------------------------------------------------------

def test_suppression_hygiene_accepts_justified_inline_comment(engine: PreCommitSecurityGuardEngine) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        test_file = tmp_p / "valid_suppression.py"
        test_file.write_text(
            "import hashlib\nhashlib.md5(b'test')  # devskim: ignore DS126858 - legacy checksum only\n",
            encoding="utf-8",
        )

        report = engine.audit_suppressions(tmp_p)
        assert report.passed is True
        assert report.valid_suppressions == 1
        assert report.unjustified_suppressions == 0
        assert report.blanket_exclusions == 0


def test_suppression_hygiene_flags_unjustified_inline_comment(engine: PreCommitSecurityGuardEngine) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        test_file = tmp_p / "unjustified.py"
        test_file.write_text(
            "import hashlib\nhashlib.md5(b'test')  # devskim: ignore\n",
            encoding="utf-8",
        )

        report = engine.audit_suppressions(tmp_p)
        assert report.passed is False
        assert report.unjustified_suppressions == 1


def test_suppression_hygiene_rejects_blanket_directory_exclusions(engine: PreCommitSecurityGuardEngine) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        cfg_file = tmp_p / ".pre-commit-config.yaml"
        cfg_file.write_text(
            "repos:\n  - repo: local\n    hooks:\n      - id: devskim\n        exclude: src/.*\n",
            encoding="utf-8",
        )

        report = engine.audit_suppressions(tmp_p)
        assert report.passed is False
        assert report.blanket_exclusions == 1


# -----------------------------------------------------------------------------
# 6. Dual-Gate CI Parity Auditing (Stage 5)
# -----------------------------------------------------------------------------

def test_dual_gate_ci_parity_check() -> None:
    engine = PreCommitSecurityGuardEngine()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        wf = tmp_p / "security.yml"
        wf.write_text(
            """
name: Security
jobs:
  scan:
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run DevSkim
        run: devskim analyze -I . -f sarif -O devskim.sarif
      - name: Upload DevSkim SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: devskim.sarif
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
            """,
            encoding="utf-8",
        )

        res = engine.audit_dual_gate_ci(wf)
        assert res.passed is True
        assert res.has_fetch_depth_zero is True
        assert res.has_sarif_upload is True
        assert res.has_secret_scanner is True
        assert res.has_sast_scanner is True


# -----------------------------------------------------------------------------
# 7. SARIF v2.1.0 Export Formatting
# -----------------------------------------------------------------------------

def test_sarif_export_schema_compliance(engine: PreCommitSecurityGuardEngine) -> None:
    finding = SecurityFinding(
        rule_id="DS126858",
        name="Weak Hash",
        severity="critical",
        scanner="sast_devskim",
        file_path="src/auth.py",
        line_number=10,
        code_snippet="hashlib.md5()",
        message="MD5 detected",
        remediation="Use SHA256",
    )
    report = ScanReport(
        target="test_target",
        passed=False,
        total_files_scanned=1,
        findings=(finding,),
    )

    sarif = engine.export_sarif(report)
    assert sarif.version == "2.1.0"
    assert sarif.finding_count == 1
    assert "runs" in sarif.sarif_dict
    assert len(sarif.sarif_dict["runs"]) == 1
    assert sarif.sarif_dict["runs"][0]["results"][0]["ruleId"] == "DS126858"


# -----------------------------------------------------------------------------
# 8. Dispatcher Script Backward Compatibility (run-devskim.py)
# -----------------------------------------------------------------------------

def test_run_devskim_delegator_passes_on_clean_file() -> None:
    script_path = (
        Path(__file__).parent.parent
        / ".agents"
        / "skills"
        / "pre-commit-security-guard"
        / "scripts"
        / "run-devskim.py"
    )
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
        tf.write("import hashlib\nh = hashlib.sha256(b'ok').hexdigest()\n")
        tf_path = tf.name

    try:
        res = subprocess.run(
            [sys.executable, str(script_path), tf_path],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0
    finally:
        Path(tf_path).unlink(missing_ok=True)


def test_run_devskim_delegator_fails_on_insecure_file() -> None:
    script_path = (
        Path(__file__).parent.parent
        / ".agents"
        / "skills"
        / "pre-commit-security-guard"
        / "scripts"
        / "run-devskim.py"
    )
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
        tf.write("import hashlib\nh = hashlib.md5(b'bad').hexdigest()\n")
        tf_path = tf.name

    try:
        res = subprocess.run(
            [sys.executable, str(script_path), tf_path],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 1
        assert "DS126858" in res.stderr
    finally:
        Path(tf_path).unlink(missing_ok=True)


# -----------------------------------------------------------------------------
# 9. Micro-Kernel IoC Service Seam (Rule 49)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ioc_service_registration_and_execution() -> None:
    context = ServiceContext()
    await plugin.on_load(context)

    svc = context.require(PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY)
    assert isinstance(svc, PreCommitSecurityGuardService)

    smoke = svc.run_synthetic_smoke_tests()
    assert smoke.passed is True
    assert smoke.fixtures_tested == 5


# -----------------------------------------------------------------------------
# 10. PluginValidator Compliance (Rule 38)
# -----------------------------------------------------------------------------

def test_plugin_validator_compliance() -> None:
    p_dir = Path(__file__).parent.parent / "plugins" / "security_and_forensics" / "pre_commit_security_guard"
    report = PluginValidator.validate_sync(p_dir)
    assert report.valid is True, f"Plugin validation failed: {report.errors}"
    assert len(report.warnings) == 0


# -----------------------------------------------------------------------------
# 11. Headless Click CLI Seams (Rule 6, Rule 10)
# -----------------------------------------------------------------------------

def test_cli_smoke_test_command() -> None:
    from harness.commands.pre_commit_security import pre_commit_security_group

    runner = CliRunner()
    res = runner.invoke(pre_commit_security_group, ["smoke-test"])
    assert res.exit_code == 0
    assert "Deliberate Synthetic Smoke Gate: PASSED" in res.output


def test_cli_audit_suppressions_command() -> None:
    from harness.commands.pre_commit_security import pre_commit_security_group

    runner = CliRunner()
    res = runner.invoke(pre_commit_security_group, ["audit-suppressions", "--json-output"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert "passed" in data
    assert "blanket_exclusions" in data


def test_cli_brief_command() -> None:
    from harness.commands.pre_commit_security import pre_commit_security_group

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
        tf_path = tf.name

    try:
        res = runner.invoke(pre_commit_security_group, ["brief", "--output", tf_path])
        assert res.exit_code == 0
        assert Path(tf_path).exists()
        assert Path(tf_path).stat().st_size > 500
    finally:
        Path(tf_path).unlink(missing_ok=True)
