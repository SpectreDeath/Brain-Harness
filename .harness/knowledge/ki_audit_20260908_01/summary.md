## Clock-Sensitive Test Smell

### Discovery
`tests/test_data_management_architect.py::TestDataContractValidatorScript::test_valid_dataset_passes`
uses a hardcoded timestamp `2026-09-06T12:00:00+00:00` in the test fixture dataset.

The `DataContractValidator` checks that a `last_updated` timestamp is <= 48 hours old
relative to `datetime.now()`. Because the fixture timestamp is hardcoded, this test will
permanently fail 48+ hours after its authoring date.

### Root Cause
Absolute UTC timestamps in test fixtures must be replaced with relative anchors
(e.g., `datetime.now(timezone.utc) - timedelta(hours=N)`) or use `freezegun`/`time_machine`
for deterministic clock mocking.

### Fix Pattern
```python
from datetime import datetime, timedelta, timezone
hardcoded = datetime.now(timezone.utc) - timedelta(hours=24)  # always within SLA
```

### Source
- tests/test_data_management_architect.py:122
- .agents/skills/data-management-architect/scripts/data_contract_validator.py

### Rule Reference
No existing AGENTS.md rule covers this pattern. Candidate for Rule 45.
