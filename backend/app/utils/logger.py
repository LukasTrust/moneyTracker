"""Small, plug-and-play logger utility for the backend.

Usage:
    from app.utils import get_logger
    logger = get_logger(__name__)
    logger.info("hello world")

Design goals:
- No external setup required: importing this module auto-configures logging if no handlers are present.
- Default output is JSON (works great with Docker logs which capture stdout/stderr).
- Optional pretty, colored console output when `LOG_PRETTY=1` and stdout is a TTY.
- Configurable via environment variables: LOG_LEVEL, LOG_PRETTY.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import datetime
from typing import Any

__all__ = ["get_logger"]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Build a JSON-friendly dict
        created = datetime.datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        message = record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": created,
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }

        # Attach exception info if present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Include any extra keys (handy when logging extra={...})
        skip = set(logging.LogRecord('', 0, '', 0, '', (), None).__dict__.keys())
        extras = {k: v for k, v in record.__dict__.items() if k not in skip}
        if extras:
            # remove keys that are not JSON serializable if needed
            safe_extras = {}
            for k, v in extras.items():
                try:
                    json.dumps({k: v})
                    safe_extras[k] = v
                except Exception:
                    safe_extras[k] = repr(v)
            payload["extra"] = safe_extras

        return json.dumps(payload, ensure_ascii=False)


class PrettyFormatter(logging.Formatter):
    # Minimal color support for common levels
    COLORS = {
        "DEBUG": "\u001b[36m",  # cyan
        "INFO": "\u001b[32m",   # green
        "WARNING": "\u001b[33m",# yellow
        "ERROR": "\u001b[31m",  # red
        "CRITICAL": "\u001b[41m",# red background
    }
    RESET = "\u001b[0m"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        color = self.COLORS.get(level, "")
        msg = record.getMessage()
        base = f"{ts} {color}{level}{self.RESET} {record.name}: {msg}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    # If the application already configured logging (handlers present), do nothing
    if logging.root.handlers:
        _CONFIGURED = True
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        level = getattr(logging, level_name)
    except Exception:
        level = logging.INFO

    pretty_env = os.getenv("LOG_PRETTY", "0")
    pretty = pretty_env.lower() in ("1", "true", "yes")

    handler = logging.StreamHandler(sys.stdout)
    # Use pretty if requested and stdout is a terminal
    if pretty and sys.stdout.isatty():
        handler.setFormatter(PrettyFormatter())
    else:
        handler.setFormatter(JsonFormatter())

    logging.basicConfig(level=level, handlers=[handler])
    # capture warnings from the warnings module
    logging.captureWarnings(True)
    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger configured by this utility.

    Example:
        from app.utils import get_logger
        log = get_logger(__name__)
        log.info("hey")
    """
    _configure_root()
    logger = logging.getLogger(name)
    # Avoid duplicate handlers when libraries configure loggers directly
    logger.propagate = True
    return logger


# Auto-configure on import for convenience
_configure_root()
