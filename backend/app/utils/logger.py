"""Small, plug-and-play logger utility for the backend.
Audit reference: 08_backend_utils.md - Make logging initialization explicit

Usage:
    from app.utils.logger import init_logging, get_logger
    
    # In main.py or app startup:
    init_logging()  # Call explicitly during startup
    
    # In other modules:
    logger = get_logger(__name__)
    logger.info("hello world")

Design goals:
- Explicit initialization via init_logging() - no auto-configure on import
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

__all__ = ["get_logger", "init_logging"]


# Pre-compute skip keys once to avoid creating dummy LogRecord repeatedly
_SKIP_KEYS = set(logging.LogRecord('', 0, '', 0, '', (), None).__dict__.keys())


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
        extras = {k: v for k, v in record.__dict__.items() if k not in _SKIP_KEYS}
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


def init_logging(level: str | None = None, pretty: bool | None = None, force: bool = False) -> None:
    """
    Initialize logging configuration explicitly.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               If None, reads from LOG_LEVEL env var (default: INFO)
        pretty: Use pretty colored output. If None, reads from LOG_PRETTY env var
        force: Force reconfiguration even if already configured
    
    Example:
        # In main.py startup:
        init_logging(level='DEBUG', pretty=True)
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    # If the application already configured logging (handlers present), do nothing unless forced
    if logging.root.handlers and not force:
        _CONFIGURED = True
        return

    # Determine log level
    if level is not None:
        level_name = level.upper()
    else:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        
    try:
        log_level = getattr(logging, level_name)
    except Exception:
        log_level = logging.INFO

    # Determine formatter
    if pretty is not None:
        use_pretty = pretty
    else:
        pretty_env = os.getenv("LOG_PRETTY", "0")
        use_pretty = pretty_env.lower() in ("1", "true", "yes")

    handler = logging.StreamHandler(sys.stdout)
    # Use pretty if requested and stdout is a terminal
    if use_pretty and sys.stdout.isatty():
        handler.setFormatter(PrettyFormatter())
    else:
        handler.setFormatter(JsonFormatter())

    # Clear existing handlers if forcing reconfiguration
    if force:
        logging.root.handlers = []
        
    logging.basicConfig(level=log_level, handlers=[handler], force=force)
    # capture warnings from the warnings module
    logging.captureWarnings(True)
    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger configured by this utility.
    
    Note: Call init_logging() during application startup before using loggers.

    Example:
        from app.utils.logger import get_logger
        log = get_logger(__name__)
        log.info("hey")
    """
    # Ensure logging is configured (defensive - app should call init_logging explicitly)
    if not _CONFIGURED:
        init_logging()
        
    logger = logging.getLogger(name)
    # Avoid duplicate handlers when libraries configure loggers directly
    # Set propagate to True so the logger integrates with other configured
    # logging handlers in the application environment.
    logger.propagate = True
    return logger
