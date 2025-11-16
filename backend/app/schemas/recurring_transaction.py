"""
Recurring Transaction Schemas - Request/Response models
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class RecurringTransactionBase(BaseModel):
    """Base schema for recurring transaction"""
    recipient: str
    average_amount: float
    average_interval_days: int
    category_id: Optional[int] = None
    notes: Optional[str] = None


class RecurringTransactionCreate(RecurringTransactionBase):
    """Schema for creating recurring transaction (manual)"""
    account_id: int
    first_occurrence: date
    last_occurrence: date
    occurrence_count: int = Field(ge=3)
    is_active: bool = True


class RecurringTransactionUpdate(BaseModel):
    """Schema for updating recurring transaction"""
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class RecurringTransactionResponse(RecurringTransactionBase):
    """Schema for recurring transaction response"""
    id: int
    account_id: int
    first_occurrence: date
    last_occurrence: date
    occurrence_count: int
    is_active: bool
    is_manually_overridden: bool
    next_expected_date: Optional[date]
    confidence_score: float
    created_at: date
    updated_at: date
    
    # Computed fields
    monthly_cost: Optional[float] = Field(None, description="Estimated monthly cost")
    
    class Config:
        from_attributes = True


class RecurringTransactionListResponse(BaseModel):
    """Schema for list of recurring transactions"""
    total: int
    recurring_transactions: list[RecurringTransactionResponse]


class RecurringTransactionStats(BaseModel):
    """Statistics about recurring transactions"""
    total_count: int
    active_count: int
    inactive_count: int
    total_monthly_cost: float
    by_category: dict[str, float] = Field(default_factory=dict, description="Monthly cost by category")


class RecurringTransactionDetectionStats(BaseModel):
    """Statistics from detection/update operation"""
    created: int
    updated: int
    deleted: int
    skipped: int
    total_recurring: int


class RecurringTransactionToggleRequest(BaseModel):
    """Request to manually toggle recurring status"""
    is_recurring: bool = Field(description="True to mark as recurring, False to unmark")
