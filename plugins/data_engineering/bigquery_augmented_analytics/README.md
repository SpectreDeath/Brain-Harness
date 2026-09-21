# BigQuery Augmented Analytics Plugin

The **BigQuery Augmented Analytics Plugin** (`plugin.bigquery_augmented_analytics`) executes AI, ML, and statistical inference directly inside Google BigQuery via Table-Valued Functions (TVFs). It implements the 5-Stage Literature Synthesis Loop to diagnose *why* business metrics change, isolate regime shifts, discover multi-dimensional Apriori key drivers, and estimate counterfactual causal lift with zero data egress.

---

## Architectural Features

1. **Zero Data Egress Tax**: Computation is pushed down entirely into Google BigQuery's distributed columnar storage engine; only small analytical summary rows return to memory.
2. **5-Stage TVF Synthesis Pipeline**:
   - `ML.TREND` & `ML.SEASONALITY`: Decomposes growth slopes and cyclical weekly/monthly calendar variations.
   - `ML.DETECT_CHANGE_POINTS`: Detects structural shifts with Bayesian probability $\ge 0.95$.
   - `AI.KEY_DRIVERS`: Apriori association rule mining to explain cohort delta across combinations of dimensions with support pruning ($\ge 0.01$).
   - `AI.CAUSAL_EFFECT`: ARIMA_PLUS counterfactual control baseline to isolate true incremental program impact.
   - `Executive Synthesis`: 4-Point diagnostic brief (When, What, Who, Impact).
3. **Micro-Kernel IoC Resolution**: Registered via `BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY` (`service.bigquery_augmented_analytics`) for direct in-memory resolution by autonomous agents and swarms (`context.require(BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY)`).
4. **Interactive HTML Visual Brief**: Generates self-contained dark-theme briefs with Mermaid DAGs and live diagnostic scorecards.

---

## Tool Entrypoints

| Tool Name | Purpose | Key Parameters |
|---|---|---|
| `bigquery_temporal_profile` | Strip noise & cyclical patterns | `table`, `data_col`, `timestamp_col`, `seasonalities` |
| `bigquery_detect_change_points` | Isolate structural step shifts $t_0$ | `table`, `data_col`, `timestamp_col`, `min_probability` |
| `bigquery_attribute_drivers` | Apriori dimension segment attribution | `table`, `metric_col`, `dimension_cols`, `interest_condition` |
| `bigquery_causal_lift` | ARIMA_PLUS counterfactual causal lift | `table`, `data_col`, `timestamp_col`, `intervention_timestamp` |
| `bigquery_augmented_pipeline` | Complete 5-stage investigation | `table`, `metric_col`, `timestamp_col`, `dimension_cols` |
| `bigquery_visual_brief` | Interactive HTML visual brief | `table`, `metric_col`, `timestamp_col`, `output_path` |

---

## Programmatic IoC Resolution

```python
from harness.kernel.context import ServiceContext
from harness.services.bigquery_augmented_analytics import (
    BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY,
    BigQueryAugmentedAnalyticsService,
)

async def investigate(context: ServiceContext) -> None:
    bq_service: BigQueryAugmentedAnalyticsService = context.require(
        BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY
    )
    result = bq_service.run_investigation(
        target_table="austin_bikeshare.trips",
        metric_col="trip_id",
        timestamp_col="start_time",
        dimension_cols=["subscriber_type", "bike_type"],
    )
    print("Executive Diagnosis:", result.narrative.impact)
```

---

## Command Line Usage

```bash
# Compile and dry-run Stage 1 Temporal Profiling
harness bq profile --table austin_bikeshare.trips --data-col trip_id --timestamp-col start_time --dry-run

# Run full investigative pipeline and output visual brief
harness bq pipeline --table austin_bikeshare.trips --metric-col trip_id --timestamp-col start_time --dims subscriber_type,bike_type --dry-run --brief report.html
```
