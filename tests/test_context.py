"""Tests for the ServiceContext IoC container."""

import pytest

from harness.kernel.context import (
    DuplicateServiceError,
    ServiceContext,
    ServiceKey,
    ServiceNotFoundError,
)


@pytest.mark.unit
class TestServiceKey:
    def test_equality(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("llm.provider")
        assert k1 == k2

    def test_inequality(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("storage.default")
        assert k1 != k2

    def test_hash(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("llm.provider")
        assert hash(k1) == hash(k2)
        assert {k1, k2} == {k1}

    def test_repr(self) -> None:
        k = ServiceKey[str]("llm.provider")
        assert "llm.provider" in repr(k)


@pytest.mark.unit
class TestServiceContext:
    def test_provide_and_require(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test.service")
        ctx.provide(key, "hello")
        assert ctx.require(key) == "hello"

    def test_require_missing_raises(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        with pytest.raises(ServiceNotFoundError):
            ctx.require(key)

    def test_optional_returns_none(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        assert ctx.optional(key) is None

    def test_optional_returns_value(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, 42)
        assert ctx.optional(key) == 42

    def test_duplicate_raises(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "first")
        with pytest.raises(DuplicateServiceError):
            ctx.provide(key, "second")

    def test_allow_override(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "first")
        ctx.provide(key, "second", allow_override=True)
        assert ctx.require(key) == "second"

    def test_has(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        assert not ctx.has(key)
        ctx.provide(key, "value")
        assert ctx.has(key)

    def test_contains(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        assert key not in ctx
        ctx.provide(key, "value")
        assert key in ctx

    def test_revoke(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "value")
        assert ctx.revoke(key) is True
        assert not ctx.has(key)

    def test_revoke_missing(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        assert ctx.revoke(key) is False

    def test_revoke_all_from(self) -> None:
        ctx = ServiceContext()
        k1 = ServiceKey[str]("svc.a")
        k2 = ServiceKey[str]("svc.b")
        k3 = ServiceKey[str]("svc.c")
        ctx.provide(k1, "a", provider="plugin-x")
        ctx.provide(k2, "b", provider="plugin-x")
        ctx.provide(k3, "c", provider="plugin-y")

        revoked = ctx.revoke_all_from("plugin-x")
        assert set(revoked) == {"svc.a", "svc.b"}
        assert not ctx.has(k1)
        assert not ctx.has(k2)
        assert ctx.has(k3)

    def test_list_services(self) -> None:
        ctx = ServiceContext()
        k1 = ServiceKey[str]("svc.a")
        k2 = ServiceKey[str]("svc.b")
        ctx.provide(k1, "a", provider="p1")
        ctx.provide(k2, "b")

        services = ctx.list_services()
        assert services == {"svc.a": "p1", "svc.b": None}


class TestServiceContextParentChild:
    def test_child_inherits_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("parent.service")
        parent.provide(key, "inherited")

        child = parent.child()
        assert child.require(key) == "inherited"

    def test_child_overrides_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("shared")
        parent.provide(key, "parent_value")

        child = parent.child()
        child.provide(key, "child_value")
        assert child.require(key) == "child_value"
        assert parent.require(key) == "parent_value"

    def test_child_does_not_leak_to_parent(self) -> None:
        parent = ServiceContext()
        child = parent.child()
        key = ServiceKey[str]("child.only")
        child.provide(key, "local")

        assert child.has(key)
        assert not parent.has(key)

    def test_has_walks_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("test")
        parent.provide(key, "val")

        child = parent.child()
        assert child.has(key)
