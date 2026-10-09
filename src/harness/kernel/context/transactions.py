"""Transactional effect boundaries and LIFO rollback on failure (Definition 51, 52, Theorem 61)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import ServiceContext


@asynccontextmanager
async def execute_transaction(
    context: ServiceContext,
) -> AsyncIterator[ServiceContext]:
    """Execute operations within a transactional effect boundary (Definition 51 & 52).

    If any error occurs within the context block, all effects registered
    during the transaction are rolled back in LIFO order (Theorem 61).
    On success, the entries and inverses are committed and merged into the parent accumulator,
    recording pre-images to guarantee safe restoration upon any subsequent disposal.
    """
    tx_ctx = context.child()
    try:
        yield tx_ctx
        with context._mutation_lock:
            # Record pre-images of existing entries that will be overwritten
            prior_entries = {
                k: context._entries[k] for k in tx_ctx._entries if k in context._entries
            }
            if prior_entries:

                def _restore_priors() -> None:
                    with context._mutation_lock:
                        new_entries = dict(context._entries)
                        for k, prior in prior_entries.items():
                            new_entries[k] = prior
                        context._entries = new_entries
                        context._interceptor_epoch += 1
                        root = context._get_root()
                        if root is not context:
                            root._interceptor_epoch += 1

                context._dispose_stack.append(_restore_priors)

            # Commit: merge transaction entries, services, and effects into parent context
            new_entries = dict(context._entries)
            new_entries.update(tx_ctx._entries)
            context._entries = new_entries
            context._interceptor_epoch += 1
            root = context._get_root()
            if root is not context:
                root._interceptor_epoch += 1

            for prov, services in tx_ctx._plugin_services.items():
                context._plugin_services.setdefault(prov, []).extend(services)

            # Compact inverses: Keep only the latest inverse per realm_key
            # in tx_ctx._dispose_stack (as seen in reversed iteration)
            seen: set[str] = set()
            compacted: list[Any] = []
            for inv in reversed(tx_ctx._dispose_stack):
                rk = getattr(inv, "_realm_key", None)
                if rk is not None:
                    if rk in seen:
                        continue
                    seen.add(rk)
                compacted.append(inv)
            context._dispose_stack.extend(reversed(compacted))
            tx_ctx._dispose_stack.clear()
    except Exception:
        # Abort: rollback all intermediate effects in LIFO order
        await tx_ctx.dispose()
        raise
