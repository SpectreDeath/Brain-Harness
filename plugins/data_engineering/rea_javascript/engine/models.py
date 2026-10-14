"""Slotted and frozen domain models for REA JavaScript reverse-engineering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RecoveredChunk:
    """Recovered source chunk descriptor."""

    relative_path: str
    size_bytes: int = 0
    recovered_type: str = "javascript"

    def __post_init__(self) -> None:
        assert self.relative_path, "relative_path cannot be empty"
        assert self.size_bytes >= 0, "size_bytes must be non-negative"


@dataclass(slots=True, frozen=True)
class IpcChannelInfo:
    """Electron IPC communication channel descriptor."""

    channel_name: str
    direction: str
    source_file: str

    def __post_init__(self) -> None:
        assert self.channel_name, "channel_name cannot be empty"
        assert self.direction in ("renderer-to-main", "main-to-renderer", "bidirectional"), (
            f"Invalid direction: {self.direction}"
        )


@dataclass(slots=True, frozen=True)
class DotnetTypeInfo:
    """Managed .NET type hierarchy descriptor."""

    type_name: str
    namespace: str
    methods_count: int
    cil_instruction_hash: str = ""

    def __post_init__(self) -> None:
        assert self.type_name, "type_name cannot be empty"
        assert self.methods_count >= 0, "methods_count must be non-negative"


@dataclass(slots=True, frozen=True)
class PinvokeImportInfo:
    """P/Invoke native DLL boundary import."""

    library: str
    function: str

    def __post_init__(self) -> None:
        assert self.library, "library cannot be empty"
        assert self.function, "function cannot be empty"


@dataclass(slots=True, frozen=True)
class HarEntryInfo:
    """Processed HTTP transaction record from a HAR capture."""

    method: str
    url: str
    status: int
    mime_type: str = ""
    response_size: int = 0

    def __post_init__(self) -> None:
        assert self.method, "method cannot be empty"
        assert self.status >= 0, "status must be non-negative"
