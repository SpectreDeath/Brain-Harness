"""Synthetic mock dataset and timeseries generator plugin for Brain Harness."""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

_FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah"]
_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
_DOMAINS = ["example.com", "test.org", "corp.net", "acme.io"]


def _generate_field_val(field_type: str, rng: random.Random) -> Any:
    t = field_type.lower().strip()

    if t == "uuid":
        return str(uuid.UUID(int=rng.getrandbits(128)))
    elif t == "name":
        return f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
    elif t == "email":
        fname = rng.choice(_FIRST_NAMES).lower()
        dom = rng.choice(_DOMAINS)
        return f"{fname}{rng.randint(10, 99)}@{dom}"
    elif t.startswith("int"):
        # e.g. int:10:100
        parts = t.split(":")
        low = int(parts[1]) if len(parts) > 1 else 0
        high = int(parts[2]) if len(parts) > 2 else 100
        return rng.randint(low, high)
    elif t.startswith("float"):
        parts = t.split(":")
        low = float(parts[1]) if len(parts) > 1 else 0.0
        high = float(parts[2]) if len(parts) > 2 else 1.0
        return round(rng.uniform(low, high), 2)
    elif t == "bool":
        return rng.choice([True, False])
    elif t.startswith("enum:"):
        options = t[5:].split(",")
        return rng.choice(options).strip()
    else:
        return f"mock_{t}_{rng.randint(100, 999)}"


def generate_mock_records(
    schema: dict[str, str],
    count: int = 10,
    seed: int | None = None,
) -> dict[str, Any]:
    """Generate synthetic records from a field schema."""
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []

    for _ in range(count):
        row: dict[str, Any] = {}
        for field_name, field_type in schema.items():
            row[field_name] = _generate_field_val(field_type, rng)
        records.append(row)

    return {
        "status": "ok",
        "record_count": len(records),
        "schema": schema,
        "records": records,
    }


def generate_synthetic_timeseries(
    days: int = 30,
    baseline: float = 100.0,
    trend: float = 0.5,
) -> dict[str, Any]:
    """Generate daily timeseries data with trend and weekly seasonality."""
    data_points: list[dict[str, Any]] = []
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    rng = random.Random(42)

    for i in range(days):
        cur_date = start_date + timedelta(days=i)
        # Weekly seasonality (sinusoidal)
        season = 10.0 * math.sin(2.0 * math.pi * (i % 7) / 7.0)
        noise = rng.uniform(-3.0, 3.0)
        val = baseline + (trend * i) + season + noise

        data_points.append({
            "date": cur_date.strftime("%Y-%m-%d"),
            "value": round(val, 2),
            "step": i + 1,
        })

    return {
        "status": "ok",
        "days": days,
        "baseline": baseline,
        "trend": trend,
        "series": data_points,
    }
