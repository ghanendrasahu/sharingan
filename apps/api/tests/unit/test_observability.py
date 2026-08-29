"""Unit tests for observability module."""

from app.observability.logging import (
    RequestContextFilter,
    StructuredFormatter,
)
from app.observability.metrics import (
    AnalysisLatencyTracker,
    ErrorTracker,
    LLMCostTracker,
    MetricsCollector,
    WorkerMonitor,
)


def test_structured_formatter():
    """Test structured formatter creation."""
    formatter = StructuredFormatter()
    assert formatter is not None


def test_request_context_filter():
    """Test request context filter."""
    filter_obj = RequestContextFilter()
    assert filter_obj._request_id is None
    assert filter_obj._user_id is None


def test_request_context_filter_set():
    """Test setting request context."""
    filter_obj = RequestContextFilter()
    filter_obj.set_request_id("req_123")
    filter_obj.set_user_id("user_456")
    filter_obj.set_organization_id("org_789")

    assert filter_obj._request_id == "req_123"
    assert filter_obj._user_id == "user_456"
    assert filter_obj._organization_id == "org_789"


def test_request_context_filter_clear():
    """Test clearing request context."""
    filter_obj = RequestContextFilter()
    filter_obj.set_request_id("req_123")
    filter_obj.clear()

    assert filter_obj._request_id is None
    assert filter_obj._user_id is None


def test_metrics_collector():
    """Test metrics collector."""
    collector = MetricsCollector()
    collector.increment("test_counter")
    collector.increment("test_counter")

    assert collector.get_counter("test_counter") == 2


def test_metrics_gauge():
    """Test gauge metrics."""
    collector = MetricsCollector()
    collector.set_gauge("test_gauge", 42.5)

    assert collector.get_gauge("test_gauge") == 42.5


def test_metrics_histogram():
    """Test histogram metrics."""
    collector = MetricsCollector()
    collector.observe("test_histogram", 10.0)
    collector.observe("test_histogram", 20.0)
    collector.observe("test_histogram", 30.0)

    stats = collector.get_histogram("test_histogram")
    assert stats["count"] == 3
    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert stats["avg"] == 20.0


def test_metrics_timer():
    """Test timer metrics."""
    collector = MetricsCollector()
    collector.record_time("test_timer", 0.5)
    collector.record_time("test_timer", 1.0)

    stats = collector.get_timer("test_timer")
    assert stats["count"] == 2
    assert stats["avg"] == 0.75


def test_metrics_reset():
    """Test resetting metrics."""
    collector = MetricsCollector()
    collector.increment("test_counter")
    collector.set_gauge("test_gauge", 42.0)
    collector.reset()

    assert collector.get_counter("test_counter") == 0
    assert collector.get_gauge("test_gauge") is None


def test_llm_cost_tracker():
    """Test LLM cost tracker."""
    tracker = LLMCostTracker()
    record = tracker.record_call(
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
    )

    assert record["model"] == "gpt-4"
    assert record["input_tokens"] == 1000
    assert record["output_tokens"] == 500
    assert tracker.get_total_tokens() == 1500


def test_llm_cost_tracker_summary():
    """Test LLM cost tracker summary."""
    tracker = LLMCostTracker()
    tracker.record_call("gpt-4", 1000, 500)
    tracker.record_call("gpt-3.5-turbo", 2000, 1000)

    summary = tracker.get_summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 4500


def test_analysis_latency_tracker():
    """Test analysis latency tracker."""
    tracker = AnalysisLatencyTracker()
    record = tracker.record_analysis(
        document_id="doc_123",
        duration_seconds=5.5,
        stages={"extraction": 2.0, "analysis": 3.5},
    )

    assert record["document_id"] == "doc_123"
    assert record["duration_seconds"] == 5.5


def test_analysis_latency_summary():
    """Test analysis latency summary."""
    tracker = AnalysisLatencyTracker()
    tracker.record_analysis("doc_1", 5.0)
    tracker.record_analysis("doc_2", 10.0)

    summary = tracker.get_summary()
    assert summary["total_analyses"] == 2
    assert summary["avg_latency"] == 7.5


def test_worker_monitor():
    """Test worker monitor."""
    monitor = WorkerMonitor()
    monitor.register_worker("worker_1", "celery")

    status = monitor.get_worker_status("worker_1")
    assert status is not None
    assert status["worker_type"] == "celery"


def test_worker_monitor_task():
    """Test worker task recording."""
    monitor = WorkerMonitor()
    monitor.register_worker("worker_1")
    monitor.record_task("worker_1", "process_document", "success", 2.5)

    summary = monitor.get_summary()
    assert summary["total_tasks_completed"] == 1


def test_error_tracker():
    """Test error tracker."""
    tracker = ErrorTracker()
    record = tracker.record_error(
        error_type="ValidationError",
        message="Invalid input",
        context={"field": "email"},
    )

    assert record["error_type"] == "ValidationError"
    assert record["message"] == "Invalid input"


def test_error_tracker_count():
    """Test error tracker count."""
    tracker = ErrorTracker()
    tracker.record_error("ValidationError", "Invalid input")
    tracker.record_error("ValidationError", "Missing field")
    tracker.record_error("DatabaseError", "Connection failed")

    assert tracker.get_error_count("ValidationError") == 2
    assert tracker.get_error_count("DatabaseError") == 1
    assert tracker.get_error_count() == 3


def test_error_tracker_summary():
    """Test error tracker summary."""
    tracker = ErrorTracker()
    tracker.record_error("ValidationError", "Invalid input")
    tracker.record_error("DatabaseError", "Connection failed")

    summary = tracker.get_summary()
    assert summary["total_errors"] == 2
    assert summary["errors_by_type"]["ValidationError"] == 1
