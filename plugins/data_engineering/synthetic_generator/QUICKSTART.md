# Quick Start Guide: `domain.synthetic_generator` (v1.0.0)

> Schema-constrained synthetic mock dataset and time-series generator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`generate_mock_records`**: Generate synthetic tabular records conforming to a schema definition (name, email, uuid, integer, float, enum)
- **`generate_synthetic_timeseries`**: Generate synthetic daily time-series values with trend, seasonality, and Gaussian noise

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.synthetic_generator.generate_mock_records', {'schema': '<schema>', 'count': '<count>', 'seed': '<seed>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.synthetic_generator
harness plugin enable domain.synthetic_generator
```

## ⚡ Available Entrypoints & Skills
- **`generate_mock_records(schema: object, count: integer, seed: integer)`**
  Generate synthetic tabular records conforming to a schema definition (name, email, uuid, integer, float, enum)
- **`generate_synthetic_timeseries(days: integer, baseline: number, trend: number)`**
  Generate synthetic daily time-series values with trend, seasonality, and Gaussian noise