# CellCog Multimodal Reference Recipes

Golden prompt recipes and parameter operating points for the top 5 high-leverage modalities.

---

## 1. 3D Model Generation (.GLB)

Transform text prompts or reference concept images into production-ready `.GLB` assets:

- **Operating Point**: `chat_mode="agent"`, `chat_tier="max"`, `timeout=1800`
- **Recommended Output Tag**: `<GENERATE_FILE>/workspace/assets/models/character_hero.glb</GENERATE_FILE>`

### Golden Prompt Recipe
```python
prompt = """
Generate a game-ready, textured 3D asset of a futuristic sci-fi hover vehicle with glowing neon thrusters.
Reference concept sketch:
<SHOW_FILE>/workspace/assets/sketches/vehicle_concept.png</SHOW_FILE>

Deliverable:
<GENERATE_FILE>/workspace/assets/models/hover_vehicle.glb</GENERATE_FILE>

Requirements:
- Production-ready PBR metallic-roughness textures
- Clean topology suitable for real-time engine import
"""
```

---

## 2. Cinematic 4K Video (.MP4)

Produce cinematic trailers, scene transitions, and short-form video content:

- **Operating Point**: `chat_mode="agent"`, `chat_tier="max"`, `timeout=3600`
- **Recommended Output Tag**: `<GENERATE_FILE>/workspace/assets/video/trailer_4k.mp4</GENERATE_FILE>`

### Golden Prompt Recipe
```python
prompt = """
Render a 30-second cinematic 4K trailer depicting an autonomous exploration rover descending onto the Martian surface during a dust storm.
Storyboard references:
<SHOW_FILE>/workspace/assets/storyboards/scene_01.png</SHOW_FILE>
<SHOW_FILE>/workspace/assets/storyboards/scene_02.png</SHOW_FILE>

Deliverables:
1. Video file: <GENERATE_FILE>/workspace/assets/video/mars_rover_trailer.mp4</GENERATE_FILE>
2. Subtitles: <GENERATE_FILE>/workspace/assets/video/mars_rover_trailer.srt</GENERATE_FILE>

Style: Photorealistic cinematic lighting, anamorphic lens flare, orchestral score.
"""
```

---

## 3. Interactive HTML5 Executive Dashboard

Generate standalone, Tailwind-styled responsive dashboards with dynamic charts:

- **Operating Point**: `chat_mode="creative"`, `chat_tier="max"`, `timeout=1800`
- **Recommended Output Tag**: `<GENERATE_FILE>/workspace/reports/q4_executive_dashboard.html</GENERATE_FILE>`

### Golden Prompt Recipe
```python
prompt = """
Analyze the attached quarterly revenue dataset and build an interactive, responsive HTML5 dashboard:
<SHOW_FILE>/workspace/data/q4_sales_breakdown.csv</SHOW_FILE>

Deliverable:
<GENERATE_FILE>/workspace/reports/q4_executive_dashboard.html</GENERATE_FILE>

Requirements:
- Dark mode theme (#0d1117 background) with Tailwind CSS
- Interactive Chart.js visualizations (revenue by product line, monthly ARR growth, churn rate)
- Metric KPI summary cards and filterable tabular breakdown
"""
```

---

## 4. Multi-Tab Financial Excel Model (.XLSX)

Synthesize financial models with active formulas, sensitivity tables, and macros:

- **Operating Point**: `chat_mode="agent"`, `chat_tier="core"`, `timeout=1800`
- **Recommended Output Tag**: `<GENERATE_FILE>/workspace/financials/dcf_valuation_model.xlsx</GENERATE_FILE>`

### Golden Prompt Recipe
```python
prompt = """
Based on the historical 10-K financial metrics:
<SHOW_FILE>/workspace/docs/historical_financials.pdf</SHOW_FILE>

Construct a 5-year discounted cash flow (DCF) valuation spreadsheet:
<GENERATE_FILE>/workspace/financials/dcf_valuation_model.xlsx</GENERATE_FILE>

Structure:
- Tab 1: Historical Financial Statements (Income Statement, Balance Sheet, Cash Flow)
- Tab 2: 5-Year Projections with dynamic revenue growth & margin assumptions
- Tab 3: WACC calculation & terminal value sensitivity table
"""
```

---

## 5. Multi-Source Deep Research Synthesis

Execute deep research with cross-validation across hundreds of primary sources:

- **Operating Point**: `chat_mode="team"`, `chat_tier="flash"`, `timeout=3600`
- **Recommended Output Tag**: `<GENERATE_FILE>/workspace/research/quantum_agent_report.pdf</GENERATE_FILE>`

### Golden Prompt Recipe
```python
prompt = """
Conduct comprehensive, citation-backed deep research on:
'State of Distributed Agent Execution Frameworks in 2026'

Reference notes and benchmark criteria:
<SHOW_FILE>/workspace/notes/runtime_benchmarks.md</SHOW_FILE>

Deliverables:
1. Executive Research Brief: <GENERATE_FILE>/workspace/research/agent_frameworks_2026.pdf</GENERATE_FILE>
2. Raw Citation & Findings Log: <GENERATE_FILE>/workspace/research/citations.json</GENERATE_FILE>

Synthesize findings with concrete architectural comparisons, memory footprints, and latency numbers.
"""
```
