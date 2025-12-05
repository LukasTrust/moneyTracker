"""
Dashboard Router - Aggregated data across all accounts
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import date

from app.database import get_db
from app.schemas.statistics import (
    CategoryDataResponse,
    BalanceHistoryResponse,
    RecipientDataResponse
)
from app.schemas.data_row import DataRowListResponse
from app.services.data_aggregator import DataAggregator
from app.models.data_row import DataRow
from app.utils import get_logger
from app.config import settings

router = APIRouter()
logger = get_logger("app.routers.dashboard")


@router.get("/summary", response_model=dict)
def get_dashboard_summary(
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs (comma-separated)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type: 'income', 'expense', 'all'"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated summary across all accounts
    
    Args:
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        transaction_type: Transaction type filter
        
    Returns:
        Summary with total income, expenses, balance, transaction count, and account count
    """
    aggregator = DataAggregator(db)
    
    # Get summary without account filter (all accounts)
    summary = aggregator.get_summary(
        account_id=None,
        from_date=from_date,
        to_date=to_date,
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type=transaction_type
    )
    logger.debug(
        "get_dashboard_summary called from_date=%s to_date=%s category_id=%s summary_keys=%s",
        from_date, to_date, category_id, list(summary.keys())
    )
    
    # Count unique accounts
    query = db.query(DataRow.account_id).distinct()
    
    if from_date:
        query = query.filter(DataRow.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(DataRow.transaction_date <= to_date)
    
    if category_id is not None:
        if category_id == -1:
            query = query.filter(DataRow.category_id.is_(None))
        else:
            query = query.filter(DataRow.category_id == category_id)
    
    account_count = query.count()
    
    return {
        **summary,
        "account_count": account_count,
        "period": {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None
        }
    }


@router.get("/categories", response_model=list[CategoryDataResponse])
def get_dashboard_categories(
    limit: int = Query(10, ge=1, le=settings.MAX_LIMIT, description="Number of categories"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type filter"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated category data across all accounts
    
    Args:
        limit: Maximum number of categories to return
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by specific category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        transaction_type: Transaction type filter
        
    Returns:
        List of category aggregations
    """
    aggregator = DataAggregator(db)
    
    categories = aggregator.get_category_aggregation(
        account_id=None,  # All accounts
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type=transaction_type
    )
    logger.debug(
        "get_dashboard_categories called from_date=%s to_date=%s category_id=%s limit=%s returned_count=%s",
        from_date, to_date, category_id, limit, len(categories) if categories is not None else 'None'
    )
    
    return categories


@router.get("/balance-history", response_model=BalanceHistoryResponse)
def get_dashboard_balance_history(
    group_by: str = Query('month', pattern='^(day|month|year)$', description="Grouping period"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type filter"),
    db: Session = Depends(get_db)
):
    """
    Get historical balance across all accounts
    
    Args:
        group_by: Grouping period (day, month, year)
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        transaction_type: Transaction type filter
        
    Returns:
        Balance history with labels, income, expenses, balance arrays
    """
    aggregator = DataAggregator(db)
    
    history = aggregator.get_balance_history(
        account_id=None,  # All accounts
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type=transaction_type
    )
    logger.debug(
        "get_dashboard_balance_history called group_by=%s from_date=%s to_date=%s category_id=%s labels_len=%s",
        group_by, from_date, to_date, category_id, len(history.get('labels') if isinstance(history, dict) and history.get('labels') else [])
    )
    
    return history


@router.get("/transactions", response_model=DataRowListResponse)
def get_dashboard_transactions(
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    category_id: Optional[int] = Query(None, description="Single category ID filter"),
    category_ids: Optional[str] = Query(None, description="Multiple category IDs (comma-separated, OR logic)"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query (case-insensitive)"),
    purpose: Optional[str] = Query(None, description="Purpose/description search query (case-insensitive)"),
    transaction_type: Optional[str] = Query(None, description="Transaction type: 'income', 'expense', 'all'"),
    db: Session = Depends(get_db)
):
    """
    Get transactions across all accounts with optional filters
    
    Args:
        limit: Number of items per page
        offset: Number of items to skip
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories (comma-separated, OR logic)
        from_date: Filter by start date
        to_date: Filter by end date
        min_amount: Filter transactions >= this amount
        max_amount: Filter transactions <= this amount
        recipient: Search in recipient field (case-insensitive)
        purpose: Search in purpose field (case-insensitive)
        transaction_type: Filter by type ('income', 'expense', 'all')
        
    Returns:
        Paginated list of transactions
    """
    # Build query
    query = db.query(DataRow)
    
    # Apply category filter (support both single and multiple)
    if category_ids:
        # Multiple categories (OR logic)
        try:
            cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
            if cat_id_list:
                # Handle uncategorized (-1) in the list
                if -1 in cat_id_list:
                    # Include uncategorized OR any of the other categories
                    other_cats = [cid for cid in cat_id_list if cid != -1]
                    if other_cats:
                        query = query.filter(
                            or_(
                                DataRow.category_id.is_(None),
                                DataRow.category_id.in_(other_cats)
                            )
                        )
                    else:
                        query = query.filter(DataRow.category_id.is_(None))
                else:
                    query = query.filter(DataRow.category_id.in_(cat_id_list))
        except (ValueError, AttributeError):
            pass  # Invalid format, skip filter
    elif category_id is not None:
        # Single category (backward compatibility)
        if category_id == -1:
            query = query.filter(DataRow.category_id.is_(None))
        else:
            query = query.filter(DataRow.category_id == category_id)
    
    if from_date:
        query = query.filter(DataRow.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(DataRow.transaction_date <= to_date)
    
    # Apply amount filters
    if min_amount is not None:
        query = query.filter(DataRow.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(DataRow.amount <= max_amount)
    
    # Apply recipient search (case-insensitive)
    if recipient:
        query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
    
    # Apply purpose search (case-insensitive)
    if purpose:
        query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
    
    # Apply transaction type filter
    if transaction_type and transaction_type != 'all':
        if transaction_type == 'income':
            query = query.filter(DataRow.amount > 0)
        elif transaction_type == 'expense':
            query = query.filter(DataRow.amount < 0)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    query = query.order_by(DataRow.transaction_date.desc())
    
    # Apply pagination (enforce server-side max limit)
    eff_limit = min(limit, settings.MAX_LIMIT)
    data_rows = query.offset(offset).limit(eff_limit).all()

    # Calculate pages
    pages = (total + eff_limit - 1) // eff_limit  # Ceiling division
    page = (offset // eff_limit) + 1
    
    return {
        "data": data_rows,
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit
    }


@router.get("/recipients-data", response_model=list[RecipientDataResponse])
def get_dashboard_recipients_data(
    limit: int = Query(10, ge=1, le=50, description="Number of recipients"),
    transaction_type: str = Query('expense', pattern='^(all|income|expense)$', description="Transaction type filter"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple categories"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated recipient/sender data across all accounts
    
    Args:
        limit: Maximum number of recipients to return
        transaction_type: Filter by transaction type ('all', 'income', 'expense')
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        
    Returns:
        List of recipient aggregations
    """
    aggregator = DataAggregator(db)
    
    recipients = aggregator.get_recipient_aggregation(
        account_id=None,  # All accounts
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        transaction_type=transaction_type,
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose
    )
    logger.debug(
        "get_dashboard_recipients_data called transaction_type=%s from_date=%s to_date=%s category_id=%s limit=%s returned_count=%s",
        transaction_type, from_date, to_date, category_id, limit, len(recipients) if recipients is not None else 'None'
    )
    
    return recipients


@router.get("/money-flow", response_model=dict)
def get_dashboard_money_flow(
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs (comma-separated)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type: 'income', 'expense', 'all'"),
    db: Session = Depends(get_db)
):
    """
    Get money flow data showing how income flows into different expense categories
    
    Args:
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        transaction_type: Transaction type filter
        
    Returns:
        Money flow data with income sources and expense categories
    """
    aggregator = DataAggregator(db)
    
    # Get total income and income by category
    income_categories = aggregator.get_category_aggregation(
        account_id=None,
        from_date=from_date,
        to_date=to_date,
        limit=100,  # Get all income categories
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type='income'  # Only income
    )
    
    # Get expense categories
    expense_categories = aggregator.get_category_aggregation(
        account_id=None,
        from_date=from_date,
        to_date=to_date,
        limit=100,  # Get all expense categories
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type='expense'  # Only expenses
    )
    
    # Get summary for total values
    summary = aggregator.get_summary(
        account_id=None,
        from_date=from_date,
        to_date=to_date,
        category_id=category_id,
        category_ids=category_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        purpose=purpose,
        transaction_type=transaction_type
    )
    
    # Format income data
    income_data = []
    if income_categories:
        for cat in income_categories:
            # Handle both dict and object responses
            total_amount = cat.get('total_amount') if isinstance(cat, dict) else cat.total_amount
            if total_amount > 0:  # Only positive amounts
                income_data.append({
                    "id": cat.get('category_id', -1) if isinstance(cat, dict) else (cat.category_id if cat.category_id else -1),
                    "name": cat.get('category_name') if isinstance(cat, dict) else cat.category_name,
                    "value": float(total_amount),
                    "color": cat.get('color') if isinstance(cat, dict) else cat.color,
                    "icon": cat.get('icon') if isinstance(cat, dict) else cat.icon,
                    "count": cat.get('transaction_count') if isinstance(cat, dict) else cat.transaction_count
                })
    
    # Format expense data
    expense_data = []
    if expense_categories:
        for cat in expense_categories:
            # Handle both dict and object responses
            total_amount = cat.get('total_amount') if isinstance(cat, dict) else cat.total_amount
            if total_amount < 0:  # Only negative amounts
                expense_data.append({
                    "id": cat.get('category_id', -1) if isinstance(cat, dict) else (cat.category_id if cat.category_id else -1),
                    "name": cat.get('category_name') if isinstance(cat, dict) else cat.category_name,
                    "value": abs(float(total_amount)),
                    "color": cat.get('color') if isinstance(cat, dict) else cat.color,
                    "icon": cat.get('icon') if isinstance(cat, dict) else cat.icon,
                    "count": cat.get('transaction_count') if isinstance(cat, dict) else cat.transaction_count
                })
    
    logger.debug(
        "get_dashboard_money_flow called from_date=%s to_date=%s income_count=%s expense_count=%s",
        from_date, to_date, len(income_data), len(expense_data)
    )
    
    return {
        "total_income": float(summary.get('total_income', 0)),
        "total_expenses": abs(float(summary.get('total_expenses', 0))),
        "income_categories": income_data,
        "expense_categories": expense_data,
        "period": {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None
        }
    }
