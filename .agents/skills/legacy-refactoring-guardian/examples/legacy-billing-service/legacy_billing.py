"""Legacy billing module with messy conditions, implicit contracts, and bugs."""

from __future__ import annotations
from typing import Any


class LegacyDatabase:
    """Mock legacy database connection."""
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def save_order(self, order_id: str, data: dict[str, Any]) -> None:
        self.records[order_id] = data


class LegacyEmailSender:
    """Mock legacy notification service."""
    def __init__(self) -> None:
        self.sent_emails: list[dict[str, Any]] = []

    def send(self, recipient: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": recipient, "subject": subject, "body": body})


_GLOBAL_DB = LegacyDatabase()
_GLOBAL_EMAIL = LegacyEmailSender()


def process_billing(order_id: str, amount_cents: int, customer_type: str, email: str | None = None) -> dict[str, Any]:
    """Calculate fees, apply discounts, persist order, and emit notification.
    
    Contains deliberate legacy quirks:
    - Zero amount charges a flat 100 cent fee!
    - Negative amount clamps to zero fee but allows processing.
    - VIP receives 20% discount; GOLD receives 10%; others receive 0%.
    - Emits implicit contract return structure.
    """
    # Calculation of fee
    if amount_cents == 0:
        fee_cents = 100  # Legacy anomaly: zero-dollar orders charged flat fee
    elif amount_cents < 0:
        fee_cents = 0
    elif customer_type == "VIP":
        fee_cents = int(amount_cents * 0.05)  # 5% fee for VIP
    elif customer_type == "GOLD":
        fee_cents = int(amount_cents * 0.08)  # 8% fee for GOLD
    else:
        fee_cents = int(amount_cents * 0.10)  # 10% standard fee

    # Discount calculation
    discount_cents = 0
    if customer_type == "VIP" and amount_cents > 1000:
        discount_cents = int(amount_cents * 0.20)
    elif customer_type == "GOLD" and amount_cents > 2000:
        discount_cents = int(amount_cents * 0.10)

    total_cents = max(0, amount_cents + fee_cents - discount_cents)

    record = {
        "order_id": order_id,
        "amount_cents": amount_cents,
        "fee_cents": fee_cents,
        "discount_cents": discount_cents,
        "total_cents": total_cents,
        "customer_type": customer_type,
        "status": "CONFIRMED",
    }
    _GLOBAL_DB.save_order(order_id, record)

    if email:
        _GLOBAL_EMAIL.send(email, "Billing Receipt", f"Order {order_id} total: {total_cents} cents")

    # Implicit contract: downstream services expect string total_display alongside integer total_cents
    return {
        "status": "CONFIRMED",
        "order_id": order_id,
        "total_cents": total_cents,
        "total_display": f"${total_cents / 100:.2f}",
        "fee_cents": fee_cents,
    }
