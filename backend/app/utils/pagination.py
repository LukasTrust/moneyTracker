from typing import Tuple, Any
from app.config import settings


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


def paginate_query(query, limit: int, offset: int) -> Tuple[list[Any], int, int, int, int]:
    """Apply limit/offset to a SQLAlchemy query and return (items, total, limit, offset, pages).

    pages is total // limit + (1 if remainder else 0)
    """
    eff_limit = clamp_limit(limit)
    try:
        total = query.order_by(None).count()
    except Exception:
        # Fallback if count fails
        items_all = query.all()
        total = len(items_all)
    items = query.offset(offset).limit(eff_limit).all()
    pages = (total // eff_limit) + (1 if total % eff_limit else 0) if eff_limit > 0 else 1
    page = (offset // eff_limit) + 1 if eff_limit > 0 else 1
    return items, total, eff_limit, offset, pages
