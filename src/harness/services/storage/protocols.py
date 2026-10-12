"""Storage service abstract protocols and service keys."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harness.kernel.context import ServiceKey
from harness.services.storage.vault_operations import KnowledgeVaultMixin


class StorageService(KnowledgeVaultMixin, ABC):
    """Abstract storage interface for plugins.

    Provides key-value, document-style, and knowledge-item operations.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found."""

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set a value by key."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if the key existed."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys, optionally filtered by prefix."""

    @abstractmethod
    async def clear(self) -> int:
        """Delete all keys. Returns the number of keys deleted."""

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values by key. Returns a mapping of existing keys to values."""
        result: dict[str, Any] = {}
        for key in keys:
            val = await self.get(key)
            if val is not None:
                result[key] = val
        return result

    async def set_many(self, mapping: dict[str, Any]) -> None:
        """Set multiple key-value pairs."""
        for key, val in mapping.items():
            await self.set(key, val)

    async def get_all(self, prefix: str = "") -> dict[str, Any]:
        """Retrieve all key-value pairs matching an optional prefix."""
        keys = await self.list_keys(prefix=prefix)
        return await self.get_many(keys)

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns the number of keys deleted."""
        deleted = 0
        for key in keys:
            if await self.delete(key):
                deleted += 1
        return deleted


STORAGE_SERVICE_KEY: ServiceKey[StorageService] = ServiceKey("storage.default")
KNOWLEDGE_VAULT_KEY: ServiceKey[StorageService] = ServiceKey("storage.knowledge_vault")
