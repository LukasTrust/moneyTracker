"""
Recurring Transactions Router - Verträge / Wiederkehrende Zahlungen
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
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
    RecurringTransactionToggleRequest,
    RecurringTransactionDetailResponse,
    LinkedTransactionInfo
)
from app.services.recurring_transaction_detector import (
    RecurringTransactionDetector,
    run_update_recurring_transactions,
    run_update_recurring_transactions_all,
)
from app.utils import get_logger
from app.utils.pagination import paginate_query
from app.config import settings

logger = get_logger(__name__)

router = APIRouter()


@router.get('/jobs/{job_id}')
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get background job status by id"""
    from app.services.job_service import JobService
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    return job.to_dict()


@router.get("/{account_id}/recurring-transactions", response_model=RecurringTransactionListResponse)
def get_recurring_transactions_for_account(
    account_id: int,
    include_inactive: bool = False,
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get recurring transactions for a specific account (by id)
    """
    # Validate account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found")

    query = db.query(RecurringTransaction).filter(
        RecurringTransaction.account_id == account.id
    )

    if not include_inactive:
        query = query.filter(RecurringTransaction.is_active == True)

    base_query = query.order_by(RecurringTransaction.average_amount.desc())
    items, total, eff_limit, eff_offset, pages = paginate_query(base_query, limit, offset)

    result = []
    for r in items:
        r_dict = RecurringTransactionResponse.from_orm(r)
        if r.average_interval_days and r.average_interval_days > 0:
            monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
            r_dict.monthly_cost = round(monthly_cost, 2)
        result.append(r_dict)

    page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1
    return RecurringTransactionListResponse(total=total, recurring_transactions=result, limit=eff_limit, offset=eff_offset, pages=pages, page=page)


@router.get("/recurring-transactions", response_model=RecurringTransactionListResponse)
def get_all_recurring_transactions(
    include_inactive: bool = False,
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all recurring transactions (Verträge) across all accounts
    
    Args:
        include_inactive: Include inactive recurring transactions
        
    Returns:
        List of recurring transactions (paginated)
    """
    query = db.query(RecurringTransaction)

    if not include_inactive:
        query = query.filter(RecurringTransaction.is_active == True)

    base_query = query.order_by(RecurringTransaction.account_id, RecurringTransaction.average_amount.desc())
    items, total, eff_limit, eff_offset, pages = paginate_query(base_query, limit, offset)

    result = []
    for r in items:
        r_dict = RecurringTransactionResponse.from_orm(r)
        if r.average_interval_days > 0:
            monthly_cost = float(r.average_amount) * (30 / r.average_interval_days)
            r_dict.monthly_cost = round(monthly_cost, 2)
        result.append(r_dict)

    page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1
    return RecurringTransactionListResponse(total=total, recurring_transactions=result, limit=eff_limit, offset=eff_offset, pages=pages, page=page)


@router.get("/{account_id}/recurring-transactions/stats", response_model=RecurringTransactionStats)
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


@router.get("/recurring-transactions/stats", response_model=RecurringTransactionStats)
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


@router.post("/{account_id}/recurring-transactions/detect", response_model=RecurringTransactionDetectionStats)
def detect_recurring_for_account(
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Manually trigger recurring transaction detection for an account
    
    Args:
        account_id: Account ID
        
    Returns:
        Detection statistics
    """
    # If a BackgroundTasks instance is provided, enqueue and return queued response
    if background_tasks is not None:
        from app.services.job_service import JobService
        job = JobService.create_job(db, task_type="recurring_detection", account_id=account.id)
        background_tasks.add_task(run_update_recurring_transactions, account.id)
        logger.info("Enqueued recurring detection for account", extra={"account_id": account.id, "job_id": getattr(job, 'id', None)})

        # Return a quick response indicating background job queued. Keep totals accurate synchronously.
        total = db.query(RecurringTransaction).filter(
            RecurringTransaction.account_id == account.id
        ).count()
        return RecurringTransactionDetectionStats(
            created=0,
            updated=0,
            deleted=0,
            skipped=0,
            total_recurring=total
        )

    # Fallback: run synchronously (e.g., during tests)
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


@router.post("/recurring-transactions/detect-all", response_model=RecurringTransactionDetectionStats)
def detect_recurring_for_all_accounts(
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Trigger recurring transaction detection for all accounts
    
    Returns:
        Aggregated detection statistics
    """
    if background_tasks is not None:
        from app.services.job_service import JobService
        job = JobService.create_job(db, task_type="recurring_detection_bulk")
        background_tasks.add_task(run_update_recurring_transactions_all)
        logger.info("Enqueued bulk recurring detection", extra={"job_id": getattr(job, 'id', None)})

        total = db.query(RecurringTransaction).count()
        return RecurringTransactionDetectionStats(
            created=0,
            updated=0,
            deleted=0,
            skipped=0,
            total_recurring=total
        )

    # Fallback synchronous execution
    detector = RecurringTransactionDetector(db)
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


@router.patch("/recurring-transactions/{recurring_id}", response_model=RecurringTransactionResponse)
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


@router.get("/recurring-transactions/{recurring_id}", response_model=RecurringTransactionDetailResponse)
def get_recurring_transaction_details(
    recurring_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific recurring transaction
    
    Args:
        recurring_id: RecurringTransaction ID
        
    Returns:
        Detailed recurring transaction with linked transactions and statistics
    """
    from app.models.data_row import DataRow
    from app.models.recurring_transaction import RecurringTransactionLink
    from decimal import Decimal
    
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id
    ).first()
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecurringTransaction {recurring_id} not found"
        )
    
    # Get linked transactions
    linked_data = (
        db.query(DataRow)
        .join(RecurringTransactionLink, RecurringTransactionLink.data_row_id == DataRow.id)
        .filter(RecurringTransactionLink.recurring_transaction_id == recurring_id)
        .order_by(DataRow.transaction_date.desc())
        .all()
    )
    
    # Build linked transaction info
    linked_transactions = [
        LinkedTransactionInfo(
            id=tx.id,
            transaction_date=tx.transaction_date,
            amount=Decimal(str(tx.amount)),
            description=tx.purpose
        )
        for tx in linked_data
    ]
    
    # Calculate statistics
    amounts = [Decimal(str(tx.amount)) for tx in linked_data]
    total_spent = sum(amounts) if amounts else Decimal('0')
    min_amount = min(amounts) if amounts else Decimal('0')
    max_amount = max(amounts) if amounts else Decimal('0')
    
    # Calculate average days between transactions
    average_days_between = None
    if len(linked_data) > 1:
        sorted_tx = sorted(linked_data, key=lambda t: t.transaction_date)
        intervals = [
            (sorted_tx[i + 1].transaction_date - sorted_tx[i].transaction_date).days
            for i in range(len(sorted_tx) - 1)
        ]
        if intervals:
            average_days_between = sum(intervals) / len(intervals)
    
    # Calculate monthly cost
    monthly_cost = None
    if recurring.average_interval_days > 0:
        monthly_cost = Decimal(str(round(float(recurring.average_amount) * (30 / recurring.average_interval_days), 2)))
    
    # Create response with all required fields
    response = RecurringTransactionDetailResponse(
        id=recurring.id,
        account_id=recurring.account_id,
        recipient=recurring.recipient,
        average_amount=recurring.average_amount,
        average_interval_days=recurring.average_interval_days,
        category_id=recurring.category_id,
        notes=recurring.notes,
        first_occurrence=recurring.first_occurrence,
        last_occurrence=recurring.last_occurrence,
        occurrence_count=recurring.occurrence_count,
        is_active=recurring.is_active,
        is_manually_overridden=recurring.is_manually_overridden,
        next_expected_date=recurring.next_expected_date,
        confidence_score=float(recurring.confidence_score),
        created_at=recurring.created_at,
        updated_at=recurring.updated_at,
        monthly_cost=monthly_cost,
        linked_transactions=linked_transactions,
        total_spent=total_spent,
        average_days_between=average_days_between,
        min_amount=min_amount,
        max_amount=max_amount
    )
    
    return response


@router.post("/recurring-transactions/{recurring_id}/toggle", response_model=RecurringTransactionResponse)
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


@router.delete("/recurring-transactions/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
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
