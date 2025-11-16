"""
Budget Tracker Service - Business logic for budget management and progress tracking
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict

from app.models.budget import Budget
from app.models.category import Category
from app.models.data_row import DataRow
from app.models.transfer import Transfer
from app.schemas.budget import BudgetProgressInfo, BudgetWithProgress, BudgetSummary


class BudgetTracker:
    """
    Service for tracking budget progress and calculating spending statistics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_transfer_transaction_ids(self) -> set:
        """
        Get set of all transaction IDs that are part of transfers.
        These should be excluded from budget calculations.
        
        Returns:
            Set of transaction IDs involved in transfers
        """
        transfer_ids = set()
        
        # Get all from_transaction_ids
        from_ids = self.db.query(Transfer.from_transaction_id).all()
        transfer_ids.update([tid[0] for tid in from_ids])
        
        # Get all to_transaction_ids
        to_ids = self.db.query(Transfer.to_transaction_id).all()
        transfer_ids.update([tid[0] for tid in to_ids])
        
        return transfer_ids
    
    def calculate_budget_progress(
        self,
        budget: Budget,
        account_id: Optional[int] = None
    ) -> BudgetProgressInfo:
        """
        Calculate progress for a single budget
        
        Args:
            budget: Budget instance
            account_id: Optional account filter (None = all accounts)
            
        Returns:
            BudgetProgressInfo with spending details
        """
        today = date.today()
        
        # Get transfer transaction IDs to exclude
        transfer_ids = self._get_transfer_transaction_ids()
        
        # Calculate total spent in this budget period
        query = self.db.query(func.sum(func.abs(DataRow.amount))).filter(
            and_(
                DataRow.category_id == budget.category_id,
                DataRow.transaction_date >= budget.start_date,
                DataRow.transaction_date <= budget.end_date,
                DataRow.amount < 0  # Only expenses (negative amounts)
            )
        )
        
        # Exclude transfer transactions
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        # Optional: Filter by account
        if account_id is not None:
            query = query.filter(DataRow.account_id == account_id)
        
        spent_raw = query.scalar()
        spent = Decimal(spent_raw) if spent_raw else Decimal('0.00')
        
        # Calculate remaining budget
        budget_amount = Decimal(str(budget.amount))
        remaining = budget_amount - spent
        
        # Calculate percentage
        percentage = float((spent / budget_amount) * 100) if budget_amount > 0 else 0.0
        
        # Check if exceeded
        is_exceeded = spent > budget_amount
        
        # Calculate days remaining
        if today > budget.end_date:
            days_remaining = 0
        elif today < budget.start_date:
            days_remaining = (budget.end_date - budget.start_date).days + 1
        else:
            days_remaining = (budget.end_date - today).days + 1
        
        # Calculate total days in period
        total_days = (budget.end_date - budget.start_date).days + 1
        
        # Calculate days elapsed
        if today < budget.start_date:
            days_elapsed = 0
        elif today > budget.end_date:
            days_elapsed = total_days
        else:
            days_elapsed = (today - budget.start_date).days + 1
        
        # Calculate average daily spending
        daily_average_spent = spent / Decimal(days_elapsed) if days_elapsed > 0 else Decimal('0.00')
        
        # Project total spending if current rate continues
        if days_elapsed > 0 and total_days > 0:
            projected_total = (spent / Decimal(days_elapsed)) * Decimal(total_days)
        else:
            projected_total = spent
        
        return BudgetProgressInfo(
            spent=spent,
            remaining=remaining,
            percentage=round(percentage, 2),
            is_exceeded=is_exceeded,
            days_remaining=days_remaining,
            daily_average_spent=daily_average_spent,
            projected_total=projected_total
        )
    
    def get_budget_with_progress(
        self,
        budget_id: int,
        account_id: Optional[int] = None
    ) -> Optional[BudgetWithProgress]:
        """
        Get a budget with its progress information
        
        Args:
            budget_id: Budget ID
            account_id: Optional account filter
            
        Returns:
            BudgetWithProgress or None if not found
        """
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        
        if not budget:
            return None
        
        # Get category info
        category = self.db.query(Category).filter(Category.id == budget.category_id).first()
        
        # Calculate progress
        progress = self.calculate_budget_progress(budget, account_id)
        
        return BudgetWithProgress(
            id=budget.id,
            category_id=budget.category_id,
            period=budget.period,
            amount=budget.amount,
            start_date=budget.start_date,
            end_date=budget.end_date,
            description=budget.description,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
            progress=progress,
            category_name=category.name if category else "Unknown",
            category_color=category.color if category else "#3b82f6",
            category_icon=category.icon if category else None
        )
    
    def get_all_budgets_with_progress(
        self,
        account_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[BudgetWithProgress]:
        """
        Get all budgets with their progress information
        
        Args:
            account_id: Optional account filter
            active_only: If True, only return budgets that are currently active
            
        Returns:
            List of BudgetWithProgress
        """
        query = self.db.query(Budget)
        
        # Filter for active budgets only
        if active_only:
            today = date.today()
            query = query.filter(
                and_(
                    Budget.start_date <= today,
                    Budget.end_date >= today
                )
            )
        
        budgets = query.all()
        
        result = []
        for budget in budgets:
            budget_with_progress = self.get_budget_with_progress(budget.id, account_id)
            if budget_with_progress:
                result.append(budget_with_progress)
        
        # Sort by percentage (highest first)
        result.sort(key=lambda x: x.progress.percentage, reverse=True)
        
        return result
    
    def get_budget_summary(
        self,
        account_id: Optional[int] = None,
        active_only: bool = True
    ) -> BudgetSummary:
        """
        Get overall budget summary statistics
        
        Args:
            account_id: Optional account filter
            active_only: If True, only include active budgets
            
        Returns:
            BudgetSummary with aggregate statistics
        """
        budgets_with_progress = self.get_all_budgets_with_progress(account_id, active_only)
        
        if not budgets_with_progress:
            return BudgetSummary(
                total_budgets=0,
                total_budget_amount=Decimal('0.00'),
                total_spent=Decimal('0.00'),
                total_remaining=Decimal('0.00'),
                budgets_exceeded=0,
                budgets_at_risk=0,
                overall_percentage=0.0
            )
        
        total_budget_amount = sum(b.amount for b in budgets_with_progress)
        total_spent = sum(b.progress.spent for b in budgets_with_progress)
        total_remaining = sum(b.progress.remaining for b in budgets_with_progress)
        
        budgets_exceeded = sum(1 for b in budgets_with_progress if b.progress.is_exceeded)
        budgets_at_risk = sum(
            1 for b in budgets_with_progress 
            if not b.progress.is_exceeded and b.progress.percentage >= 80
        )
        
        overall_percentage = float(
            (total_spent / total_budget_amount) * 100
        ) if total_budget_amount > 0 else 0.0
        
        return BudgetSummary(
            total_budgets=len(budgets_with_progress),
            total_budget_amount=total_budget_amount,
            total_spent=total_spent,
            total_remaining=total_remaining,
            budgets_exceeded=budgets_exceeded,
            budgets_at_risk=budgets_at_risk,
            overall_percentage=round(overall_percentage, 2)
        )
    
    def check_budget_conflicts(
        self,
        category_id: int,
        start_date: date,
        end_date: date,
        exclude_budget_id: Optional[int] = None
    ) -> List[Budget]:
        """
        Check for overlapping budgets for the same category
        
        Args:
            category_id: Category ID
            start_date: New budget start date
            end_date: New budget end date
            exclude_budget_id: Budget ID to exclude from check (for updates)
            
        Returns:
            List of conflicting budgets
        """
        query = self.db.query(Budget).filter(
            and_(
                Budget.category_id == category_id,
                # Check for date range overlap
                Budget.start_date <= end_date,
                Budget.end_date >= start_date
            )
        )
        
        if exclude_budget_id is not None:
            query = query.filter(Budget.id != exclude_budget_id)
        
        return query.all()
