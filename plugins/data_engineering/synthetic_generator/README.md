# domain.synthetic_generator (v1.0.0)

Schema-constrained synthetic mock dataset and time-series generator

---

## Overview & Metadata

- **Plugin Directory**: `plugins/data_engineering/synthetic_generator`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `generate_mock_records` | `(schema, count, seed)` | Generate synthetic tabular records conforming to a schema definition (name, email, uuid, integer, float, enum) |
| `generate_synthetic_timeseries` | `(days, baseline, trend)` | Generate synthetic daily time-series values with trend, seasonality, and Gaussian noise |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Synthetic mock dataset and timeseries generator plugin for Brain Harness.

#### Functions

- `def generate_mock_records(schema, count, seed) -> dict[str, Any]`
  - Generate synthetic records from a field schema.
- `def generate_synthetic_timeseries(days, baseline, trend) -> dict[str, Any]`
  - Generate daily timeseries data with trend and weekly seasonality.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
