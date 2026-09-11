# Tutorial: End-to-End Execution with Google ADK, Styleguide & Perfetto Plugins

This hands-on tutorial guides you through your first complete cycle with the Brain Harness Google Integration Suite:
1. Executing an autonomous Agent Development Kit (ADK) multi-turn workflow.
2. Auditing Python code against Google Style Guide rules.
3. Ingesting and querying system execution traces using the Perfetto Trace Processor.

---

## Prerequisites

Ensure you have Brain Harness running with Python >= 3.10 and the following plugins enabled:
- `plugin.google_adk_runtime`
- `plugin.google_styleguide_auditor`
- `plugin.perfetto_trace_processor`

---

## Step 1: Execute an ADK Agent Workflow

Run an ADK agent through the Harness `ServiceContext`:

```python
import asyncio
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.google_adk_runtime.main import (
    GOOGLE_ADK_RUNTIME_SERVICE_KEY,
    GoogleAdkRuntimePlugin,
)

async def main():
    ctx = ServiceContext()
    adk_plugin = GoogleAdkRuntimePlugin()
    await adk_plugin.enable(ctx)

    service = ctx.require(GOOGLE_ADK_RUNTIME_SERVICE_KEY)
    response = service.run_agent(
        agent_name="research_analyst",
        prompt="Analyze system performance bottlenecks in trace data.",
        session_id="session_tutorial_01",
    )
    print("Agent Output:", response["output"])

asyncio.run(main())
```

---

## Step 2: Audit Source Code Against Google Style Guide

Verify your script meets Google's style conventions before committing:

```python
from plugins.software_engineering.google_styleguide_auditor.main import (
    GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY,
    GoogleStyleguideAuditorPlugin,
)

async def run_audit():
    ctx = ServiceContext()
    auditor = GoogleStyleguideAuditorPlugin()
    await auditor.enable(ctx)

    service = ctx.require(GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY)
    report = service.audit_file("main.py", language="python")

    print(f"Compliant: {report['compliant']}")
    for violation in report["violations"]:
        print(f"Line {violation['line']}: {violation['message']}")
```

---

## Step 3: Ingest and Analyze Execution Traces in Perfetto

Profile your execution performance using SQL queries on trace data:

```python
from plugins.software_engineering.perfetto_trace_processor.main import (
    PERFETTO_TRACE_PROCESSOR_SERVICE_KEY,
    PerfettoTraceProcessorPlugin,
)

async def trace_analysis():
    ctx = ServiceContext()
    perfetto = PerfettoTraceProcessorPlugin()
    await perfetto.enable(ctx)

    service = ctx.require(PERFETTO_TRACE_PROCESSOR_SERVICE_KEY)
    trace = service.load_trace("execution.perfetto-trace")
    tid = trace["trace_id"]

    query = "SELECT name, dur FROM slice WHERE dur > 500000"
    results = service.query_sql(tid, query)
    print("Long slices:", results["rows"])

    metrics = service.compute_metrics(tid)
    print("Metrics summary:", metrics["metrics"])
```

Congratulations! You have completed a full cycle with the Google Integration Suite.
