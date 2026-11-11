"""Hardening test suite for REA Reverse-Engineering Unified Toolkit Service.

Verifies:
- 13 artifact categories detection and routing
- Slotted and frozen dataclass immutability (Rule 12 & Rule 43 direct assignment)
- Dict-like key access compatibility
- Polyglot indicators and absence claimability gates
- Dissection envelopes and budget truncation
- Live differential comparison across providers
- Endogenous Knowledge Vault dual-file persistence (Rule 40)
"""

from __future__ import annotations

import json
from pathlib import Path
import struct
import zipfile
import pytest

from harness.services.differential_facet import FacetAvailability
from harness.services.rea_toolkit import (
    ArtifactIdentity,
    DissectionEnvelope,
    FacetEnvelope,
    ProviderProvenance,
    ReaDissectionBudgets,
    SemanticSignature,
    StandardReaToolkitService,
    resolve_rea_toolkit,
)


# -----------------------------------------------------------------------------
# Fixtures for synthetic artifact generation
# -----------------------------------------------------------------------------


@pytest.fixture
def service() -> StandardReaToolkitService:
    return StandardReaToolkitService()


@pytest.fixture
def synthetic_fixtures(tmp_path: Path) -> dict[str, Path]:
    """Generates synthetic minimal byte fixtures for 13 artifact categories."""
    fixtures: dict[str, Path] = {}

    # 1. ELF
    elf_file = tmp_path / "sample.so"
    elf_file.write_bytes(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 40)
    fixtures["elf"] = elf_file

    # 2. Native PE (pe_native)
    pe_file = tmp_path / "native.dll"
    pe_data = bytearray(b"MZ" + b"\x00" * 58)
    pe_data.extend(struct.pack("<I", 0x80))  # e_lfanew
    pe_data.extend(b"\x00" * (0x80 - len(pe_data)))
    pe_data.extend(b"PE\x00\x00")  # PE signature
    pe_data.extend(struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 240, 0x2022))
    opt_hdr = bytearray(240)
    struct.pack_into("<H", opt_hdr, 0, 0x20B)  # PE32+
    struct.pack_into("<I", opt_hdr, 16, 0x1000)
    struct.pack_into("<I", opt_hdr, 108, 16)
    struct.pack_into("<II", opt_hdr, 224, 0, 0)  # CLR header RVA=0 -> native PE
    pe_data.extend(opt_hdr)
    pe_file.write_bytes(bytes(pe_data))
    fixtures["pe_native"] = pe_file

    # 3. Managed .NET PE (pe_managed)
    managed_file = tmp_path / "managed.dll"
    m_data = bytearray(pe_data)
    struct.pack_into("<II", m_data, 0x80 + 4 + 20 + 224, 0x2000, 72)  # CLR RVA > 0
    managed_file.write_bytes(bytes(m_data))
    fixtures["pe_managed"] = managed_file

    # 4. DOS MZ (dos_mz)
    dos_file = tmp_path / "dosapp.exe"
    dos_file.write_bytes(b"MZ" + b"\x00" * 128)
    fixtures["dos_mz"] = dos_file

    # 5. WebAssembly (wasm)
    wasm_file = tmp_path / "module.wasm"
    wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"\x01\x04\x01\x60\x00\x00")
    fixtures["wasm"] = wasm_file

    # 6. Unity IL2CPP global-metadata.dat
    il2cpp_file = tmp_path / "global-metadata.dat"
    il2cpp_file.write_bytes(b"\xaf\x1b\xb1\xfa" + struct.pack("<I", 29) + b"\x00" * 32)
    fixtures["il2cpp_metadata"] = il2cpp_file

    # 7. AI Model: GGUF
    gguf_file = tmp_path / "model.gguf"
    gguf_file.write_bytes(b"GGUF\x03\x00\x00\x00" + b"\x00" * 16)
    fixtures["ai_model"] = gguf_file

    # 8. AI Model: Safetensors
    safetensors_file = tmp_path / "weights.safetensors"
    hdr_bytes = b'{"__metadata__":{"format":"pt"}}'
    safetensors_file.write_bytes(struct.pack("<Q", len(hdr_bytes)) + hdr_bytes)
    fixtures["safetensors"] = safetensors_file

    # 9. CPython .pyc
    pyc_file = tmp_path / "module.cpython-311.pyc"
    pyc_file.write_bytes(struct.pack("<IIII", 3495 | 0x0A0D0000, 0, 0, 100) + b"\x00" * 16)
    fixtures["cpython_pyc"] = pyc_file

    # 10. Electron ASAR
    asar_file = tmp_path / "app.asar"
    asar_header = json.dumps({"files": {"index.js": {"size": 42, "offset": "0"}}}).encode("utf-8")
    asar_data = struct.pack("<IIII", 4, len(asar_header) + 8, len(asar_header) + 4, len(asar_header)) + asar_header
    asar_file.write_bytes(asar_data)
    fixtures["asar"] = asar_file

    # 11. Android APK
    apk_file = tmp_path / "test.apk"
    with zipfile.ZipFile(apk_file, "w") as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest package='com.test.app'/>")
        zf.writestr("classes.dex", b"dex\n035\x00" + b"\x00" * 32)
    fixtures["apk"] = apk_file

    # 12. HAR Capture
    har_file = tmp_path / "traffic.har"
    har_file.write_text(json.dumps({"log": {"version": "1.2", "creator": {"name": "test"}, "entries": []}}), encoding="utf-8")
    fixtures["har"] = har_file

    # 13. JavaScript Bundle
    js_file = tmp_path / "app.bundle.js"
    js_file.write_text("function initApp() { console.log('ready'); }; initApp();", encoding="utf-8")
    fixtures["javascript_bundle"] = js_file

    # 14. EVM Bytecode
    evm_file = tmp_path / "contract.evm"
    evm_file.write_text("608060405234801561001057600080fd5b50", encoding="utf-8")
    fixtures["evm_bytecode"] = evm_file

    # 15. Firmware Image
    fw_file = tmp_path / "router.bin"
    fw_file.write_bytes(b"\x00" * 64 + b"U-Boot 2022.01" + b"\x00" * 128)
    fixtures["firmware"] = fw_file

    return fixtures


