"""Tests for Google Perfetto Trace Processor Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.software_engineering.perfetto_trace_processor.main import (
    PERFETTO_TRACE_PROCESSOR_SERVICE_KEY,
    PerfettoTraceProcessorPlugin,
)

@pytest.mark.asyncio
async def test_perfetto_trace_processor_tools():
    ctx = ServiceContext()
    p = PerfettoTraceProcessorPlugin()
    await p.enable(ctx)

    service = ctx.require(PERFETTO_TRACE_PROCESSOR_SERVICE_KEY)
    assert service is not None

    # Test load_trace
    load_res = service.load_trace("synthetic_test.perfetto-trace")
    assert load_res["status"] == "success"
    tid = load_res["trace_id"]

    # Test query_sql
    query_res = service.query_sql(tid, "SELECT name, dur FROM slice WHERE dur > 600000")
    assert query_res["status"] == "success"
    assert query_res["row_count"] >= 2
    assert "name" in query_res["columns"]

    # Test compute_metrics
    metrics = service.compute_metrics(tid)
    assert metrics["status"] == "success"
    assert metrics["metrics"]["execution_slices"]["slice_count"] == 2

    # Test export_flamegraph
    flame = service.export_flamegraph(tid)
    assert flame["status"] == "success"
    assert flame["flamegraph"]["name"] == "root"

    await p.disable(ctx)
