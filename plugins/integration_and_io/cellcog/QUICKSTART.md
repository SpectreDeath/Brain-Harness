# CellCog Multimodal Sub-Agent Plugin — Quickstart

## Overview

The `plugin.cellcog` plugin provides first-class, typed any-to-any sub-agent delegation to CellCog for generative tasks beyond code:
- **3D Asset Modeling**: Text or sketches to production-ready `.GLB` assets.
- **Cinematic Video**: 4K scene rendering, viral 9:16 short-form, and long-form video.
- **Audio & Music**: Multi-host podcasts, sound effects, voice cloning, and original music.
- **Executive Documents**: Formatted PDF reports, Excel spreadsheets (`.XLSX`), and slide decks.
- **Deep Research**: Citation-backed multi-source synthesis (#1 on DeepResearch Bench).

---

## Configuration

Set your `CELLCOG_API_KEY` environment variable:

```bash
export CELLCOG_API_KEY="sk_..."
```

On Windows PowerShell:
```powershell
$env:CELLCOG_API_KEY = "sk_..."
```

---

## Tools

### 1. `cellcog_run`

Execute any general multimodal task in `agent` or `creative` mode:

```python
result = cellcog_run(
    prompt="""
    Analyze this quarterly report and generate a PDF summary and 3D product asset:
    <SHOW_FILE>/workspace/data/q4_sales.csv</SHOW_FILE>
    <GENERATE_FILE>/workspace/output/q4_summary.pdf</GENERATE_FILE>
    <GENERATE_FILE>/workspace/output/product_v1.glb</GENERATE_FILE>
    """,
    chat_mode="agent",
    chat_tier="max",
    timeout=1800,
)
```

### 2. `cellcog_research`

Execute deep multi-source research in `team` mode with citation tracking:

```python
result = cellcog_research(
    topic="Competitive landscape of local LLM agent runtimes in 2026",
    attachments=["/workspace/notes/benchmarks.txt"],
    chat_tier="flash",
    timeout=3600,
)
```

### 3. `cellcog_list_capabilities`

Inspect the 39 available CellCog modality capabilities across 7 categories:

```python
catalog = cellcog_list_capabilities()
print(f"Total capabilities: {catalog['total_capabilities']}")
```

---

## The `<SHOW_FILE>` & `<GENERATE_FILE>` Tag Protocol

- **`<SHOW_FILE>/path/to/file</SHOW_FILE>`**: Tells CellCog to upload and visually/structurally inspect the file contents (PDF, CSV, audio, image, code).
- **`<GENERATE_FILE>/path/to/target</GENERATE_FILE>`**: Tells CellCog where to save the generated output artifact on your local filesystem.

> **Security Invariant**: Never enclose credentials, private keys, `.env` files, or `.ssh/` paths in `<SHOW_FILE>` tags. The plugin automatically filters and redacts sensitive file patterns before dispatch.