# -----------------------------------------------------------------------------
# Tests: Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------


def test_slotted_frozen_immutability() -> None:
    """Dataclasses must be frozen and slotted; direct mutation raises AttributeError/TypeError."""
    identity = ArtifactIdentity(
        path="test.bin",
        sha256="abc",
        size_bytes=100,
        detected_kind="elf",
        mime_type="application/x-executable",
        magic_summary="ELF",
    )
    with pytest.raises((AttributeError, TypeError)):
        identity.path = "other.bin"

    with pytest.raises((AttributeError, TypeError)):
        identity.new_attr = "invalid"

    prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_elf_layout", binary_version="1.0.0")
    with pytest.raises((AttributeError, TypeError)):
        prov.plugin = "other"

    sig = SemanticSignature(kind="import", name="libc.so.6!printf", details={"lib": "libc.so.6"})
    with pytest.raises((AttributeError, TypeError)):
        sig.kind = "other"

    budgets = ReaDissectionBudgets()
    with pytest.raises((AttributeError, TypeError)):
        budgets.max_symbols = 999


def test_dict_like_key_access_compatibility() -> None:
    """Dataclasses must support dict-like indexing and .get() for transparent compatibility."""
    identity = ArtifactIdentity(
        path="foo.wasm",
        sha256="deadbeef",
        size_bytes=42,
        detected_kind="wasm",
        mime_type="application/wasm",
        magic_summary="WASM Module",
    )
    assert identity["path"] == "foo.wasm"
    assert identity["detected_kind"] == "wasm"
    assert identity.get("size_bytes") == 42
    assert identity.get("nonexistent", "fallback") == "fallback"

    sig = SemanticSignature(kind="import", name="printf", details={"lib": "libc"})
    assert sig["kind"] == "import"
    assert sig["name"] == "printf"
    assert sig.get("signature_hash") != ""


# -----------------------------------------------------------------------------
# Tests: Artifact Classification Matrix (13 Categories)
# -----------------------------------------------------------------------------


