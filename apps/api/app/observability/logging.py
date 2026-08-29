"""Structured logging configuration."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id  # type: ignore[attr-defined]

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id  # type: ignore[attr-defined]

        if hasattr(record, "organization_id"):
            log_entry["organization_id"] = record.organization_id  # type: ignore[attr-defined]

        if record.exc_info:
            log_entry["exception"] = {
                "type": str(record.exc_info[0]),
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data  # type: ignore[attr-defined]

        return json.dumps(log_entry, default=str)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records."""

    def __init__(self) -> None:
        super().__init__()
        self._request_id: str | None = None
        self._user_id: str | None = None
        self._organization_id: str | None = None

    def set_request_id(self, request_id: str) -> None:
        self._request_id = request_id

    def set_user_id(self, user_id: str) -> None:
        self._user_id = user_id

    def set_organization_id(self, organization_id: str) -> None:
        self._organization_id = organization_id

    def clear(self) -> None:
        self._request_id = None
        self._user_id = None
        self._organization_id = None

    def filter(self, record: logging.LogRecord) -> bool:
        if self._request_id:
            record.request_id = self._request_id
        if self._user_id:
            record.user_id = self._user_id
        if self._organization_id:
            record.organization_id = self._organization_id
        return True


def setup_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Setup structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if json_output:
        formatter: logging.Formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    request_filter = RequestContextFilter()
    console_handler.addFilter(request_filter)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
