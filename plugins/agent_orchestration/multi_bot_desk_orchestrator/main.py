"""Multi-Bot Desk Orchestrator Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeVar

import structlog

T = TypeVar("T")

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.multi_bot_desk import (  # noqa: E402
    MULTI_BOT_DESK_SERVICE_KEY,
    BotDeskLease,
    BotHopDispatchOutcome,
    BotHopDispatchRequest,
    McpApprovalOutcome,
    McpApprovalRequest,
    MultiBotDeskProtocol,
)

try:
    from .service import DefaultMultiBotDeskService
except ImportError:
    from service import DefaultMultiBotDeskService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class MultiBotDeskOrchestratorPlugin(HarnessPlugin, MultiBotDeskProtocol):
    """HarnessPlugin providing MultiBotDeskProtocol in the IoC container (Rule 45)."""

    name = "plugin.multi_bot_desk_orchestrator"
    version = "1.0.0"
    description = (
        "Multi-bot desk orchestrator with hop-depth guards, in-band MCP "
        "approval gates, and isolated display/gateway leases"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultMultiBotDeskService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MULTI_BOT_DESK_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(MULTI_BOT_DESK_SERVICE_KEY, self, provider=self.name)
        logger.info("MultiBotDeskOrchestratorPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    async def enqueue_bot_turn(
        self, bot_id: str, turn_fn: Callable[[], Awaitable[T]]
    ) -> T:
        return await self._service.enqueue_bot_turn(bot_id, turn_fn)

    def evaluate_bot_hop_dispatch(
        self, request: BotHopDispatchRequest
    ) -> BotHopDispatchOutcome:
        return self._service.evaluate_bot_hop_dispatch(request)

    def evaluate_mcp_tool_approval(
        self, request: McpApprovalRequest
    ) -> McpApprovalOutcome:
        return self._service.evaluate_mcp_tool_approval(request)

    def allocate_bot_desk_lease(
        self,
        bot_id: str,
        *,
        is_primary: bool = False,
        occupied_displays: tuple[int, ...] = (),
    ) -> BotDeskLease:
        return self._service.allocate_bot_desk_lease(
            bot_id,
            is_primary=is_primary,
            occupied_displays=occupied_displays,
        )


plugin = MultiBotDeskOrchestratorPlugin()


# --- Subprocess JSON-RPC Entrypoint Functions ---


def desk_evaluate_bot_hop(
    from_bot_id: str,
    to_bot_id: str,
    message_text: str = "",
    current_depth: int = 0,
    max_depth: int = 3,
    is_room_broadcast: bool = False,
    room_member_ids: list[str] | None = None,
    mentioned_bot_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate whether a bot-to-bot or room dispatch is permitted."""
    req = BotHopDispatchRequest(
        from_bot_id=from_bot_id,
        to_bot_id=to_bot_id,
        message_text=message_text,
        current_depth=current_depth,
        max_depth=max_depth,
        is_room_broadcast=is_room_broadcast,
        room_member_ids=tuple(room_member_ids or []),
        mentioned_bot_ids=tuple(mentioned_bot_ids or []),
    )
    return asdict(plugin.evaluate_bot_hop_dispatch(req))


def desk_evaluate_mcp_approval(
    bot_id: str,
    tool_name: str,
    is_read_only: bool = False,
    always_allowed_tools: list[str] | None = None,
    user_interrupted: bool = False,
) -> dict[str, Any]:
    """Evaluate an in-band MCP tool call approval."""
    req = McpApprovalRequest(
        bot_id=bot_id,
        tool_name=tool_name,
        is_read_only=is_read_only,
        always_allowed_tools=tuple(always_allowed_tools or []),
        user_interrupted=user_interrupted,
    )
    return asdict(plugin.evaluate_mcp_tool_approval(req))


def desk_allocate_lease(
    bot_id: str,
    is_primary: bool = False,
    occupied_displays: list[int] | None = None,
) -> dict[str, Any]:
    """Allocate an isolated display, gateway port, and CDP port lease."""
    lease = plugin.allocate_bot_desk_lease(
        bot_id,
        is_primary=is_primary,
        occupied_displays=tuple(occupied_displays or []),
    )
    return asdict(lease)