def test_detect_all_categories(service: StandardReaToolkitService, synthetic_fixtures: dict[str, Path]) -> None:
    """Verifies that each synthetic fixture is correctly identified by detect_artifact."""
    expected_mappings = {
        "elf": "elf",
        "pe_native": "pe_native",
        "pe_managed": "pe_managed",
        "dos_mz": "dos_mz",
        "wasm": "wasm",
        "il2cpp_metadata": "il2cpp_metadata",
        "ai_model": "ai_model",
        "safetensors": "ai_model",
        "cpython_pyc": "cpython_pyc",
        "asar": "asar",
        "apk": "apk",
        "har": "har",
        "javascript_bundle": "javascript_bundle",
        "evm_bytecode": "evm_bytecode",
        "firmware": "firmware",
    }

    for fix_key, expected_kind in expected_mappings.items():
        path = synthetic_fixtures[fix_key]
        ident = service.detect_artifact(path)
        assert ident.detected_kind == expected_kind, (
            f"Expected {expected_kind} for fixture {fix_key}, got {ident.detected_kind} (summary: {ident.magic_summary})"
        )
        assert len(ident.sha256) == 64
        assert ident.size_bytes > 0


# -----------------------------------------------------------------------------
# Tests: Polyglot Indicators & Absence Claimability
# -----------------------------------------------------------------------------


def test_polyglot_detection(tmp_path: Path, service: StandardReaToolkitService) -> None:
    """A file embedding multiple magic signatures triggers polyglot warnings."""
    poly_file = tmp_path / "polyglot.bin"
    data = bytearray(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 60)
    data.extend(b"PK\x03\x04" + b"\x00" * 30)
    poly_file.write_bytes(bytes(data))

    ident = service.detect_artifact(poly_file)
    assert ident.detected_kind == "elf"
    assert len(ident.polyglot_warnings) > 0
    assert any("polyglot" in w.lower() for w in ident.polyglot_warnings)


# -----------------------------------------------------------------------------
# Tests: Dissection & Budget Truncation
# -----------------------------------------------------------------------------


def test_dissect_and_budget_truncation(service: StandardReaToolkitService, synthetic_fixtures: dict[str, Path]) -> None:
    """Tight budgets truncate output and revoke absence claimability."""
    elf_path = synthetic_fixtures["elf"]

    # Request decompilation with symbols exceeding max_symbols budget
    tight_budgets = ReaDissectionBudgets(max_symbols=1)
    tight_envelope = service.dissect(
        elf_path,
        symbols=["main", "init", "cleanup"],
        budgets=tight_budgets,
    )
    decomp_facet = tight_envelope.facets.get("decompilation")
    assert decomp_facet is not None
    assert decomp_facet.coverage.truncated is True
    assert decomp_facet.coverage.omitted_count == 2
    assert decomp_facet.coverage.absence_claimable is False


# -----------------------------------------------------------------------------
# Tests: Provider Auditing
# -----------------------------------------------------------------------------


def test_providers_enumeration(service: StandardReaToolkitService) -> None:
    """Auditing providers lists external binaries and maps them to REA plugins."""
    prov_map = service.providers()
    assert isinstance(prov_map, dict)
    assert len(prov_map) >= 8
    assert "ghidra" in prov_map
    assert "wabt" in prov_map
    assert "jadx" in prov_map
    assert "wakaru" in prov_map

    for name, p in prov_map.items():
        assert p.plugin.startswith("plugin.rea_")
        assert p.tool


# -----------------------------------------------------------------------------
# Tests: Multi-Provider Differential Comparison
# -----------------------------------------------------------------------------


def test_diff_differential_comparison(service: StandardReaToolkitService, synthetic_fixtures: dict[str, Path]) -> None:
    """Differential analysis across provider tools yields 3-valued outcome."""
    elf_path = synthetic_fixtures["elf"]
    report = service.diff(elf_path, providers=("ghidra", "hopper"), symbols=["main"])
    assert report.report_id.startswith("rep:")
    assert report.overall_status in ("equal", "different", "degraded", "unknown")
    assert len(report.dimensions) > 0


# -----------------------------------------------------------------------------
# Tests: Endogenous Learn Loop & Vault Persistence (Rule 40)
# -----------------------------------------------------------------------------


