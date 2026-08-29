"""Metrics collection for observability."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any


class MetricsCollector:
    """Collects and stores application metrics."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] += value

    def decrement(self, name: str, value: int = 1) -> None:
        """Decrement a counter."""
        self._counters[name] -= value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        """Observe a value in a histogram."""
        self._histograms[name].append(value)

    def record_time(self, name: str, duration: float) -> None:
        """Record a timing."""
        self._timers[name].append(duration)

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float | None:
        """Get gauge value."""
        return self._gauges.get(name)

    def get_histogram(self, name: str) -> dict[str, float]:
        """Get histogram statistics."""
        values = self._histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }

    def get_timer(self, name: str) -> dict[str, float]:
        """Get timer statistics."""
        values = self._timers.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {name: self.get_histogram(name) for name in self._histograms},
            "timers": {name: self.get_timer(name) for name in self._timers},
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()


class LLMCostTracker:
    """Track LLM API costs."""

    def __init__(self) -> None:
        self._costs: list[dict[str, Any]] = []
        self._total_cost: float = 0.0
        self._total_tokens: int = 0

    def record_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_input_token: float = 0.00003,
        cost_per_output_token: float = 0.00006,
    ) -> dict[str, Any]:
        """Record an LLM API call."""
        input_cost = input_tokens * cost_per_input_token
        output_cost = output_tokens * cost_per_output_token
        total_cost = input_cost + output_cost

        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

        self._costs.append(record)
        self._total_cost += total_cost
        self._total_tokens += input_tokens + output_tokens

        return record

    def get_total_cost(self) -> float:
        """Get total cost."""
        return self._total_cost

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self._total_tokens

    def get_cost_by_model(self) -> dict[str, float]:
        """Get cost breakdown by model."""
        costs: dict[str, float] = defaultdict(float)
        for record in self._costs:
            costs[record["model"]] += record["total_cost"]
        return dict(costs)

    def get_recent_calls(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent LLM calls."""
        return self._costs[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Get cost summary."""
        return {
            "total_cost": self._total_cost,
            "total_tokens": self._total_tokens,
            "total_calls": len(self._costs),
            "cost_by_model": self.get_cost_by_model(),
            "avg_cost_per_call": self._total_cost / len(self._costs) if self._costs else 0,
        }


class AnalysisLatencyTracker:
    """Track analysis latency."""

    def __init__(self) -> None:
        self._latencies: list[dict[str, Any]] = []

    def record_analysis(
        self,
        document_id: str,
        duration_seconds: float,
        stages: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Record analysis latency."""
        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "document_id": document_id,
            "duration_seconds": duration_seconds,
            "stages": stages or {},
        }

        self._latencies.append(record)
        return record

    def get_average_latency(self) -> float:
        """Get average analysis latency."""
        if not self._latencies:
            return 0.0
        return sum(r["duration_seconds"] for r in self._latencies) / len(self._latencies)

    def get_p95_latency(self) -> float:
        """Get 95th percentile latency."""
        if not self._latencies:
            return 0.0
        durations = sorted(r["duration_seconds"] for r in self._latencies)
        idx = int(len(durations) * 0.95)
        return durations[min(idx, len(durations) - 1)]

    def get_recent_analyses(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent analyses."""
        return self._latencies[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Get latency summary."""
        return {
            "total_analyses": len(self._latencies),
            "avg_latency": self.get_average_latency(),
            "p95_latency": self.get_p95_latency(),
            "recent_analyses": self.get_recent_analyses(5),
        }


class WorkerMonitor:
    """Monitor background workers."""

    def __init__(self) -> None:
        self._workers: dict[str, dict[str, Any]] = {}
        self._tasks: list[dict[str, Any]] = []

    def register_worker(self, worker_id: str, worker_type: str = "celery") -> None:
        """Register a worker."""
        self._workers[worker_id] = {
            "worker_id": worker_id,
            "worker_type": worker_type,
            "status": "active",
            "registered_at": datetime.now(tz=UTC).isoformat(),
            "tasks_completed": 0,
            "tasks_failed": 0,
        }

    def record_task(
        self,
        worker_id: str,
        task_name: str,
        status: str,
        duration: float | None = None,
    ) -> None:
        """Record a task execution."""
        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "worker_id": worker_id,
            "task_name": task_name,
            "status": status,
            "duration": duration,
        }

        self._tasks.append(record)

        if worker_id in self._workers:
            if status == "success":
                self._workers[worker_id]["tasks_completed"] += 1
            elif status == "failure":
                self._workers[worker_id]["tasks_failed"] += 1

    def get_worker_status(self, worker_id: str) -> dict[str, Any] | None:
        """Get worker status."""
        return self._workers.get(worker_id)

    def get_all_workers(self) -> dict[str, dict[str, Any]]:
        """Get all workers."""
        return self._workers.copy()

    def get_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent tasks."""
        return self._tasks[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Get worker summary."""
        total_completed = sum(w["tasks_completed"] for w in self._workers.values())
        total_failed = sum(w["tasks_failed"] for w in self._workers.values())
        return {
            "total_workers": len(self._workers),
            "active_workers": sum(1 for w in self._workers.values() if w["status"] == "active"),
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "success_rate": (
                total_completed / (total_completed + total_failed)
                if (total_completed + total_failed) > 0
                else 0
            ),
        }


class ErrorTracker:
    """Track application errors."""

    def __init__(self) -> None:
        self._errors: list[dict[str, Any]] = []
        self._error_counts: dict[str, int] = defaultdict(int)

    def record_error(
        self,
        error_type: str,
        message: str,
        context: dict[str, Any] | None = None,
        stack_trace: str | None = None,
    ) -> dict[str, Any]:
        """Record an error."""
        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "error_type": error_type,
            "message": message,
            "context": context or {},
            "stack_trace": stack_trace,
        }

        self._errors.append(record)
        self._error_counts[error_type] += 1

        return record

    def get_error_count(self, error_type: str | None = None) -> int:
        """Get error count."""
        if error_type:
            return self._error_counts.get(error_type, 0)
        return sum(self._error_counts.values())

    def get_errors_by_type(self) -> dict[str, int]:
        """Get errors by type."""
        return dict(self._error_counts)

    def get_recent_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent errors."""
        return self._errors[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Get error summary."""
        return {
            "total_errors": self.get_error_count(),
            "errors_by_type": self.get_errors_by_type(),
            "recent_errors": self.get_recent_errors(5),
        }


# Global instances
metrics = MetricsCollector()
llm_cost_tracker = LLMCostTracker()
analysis_latency_tracker = AnalysisLatencyTracker()
worker_monitor = WorkerMonitor()
error_tracker = ErrorTracker()
