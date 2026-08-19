---
name: structured-data-scout
description: Discover and retrieve pre-cleaned, standardized tabular datasets from curated repositories (UCI, Kaggle, OpenData, HuggingFace Datasets). Use when the user requests dataset acquisition, tabular benchmarks, structured data sourcing, or downloading datasets without web scraping.
---

# Structured Data Scout Engine

The `structured-data-scout` engine operationalizes the *Curated Pipeline* methodology. It bypasses brittle web scrapers and unstructured HTML rendering by querying authoritative, curated data registries to pull standardized tabular formats (`.csv`, `.parquet`, `.jsonl`) directly into `data/`.

Every sourcing cycle follows a strict five-stage progression:

```
[1. Resolve Registry] → [2. Streamed Fetch & Validation] → [3. Localize & Normalize] → [4. Visual Sourcing Brief (Temp HTML)] → [5. Verification Checkpoint]
```

See [CARD.md](CARD.md) for the quick-reference cheat sheet, supported registries, and completion criteria.
Consult `/crafting-skills` for the underlying design standard and three foundational pillars.

---

## 1. Resolve Registry (The Curated Pipeline)

Match the target domain to primary curated repositories instead of initiating unstructured web scraping:
1. **UCI Machine Learning Repository**: Benchmark datasets, classification, regression, and clustering matrices.
2. **Kaggle API / Hugging Face Datasets**: Domain-specific annotated matrices and multimodal feature tables.
3. **Open Data Portals (data.gov / Eurostat)**: Macroeconomic, public health, and demographic records.
4. **Registry Priority Rule**: Always select structured endpoints (`.parquet` > `.csv` > `.jsonl`) before considering raw web DOM scraping.

> **Completion criterion**: Target dataset endpoint resolved to a direct download URI or official SDK client call.

---

## 2. Streamed Fetch & Magic Number Validation

Retrieve the dataset using out-of-core streaming without buffering the entire payload into model context:
1. Stream file chunks directly into `data/raw/<dataset_id>.<ext>`.
2. Inspect tabular headers and magic numbers to verify file integrity.
3. Reject HTML error payloads, truncated HTTP streams, or corrupted archives immediately.

> **Completion criterion**: Raw file written to disk; schema verified with valid header row and correct MIME type.

---

## 3. Localize & Normalize (Columnar Conversion)

Standardize the raw tabular data into memory-efficient formats:
1. Normalize column headers to `snake_case` with special characters stripped.
2. Convert dense CSV files to `.parquet` or memory-mapped `.feather` in `data/processed/<dataset_id>.parquet`.
3. Preserve the original raw file in `data/raw/` as an immutable source node.

> **Completion criterion**: Normalized tabular file saved in `data/processed/` with clean column headers and UTF-8 encoding.

---

## 4. Recommend (The Visual Sourcing Brief)

Synthesize source provenance, column types, and storage footprint into an interactive HTML visual brief:

1. **Target Path**: Write to `%TEMP%\data-scout-<timestamp>.html` (Windows) or `/tmp/data-scout-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
   - Include a Mermaid **Lineage & Schema Topology** graph showing registry origin, processing steps, and output files.
   - Render column cards displaying data types, non-null counts, and memory footprint.
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\data-scout-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Structured Data Scout Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Structured Data Sourcing Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Curated Registry Ingestion & Normalization Report</p>
  </header>
  <!-- Interactive Schema Topology & Ingestion Stats -->
</body>
</html>
```

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 5. Verification Checkpoint (Metadata Receipt)

Present the verified metadata receipt and pause execution for user confirmation:

1. Emit a structured markdown summary block:
   ```markdown
   ### [Data Ingestion Receipt]
   - **Source**: `UCI Machine Learning Repository (ID: 186)`
   - **Raw File**: `data/raw/wine_quality.csv` (264 KB)
   - **Normalized File**: `data/processed/wine_quality.parquet` (82 KB)
   - **Dimensions**: 4,898 rows × 12 columns
   - **Status**: [VERIFIED & LOCALIZED]
   ```
2. Update `implementation_plan.md` with `RequestFeedback: true` if downstream analysis or modeling requires approval.

> **Completion criterion**: Summary receipt delivered to user; user signs off before downstream modeling.

---

## Anti-Patterns

- **Raw DOM Scraping Fallback** — Scraping messy HTML tables with browser automation when a direct API/Parquet endpoint exists.
- **Context Flooding** — Dumping raw CSV rows or `head -n 500` dumps directly into the conversation context window.
- **Monolithic In-Memory Buffering** — Loading multi-GB datasets into RAM all at once instead of streaming chunks to disk.
- **Unvalidated Ingestion** — Proceeding with unverified files containing corrupted headers, null bytes, or mismatched schemas.