def test_learn_dry_run_does_not_mutate_disk(service: StandardReaToolkitService, synthetic_fixtures: dict[str, Path]) -> None:
    """Learn loop in dry-run mode returns synthesis without writing to disk."""
    evm_path = synthetic_fixtures["evm_bytecode"]
    res = service.learn(evm_path, domain="web3_smart_contracts", dry_run=True)
    assert res["dry_run"] is True
    assert res["ki_id"].startswith("ki-rea-sig-")
    assert res["evidence_id"].startswith("ev:")
    assert not Path(res["vault_dir"]).exists()


def test_learn_commits_canonical_dual_files(tmp_path: Path, synthetic_fixtures: dict[str, Path]) -> None:
    """Learn loop commit creates valid metadata.json and summary.md (Rule 40)."""
    vault_root = tmp_path / "knowledge_vault"
    service = StandardReaToolkitService(vault_dir=vault_root)
    wasm_path = synthetic_fixtures["wasm"]

    res = service.learn(
        wasm_path,
        domain="reverse_engineering",
        tags=["webassembly", "wabt", "hardening_test"],
        dry_run=False,
    )

    ki_dir = Path(res["vault_dir"])
    assert ki_dir.exists()
    assert (ki_dir / "metadata.json").exists()
    assert (ki_dir / "summary.md").exists()

    meta = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
    assert meta["id"] == res["ki_id"]
    assert meta["domain"] == "reverse_engineering"
    assert "webassembly" in meta["tags"]
    assert meta["evidence_id"].startswith("ev:")
    assert meta["status"] == "validated"

    summary = (ki_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Semantic Signatures:" in summary
    assert "## Isnad Lineage Chain" in summary
    assert meta["evidence_id"] in summary


def test_dissect_extended_ai_models_and_js_signatures(tmp_path: Path, service: StandardReaToolkitService) -> None:
    """Verify TFLite, HDF5, SavedModel PB, TF.js weight shards, and JS bundle signature extraction."""
    # 1. TFLite (TFL3 FlatBuffer)
    tflite_file = tmp_path / "model.tflite"
    tflite_file.write_bytes(struct.pack("<I", 16) + b"TFL3" + b"\x00" * 16 + b"conv2d/kernel\x00dense/bias\x00")
    tflite_env = service.dissect(tflite_file)
    assert tflite_env.artifact.detected_kind == "ai_model"
    assert tflite_env.facets["model_headers"].state == "available"
    assert any(s.kind == "model_tensor" and "conv2d/kernel" in s.name for s in tflite_env.signatures)

    # 2. Keras / HDF5
    h5_file = tmp_path / "model.h5"
    h5_file.write_bytes(b"\x89HDF\r\n\x1a\n\x00" + b"\x00" * 16 + b"model_config\x00lstm/kernel:0\x00")
    h5_env = service.dissect(h5_file)
    assert h5_env.artifact.detected_kind == "ai_model"
    assert h5_env.facets["model_headers"].state == "available"
    assert any(s.kind == "model_tensor" and "lstm/kernel:0" in s.name for s in h5_env.signatures)

    # 3. TensorFlow.js shard + sibling model.json
    tfjs_dir = tmp_path / "tfjs"
    tfjs_dir.mkdir()
    shard_file = tfjs_dir / "group1-shard1of1.bin"
    shard_file.write_bytes(b"\x00" * 64)
    (tfjs_dir / "model.json").write_text(
        json.dumps({
            "format": "layers-model",
            "generatedBy": "keras v2.3.0-tf",
            "weightsManifest": [{
                "paths": ["group1-shard1of1.bin"],
                "weights": [{"name": "dense/kernel", "shape": [8, 2], "dtype": "float32"}],
            }],
        }),
        encoding="utf-8",
    )
    tfjs_env = service.dissect(shard_file)
    assert tfjs_env.artifact.detected_kind == "ai_model"
    assert tfjs_env.facets["model_headers"].state == "available"
    assert any(s.kind == "model_tensor" and s.name == "dense/kernel" for s in tfjs_env.signatures)

    # 4. JavaScript Bundle static symbols
    js_file = tmp_path / "bundle.js"
    js_file.write_text("class AntheaEval {} function runSegment() { return 1; }", encoding="utf-8")
    js_env = service.dissect(js_file)
    assert js_env.artifact.detected_kind == "javascript_bundle"
    assert any(s.kind == "js_class" and s.name == "AntheaEval" for s in js_env.signatures)
    assert any(s.kind == "js_function" and s.name == "runSegment" for s in js_env.signatures)


def test_rea_parser_precision_regressions(tmp_path: Path, service: StandardReaToolkitService) -> None:
    """Verify precision fixes: probe JS with only comments yields 0 signatures, and real TFLite yields no junk fragments."""
    # 1. Probe JS with prose comments and no declarations must yield zero signatures
    probe_js = tmp_path / "probe_comments_only.js"
    probe_js.write_text(
        "// This class keeps track of user interactions.\n"
        "// Another class names the active element.\n"
        "// In this class encapsulating the view is important.\n"
        "// This function always checks preconditions.\n"
        "// This function also computes the hash.\n"
        "// This function will fail if empty.\n",
        encoding="utf-8",
    )
    js_env = service.dissect(probe_js, artifact_type="javascript_bundle")
    assert len(js_env.signatures) == 0, f"Expected 0 signatures from comment-only JS probe, got {js_env.signatures}"

    # 2. Real model1_wfrontend.tflite yields no junk fragments (Track 0.6)
    real_tflite = Path(
        r"D:\GitHub\cloned\Google\google-research-master\google-research-master"
        r"\non_semantic_speech_benchmark\data_prep\testdata\model1_wfrontend.tflite"
    )
    if real_tflite.exists():
        tflite_env = service.dissect(real_tflite)
        tensor_names = [s.name for s in tflite_env.signatures if s.kind == "model_tensor"]
        assert "p/T" not in tensor_names
        assert "l/8" not in tensor_names
        assert "_/N" not in tensor_names
        assert "audio_samples" in tensor_names
        assert "Identity" in tensor_names
        assert len(tensor_names) == 7
    else:
        noise_tflite = tmp_path / "noise.tflite"
        noise_tflite.write_bytes(
            struct.pack("<I", 16) + b"TFL3" + b"\x00" * 16 + b"p/T\x00l/8\x00_/N\x00valid/tensor\x00"
        )
        tflite_env = service.dissect(noise_tflite)
        tensor_names = [s.name for s in tflite_env.signatures if s.kind == "model_tensor"]
        assert "p/T" not in tensor_names
        assert "l/8" not in tensor_names
        assert "_/N" not in tensor_names
        assert "valid/tensor" in tensor_names


def test_dissect_saved_model_protobuf_parser(tmp_path: Path, service: StandardReaToolkitService) -> None:
    """Verify SavedModel PB parser (_parse_protobuf_model) extracts graph symbols (Track 2.1)."""
    real_pb = Path(
        r"D:\GitHub\cloned\Google\google-research-master\google-research-master"
        r"\bustle\models\1000_epochs__64_64__e2__1e-5\saved_model.pb"
    )
    if real_pb.exists():
        pb_env = service.dissect(real_pb)
        assert pb_env.artifact.detected_kind == "ai_model"
        assert pb_env.facets["model_headers"].state == "available"
        assert pb_env.facets["model_headers"].data.get("format") == "tf_saved_model_pb"
        assert pb_env.facets["model_headers"].data.get("tensors_count", 0) > 0
        tensor_names = [s.name for s in pb_env.signatures if s.kind == "model_tensor"]
        assert any("dense/kernel" in name for name in tensor_names)
        assert any("embedding/embeddings" in name for name in tensor_names)
    else:
        pb_file = tmp_path / "saved_model.pb"
        pb_file.write_bytes(b"\x08\x01\x12\x04node\x1a\x12embedding/embeddings\x1a\x0cdense/kernel\x00" + b"\x00" * 32)
        pb_env = service.dissect(pb_file)
        assert pb_env.artifact.detected_kind == "ai_model"
        assert pb_env.facets["model_headers"].state == "available"
        assert any("dense/kernel" in s.name for s in pb_env.signatures)


def test_dissect_real_tflite_and_hdf5_models(tmp_path: Path, service: StandardReaToolkitService) -> None:
    """Verify real-file parsing for TFLite and HDF5 models with fixture fallback in CI (Track 0.2 / 2.2)."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "rea_model_artifact"

    # 1. TFLite file (real clone path if available, vendored fixture in CI)
    real_tflite = Path(
        r"D:\GitHub\cloned\Google\google-research-master\google-research-master"
        r"\non_semantic_speech_benchmark\data_prep\testdata\model1_wfrontend.tflite"
    )
    target_tflite = real_tflite if real_tflite.exists() else (fixtures_dir / "minimal_speech.tflite")
    assert target_tflite.exists(), f"Neither real clone nor fixture exists: {target_tflite}"

    tflite_env = service.dissect(target_tflite)
    assert tflite_env.artifact.detected_kind == "ai_model"
    assert tflite_env.facets["model_headers"].data.get("format") == "tflite_v3"
    assert tflite_env.facets["model_headers"].data.get("tensors_count") == 7
    t_names = [s.name for s in tflite_env.signatures if s.kind == "model_tensor"]
    assert "audio_samples" in t_names
    assert "Identity" in t_names
    assert "p/T" not in t_names
    assert "l/8" not in t_names
    assert "_/N" not in t_names
    assert len(t_names) == 7

    # 2. HDF5 Keras model (real clone path if available, vendored fixture in CI)
    real_h5 = Path(
        r"D:\GitHub\cloned\Google\google-research-master\google-research-master"
        r"\sign_language_detection\models\py\model.h5"
    )
    target_h5 = real_h5 if real_h5.exists() else (fixtures_dir / "minimal_keras.h5")
    assert target_h5.exists(), f"Neither real clone nor fixture exists: {target_h5}"

    h5_env = service.dissect(target_h5)
    assert h5_env.artifact.detected_kind == "ai_model"
    assert h5_env.facets["model_headers"].data.get("format") == "hdf5_v0"
    assert h5_env.facets["model_headers"].data.get("tensors_count") == 4
    h5_names = [s.name for s in h5_env.signatures if s.kind == "model_tensor"]
    assert any("dense/kernel" in n for n in h5_names)
    assert any("lstm_cell/kernel" in n for n in h5_names)
    assert len(h5_names) == 4


def test_dissect_vendored_fixtures_deterministic_ci_signal(service: StandardReaToolkitService) -> None:
    """Verify vendored fixtures unconditionally execute exact assertions under pure CI conditions (Track 0.2)."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "rea_model_artifact"
    tflite_fixture = fixtures_dir / "minimal_speech.tflite"
    h5_fixture = fixtures_dir / "minimal_keras.h5"

    assert tflite_fixture.is_file()
    assert h5_fixture.is_file()

    # Exact TFLite precision: FlatBuffer traversal ignores embedded noise tokens
    tflite_env = service.dissect(tflite_fixture)
    assert tflite_env.artifact.detected_kind == "ai_model"
    assert tflite_env.facets["model_headers"].data.get("format") == "tflite_v3"
    assert tflite_env.facets["model_headers"].data.get("tensors_count") == 7
    t_names = [s.name for s in tflite_env.signatures if s.kind == "model_tensor"]
    assert "audio_samples" in t_names
    assert "Identity" in t_names
    assert "p/T" not in t_names
    assert "l/8" not in t_names
    assert "_/N" not in t_names
    assert len(t_names) == 7

    # Exact HDF5 structure: 4 layer weights
    h5_env = service.dissect(h5_fixture)
    assert h5_env.artifact.detected_kind == "ai_model"
    assert h5_env.facets["model_headers"].data.get("format") == "hdf5_v0"
    assert h5_env.facets["model_headers"].data.get("tensors_count") == 4
    h5_names = [s.name for s in h5_env.signatures if s.kind == "model_tensor"]
    assert "dense/kernel:0" in h5_names
    assert "dense/bias:0" in h5_names
    assert "lstm_cell/kernel:0" in h5_names
    assert "lstm_cell/bias:0" in h5_names
    assert len(h5_names) == 4




