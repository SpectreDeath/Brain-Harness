# Skill Summary Card: `structured-data-scout`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        structured-data-scout                     │
│ Category:    data-science / ingestion                  │
│ Invocation:  /structured-data-scout                    │
│ Trigger:     "scout dataset", "fetch structured data", │
│              "pull tabular data", "source dataset"     │
│ Version:     1.0.0                                     │
│ Requires:    "crafting-skills"                         │
│ Provides:    "dataset_sourcing"                        │
├────────────────────────────────────────────────────────┤
│ Target:      Fetch pre-cleaned tabular data from       │
│              curated registries (UCI, Kaggle, OpenData)│
│              directly to disk, bypassing web scrapers. │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Data Sourcing Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Resolve Registry** | Map query to authoritative repository (UCI, Kaggle, OpenData) | Direct download URI / SDK query | Structured endpoint prioritized |
| **2. Streamed Fetch** | Stream raw file directly to `data/raw/` | `data/raw/<id>.<ext>` | Magic numbers & headers verified |
| **3. Localize & Normalize** | Standardize column headers and convert to `.parquet` | `data/processed/<id>.parquet` | UTF-8, snake_case schema saved |
| **4. Visual Brief** | Render interactive HTML schema & lineage report | `%TEMP%\data-scout-*.html` | Dark-mode HTML written and delivered |
| **5. Verification Gate** | Emit compact metadata receipt and confirm before modeling | Ingestion receipt block | User approval received |

---

## Curated Registry Precedence Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRY PRECEDENCE                          │
├────────────────────────────────┬────────────────────────────────┤
│ 1. Direct Columnar / Parquet   │ HuggingFace Datasets, OpenML   │
├────────────────────────────────┼────────────────────────────────┤
│ 2. Standard Benchmark Tabular  │ UCI Machine Learning Repo      │
├────────────────────────────────┼────────────────────────────────┤
│ 3. Public Domain / Gov Portals │ Data.gov, Eurostat, World Bank │
├────────────────────────────────┼────────────────────────────────┤
│ 4. Domain Archives             │ Kaggle API, Zenodo, Dryad      │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Anti-Patterns Cheat Sheet

- **Raw DOM Scraping Fallback**: Scraping messy HTML tables when direct API/Parquet endpoints exist.
- **Context Flooding**: Dumping raw CSV rows or large dumps directly into chat context.
- **Monolithic Buffering**: Loading multi-GB datasets into RAM all at once instead of streaming to disk.
- **Unvalidated Ingestion**: Proceeding with unverified files containing corrupted headers.

---

## Invariants & Guardrails

- [ ] **No Context Flooding**: Raw rows are never printed directly into the chat prompt.
- [ ] **Streamed to Disk**: Files are saved to `data/raw/` with zero in-memory buffering.
- [ ] **Normalized Parquet Saved**: Clean columnar copies created in `data/processed/`.
- [ ] **Visual Sourcing Brief Present**: Temp HTML report generated and delivered.
- [ ] **Verification Receipt Emitted**: Ingestion receipt delivered before downstream modeling.
