"""Architecture Linter and Coupling Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class CircularImportResult(BaseModel):
    """Result of circular import detection."""

    status: str = Field(default="ok", description="Status indicator")
    root_path: str = Field(default="src", description="Scanned source directory")
    total_modules: int = Field(default=0, description="Total internal modules analyzed")
    has_circular_imports: bool = Field(default=False, description="True if any cyclic dependency loops found")
    cycles_count: int = Field(default=0, description="Count of circular import cycles detected")
    cycles: list[list[str]] = Field(default_factory=list, description="Detected circular dependency cycles")
    error: str | None = Field(default=None, description="Error details if analysis failed")


class ModuleCouplingResult(BaseModel):
    """Result of module coupling calculation."""

    status: str = Field(default="ok", description="Status indicator")
    total_modules: int = Field(default=0, description="Total modules analyzed")
    metrics: list[dict[str, Any]] = Field(default_factory=list, description="Afferent (Ca), Efferent (Ce), and Instability (I) metrics")
    error: str | None = Field(default=None, description="Error details if analysis failed")


class BoundaryCheckResult(BaseModel):
    """Result of layer boundary verification."""

    status: str = Field(default="ok", description="Status indicator")
    layer_hierarchy: list[str] = Field(default_factory=list, description="Ordered layer hierarchy enforced")
    clean: bool = Field(default=True, description="True if no inward dependency violations found")
    violations_count: int = Field(default=0, description="Count of layer boundary violations")
    violations: list[dict[str, Any]] = Field(default_factory=list, description="Details of illegal cross-layer imports")
    error: str | None = Field(default=None, description="Error details if check failed")


@runtime_checkable
class ArchLinterService(Protocol):
    """Protocol for architecture linting, circular import detection, and coupling metrics."""

    def detect_circular_imports(self, root_path: str = "src") -> CircularImportResult:
        """Scan a Python directory, build module import graph, and detect circular loops."""
        ...

    def compute_module_coupling(self, root_path: str = "src") -> ModuleCouplingResult:
        """Compute afferent (Ca) and efferent (Ce) coupling and instability metrics."""
        ...

    def verify_clean_boundaries(
        self,
        root_path: str = "src",
        layer_hierarchy: list[str] | None = None,
    ) -> BoundaryCheckResult:
        """Verify that inner architectural layers do not import outer layers."""
        ...


ARCH_LINTER_KEY: ServiceKey[ArchLinterService] = ServiceKey("service.arch_linter")
