"""Contract verification tests for Prometheus Metric Exporter (Phase 4 Vector 5)."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.prometheus import (
    PROMETHEUS_EXPORTER_SERVICE_KEY,
    DefaultPrometheusExporterService,
    MetricDefinition,
    MetricSample,
    PrometheusExporterService,
    resolve_prometheus_exporter,
)
from harness.ui.server.app import create_app
from plugins.infra_and_cloud.prometheus_exporter.main import (
    PrometheusExporterPlugin,
    plugin,
)


@pytest.mark.unit
class TestPrometheusDataStructures:
    """Verifies slotted frozen dataclass immutability and post-init assertions (Rule 12, Rule 43)."""

    def test_metric_definition_immutability(self) -> None:
        defn = MetricDefinition(name="step_latency_seconds", help_text="Latency per step", metric_type="histogram")
        assert defn.name == "step_latency_seconds"
        assert defn.metric_type == "histogram"

        # Rule 43: direct assignment must raise AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            defn.name = "mutated_metric"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            defn.metric_type = "counter"  # type: ignore[misc]

    def test_metric_definition_post_init_validation(self) -> None:
        with pytest.raises(ValueError, match="Invalid metric name"):
            MetricDefinition(name="invalid-name-with-dashes", help_text="bad name")

        with pytest.raises(ValueError, match="metric_type must be one of"):
            MetricDefinition(name="valid_name", help_text="bad type", metric_type="invalid_type")

    def test_metric_sample_immutability(self) -> None:
        sample = MetricSample(name="token_count", labels=(("model", "claude"),), value=42.0)
        assert sample.value == 42.0

        with pytest.raises((AttributeError, TypeError)):
            sample.value = 100.0  # type: ignore[misc]


@pytest.mark.unit
class TestPrometheusExporterService:
    """Verifies metric recording, text format exposition, and thread safety."""

    def test_counter_monotonicity(self) -> None:
        svc = DefaultPrometheusExporterService()
        svc.register_metric(MetricDefinition(name="invocations_total", help_text="Total invocations", metric_type="counter"))
        svc.increment("invocations_total", labels={"tool": "search"}, value=2.0)
        svc.increment("invocations_total", labels={"tool": "search"}, value=3.0)

        export = svc.generate_text_export()
        assert '# HELP invocations_total Total invocations' in export
        assert '# TYPE invocations_total counter' in export
        assert 'invocations_total{tool="search"} 5.0' in export

        with pytest.raises(ValueError, match="Counter increments must be non-negative"):
            svc.increment("invocations_total", value=-1.0)

    def test_gauge_values(self) -> None:
        svc = DefaultPrometheusExporterService()
        svc.register_metric(MetricDefinition(name="active_sessions", help_text="Active sessions count", metric_type="gauge"))
        svc.set_gauge("active_sessions", value=10.0)
        assert 'active_sessions 10.0' in svc.generate_text_export()

        svc.set_gauge("active_sessions", value=3.0)
        assert 'active_sessions 3.0' in svc.generate_text_export()

    def test_histogram_quantiles_and_sums(self) -> None:
        svc = DefaultPrometheusExporterService()
        defn = MetricDefinition(
            name="task_duration_seconds",
            help_text="Task duration",
            metric_type="histogram",
            buckets=(0.1, 0.5, 1.0, 5.0),
        )
        svc.register_metric(defn)
        svc.observe("task_duration_seconds", value=0.05)
        svc.observe("task_duration_seconds", value=0.4)
        svc.observe("task_duration_seconds", value=2.0)

        export = svc.generate_text_export()
        assert 'task_duration_seconds_bucket{le="0.1"} 1' in export
        assert 'task_duration_seconds_bucket{le="0.5"} 2' in export
        assert 'task_duration_seconds_bucket{le="1.0"} 2' in export
        assert 'task_duration_seconds_bucket{le="5.0"} 3' in export
        assert 'task_duration_seconds_bucket{le="+Inf"} 3' in export
        assert 'task_duration_seconds_count 3' in export
        assert 'task_duration_seconds_sum 2.45' in export

    def test_thread_safety_convergence(self) -> None:
        svc = DefaultPrometheusExporterService()
        svc.register_metric(MetricDefinition(name="concurrent_counter", help_text="Thread test", metric_type="counter"))

        def worker() -> None:
            for _ in range(100):
                svc.increment("concurrent_counter", value=1.0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            concurrent.futures.wait(futures)

        export = svc.generate_text_export()
        assert 'concurrent_counter 1000.0' in export

    def test_single_seam_resolver(self) -> None:
        ctx = ServiceContext()
        custom = DefaultPrometheusExporterService()
        ctx.provide(PROMETHEUS_EXPORTER_SERVICE_KEY, custom)

        resolved = resolve_prometheus_exporter(ctx)
        assert resolved is custom


@pytest.mark.asyncio
class TestPrometheusIntegrationAndRoutes:
    """Verifies FastAPI /metrics exposition route and PluginValidator compliance."""

    async def test_metrics_http_route(self) -> None:
        ctx = ServiceContext()
        svc = DefaultPrometheusExporterService()
        svc.register_metric(MetricDefinition(name="http_requests_total", help_text="Total requests", metric_type="counter"))
        svc.increment("http_requests_total", labels={"method": "GET", "status": "200"}, value=12.0)
        ctx.provide(PROMETHEUS_EXPORTER_SERVICE_KEY, svc)

        from harness.kernel.lifecycle import PluginLifecycle

        lifecycle = PluginLifecycle(ctx)
        app = create_app(ctx, lifecycle=lifecycle)
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert 'http_requests_total{method="GET",status="200"} 12.0' in response.text

    async def test_plugin_on_load(self) -> None:
        ctx = ServiceContext()
        p = PrometheusExporterPlugin()
        assert PROMETHEUS_EXPORTER_SERVICE_KEY in p.provides

        await p.on_load(ctx)
        assert ctx.has(PROMETHEUS_EXPORTER_SERVICE_KEY)
        svc = ctx.require(PROMETHEUS_EXPORTER_SERVICE_KEY)
        assert isinstance(svc, PrometheusExporterService)

        # Module-level singleton export (Rule 45)
        assert plugin is not None
        assert plugin.name == "domain.prometheus_exporter"

    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/infra_and_cloud/prometheus_exporter")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
