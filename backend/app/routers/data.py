"""
Data Router - Retrieve and analyze transaction data
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime

from app.database import get_db
from app.models.account import Account
from app.models.data_row import DataRow
from app.schemas.data_row import DataRowListResponse, DataRowResponse
from app.schemas.statistics import (
    SummaryResponse,
    ChartDataResponse,
    CategoryDataResponse,
    RecipientDataResponse
)
from app.services.data_aggregator import DataAggregator

router = APIRouter()


@router.get("/{account_id}/data", response_model=DataRowListResponse)
def get_account_data(
    account_id: int,
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get paginated transaction data for an account
    
    Args:
        account_id: Account ID
        limit: Number of items per page
        offset: Number of items to skip
        from_date: Filter by start date
        to_date: Filter by end date
        
    Returns:
        Paginated list of transactions
        
    Raises:
        404: Account not found
    """
    # Check if account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Build query
    query = db.query(DataRow).filter(DataRow.account_id == account_id)
    
    # Apply date filters using direct column access
    if from_date:
        query = query.filter(DataRow.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(DataRow.transaction_date <= to_date)
    
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


@router.get("/{account_id}/summary", response_model=SummaryResponse)
def get_account_summary(
    account_id: int,
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for an account
    
    Args:
        account_id: Account ID
        from_date: Filter by start date
        to_date: Filter by end date
        
    Returns:
        Summary with income, expenses, balance, and transaction count
        
    Raises:
        404: Account not found
    """
    # Check if account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    aggregator = DataAggregator(db)
    summary = aggregator.get_summary(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date
    )
    
    return summary


@router.get("/{account_id}/statistics", response_model=ChartDataResponse)
def get_account_statistics(
    account_id: int,
    group_by: str = Query('month', regex='^(day|month|year)$', description="Grouping period"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get historical statistics for charts
    
    Args:
        account_id: Account ID
        group_by: Grouping period (day, month, year)
        from_date: Filter by start date
        to_date: Filter by end date
        
    Returns:
        Chart data with labels, income, expenses, balance arrays
        
    Raises:
        404: Account not found
    """
    # Check if account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    aggregator = DataAggregator(db)
    statistics = aggregator.get_balance_history(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        group_by=group_by
    )
    
    return statistics


@router.get("/{account_id}/categories-data", response_model=list[CategoryDataResponse])
def get_account_categories_data(
    account_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of categories"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated data by category for an account
    
    Args:
        account_id: Account ID
        limit: Maximum number of categories to return
        from_date: Filter by start date
        to_date: Filter by end date
        
    Returns:
        List of category aggregations
        
    Raises:
        404: Account not found
    """
    # Check if account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    aggregator = DataAggregator(db)
    categories = aggregator.get_category_aggregation(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    
    return categories


@router.get("/{account_id}/recipients-data", response_model=list[RecipientDataResponse])
def get_account_recipients_data(
    account_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recipients"),
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    transaction_type: str = Query('all', regex='^(all|income|expense)$', description="Transaction type filter"),
    category_id: Optional[int] = Query(None, description="Category ID filter"),
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
        category_id: Filter by category ID
        
    Returns:
        List of recipient aggregations
        
    Raises:
        404: Account not found
    """
    # Check if account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    aggregator = DataAggregator(db)
    recipients = aggregator.get_recipient_aggregation(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        transaction_type=transaction_type,
        category_id=category_id
    )
    
    return recipients
