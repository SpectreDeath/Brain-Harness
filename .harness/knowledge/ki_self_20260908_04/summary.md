## Time-Relative Fixture Anchoring Invariant

### Problem
Test fixtures containing timestamps that are validated against time-window SLAs 
(freshness checks, recency assertions, TTL validations) must NOT use hardcoded 
past datetime strings.

### Confirmed Failure
```python
# tests/test_data_management_architect.py:122 — FAILS PERMANENTLY
dataset = {
    "last_updated": "2026-09-06T12:00:00+00:00",  # WRONG: hardcoded past timestamp
    ...
}
# DataContractValidator checks: last_updated <= 48h old → fails 48h after 2026-09-06
```

### Invariant
All SLA-validated fixture timestamps must use relative anchors:

```python
from datetime import datetime, timedelta, timezone

# CORRECT: always within any reasonable SLA window
dataset = {
    "last_updated": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
    ...
}
```

### Alternative
Use `freezegun` or `time_machine` for deterministic clock mocking when the SLA 
boundary itself must be tested precisely:

```python
from freezegun import freeze_time

@freeze_time("2026-09-08 12:00:00+00:00")
def test_valid_dataset_passes():
    dataset = {"last_updated": "2026-09-08T11:00:00+00:00"}  # 1h ago → within 48h
    assert DataContractValidator().validate(dataset).passed
```

### Scope
This invariant applies to any field that will be compared against `datetime.now()`:
- `last_updated`, `created_at`, `expires_at`, `refreshed_at`
- SLA windows: freshness checks, TTL assertions, recency validations
- Data contract validators, quality metric evaluators

### Related
- ki_audit_20260908_01: same failure, anti-pattern focus
- AGENTS.md Rule 33: JSON null-field fallback (related data fixture hygiene)
