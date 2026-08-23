# Data Engineering Context

The Data Engineering context governs curated tabular dataset acquisition, out-of-core statistical moment profiling, schema transformation, and relational database execution.

## Language

**Topology Profile**:
A compact, out-of-core statistical fingerprint capturing moments, null ratios, and outlier contamination without loading raw rows into context.
_Avoid_: Data summary, table stats, EDA dump

**Curated Pipeline**:
A direct ingestion path targeting standardized tabular repositories (UCI, Kaggle, OpenData) that eliminates unstructured scraping.
_Avoid_: Data scraper, downloader, fetcher

**Transformer**:
A deterministic schema reshaping and column normalization pipeline converting raw inputs into memory-efficient columnar formats.
_Avoid_: Cleaner, converter, sanitizer

**Synthetic Matrix**:
An artificially generated tabular dataset preserving target statistical distributions and correlation structures for benchmarking.
_Avoid_: Fake data, mock table, dummy data

**Time-to-Event Model**:
A semiparametric or nonparametric statistical model (Cox PH, Kaplan-Meier) analyzing duration until a binary event under right-censoring.
_Avoid_: Survival calculator, churn predictor, failure timer

**Data Topology Map**:
A formal graph representation of data structures, causal DAG lineages, and execution queues across system boundaries.
_Avoid_: Data flow diagram, schema map, entity relationship chart

