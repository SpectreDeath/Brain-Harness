# Quick Start Guide: `domain.dataset_profiler` (v1.0.0)

> Tabular statistical profiling, outlier detection (Z-score), and correlation matrix calculator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`profile_tabular_dataset`**: Compute comprehensive statistics, null ratios, uniqueness, and distributions across all columns
- **`detect_outliers_zscore`**: Detect numerical anomalies using standard Z-score deviations (> threshold)
- **`compute_correlation_matrix`**: Compute Pearson correlation coefficients between numerical columns

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.dataset_profiler.profile_tabular_dataset', {'records': '<records>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.dataset_profiler
harness plugin enable domain.dataset_profiler
```

## ⚡ Available Entrypoints & Skills
- **`profile_tabular_dataset(records: array)`**
  Compute comprehensive statistics, null ratios, uniqueness, and distributions across all columns
- **`detect_outliers_zscore(values: array, threshold: number)`**
  Detect numerical anomalies using standard Z-score deviations (> threshold)
- **`compute_correlation_matrix(records: array, columns: array)`**
  Compute Pearson correlation coefficients between numerical columns