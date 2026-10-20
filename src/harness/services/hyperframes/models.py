"""Slotted frozen data models for HyperFrames multimedia rendering."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class VideoScene:
    """A single programmatic animation scene rendered via HTML/Tailwind/GSAP."""

    scene_id: str
    title: str
    duration_ms: int
    html_template: str
    transition: str = "fade"

    def __post_init__(self) -> None:
        if not self.scene_id:
            raise ValueError("scene_id must not be empty")
        if self.duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        if not self.html_template:
            raise ValueError("html_template must not be empty")
        if self.transition not in {"fade", "slide", "zoom", "none"}:
            raise ValueError(f"Invalid transition: {self.transition}")


@dataclass(slots=True, frozen=True)
class RenderRequest:
    """A multi-scene video rendering request."""

    scenes: tuple[VideoScene, ...]
    fps: int = 30
    resolution: tuple[int, int] = (1280, 720)
    output_format: str = "mp4"

    def __post_init__(self) -> None:
        if not self.scenes:
            raise ValueError("scenes must contain at least one VideoScene")
        if self.fps <= 0 or self.fps > 120:
            raise ValueError("fps must be between 1 and 120")
        if len(self.resolution) != 2 or self.resolution[0] <= 0 or self.resolution[1] <= 0:
            raise ValueError("resolution must be a tuple of two positive integers")
        if self.output_format not in {"mp4", "webp", "gif", "webm"}:
            raise ValueError(f"Unsupported output_format: {self.output_format}")


@dataclass(slots=True, frozen=True)
class RenderOutput:
    """Result of rendering a programmatic video."""

    artifact_path: str
    duration_ms: int
    frame_count: int
    size_bytes: int
    render_time_ms: float
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.artifact_path:
            raise ValueError("artifact_path must not be empty")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.frame_count < 0:
            raise ValueError("frame_count must be non-negative")
