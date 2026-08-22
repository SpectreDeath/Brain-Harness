"""Unit and integration tests for new capability plugins:
- plugin.secret_scanner (Security & Forensics)
- plugin.test_runner (Software Engineering)
- plugin.critic_loop (Agent Orchestration)
- plugin.semantic_cache (Memory & Epistemics)
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle, PluginState

from plugins.security_and_forensics.secret_scanner.main import (
    SECRET_SCANNER_KEY,
    SecretScannerPlugin,
    SecretScannerService,
    scan_directory,
    scan_file,
    scan_text,
)
from plugins.software_engineering.test_runner.main import (
    TEST_RUNNER_KEY,
    TestRunnerPlugin,
    TestRunnerService,
    discover_tests,
    run_tests,
)
from plugins.agent_orchestration.critic_loop.main import (
    CRITIC_LOOP_KEY,
    CriticLoopPlugin,
    CriticLoopService,
    evaluate_rubric,
    run_critic_loop,
)
from plugins.memory_and_epistemics.semantic_cache.main import (
    SEMANTIC_CACHE_KEY,
    SemanticCachePlugin,
    SemanticCacheService,
    cache_clear,
    cache_get,
    cache_set,
    cache_stats,
)


# =========================================================================
# 1. Secret Scanner Plugin Tests
# =========================================================================

@pytest.mark.unit
def test_secret_scanner_detection_patterns() -> None:
    # Clean text
    clean_res = scan_text("def hello(): return 'world'")
    assert clean_res["clean"] is True
    assert clean_res["findings_count"] == 0

    # OpenAI key leak
    openai_leak = scan_text("OPENAI_KEY = 'sk-1234567890abcdef1234567890abcdef12345678'")
    assert openai_leak["clean"] is False
    assert openai_leak["findings_count"] >= 1
    assert any("OpenAI" in f["rule"] for f in openai_leak["findings"])

    # Private key leak
    key_leak = scan_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...")
    assert key_leak["clean"] is False
    assert any("Private Key" in f["rule"] for f in key_leak["findings"])

    # High entropy string assignment
    entropy_leak = scan_text("api_token = 'aB9$zQ8#kL2!vN5^pX4*mJ7&'")
    assert entropy_leak["findings_count"] >= 1


@pytest.mark.unit
def test_secret_scanner_file_and_directory(tmp_path: Path) -> None:
    d = tmp_path / "scan_test"
    d.mkdir()
    clean_f = d / "clean.py"
    clean_f.write_text("print('clean code')", encoding="utf-8")

    secret_f = d / "secret.py"
    secret_f.write_text("AWS_TOKEN = 'AKIA1234567890ABCDEF'", encoding="utf-8")

    file_res = scan_file(str(secret_f))
    assert file_res["clean"] is False
    assert file_res["findings_count"] >= 1

    dir_res = scan_directory(str(d))
    assert dir_res["clean"] is False
    assert dir_res["findings_count"] >= 1
    assert dir_res["scanned_files"] >= 2


@pytest.mark.asyncio
async def test_secret_scanner_plugin_lifecycle() -> None:
    ctx = ServiceContext()
    lc = PluginLifecycle(ctx)
    plugin = SecretScannerPlugin()

    lc.discover(plugin)
    await lc.load(plugin.name)
    await lc.validate(plugin.name)
    await lc.enable(plugin.name)

    assert lc.get_state(plugin.name) == PluginState.ENABLED
    assert ctx.has(SECRET_SCANNER_KEY)
    service: SecretScannerService = ctx.require(SECRET_SCANNER_KEY)
    res = service.scan_text("token = 'ghp_123456789012345678901234567890123456'")
    assert res["clean"] is False


# =========================================================================
# 2. Test Runner Plugin Tests
# =========================================================================

@pytest.mark.unit
def test_test_runner_discovery(tmp_path: Path) -> None:
    d = tmp_path / "test_disc"
    d.mkdir()
    test_f = d / "test_example.py"
    test_f.write_text("def test_one(): pass\ndef test_two(): pass\n", encoding="utf-8")

    res = discover_tests(str(d))
    assert res["status"] == "ok"
    assert res["total_test_files"] == 1
    assert res["total_test_functions"] == 2


@pytest.mark.asyncio
async def test_test_runner_run_execution(tmp_path: Path) -> None:
    d = tmp_path / "test_exec"
    d.mkdir()
    test_f = d / "test_pass.py"
    test_f.write_text("def test_sanity(): assert 1 + 1 == 2\n", encoding="utf-8")

    res = await run_tests(str(test_f), root_dir=str(d))
    assert res["status"] == "ok"
    assert res["passed"] == 1
    assert res["failed"] == 0
    assert res["success"] is True


@pytest.mark.asyncio
async def test_test_runner_plugin_lifecycle() -> None:
    ctx = ServiceContext()
    lc = PluginLifecycle(ctx)
    plugin = TestRunnerPlugin()

    lc.discover(plugin)
    await lc.load(plugin.name)
    await lc.validate(plugin.name)
    await lc.enable(plugin.name)

    assert lc.get_state(plugin.name) == PluginState.ENABLED
    assert ctx.has(TEST_RUNNER_KEY)
    service: TestRunnerService = ctx.require(TEST_RUNNER_KEY)
    disc = service.discover()
    assert disc["status"] == "ok"


# =========================================================================
# 3. Critic Loop Plugin Tests
# =========================================================================

@pytest.mark.unit
def test_critic_evaluate_rubric() -> None:
    typed_code = """
