"""Budget constants and isolation ServiceKeys for Harness Spawner."""

from __future__ import annotations

from harness.kernel.context import ServiceKey
from harness.services.recursive_harnessing.library import ExperienceLibrary

HARD_MAX_SPAWN_DEPTH: int = 3
DEFAULT_MAX_SPAWN_DEPTH: int = 1
DEFAULT_MAX_TOKENS: int = 16_000
DEFAULT_K: int = 1
DEFAULT_MAX_ROLLOUTS: int = 4
DEFAULT_MAX_SESSIONS: int = 3

EXPERIENCE_LIBRARY_KEY: ServiceKey[ExperienceLibrary] = ServiceKey("service.experience_library")
SPAWN_DEPTH_KEY: ServiceKey[int] = ServiceKey("service.spawn_depth")
SPAWN_MAX_DEPTH_KEY: ServiceKey[int] = ServiceKey("service.spawn_max_depth")

__all__ = [
    "DEFAULT_K",
    "DEFAULT_MAX_ROLLOUTS",
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_MAX_SPAWN_DEPTH",
    "DEFAULT_MAX_TOKENS",
    "EXPERIENCE_LIBRARY_KEY",
    "HARD_MAX_SPAWN_DEPTH",
    "SPAWN_DEPTH_KEY",
    "SPAWN_MAX_DEPTH_KEY",
]
