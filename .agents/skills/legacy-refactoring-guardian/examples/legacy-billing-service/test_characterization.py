"""Characterization test suite capturing existing observable behavior of process_billing."""

from __future__ import annotations
import pytest
from legacy_billing import process_billing, _GLOBAL_DB, _GLOBAL_EMAIL


class TestBillingCharacterization:
    """Documents what the billing system does TODAY (including historical quirks)."""

    def setup_method(self) -> None:
        _GLOBAL_DB.records.clear()
        _GLOBAL_EMAIL.sent_emails.clear()

    def test_characterize_zero_dollar_charges_flat_100_fee(self) -> None:
        # Documenting observed behavior today (anomaly quarantined)
        res = process_billing("ord-zero", 0, "STANDARD")
        assert res["status"] == "CONFIRMED"
        assert res["fee_cents"] == 100
        assert res["total_cents"] == 100
        assert res["total_display"] == "$1.00"
        assert _GLOBAL_DB.records["ord-zero"]["fee_cents"] == 100

    def test_characterize_vip_large_order_discount(self) -> None:
        # 5000 cents with VIP: 5% fee (250), 20% discount (1000) -> 4250
        res = process_billing("ord-vip", 5000, "VIP", email="vip@example.com")
        assert res["fee_cents"] == 250
        assert res["total_cents"] == 4250
        assert res["total_display"] == "$42.50"
        assert len(_GLOBAL_EMAIL.sent_emails) == 1
        assert _GLOBAL_EMAIL.sent_emails[0]["to"] == "vip@example.com"

    def test_characterize_negative_amount_clamps_to_zero(self) -> None:
        res = process_billing("ord-neg", -500, "STANDARD")
        assert res["fee_cents"] == 0
        assert res["total_cents"] == 0
        assert res["total_display"] == "$0.00"

    def test_characterize_standard_customer_rate(self) -> None:
        res = process_billing("ord-std", 2000, "STANDARD")
        assert res["fee_cents"] == 200
        assert res["total_cents"] == 2200
        assert res["total_display"] == "$22.00"
