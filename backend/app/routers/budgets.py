"""
Budget Router - CRUD operations for budgets and progress tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetWithProgress,
    BudgetSummary
)
from app.services.budget_tracker import BudgetTracker

router = APIRouter()


@router.get("", response_model=List[BudgetResponse])
def get_budgets(
    active_only: bool = Query(False, description="Only return currently active budgets"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db)
):
    """
    Get all budgets
    
    Args:
        active_only: If True, only return budgets that are currently active (today is within date range)
        category_id: Optional category filter
        
    Returns:
        List of budgets
    """
    query = db.query(Budget)
    
    if category_id is not None:
        query = query.filter(Budget.category_id == category_id)
    
    if active_only:
        from datetime import date
        today = date.today()
        query = query.filter(
            Budget.start_date <= today,
            Budget.end_date >= today
        )
    
    budgets = query.order_by(Budget.start_date.desc()).all()
    return budgets


@router.get("/progress", response_model=List[BudgetWithProgress])
def get_budgets_with_progress(
    active_only: bool = Query(True, description="Only return currently active budgets"),
    account_id: Optional[int] = Query(None, description="Filter spending by account"),
    db: Session = Depends(get_db)
):
    """
    Get all budgets with progress information
    
    Args:
        active_only: If True, only return currently active budgets
        account_id: Optional account filter for spending calculation
        
    Returns:
        List of budgets with progress data
    """
    tracker = BudgetTracker(db)
    return tracker.get_all_budgets_with_progress(account_id, active_only)


@router.get("/summary", response_model=BudgetSummary)
def get_budget_summary(
    active_only: bool = Query(True, description="Only include currently active budgets"),
    account_id: Optional[int] = Query(None, description="Filter spending by account"),
    db: Session = Depends(get_db)
):
    """
    Get overall budget summary with aggregate statistics
    
    Args:
        active_only: If True, only include currently active budgets
        account_id: Optional account filter for spending calculation
        
    Returns:
        Budget summary with totals and statistics
    """
    tracker = BudgetTracker(db)
    return tracker.get_budget_summary(account_id, active_only)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """
    Get a specific budget by ID
    
    Args:
        budget_id: Budget ID
        
    Returns:
        Budget details
        
    Raises:
        404: Budget not found
    """
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found"
        )
    
    return budget


@router.get("/{budget_id}/progress", response_model=BudgetWithProgress)
def get_budget_with_progress(
    budget_id: int,
    account_id: Optional[int] = Query(None, description="Filter spending by account"),
    db: Session = Depends(get_db)
):
    """
    Get a budget with its progress information
    
    Args:
        budget_id: Budget ID
        account_id: Optional account filter for spending calculation
        
    Returns:
        Budget with progress data
        
    Raises:
        404: Budget not found
    """
    tracker = BudgetTracker(db)
    budget_with_progress = tracker.get_budget_with_progress(budget_id, account_id)
    
    if not budget_with_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found"
        )
    
    return budget_with_progress


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(budget_data: BudgetCreate, db: Session = Depends(get_db)):
    """
    Create a new budget
    
    Args:
        budget_data: Budget creation data
        
    Returns:
        Created budget
        
    Raises:
        400: Validation errors (category not found, date conflicts, etc.)
    """
    # Verify category exists
    category = db.query(Category).filter(Category.id == budget_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with ID {budget_data.category_id} not found"
        )
    
    # Check for overlapping budgets
    tracker = BudgetTracker(db)
    conflicts = tracker.check_budget_conflicts(
        budget_data.category_id,
        budget_data.start_date,
        budget_data.end_date
    )
    
    if conflicts:
        conflict_info = [
            f"Budget #{b.id} ({b.start_date} to {b.end_date})"
            for b in conflicts
        ]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget overlaps with existing budgets for this category: {', '.join(conflict_info)}"
        )
    
    # Create new budget
    new_budget = Budget(
        category_id=budget_data.category_id,
        period=budget_data.period,
        amount=budget_data.amount,
        start_date=budget_data.start_date,
        end_date=budget_data.end_date,
        description=budget_data.description
    )
    
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    
    return new_budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a budget
    
    Args:
        budget_id: Budget ID
        budget_data: Budget update data
        
    Returns:
        Updated budget
        
    Raises:
        404: Budget not found
        400: Validation errors
    """
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found"
        )
    
    # Verify category if being updated
    if budget_data.category_id is not None:
        category = db.query(Category).filter(Category.id == budget_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {budget_data.category_id} not found"
            )
    
    # Prepare data for conflict check
    check_category_id = budget_data.category_id if budget_data.category_id is not None else budget.category_id
    check_start_date = budget_data.start_date if budget_data.start_date is not None else budget.start_date
    check_end_date = budget_data.end_date if budget_data.end_date is not None else budget.end_date
    
    # Check for overlapping budgets (excluding this one)
    tracker = BudgetTracker(db)
    conflicts = tracker.check_budget_conflicts(
        check_category_id,
        check_start_date,
        check_end_date,
        exclude_budget_id=budget_id
    )
    
    if conflicts:
        conflict_info = [
            f"Budget #{b.id} ({b.start_date} to {b.end_date})"
            for b in conflicts
        ]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget would overlap with existing budgets: {', '.join(conflict_info)}"
        )
    
    # Update budget fields
    update_data = budget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """
    Delete a budget
    
    Args:
        budget_id: Budget ID
        
    Raises:
        404: Budget not found
    """
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found"
        )
    
    db.delete(budget)
    db.commit()
    
    return None
