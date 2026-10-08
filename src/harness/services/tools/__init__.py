"""Tool registry service and middleware interceptor pipeline (decomposed).

Exposes execution context, tool specs, middleware interceptors, execution pipeline,
central tool registry, and IoC plugin. Preserves 100% backward compatibility for all
module-level imports from `harness.services.tools`.
"""

from __future__ import annotations

# 1. Models & Context
from harness.services.tools.models import (
    ToolExecutionContext,
    ToolExecutor,
    ToolSpec,
)

# 2. Interceptors
from harness.services.tools.interceptors import (
    AccessControlInterceptor,
    MemoizationInterceptor,
    RateLimitInterceptor,
    SchemaValidationInterceptor,
    TelemetryInterceptor,
    TimeoutGuardInterceptor,
    ToolInterceptor,
)

# 3. Execution Pipeline
from harness.services.tools.pipeline import ToolExecutionPipeline

# 4. Registry & ServiceKey
from harness.services.tools.registry import (
    TOOL_REGISTRY_KEY,
    ToolRegistry,
)

# 5. IoC Plugin
from harness.services.tools.plugin import ToolRegistryPlugin

__all__ = [
    # Models & Context
    "ToolExecutionContext",
    "ToolExecutor",
    "ToolSpec",
    # Interceptors
    "AccessControlInterceptor",
    "MemoizationInterceptor",
    "RateLimitInterceptor",
    "SchemaValidationInterceptor",
    "TelemetryInterceptor",
    "TimeoutGuardInterceptor",
    "ToolInterceptor",
    # Pipeline
    "ToolExecutionPipeline",
    # Registry
    "TOOL_REGISTRY_KEY",
    "ToolRegistry",
    # Plugin
    "ToolRegistryPlugin",
]