def calculate_metrics(values: list[float]) -> dict[str, float]:
    \"\"\"Calculate statistical metrics for numbers.\"\"\"
    try:
        if not values:
            return {"mean": 0.0}
        return {"mean": sum(values) / len(values)}
    except Exception as e:
        return {"error": -1.0}
"""
    rubric = [
        "Include strict type annotations on all function signatures",
        "Provide clear docstrings with parameters and return descriptions",
        "Implement robust error handling and input validation",
    ]
    res = evaluate_rubric(typed_code, rubric)
    assert res["passed"] is True
    assert res["overall_score"] >= 0.85
    assert len(res["breakdown"]) == 3


@pytest.mark.asyncio
async def test_critic_loop_refinement() -> None:
    task = "Write a typed statistical calculation helper"
    draft = "def calc(v):\n    return sum(v)/len(v)"
    rubric = ["Include strict type annotations", "Provide clear docstrings"]

    res = await run_critic_loop(task, draft, rubric=rubric, max_iterations=2, threshold=0.90)
    assert res["status"] == "ok"
    assert res["iterations_completed"] >= 1
    assert "trajectory" in res


@pytest.mark.asyncio
async def test_critic_loop_plugin_lifecycle() -> None:
    ctx = ServiceContext()
    lc = PluginLifecycle(ctx)
    plugin = CriticLoopPlugin()

    lc.discover(plugin)
    await lc.load(plugin.name)
    await lc.validate(plugin.name)
    await lc.enable(plugin.name)

    assert lc.get_state(plugin.name) == PluginState.ENABLED
    assert ctx.has(CRITIC_LOOP_KEY)
    service: CriticLoopService = ctx.require(CRITIC_LOOP_KEY)
    eval_res = service.evaluate("def foo(): pass", ["docstring"])
    assert eval_res["criteria_count"] == 1


# =========================================================================
# 4. Semantic Cache Plugin Tests
# =========================================================================

@pytest.mark.unit
def test_semantic_cache_operations() -> None:
    cache_clear()
    cache_set("How do I configure PostgreSQL connection pool in Python?", "Use asyncpg pool with min/max connections.")

    # High similarity hit
    hit = cache_get("How do I configure a PostgreSQL connection pool in Python?", similarity_threshold=0.80)
    assert hit["status"] == "hit"
    assert hit["hit"] is True
    assert "asyncpg" in hit["response"]
    assert hit["similarity"] >= 0.80

    # Miss for completely unrelated prompt
    miss = cache_get("Explain quantum entanglement and qubits", similarity_threshold=0.80)
    assert miss["status"] == "miss"
    assert miss["hit"] is False

    stats = cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_entries"] == 1

    cache_clear()
    assert cache_stats()["total_entries"] == 0


@pytest.mark.asyncio
async def test_semantic_cache_plugin_lifecycle() -> None:
    ctx = ServiceContext()
    lc = PluginLifecycle(ctx)
    plugin = SemanticCachePlugin()

    lc.discover(plugin)
    await lc.load(plugin.name)
    await lc.validate(plugin.name)
    await lc.enable(plugin.name)

    assert lc.get_state(plugin.name) == PluginState.ENABLED
    assert ctx.has(SEMANTIC_CACHE_KEY)
    service: SemanticCacheService = ctx.require(SEMANTIC_CACHE_KEY)
    service.set("hello", "world")
    res = service.get("hello")
    assert res is not None
    assert res["response"] == "world"
