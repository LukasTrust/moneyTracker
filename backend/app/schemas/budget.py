"""
Budget Schemas - Pydantic models for budget validation and serialization
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class BudgetPeriodEnum(str, Enum):
    """Budget period types"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class BudgetBase(BaseModel):
    """Base schema for Budget"""
    category_id: int = Field(..., gt=0, description="Category ID")
    period: BudgetPeriodEnum = Field(..., description="Budget period type")
    amount: Decimal = Field(..., gt=0, description="Budget amount (must be positive)")
    start_date: date = Field(..., description="Budget start date")
    end_date: date = Field(..., description="Budget end date (inclusive)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Ensure end_date is after or equal to start_date"""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after or equal to start_date')
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget"""
    pass


class BudgetUpdate(BaseModel):
    """Schema for updating a budget"""
    category_id: Optional[int] = Field(None, gt=0)
    period: Optional[BudgetPeriodEnum] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Ensure end_date is after or equal to start_date if both are provided"""
        if v is not None and 'start_date' in info.data and info.data['start_date'] is not None:
            if v < info.data['start_date']:
                raise ValueError('end_date must be after or equal to start_date')
        return v


class BudgetResponse(BudgetBase):
    """Schema for budget response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BudgetProgressInfo(BaseModel):
    """Schema for budget progress information"""
    spent: Decimal = Field(..., description="Amount spent in this budget period")
    remaining: Decimal = Field(..., description="Remaining budget (can be negative)")
    percentage: float = Field(..., ge=0, description="Percentage of budget spent (can exceed 100)")
    is_exceeded: bool = Field(..., description="Whether budget has been exceeded")
    days_remaining: int = Field(..., description="Days remaining in budget period")
    daily_average_spent: Decimal = Field(..., description="Average daily spending so far")
    projected_total: Decimal = Field(..., description="Projected total spending if current rate continues")
    

class BudgetWithProgress(BudgetResponse):
    """Schema for budget with progress calculation"""
    progress: BudgetProgressInfo
    category_name: str = Field(..., description="Name of the associated category")
    category_color: str = Field(..., description="Color of the associated category")
    category_icon: Optional[str] = Field(None, description="Icon of the associated category")


class BudgetSummary(BaseModel):
    """Schema for overall budget summary"""
    total_budgets: int = Field(..., description="Total number of active budgets")
    total_budget_amount: Decimal = Field(..., description="Sum of all budget amounts")
    total_spent: Decimal = Field(..., description="Total amount spent across all budgets")
    total_remaining: Decimal = Field(..., description="Total remaining across all budgets")
    budgets_exceeded: int = Field(..., description="Number of budgets that have been exceeded")
    budgets_at_risk: int = Field(..., description="Number of budgets at >80% but not exceeded")
    overall_percentage: float = Field(..., ge=0, description="Overall budget utilization percentage")
