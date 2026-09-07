"""Refactored billing module with extracted policy and injected dependency seams."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


class DatabaseStore(Protocol):
    def save_order(self, order_id: str, data: dict[str, Any]) -> None: ...


class NotificationService(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...


@dataclass(frozen=True, slots=True)
class BillingResult:
    """Immutable value object representing calculated billing components."""
    amount_cents: int
    fee_cents: int
    discount_cents: int
    total_cents: int

    @property
    def total_display(self) -> str:
        return f"${self.total_cents / 100:.2f}"


class BillingPolicy:
    """Pure domain logic separated from database and network infrastructure."""

    @staticmethod
    def calculate(amount_cents: int, customer_type: str) -> BillingResult:
        # Preserve historical quirk: zero amount charges flat fee
        if amount_cents == 0:
            fee_cents = 100
        elif amount_cents < 0:
            fee_cents = 0
        elif customer_type == "VIP":
            fee_cents = int(amount_cents * 0.05)
        elif customer_type == "GOLD":
            fee_cents = int(amount_cents * 0.08)
        else:
            fee_cents = int(amount_cents * 0.10)

        discount_cents = 0
        if customer_type == "VIP" and amount_cents > 1000:
            discount_cents = int(amount_cents * 0.20)
        elif customer_type == "GOLD" and amount_cents > 2000:
            discount_cents = int(amount_cents * 0.10)

        total_cents = max(0, amount_cents + fee_cents - discount_cents)
        return BillingResult(
            amount_cents=amount_cents,
            fee_cents=fee_cents,
            discount_cents=discount_cents,
            total_cents=total_cents,
        )


class BillingService:
    """Application coordinator with injected dependencies (Seam architecture)."""

    def __init__(self, db: DatabaseStore | None = None, notifier: NotificationService | None = None) -> None:
        from legacy_billing import _GLOBAL_DB, _GLOBAL_EMAIL
        self.db = db or _GLOBAL_DB
        self.notifier = notifier or _GLOBAL_EMAIL

    def process(self, order_id: str, amount_cents: int, customer_type: str, email: str | None = None) -> dict[str, Any]:
        result = BillingPolicy.calculate(amount_cents, customer_type)

        record = {
            "order_id": order_id,
            "amount_cents": result.amount_cents,
            "fee_cents": result.fee_cents,
            "discount_cents": result.discount_cents,
            "total_cents": result.total_cents,
            "customer_type": customer_type,
            "status": "CONFIRMED",
        }
        self.db.save_order(order_id, record)

        if email:
            self.notifier.send(email, "Billing Receipt", f"Order {order_id} total: {result.total_cents} cents")

        return {
            "status": "CONFIRMED",
            "order_id": order_id,
            "total_cents": result.total_cents,
            "total_display": result.total_display,
            "fee_cents": result.fee_cents,
        }


# Backward-compatible public functional interface
def process_billing(
    order_id: str,
    amount_cents: int,
    customer_type: str,
    email: str | None = None,
    service: BillingService | None = None,
) -> dict[str, Any]:
    active_service = service or BillingService()
    return active_service.process(order_id, amount_cents, customer_type, email=email)
