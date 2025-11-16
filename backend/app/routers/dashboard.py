"""
Dashboard Router - Aggregated data across all accounts
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
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

router = APIRouter()


@router.get("/summary", response_model=dict)
def get_dashboard_summary(
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by specific category ID"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated summary across all accounts
    
    Args:
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by specific category ID
        
    Returns:
        Summary with total income, expenses, balance, transaction count, and account count
    """
    aggregator = DataAggregator(db)
    
    # Get summary without account filter (all accounts)
    summary = aggregator.get_summary(
        account_id=None,
        from_date=from_date,
        to_date=to_date,
        category_id=category_id
    )
    print(f"[dashboard] get_dashboard_summary called with from_date={from_date} to_date={to_date} category_id={category_id}; summary_keys={list(summary.keys())}")
    
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
    limit: int = Query(10, ge=1, le=50, description="Number of categories"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by specific category ID"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated category data across all accounts
    
    Args:
        limit: Maximum number of categories to return
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by specific category ID
        
    Returns:
        List of category aggregations
    """
    aggregator = DataAggregator(db)
    
    categories = aggregator.get_category_aggregation(
        account_id=None,  # All accounts
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        category_id=category_id
    )
    print(f"[dashboard] get_dashboard_categories called with from_date={from_date} to_date={to_date} category_id={category_id} limit={limit}; returned_count={len(categories) if categories is not None else 'None'}")
    
    return categories


@router.get("/balance-history", response_model=BalanceHistoryResponse)
def get_dashboard_balance_history(
    group_by: str = Query('month', regex='^(day|month|year)$', description="Grouping period"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by specific category ID"),
    db: Session = Depends(get_db)
):
    """
    Get historical balance across all accounts
    
    Args:
        group_by: Grouping period (day, month, year)
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by specific category ID
        
    Returns:
        Balance history with labels, income, expenses, balance arrays
    """
    aggregator = DataAggregator(db)
    
    history = aggregator.get_balance_history(
        account_id=None,  # All accounts
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
        category_id=category_id
    )
    print(f"[dashboard] get_dashboard_balance_history called with group_by={group_by} from_date={from_date} to_date={to_date} category_id={category_id}; labels_len={len(history.get('labels') if isinstance(history, dict) and history.get('labels') else [])}")
    
    return history


@router.get("/transactions", response_model=DataRowListResponse)
def get_dashboard_transactions(
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get transactions across all accounts with optional filters
    
    Args:
        limit: Number of items per page
        offset: Number of items to skip
        category_id: Filter by category ID
        from_date: Filter by start date
        to_date: Filter by end date
        
    Returns:
        Paginated list of transactions
    """
    # Build query
    query = db.query(DataRow)
    
    # Apply filters
    if category_id is not None:
        query = query.filter(DataRow.category_id == category_id)
    
    if from_date:
        query = query.filter(DataRow.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(DataRow.transaction_date <= to_date)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    data_rows = query.offset(offset).limit(limit).all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit  # Ceiling division
    page = (offset // limit) + 1
    
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
    transaction_type: str = Query('expense', regex='^(all|income|expense)$', description="Transaction type filter"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated recipient/sender data across all accounts
    
    Args:
        limit: Maximum number of recipients to return
        transaction_type: Filter by transaction type ('all', 'income', 'expense')
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by category ID
        
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
        category_id=category_id
    )
    print(f"[dashboard] get_dashboard_recipients_data called with transaction_type={transaction_type} from_date={from_date} to_date={to_date} category_id={category_id} limit={limit}; returned_count={len(recipients) if recipients is not None else 'None'}")
    
    return recipients
