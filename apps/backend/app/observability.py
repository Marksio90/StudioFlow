import contextvars
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None) or correlation_id_var.get(),
            "tenant_id": getattr(record, "tenant_id", None),
            "project_id": getattr(record, "project_id", None),
            "workflow_run_id": getattr(record, "workflow_run_id", None),
            "task_id": getattr(record, "task_id", None),
            "trace_id": getattr(record, "trace_id", None) or trace_id_var.get(),
            "logger": record.name,
        }
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_studioflow_structured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    root._studioflow_structured = True


@dataclass
class Span:
    name: str
    start_time: float
    trace_id: str


class TraceContext:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def __enter__(self):
        self._token = trace_id_var.set(self.trace_id)
        return Span(name="", start_time=time.monotonic(), trace_id=self.trace_id)

    def __exit__(self, exc_type, exc, tb):
        trace_id_var.reset(self._token)


class Metrics:
    def __init__(self):
        self._lock = Lock()
        self.counters: dict[str, float] = {
            "rework_rate": 0.0,
            "publish_failures": 0.0,
            "quota_usage": 0.0,
            "llm_cost_usd": 0.0,
        }
        self.hist: dict[str, list[float]] = {"cycle_time": [], "approval_latency": []}

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self.hist.setdefault(name, []).append(value)

    def inc(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self.counters[name] = self.counters.get(name, 0.0) + value


metrics = Metrics()
