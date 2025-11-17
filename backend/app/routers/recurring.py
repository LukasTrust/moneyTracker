"""
Recurring Transactions Router - Verträge / Wiederkehrende Zahlungen
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional

from app.database import get_db
from app.models.recurring_transaction import RecurringTransaction
from app.models.account import Account
from app.routers.deps import get_account_by_id
from app.schemas.recurring_transaction import (
    RecurringTransactionResponse,
    RecurringTransactionListResponse,
    RecurringTransactionStats,
    RecurringTransactionDetectionStats,
    RecurringTransactionUpdate,
    RecurringTransactionToggleRequest
)
from app.services.recurring_transaction_detector import RecurringTransactionDetector

router = APIRouter()


@router.get("/accounts/{account_id}/recurring", response_model=RecurringTransactionListResponse)
def get_recurring_transactions_for_account(
    include_inactive: bool = False,
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get all recurring transactions (Verträge) for a specific account
    
    Args:
        account_id: Account ID
        include_inactive: Include inactive recurring transactions
        
    Returns:
        List of recurring transactions
    """
    # Query recurring transactions
    query = db.query(RecurringTransaction).filter(
        RecurringTransaction.account_id == account.id
    )
    
    if not include_inactive:
        query = query.filter(RecurringTransaction.is_active == True)
    
    recurring = query.order_by(RecurringTransaction.average_amount.desc()).all()
    
    # Add computed monthly_cost field
    result = []
    for r in recurring:
        r_dict = RecurringTransactionResponse.from_orm(r)
        # Calculate monthly cost based on interval
        if r.average_interval_days > 0:
            monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
            r_dict.monthly_cost = round(monthly_cost, 2)
        result.append(r_dict)
    
    return RecurringTransactionListResponse(
        total=len(result),
        recurring_transactions=result
    )


@router.get("/recurring", response_model=RecurringTransactionListResponse)
def get_all_recurring_transactions(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all recurring transactions (Verträge) across all accounts
    
    Args:
        include_inactive: Include inactive recurring transactions
        
    Returns:
        List of recurring transactions
    """
    query = db.query(RecurringTransaction)
    
    if not include_inactive:
        query = query.filter(RecurringTransaction.is_active == True)
    
    recurring = query.order_by(
        RecurringTransaction.account_id,
        RecurringTransaction.average_amount.desc()
    ).all()
    
    # Add computed monthly_cost field
    result = []
    for r in recurring:
        r_dict = RecurringTransactionResponse.from_orm(r)
        if r.average_interval_days > 0:
            monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
            r_dict.monthly_cost = round(monthly_cost, 2)
        result.append(r_dict)
    
    return RecurringTransactionListResponse(
        total=len(result),
        recurring_transactions=result
    )


@router.get("/accounts/{account_id}/recurring/stats", response_model=RecurringTransactionStats)
def get_recurring_stats_for_account(
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Get statistics for recurring transactions
    
    Args:
        account_id: Account ID
        
    Returns:
        Statistics (counts, monthly costs)
    """

    # Get all recurring transactions for this account
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.account_id == account.id
    ).all()

    total_count = len(recurring)
    active_count = sum(1 for r in recurring if r.is_active)
    inactive_count = total_count - active_count

    # Calculate total monthly cost (only active)
    total_monthly_cost = 0.0
    by_category = {}

    for r in recurring:
        if not r.is_active:
            continue

        # Protect against zero interval
        if r.average_interval_days and r.average_interval_days > 0:
            monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
        else:
            monthly_cost = 0.0

        total_monthly_cost += monthly_cost

        # Group by category name
        if r.category_id:
            category_name = r.category.name if r.category else "Uncategorized"
            by_category[category_name] = by_category.get(category_name, 0.0) + monthly_cost

    return RecurringTransactionStats(
        total_count=total_count,
        active_count=active_count,
        inactive_count=inactive_count,
        total_monthly_cost=round(total_monthly_cost, 2),
        by_category={k: round(v, 2) for k, v in by_category.items()}
    )


