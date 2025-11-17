"""
Comparison Router - Compare time periods for financial analysis
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from app.database import get_db
from app.schemas.statistics import ComparisonResponse
from app.services.data_aggregator import DataAggregator
from app.models.account import Account
from app.routers.deps import get_account_by_id

router = APIRouter()


@router.get("/{account_id}", response_model=dict)
def get_period_comparison(
    comparison_type: str = Query(..., description="Type of comparison: 'month' or 'year'"),
    period1: str = Query(..., description="First period (YYYY-MM for month, YYYY for year)"),
    period2: str = Query(..., description="Second period (YYYY-MM for month, YYYY for year)"),
    top_limit: int = Query(5, description="Number of top recipients to include", ge=1, le=20),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Compare two time periods for a specific account
    
    Args:
        account_id: Account ID to compare
        comparison_type: Type of comparison ('month' or 'year')
        period1: First period to compare (format: YYYY-MM or YYYY)
        period2: Second period to compare (format: YYYY-MM or YYYY)
        top_limit: Number of top recipients to include (default: 5)
        
    Returns:
        Comprehensive comparison data including summary, categories, and top recipients
        
    Example:
        GET /api/comparison/1?comparison_type=month&period1=2024-12&period2=2023-12
        GET /api/comparison/1?comparison_type=year&period1=2024&period2=2023
    """
    # Validate and parse periods
    try:
        if comparison_type == 'month':
            # Parse month format (YYYY-MM)
            period1_date = datetime.strptime(period1, '%Y-%m')
            period2_date = datetime.strptime(period2, '%Y-%m')
            
            # Calculate start and end dates for each month
            period1_start = period1_date.date()
            period1_end = (period1_date + relativedelta(months=1, days=-1)).date()
            
            period2_start = period2_date.date()
            period2_end = (period2_date + relativedelta(months=1, days=-1)).date()
            
        elif comparison_type == 'year':
            # Parse year format (YYYY)
            period1_year = int(period1)
            period2_year = int(period2)
            
            # Calculate start and end dates for each year
            period1_start = date(period1_year, 1, 1)
            period1_end = date(period1_year, 12, 31)
            
            period2_start = date(period2_year, 1, 1)
            period2_end = date(period2_year, 12, 31)
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid comparison_type. Must be 'month' or 'year'"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format. Use YYYY-MM for months or YYYY for years. Error: {str(e)}"
        )
    
    # Get comparison data
    aggregator = DataAggregator(db)
    comparison_data = aggregator.get_period_comparison(
        account_id=account.id,
        period1_start=period1_start,
        period1_end=period1_end,
        period2_start=period2_start,
        period2_end=period2_end,
        top_limit=top_limit
    )
    
    return comparison_data


@router.get("/{account_id}/quick-compare", response_model=dict)
def get_quick_comparison(
    compare_to: str = Query(..., description="Quick comparison: 'last_month', 'last_year', 'month_yoy', 'year_yoy'"),
    reference_period: Optional[str] = Query(None, description="Reference period (YYYY-MM or YYYY), defaults to current"),
    top_limit: int = Query(5, description="Number of top recipients to include", ge=1, le=20),
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Quick comparison presets for common scenarios
    
    Args:
        account_id: Account ID to compare
        compare_to: Comparison type:
            - 'last_month': Current month vs last month
            - 'last_year': Current year vs last year
            - 'month_yoy': Specific month vs same month last year
            - 'year_yoy': Specific year vs previous year
        reference_period: Reference period (optional, defaults to current)
        top_limit: Number of top recipients to include
        
    Returns:
        Comprehensive comparison data
        
    Example:
        GET /api/comparison/1/quick-compare?compare_to=last_month
        GET /api/comparison/1/quick-compare?compare_to=month_yoy&reference_period=2024-12
    """
    today = date.today()
    
    try:
        if compare_to == 'last_month':
            # Current month vs last month
            if reference_period:
                period2_date = datetime.strptime(reference_period, '%Y-%m').date()
            else:
                period2_date = date(today.year, today.month, 1)
            
            period2_start = period2_date
            period2_end = (datetime(period2_date.year, period2_date.month, 1) + relativedelta(months=1, days=-1)).date()
            
            period1_date = period2_date - relativedelta(months=1)
            period1_start = period1_date
            period1_end = (datetime(period1_date.year, period1_date.month, 1) + relativedelta(months=1, days=-1)).date()
            
        elif compare_to == 'last_year':
            # Current year vs last year
            if reference_period:
                period2_year = int(reference_period)
            else:
                period2_year = today.year
            
            period2_start = date(period2_year, 1, 1)
            period2_end = date(period2_year, 12, 31)
            
            period1_year = period2_year - 1
            period1_start = date(period1_year, 1, 1)
            period1_end = date(period1_year, 12, 31)
            
        elif compare_to == 'month_yoy':
            # Month vs same month last year
            if reference_period:
                period2_date = datetime.strptime(reference_period, '%Y-%m').date()
            else:
                period2_date = date(today.year, today.month, 1)
            
            period2_start = period2_date
            period2_end = (datetime(period2_date.year, period2_date.month, 1) + relativedelta(months=1, days=-1)).date()
            
            period1_date = period2_date - relativedelta(years=1)
            period1_start = period1_date
            period1_end = (datetime(period1_date.year, period1_date.month, 1) + relativedelta(months=1, days=-1)).date()
            
        elif compare_to == 'year_yoy':
            # Year vs previous year
            if reference_period:
                period2_year = int(reference_period)
            else:
                period2_year = today.year
            
            period2_start = date(period2_year, 1, 1)
            period2_end = date(period2_year, 12, 31)
            
            period1_year = period2_year - 1
            period1_start = date(period1_year, 1, 1)
            period1_end = date(period1_year, 12, 31)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid compare_to value. Must be 'last_month', 'last_year', 'month_yoy', or 'year_yoy'"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format. Error: {str(e)}"
        )
    
    # Get comparison data
    aggregator = DataAggregator(db)
    comparison_data = aggregator.get_period_comparison(
        account_id=account.id,
        period1_start=period1_start,
        period1_end=period1_end,
        period2_start=period2_start,
        period2_end=period2_end,
        top_limit=top_limit
    )
    
    return comparison_data
