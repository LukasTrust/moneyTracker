import importlib
import json
import logging
import os
import sys

import pytest


def _reload_logger_module(tmp_env: dict[str, str] | None = None, isatty: bool = False):
    """Reload the logger module with controlled environment and stdout.isatty."""
    # Prepare environment
    old_env = os.environ.copy()
    if tmp_env is not None:
        os.environ.update(tmp_env)

    # Patch isatty
    old_isatty = sys.stdout.isatty

    try:
        sys.stdout.isatty = lambda: isatty
        # Remove handlers so configuration will run fresh
        logging.root.handlers = []
        # Import/reload
        import app.utils.logger as logger_mod
        importlib.reload(logger_mod)
        return logger_mod
    finally:
        # restore environment and isatty for caller control (tests may want fresh state)
        os.environ.clear()
        os.environ.update(old_env)
        sys.stdout.isatty = old_isatty


def test_json_formatter_serializes_extras_and_exception():
    from app.utils.logger import JsonFormatter

    fmt = JsonFormatter()

    # Create a LogRecord with non-serializable extra and an exception
    record = logging.LogRecord("test", logging.ERROR, __file__, 10, "oh %s", ("no",), None)
    # add non-serializable extra
    record.__dict__["custom_callable"] = lambda x: x

    # add exception info
    try:
        1 / 0
    except ZeroDivisionError:
        record.exc_info = sys.exc_info()

    out = fmt.format(record)
    # Should be valid JSON
    data = json.loads(out)

    assert data["level"] == "ERROR"
    assert "exc_info" in data
    assert "extra" in data
    # The non-serializable callable should have been converted to a string representation
    assert "custom_callable" in data["extra"]
    assert isinstance(data["extra"]["custom_callable"], str)


def test_pretty_formatter_includes_color_and_exception():
    from app.utils.logger import PrettyFormatter

    fmt = PrettyFormatter()
    record = logging.LogRecord("mod", logging.CRITICAL, __file__, 5, "boom", (), None)

    try:
        raise RuntimeError("boom!")
    except RuntimeError:
        record.exc_info = sys.exc_info()

    out = fmt.format(record)
    # Should include colored level and the exception text
    assert "CRITICAL" in out
    assert "RuntimeError" in out


def test_configure_root_uses_pretty_when_isatty(monkeypatch):
    # Simulate LOG_PRETTY and a TTY stdout
    monkeypatch.setenv("LOG_PRETTY", "1")
    # Ensure fresh handlers and reload module to pick up env
    logging.root.handlers = []
    # monkeypatch isatty on stdout to True
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    import app.utils.logger as logger_mod
    importlib.reload(logger_mod)

    # After reload, logging.root should have a handler with PrettyFormatter
    assert logging.root.handlers, "root should have handlers configured"
    fmt = logging.root.handlers[0].formatter
    from app.utils.logger import PrettyFormatter

    assert isinstance(fmt, PrettyFormatter)


def test_get_logger_returns_logger_and_propagate_true():
    from app.utils.logger import get_logger

    logger = get_logger("my.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "my.test"
    # propagate should be enabled by the utility
    assert logger.propagate is True


def test_json_formatter_without_extras_or_exception():
    from app.utils.logger import JsonFormatter

    fmt = JsonFormatter()
    record = logging.LogRecord("plain", logging.INFO, __file__, 1, "hello", (), None)
    out = fmt.format(record)
    data = json.loads(out)

    assert data["level"] == "INFO"
    assert "extra" not in data
    assert "exc_info" not in data


def test_json_formatter_with_serializable_extra():
    from app.utils.logger import JsonFormatter

    fmt = JsonFormatter()
    record = logging.LogRecord("plain", logging.INFO, __file__, 1, "hello", (), None)
    # add a serializable extra
    record.__dict__["n"] = 123
    out = fmt.format(record)
    data = json.loads(out)

    assert "extra" in data
    assert data["extra"]["n"] == 123


def test_configure_root_respects_existing_handlers(monkeypatch):
    # Put one handler on the root and reload the module. It should not replace handlers.
    existing = logging.StreamHandler()
    logging.root.handlers = [existing]

    # Set env so configure runs but should early-return due to handlers present
    monkeypatch.setenv("LOG_PRETTY", "0")

    import app.utils.logger as logger_mod
    importlib.reload(logger_mod)

    # root handlers should still be the same list (not replaced)
    assert len(logging.root.handlers) == 1
    assert logging.root.handlers[0] is existing


def test_invalid_log_level_defaults_to_info(monkeypatch):
    # Set an invalid LOG_LEVEL and ensure fallback to INFO
    monkeypatch.setenv("LOG_LEVEL", "NOT_A_LEVEL")
    logging.root.handlers = []
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    import app.utils.logger as logger_mod
    importlib.reload(logger_mod)

    # root level should be INFO
    assert logging.getLogger().level == logging.INFO
