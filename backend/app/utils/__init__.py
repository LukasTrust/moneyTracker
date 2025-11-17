"""Utilities package for the backend.

Expose `get_logger` for easy import:

    from app.utils import get_logger

"""
from .logger import get_logger

__all__ = ["get_logger"]
