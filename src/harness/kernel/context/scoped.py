"""Plugin-scoped service context for automatic provider binding and teardown."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .core import ServiceContext

if TYPE_CHECKING:
    from .models import ServiceKey

T = TypeVar("T")


class ScopedServiceContext(ServiceContext):
    """A plugin-scoped service context.

    Automatically binds any registered service to the owning plugin's name,
    enabling transactional lifecycle management without boilerplate.
    """

    def __init__(self, parent: ServiceContext, plugin_name: str) -> None:
        super().__init__(parent=parent)
        self.plugin_name = plugin_name
        self._provided_keys: set[str] = set()

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        actual_provider = provider or self.plugin_name
        self._provided_keys.add(key.name)
        if self._parent is not None:
            self._parent.provide(
                key,
                instance,
                provider=actual_provider,
                allow_override=allow_override,
            )
        else:
            super().provide(
                key,
                instance,
                provider=actual_provider,
                allow_override=allow_override,
            )

    @property
    def provided_keys(self) -> set[str]:
        """Names of keys registered through this scoped context."""
        return set(self._provided_keys)

    async def dispose(self) -> None:
        """Dispose all scoped effects and revoke provided services in LIFO order."""
        await super().dispose()
        if self._parent is not None:
            self._parent.revoke_all_from(self.plugin_name)

    def __repr__(self) -> str:
        return f"<ScopedServiceContext plugin={self.plugin_name!r} keys={len(self._provided_keys)}>"
