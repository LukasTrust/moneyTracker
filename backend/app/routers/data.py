"""
Data Router - Retrieve and analyze transaction data
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import date, datetime

from app.database import get_db
from app.models.account import Account
from app.models.data_row import DataRow
from app.routers.deps import get_account_by_id
from app.schemas.data_row import DataRowListResponse, DataRowResponse
from app.schemas.statistics import (
    SummaryResponse,
    ChartDataResponse,
    CategoryDataResponse,
    RecipientDataResponse
)
from app.services.data_aggregator import DataAggregator

router = APIRouter()


@router.get("/{account_id}/transactions", response_model=DataRowListResponse)
def get_account_data(
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by category ID (-1 for uncategorized)"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs (comma-separated, OR logic)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter (inclusive)"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter (inclusive)"),
    recipient: Optional[str] = Query(None, description="Filter by recipient (partial match, case-insensitive)"),
    purpose: Optional[str] = Query(None, description="Filter by purpose (partial match, case-insensitive)"),
    transaction_type: Optional[str] = Query(None, description="Filter by type: 'income' or 'expense'"),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get filtered and paginated transaction data for an account
    
    Args:
        account_id: Account ID
        limit: Number of items per page
        offset: Number of items to skip
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category (-1 for uncategorized)
        category_ids: Filter by multiple categories (comma-separated, OR logic)
        min_amount: Filter transactions >= this amount
        max_amount: Filter transactions <= this amount
        recipient: Search in recipient field (case-insensitive, partial match)
        purpose: Search in purpose field (case-insensitive, partial match)
        transaction_type: Filter by type ('income' for positive, 'expense' for negative)
        
    Returns:
        Paginated list of transactions
        
    Raises:
        404: Account not found
    """
    # Build query
    query = db.query(DataRow).filter(DataRow.account_id == account.id)
    
    # Apply date filters using direct column access
    if from_date:
        query = query.filter(DataRow.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(DataRow.transaction_date <= to_date)
    
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
            # Uncategorized transactions
            query = query.filter(DataRow.category_id.is_(None))
        else:
            query = query.filter(DataRow.category_id == category_id)
    
    # Apply amount filters
    if min_amount is not None:
        query = query.filter(DataRow.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(DataRow.amount <= max_amount)
    
    # Apply transaction type filter
    if transaction_type and transaction_type != 'all':
        if transaction_type == 'income':
            query = query.filter(DataRow.amount > 0)
        elif transaction_type == 'expense':
            query = query.filter(DataRow.amount < 0)
    
    # Apply recipient search (case-insensitive)
    if recipient:
        query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
    
    # Apply purpose/description search (case-insensitive)
    if purpose:
        query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
    
    # Get total count
    total = query.count()
    
    # Apply sorting: ORDER BY transaction_date DESC (newest first)
    # Now done in SQL instead of Python!
    query = query.order_by(DataRow.transaction_date.desc())
    
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


@router.get("/{account_id}/transactions/summary", response_model=SummaryResponse)
def get_account_summary(
    account_id: int,
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type filter"),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for an account
    
    Args:
        account_id: Account ID
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
        Summary with income, expenses, balance, and transaction count
        
    Raises:
        404: Account not found
    """
    aggregator = DataAggregator(db)
    summary = aggregator.get_summary(
        account_id=account.id,
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
    
    return summary


@router.get("/{account_id}/transactions/statistics", response_model=ChartDataResponse)
def get_account_statistics(
    account_id: int,
    group_by: str = Query('month', regex='^(day|month|year)$', description="Grouping period"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type filter"),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get historical statistics for charts
    
    Args:
        account_id: Account ID
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
        Chart data with labels, income, expenses, balance arrays
        
    Raises:
        404: Account not found
    """
    aggregator = DataAggregator(db)
    statistics = aggregator.get_balance_history(
        account_id=account.id,
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
    
    return statistics


@router.get("/{account_id}/transactions/categories", response_model=list[CategoryDataResponse])
def get_account_categories_data(
    limit: int = Query(10, ge=1, le=50, description="Number of categories"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by single category ID"),
    category_ids: Optional[str] = Query(None, description="Filter by multiple category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    transaction_type: Optional[str] = Query(None, description="Transaction type filter"),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get aggregated data by category for an account
    
    Args:
        account_id: Account ID
        limit: Maximum number of categories to return
        from_date: Filter by start date
        to_date: Filter by end date
        category_id: Filter by single category
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        transaction_type: Transaction type filter
        
    Returns:
        List of category aggregations
        
    Raises:
        404: Account not found
    """
    aggregator = DataAggregator(db)
    categories = aggregator.get_category_aggregation(
        account_id=account.id,
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
    
    return categories


@router.get("/{account_id}/transactions/recipients", response_model=list[RecipientDataResponse])
def get_account_recipients_data(
    account_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recipients"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    transaction_type: str = Query('all', regex='^(all|income|expense)$', description="Transaction type filter"),
    category_id: Optional[int] = Query(None, description="Single category ID filter"),
    category_ids: Optional[str] = Query(None, description="Multiple category IDs (comma-separated)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    recipient: Optional[str] = Query(None, description="Recipient search query"),
    purpose: Optional[str] = Query(None, description="Purpose search query"),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get aggregated data by recipient for an account
    
    Args:
        account_id: Account ID
        limit: Maximum number of recipients to return
        from_date: Filter by start date
        to_date: Filter by end date
        transaction_type: Filter by transaction type ('all', 'income', 'expense')
        category_id: Filter by single category ID
        category_ids: Filter by multiple categories
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        recipient: Recipient search query
        purpose: Purpose search query
        
    Returns:
        List of recipient aggregations
        
    Raises:
        404: Account not found
    """
    aggregator = DataAggregator(db)
    recipients = aggregator.get_recipient_aggregation(
        account_id=account.id,
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
    
    return recipients
