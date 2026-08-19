# Skill Summary Card: `data-topology-mapper`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        data-topology-mapper                      │
│ Category:    data-science / profiling                  │
│ Invocation:  /data-topology-mapper                     │
│ Trigger:     "map data topology", "profile dataset",   │
│              "statistical pre-flight", "anomaly scan"  │
│ Version:     1.0.0                                     │
├────────────────────────────────────────────────────────┤
│ Target:      Extract out-of-core statistical moments   │
│              and anomaly fingerprints from datasets    │
│              without flooding LLM context or VRAM.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Data Topology Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Target Seam** | Verify target file path and disk size in `data/` | Path & disk metadata | Raw rows kept out of context |
| **2. Pre-Flight Probe** | Run `auditor.py` in isolated subprocess for moments | JSON summary receipt | Zero raw data printed to stdout |
| **3. Anomaly Mapping** | Compute Isolation Forest contamination & distribution types | Outlier scores & distributions | Contamination rate classified |
| **4. Visual Brief** | Render interactive HTML histogram & correlation heatmap | `%TEMP%\data-topology-*.html` | Dark-mode HTML written and delivered |
| **5. Distilled Emission** | Emit $\le 200$-token state fingerprint and confirm plan | Markdown fingerprint block | User approval received |

---

## Statistical Extraction Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│                   MOMENT EXTRACTION LENS                        │
├────────────────────────────────┬────────────────────────────────┤
│ Central Tendency               │ Mean (μ), Median (Q2)          │
├────────────────────────────────┼────────────────────────────────┤
│ Dispersion                     │ Std Dev (σ), IQR (Q3 - Q1)     │
├────────────────────────────────┼────────────────────────────────┤
│ Distribution Shape             │ Skewness (γ1), Kurtosis (γ2)   │
├────────────────────────────────┼────────────────────────────────┤
│ Anomaly Quantification         │ Isolation Forest Contamination │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Verification & Quality Checklist

- [ ] **Zero Context Flooding**: Dataset rows are processed strictly out-of-core.
- [ ] **Moments Extracted**: Mean, std, skewness, and IQR computed via `auditor.py`.
- [ ] **Visual Topology Brief Present**: Temp HTML report generated and delivered.
- [ ] **Compact Emission**: Final fingerprint constrained to $\le 200$ tokens.
