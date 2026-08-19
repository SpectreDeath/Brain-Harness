"""Unit and integration tests for Isolation Realms, Interception, and Transactions.

Tests:
1. Coeffect Isolation Realms (Definition 28 & 29, ctx.isolate).
2. Coeffect Interception (Definition 30 & 31, ctx.intercept).
3. Transactional Effect Boundaries (Definition 51 & 52, ctx.transaction).
4. Self-evolving trial run with automatic rollback on validation failure.
"""

from __future__ import annotations

from typing import Any

import pytest

from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.kernel.context import ServiceContext, ServiceKey, ServiceNotFoundError
from harness.plugins.base import HarnessPlugin


class MockStorageService:
    def __init__(self, tag: str = "global") -> None:
        self.tag = tag
        self.data: dict[str, Any] = {}

    def set(self, k: str, v: Any) -> None:
        self.data[k] = v

    def get(self, k: str) -> Any:
        return self.data.get(k)


STORAGE_KEY = ServiceKey[MockStorageService]("mock.storage")


class MockLLMService:
    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return f"Response to: {prompt}"


LLM_KEY = ServiceKey[MockLLMService]("mock.llm")


# --- Tests ---


@pytest.mark.unit
def test_coeffect_isolation_realms() -> None:
    """Test that ctx.isolate() allows overriding a service key in an isolated realm."""
    root_ctx = ServiceContext()
    global_storage = MockStorageService("global")
    root_ctx.provide(STORAGE_KEY, global_storage)

    # Derive two isolated scopes
    scope_a = root_ctx.isolate(STORAGE_KEY, realm="realm_a")
    scope_b = root_ctx.isolate(STORAGE_KEY, realm="realm_b")

    storage_a = MockStorageService("isolated_a")
    storage_b = MockStorageService("isolated_b")

    scope_a.provide(STORAGE_KEY, storage_a)
    scope_b.provide(STORAGE_KEY, storage_b)

    # Root should still see global storage
    assert root_ctx.require(STORAGE_KEY).tag == "global"

    # Scope A should see isolated_a
    assert scope_a.require(STORAGE_KEY).tag == "isolated_a"

    # Scope B should see isolated_b
    assert scope_b.require(STORAGE_KEY).tag == "isolated_b"


@pytest.mark.unit
def test_coeffect_interception() -> None:
    """Test that ctx.intercept() transparently wraps a service on require()."""
    root_ctx = ServiceContext()
    raw_llm = MockLLMService("gpt-4o")
    root_ctx.provide(LLM_KEY, raw_llm)

    # Interceptor that adds an audit prefix
    class AuditLLMWrapper:
        def __init__(self, inner: MockLLMService) -> None:
            self.inner = inner

        def generate(self, prompt: str) -> str:
            res = self.inner.generate(prompt)
            return f"[AUDITED] {res}"

    child_ctx = root_ctx.intercept(LLM_KEY, lambda llm: AuditLLMWrapper(llm))

    # Root gets unwrapped instance
    assert root_ctx.require(LLM_KEY).generate("hello") == "Response to: hello"

    # Child gets intercepted wrapper
    assert child_ctx.require(LLM_KEY).generate("hello") == "[AUDITED] Response to: hello"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transactional_rollback_on_failure() -> None:
    """Test that ctx.transaction() rolls back all intermediate operations upon exception."""
    root_ctx = ServiceContext()
    root_ctx.provide(STORAGE_KEY, MockStorageService("root"))

    new_key = ServiceKey[str]("transient.key")
    side_effects: list[str] = []

    with pytest.raises(RuntimeError, match="Intentional failure"):
        async with root_ctx.transaction() as tx:
            # Provide a new service inside transaction
            tx.provide(new_key, "temp_value")
            assert tx.has(new_key)

            # Record a custom effect
            def _effect() -> Any:
                side_effects.append("applied")
                return lambda: side_effects.append("reverted")

            tx.effect(_effect)
            assert side_effects == ["applied"]

            # Trigger failure
            raise RuntimeError("Intentional failure in transaction")

    # After rollback, new_key should not exist in root_ctx or tx
    assert not root_ctx.has(new_key)
    # The custom effect should have had its inverse executed
    assert side_effects == ["applied", "reverted"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transactional_commit_on_success() -> None:
    """Test that ctx.transaction() commits its effects into parent context on success."""
    root_ctx = ServiceContext()
    new_key = ServiceKey[str]("permanent.key")

    async with root_ctx.transaction() as tx:
        tx.provide(new_key, "committed_value")

    # Service should be available in root
    assert root_ctx.has(new_key)
    assert root_ctx.require(new_key) == "committed_value"

    # Disposing root should clean up committed transaction effects
    await root_ctx.dispose()
    assert not root_ctx.has(new_key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_trial_run_with_clean_rollback() -> None:
    """Test PluginIngestionPipeline.trial_run sandboxing with clean rollback."""
    pipeline = PluginIngestionPipeline()
    base_ctx = ServiceContext()

    class FlakyPlugin(HarnessPlugin):
        name = "flaky.plugin"
        version = "1.0.0"
        provides = [ServiceKey[str]("flaky.svc")]

        async def on_load(self, ctx: ServiceContext) -> None:
            ctx.provide(self.provides[0], "flaky_data")

    plugin = FlakyPlugin()

    # Validation function that rejects the plugin
    async def _failing_validator(scoped_ctx: ServiceContext) -> Any:
        raise ValueError("Security scan failed: untrusted AST construct detected")

    with pytest.raises(ValueError, match="Security scan failed"):
        await pipeline.trial_run(plugin, _failing_validator, parent_context=base_ctx)

    # Base context must remain completely clean
    assert not base_ctx.has(ServiceKey("flaky.svc"))
