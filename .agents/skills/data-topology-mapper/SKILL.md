---
name: data-topology-mapper
description: Run statistical pre-flight profiling on tabular datasets using lightweight moment extraction and Isolation Forests. Use when the user asks to analyze data distributions, detect anomalies, profile dataset topology, or inspect dataset health without flooding the context window.
---

# Data Topology Mapper Engine

The `data-topology-mapper` engine operationalizes the *Parameter Sandbox* and *Distiller* methodologies. It runs an out-of-core statistical audit on tabular files via `auditor.py`, producing a high-density, low-token topological fingerprint ($\le 200$ tokens) covering statistical moments, sparsity, and anomaly contamination while protecting the 6GB VRAM hardware ceiling.

Every profiling cycle follows a strict five-stage progression:

```
[1. Target Seam] → [2. Statistical Pre-Flight] → [3. Anomaly & Distribution Mapping] → [4. Visual Topology Brief (Temp HTML)] → [5. Distilled State Emission]
```

See [CARD.md](CARD.md) for the quick-reference cheat sheet, statistical moment formulas, and completion criteria.
Consult `/crafting-skills` for the underlying design standard and three foundational pillars.

---

## 1. Target Seam Identification

Identify the target dataset path and verify format bounds before inspection:
1. Locate target file in `data/processed/` or `data/raw/` (`.parquet`, `.csv`, `.feather`).
2. Verify file size on disk using filesystem metadata.
3. **Never** execute raw `view_file` or `cat` on large data tables.

> **Completion criterion**: Target dataset path verified with disk size and format metadata.

---

## 2. Statistical Pre-Flight Probe (The Parameter Sandbox)

Execute an out-of-core statistical audit in an isolated subprocess via `auditor.py`:
1. Calculate parametric & non-parametric moments:
   - **Central Tendency & Spread**: Mean ($\mu$), Standard Deviation ($\sigma$), Median, Interquartile Range ($\text{IQR}$).
   - **Shape**: Skewness ($\gamma_1$) and Excess Kurtosis ($\gamma_2$).
2. Compute completeness:
   - Missing value percentage per column.
   - Zero-variance / constant feature detection.
   - Total memory footprint in bytes.

```bash
python -m harness.utils.auditor --input "data/processed/dataset.parquet" --output-format json
```

> **Completion criterion**: JSON statistical receipt emitted with zero raw rows printed to stdout.

---

## 3. Anomaly & Distribution Mapping

Run topological anomaly detection and feature classification:
1. **Isolation Forest Profiling**: Run a fast `IsolationForest(n_estimators=50, contamination='auto')` or Tukey IQR fences to quantify outlier contamination rate ($C_{\text{outlier}}$).
2. **Distribution Classification**: Classify each numeric feature into standard taxonomies (`Gaussian`, `Log-Normal`, `Bimodal`, `Uniform`, `Zero-Inflated/Sparse`).
3. **Collinearity Scan**: Rank top pairwise Pearson/Spearman correlation coefficients ($|r| \ge 0.80$).

> **Completion criterion**: Contamination score, distribution classifications, and collinearity pairs computed.

---

## 4. Recommend (The Visual Topology Brief)

Synthesize distributions, outlier scores, and correlation heatmaps into an interactive HTML visual brief:

1. **Target Path**: Write to `%TEMP%\data-topology-<timestamp>.html` (Windows) or `/tmp/data-topology-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
   - Include distribution histogram cards for high-variance features.
   - Render an interactive **Anomaly & Collinearity Heatmap** identifying feature clusters.
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\data-topology-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dataset Topology Report</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Dataset Topology & Statistical Fingerprint</h1>
    <p class="text-sm text-gray-400 mt-1">Out-of-Core Moment Extraction & Anomaly Profiling</p>
  </header>
  <!-- Interactive Distribution Cards & Anomaly Metrics -->
</body>
</html>
```

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 5. Distilled State Emission & Checkpoint (The Distiller)

Emit a high-leverage markdown fingerprint block ($\le 200$ tokens) into the conversation context window:

```markdown
### [Data Topology Fingerprint]
- **Target**: `data/processed/wine_quality.parquet` (Rows: 4,898 | Cols: 12 | Size: 82 KB)
- **Data Health**: Completeness 100.0% | Anomaly Contamination: 2.8%
- **Key Distributions**:
  - `alcohol` (Continuous, $\mu=10.4$, $\sigma=1.2$, Skew: 0.56, Right-Skewed)
  - `density` (Normal-like, $\mu=0.994$, $\sigma=0.003$)
  - `chlorides` (Zero-Inflated / Long-Tail, Outliers: 4.2%)
- **Collinearity Flags**: (`free_sulfur_dioxide`, `total_sulfur_dioxide`, $r=0.62$)
- **Action Gate**: Distribution verified; ready for downstream modeling.
```

1. Update `implementation_plan.md` with `RequestFeedback: true` prior to training or mutating models.
2. Proceed with reasoning/modeling strictly using the abstracted state.

> **Completion criterion**: Compact fingerprint emitted; raw data remains safely out of VRAM/context; user approval received.

---

## Anti-Patterns

- **Context Window Flooding** — Using `cat`, `head -n 500`, or raw `view_file` on large data tables.
- **In-Memory Giant Scans** — Loading multi-GB tables into memory at once instead of streaming chunks through `auditor.py`.
- **Heuristic-Free Modeling** — Initiating model training or inference before knowing feature distribution skewness or contamination rates.
- **Silent Truncation** — Relying on arbitrary head/tail slices rather than computing true population moments.