@router.get("/recurring/stats", response_model=RecurringTransactionStats)
def get_all_recurring_stats(
    db: Session = Depends(get_db)
):
    """
    Get statistics about all recurring transactions (global)
    
    Returns:
        Statistics (counts, monthly costs)
    """
    recurring = db.query(RecurringTransaction).all()
    
    total_count = len(recurring)
    active_count = sum(1 for r in recurring if r.is_active)
    inactive_count = total_count - active_count
    
    # Calculate total monthly cost (only active)
    total_monthly_cost = 0.0
    by_category = {}
    
    for r in recurring:
        if not r.is_active:
            continue
        
        monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
        total_monthly_cost += monthly_cost
        
        # Group by category
        if r.category_id:
            category_name = r.category.name if r.category else "Uncategorized"
            by_category[category_name] = by_category.get(category_name, 0.0) + monthly_cost
    
    return RecurringTransactionStats(
        total_count=total_count,
        active_count=active_count,
        inactive_count=inactive_count,
        total_monthly_cost=round(total_monthly_cost, 2),
        by_category={k: round(v, 2) for k, v in by_category.items()}
    )


@router.post("/accounts/{account_id}/recurring/detect", response_model=RecurringTransactionDetectionStats)
def detect_recurring_for_account(
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Manually trigger recurring transaction detection for an account
    
    Args:
        account_id: Account ID
        
    Returns:
        Detection statistics
    """
    detector = RecurringTransactionDetector(db)
    stats = detector.update_recurring_transactions(account.id)
    
    # Get total count
    total = db.query(RecurringTransaction).filter(
        RecurringTransaction.account_id == account.id
    ).count()
    
    return RecurringTransactionDetectionStats(
        created=stats["created"],
        updated=stats["updated"],
        deleted=stats["deleted"],
        skipped=stats["skipped"],
        total_recurring=total
    )


@router.post("/recurring/detect-all", response_model=RecurringTransactionDetectionStats)
def detect_recurring_for_all_accounts(
    db: Session = Depends(get_db)
):
    """
    Trigger recurring transaction detection for all accounts
    
    Returns:
        Aggregated detection statistics
    """
    detector = RecurringTransactionDetector(db)
    
    # Get all accounts
    accounts = db.query(Account).all()
    
    total_stats = {"created": 0, "updated": 0, "deleted": 0, "skipped": 0}
    
    for account in accounts:
        stats = detector.update_recurring_transactions(account.id)
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Get total count
    total = db.query(RecurringTransaction).count()
    
    return RecurringTransactionDetectionStats(
        created=total_stats["created"],
        updated=total_stats["updated"],
        deleted=total_stats["deleted"],
        skipped=total_stats["skipped"],
        total_recurring=total
    )


@router.patch("/recurring/{recurring_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    recurring_id: int,
    update_data: RecurringTransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a recurring transaction (notes, category, active status)
    
    Args:
        recurring_id: RecurringTransaction ID
        update_data: Update data
        
    Returns:
        Updated recurring transaction
    """
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id
    ).first()
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecurringTransaction {recurring_id} not found"
        )
    
    # Update fields
    if update_data.notes is not None:
        recurring.notes = update_data.notes
    if update_data.is_active is not None:
        recurring.is_active = update_data.is_active
        recurring.is_manually_overridden = True
    if update_data.category_id is not None:
        recurring.category_id = update_data.category_id
    
    db.commit()
    db.refresh(recurring)
    
    # Add computed field
    response = RecurringTransactionResponse.from_orm(recurring)
    if recurring.average_interval_days > 0:
        monthly_cost = float(recurring.average_amount) * (30 / recurring.average_interval_days)
        response.monthly_cost = round(monthly_cost, 2)
    
    return response


@router.post("/recurring/{recurring_id}/toggle", response_model=RecurringTransactionResponse)
def toggle_recurring_status(
    recurring_id: int,
    toggle_data: RecurringTransactionToggleRequest,
    db: Session = Depends(get_db)
):
    """
    Manually toggle recurring status (mark/unmark as recurring)
    
    Args:
        recurring_id: RecurringTransaction ID
        toggle_data: Toggle request
        
    Returns:
        Updated recurring transaction
    """
    detector = RecurringTransactionDetector(db)
    
    try:
        recurring = detector.toggle_manual_override(recurring_id, toggle_data.is_recurring)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Add computed field
    response = RecurringTransactionResponse.from_orm(recurring)
    if recurring.average_interval_days > 0:
        monthly_cost = float(recurring.average_amount) * (30 / recurring.average_interval_days)
        response.monthly_cost = round(monthly_cost, 2)
    
    return response


@router.delete("/recurring/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_transaction(
    recurring_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a recurring transaction
    
    Args:
        recurring_id: RecurringTransaction ID
    """
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id
    ).first()
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecurringTransaction {recurring_id} not found"
        )
    
    db.delete(recurring)
    db.commit()
