"""
Pagination utilities for SQLAlchemy queries.
Audit reference: 08_backend_utils.md - Remove .all() fallback and improve count logic
"""
from typing import Tuple, Any
from sqlalchemy import func, select
from sqlalchemy.orm import Query
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def clamp_limit(limit: int) -> int:
    """Clamp requested limit to server-enforced max.

    Returns the effective limit.
    """
    try:
        l = int(limit)
    except Exception:
        l = settings.DEFAULT_LIMIT
    if l <= 0:
        return settings.DEFAULT_LIMIT
    return min(l, settings.MAX_LIMIT)


def safe_count(query: Query) -> int:
    """
    Safely count query results without loading all rows.
    
    Args:
        query: SQLAlchemy Query object
        
    Returns:
        Total count of results
        
    Raises:
        RuntimeError: If count cannot be determined safely
    """
    try:
        # Try standard count (works for simple queries)
        return query.order_by(None).count()
    except Exception as e:
        logger.warning("Standard count() failed: %s. Query may be complex.", e)
        # For complex queries, we cannot safely count without a subquery
        # Refuse to fall back to .all() which loads entire result set
        raise RuntimeError(
            "Cannot count query results safely. "
            "Query may be too complex or use unsupported features. "
            "Consider simplifying the query or using a subquery for counting."
        ) from e


def paginate_query(query, limit: int, offset: int) -> Tuple[list[Any], int, int, int, int]:
    """Apply limit/offset to a SQLAlchemy query and return (items, total, limit, offset, pages).
    
    Args:
        query: SQLAlchemy Query object
        limit: Requested page size
        offset: Requested offset
        
    Returns:
        Tuple of (items, total, eff_limit, eff_offset, pages)
        
    Raises:
        RuntimeError: If safe counting fails
        
    Note: pages is total // limit + (1 if remainder else 0)
    """
    eff_limit = clamp_limit(limit)
    # Normalize offset (ensure non-negative integer)
    eff_offset = max(0, int(offset) if offset is not None else 0)
    
    # Get total count safely (no .all() fallback - Audit recommendation)
    total = safe_count(query)
    
    # Fetch page
    items = query.offset(eff_offset).limit(eff_limit).all()
    
    # Calculate page number
    pages = (total // eff_limit) + (1 if total % eff_limit else 0) if eff_limit > 0 else 1
    
    return items, total, eff_limit, eff_offset, pages
