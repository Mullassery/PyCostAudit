"""
OpenTelemetry integration for PyCostAudit.
Tracks cost operations, API calls, and performance metrics.
"""

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter as JaegerMetricsExporter
from prometheus_client import Counter, Histogram, Gauge
import time
from typing import Optional
import os


class OpenTelemetrySetup:
    """Initialize OpenTelemetry for PyCostAudit"""

    def __init__(self, service_name: str = "pycostaudit", jaeger_host: str = "localhost"):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.tracer = None
        self.meter = None

    def setup(self):
        """Initialize OpenTelemetry"""
        # Jaeger exporter for tracing
        jaeger_exporter = JaegerExporter(
            agent_host_name=self.jaeger_host,
            agent_port=6831,
        )

        # Create trace provider
        trace_provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: self.service_name})
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        trace.set_tracer_provider(trace_provider)

        self.tracer = trace.get_tracer(__name__)

        # Prometheus metrics
        prometheus_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(metric_readers=[prometheus_reader])
        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(__name__)

        # Auto-instrumentation
        FastAPIInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()
        RequestsInstrumentor.instrument()
        HTTPXClientInstrumentor.instrument()

        print(f"✅ OpenTelemetry initialized for {self.service_name}")
        print(f"   Jaeger: http://{self.jaeger_host}:16686")
        print(f"   Prometheus: http://localhost:8000/metrics")

    def create_cost_tracking_span(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ):
        """Create span for cost tracking"""
        with self.tracer.start_as_current_span("track_cost") as span:
            span.set_attribute("provider", provider)
            span.set_attribute("model", model)
            span.set_attribute("input_tokens", input_tokens)
            span.set_attribute("output_tokens", output_tokens)
            span.set_attribute("total_cost", cost)
            return span

    def record_cost_metric(
        self,
        provider: str,
        cost: float,
        tokens: int,
    ):
        """Record cost metrics"""
        # Counter: total costs by provider
        cost_counter = self.meter.create_counter(
            "cost_total",
            unit="USD",
            description="Total costs by provider",
        )
        cost_counter.add(cost, {"provider": provider})

        # Histogram: token distribution
        token_histogram = self.meter.create_histogram(
            "tokens_per_request",
            unit="1",
            description="Tokens per request",
        )
        token_histogram.record(tokens, {"provider": provider})


class CostMetrics:
    """Prometheus metrics for cost tracking"""

    # Counters
    cost_total = Counter(
        "pycostaudit_cost_total",
        "Total costs by provider and model",
        ["provider", "model"],
    )

    operations_total = Counter(
        "pycostaudit_operations_total",
        "Total operations tracked",
        ["provider"],
    )

    # Histograms
    cost_per_request = Histogram(
        "pycostaudit_cost_per_request",
        "Cost per request in USD",
        ["provider"],
        buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    )

    tokens_per_request = Histogram(
        "pycostaudit_tokens_per_request",
        "Tokens per request",
        ["provider"],
        buckets=(100, 500, 1000, 5000, 10000, 50000),
    )

    # Gauges
    budget_usage = Gauge(
        "pycostaudit_budget_usage_percent",
        "Budget usage percentage",
        ["user_id"],
    )

    daily_cost = Gauge(
        "pycostaudit_daily_cost_usd",
        "Daily cost in USD",
        ["user_id", "provider"],
    )

    @staticmethod
    def record_cost(provider: str, model: str, cost: float, tokens: int):
        """Record a cost operation"""
        CostMetrics.cost_total.labels(provider=provider, model=model).inc(cost)
        CostMetrics.operations_total.labels(provider=provider).inc()
        CostMetrics.cost_per_request.labels(provider=provider).observe(cost)
        CostMetrics.tokens_per_request.labels(provider=provider).observe(tokens)

    @staticmethod
    def update_budget_usage(user_id: str, percent: float):
        """Update budget usage gauge"""
        CostMetrics.budget_usage.labels(user_id=user_id).set(percent)

    @staticmethod
    def update_daily_cost(user_id: str, provider: str, cost: float):
        """Update daily cost gauge"""
        CostMetrics.daily_cost.labels(user_id=user_id, provider=provider).set(cost)


def get_or_create_otel() -> Optional[OpenTelemetrySetup]:
    """Get or create OpenTelemetry setup"""
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_enabled = os.getenv("JAEGER_ENABLED", "true").lower() == "true"

    if not jaeger_enabled:
        return None

    otel = OpenTelemetrySetup(jaeger_host=jaeger_host)
    try:
        otel.setup()
        return otel
    except Exception as e:
        print(f"⚠️  OpenTelemetry setup failed: {e}")
        print("   Continuing without telemetry...")
        return None


def trace_cost_operation(otel: Optional[OpenTelemetrySetup]):
    """Decorator to trace cost operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if otel:
                with otel.tracer.start_as_current_span(func.__name__) as span:
                    span.set_attribute("function", func.__name__)
                    result = func(*args, **kwargs)
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, (int, float, str)):
                                span.set_attribute(key, value)
                    return result
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator
