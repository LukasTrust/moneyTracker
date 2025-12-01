"""Utilities package for the backend.

Expose `get_logger` and `init_logging` for easy import:

    from app.utils import get_logger, init_logging

"""
from .logger import get_logger, init_logging

__all__ = ["get_logger", "init_logging"]
