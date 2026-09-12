# domain.dataset_profiler (v1.0.0)

Tabular statistical profiling, outlier detection (Z-score), and correlation matrix calculator

---

## Overview & Metadata

- **Plugin Directory**: `plugins/data_engineering/dataset_profiler`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `profile_tabular_dataset` | `(records)` | Compute comprehensive statistics, null ratios, uniqueness, and distributions across all columns |
| `detect_outliers_zscore` | `(values, threshold)` | Detect numerical anomalies using standard Z-score deviations (> threshold) |
| `compute_correlation_matrix` | `(records, columns)` | Compute Pearson correlation coefficients between numerical columns |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Tabular dataset profiler, Z-score outlier detector, and correlation matrix plugin.

#### Functions

- `def profile_tabular_dataset(records) -> dict[str, Any]`
  - Compute rich tabular statistics across all columns.
- `def detect_outliers_zscore(values, threshold) -> dict[str, Any]`
  - Identify outliers in a list of numbers using the Z-score method.
- `def compute_correlation_matrix(records, columns) -> dict[str, Any]`
  - Compute Pearson correlation matrix between numerical columns.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
