"""
Statistics and Aggregation Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SummaryResponse(BaseModel):
    """Schema for account summary"""
    total_income: float = Field(..., description="Total income")
    total_expenses: float = Field(..., description="Total expenses (negative)")
    net_balance: float = Field(..., description="Net balance (income + expenses)")
    transaction_count: int = Field(..., description="Number of transactions")


class ChartDataResponse(BaseModel):
    """Schema for chart data (time series)"""
    labels: List[str] = Field(..., description="Time period labels")
    income: List[float] = Field(..., description="Income per period")
    expenses: List[float] = Field(..., description="Expenses per period")
    balance: List[float] = Field(..., description="Cumulative balance per period")


class CategoryDataResponse(BaseModel):
    """Schema for category aggregation"""
    category_id: Optional[int] = Field(None, description="Category ID (null for uncategorized)")
    category_name: str = Field(..., description="Category name")
    color: str = Field(..., description="Category color")
    icon: Optional[str] = Field(None, description="Category icon")
    total_amount: float = Field(..., description="Total amount for this category")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total")


class RecipientDataResponse(BaseModel):
    """Schema for recipient aggregation"""
    recipient: str = Field(..., description="Recipient/Sender name")
    total_amount: float = Field(..., description="Total amount")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total")
    category_id: Optional[int] = Field(None, description="Associated category")
    category_name: Optional[str] = Field(None, description="Associated category name")


class BalanceHistoryResponse(BaseModel):
    """Schema for balance history (dashboard)"""
    labels: List[str] = Field(..., description="Time period labels")
    income: List[float] = Field(..., description="Income per period")
    expenses: List[float] = Field(..., description="Expenses per period")
    balance: List[float] = Field(..., description="Cumulative balance")


class StatisticsResponse(BaseModel):
    """Schema for account statistics"""
    summary: SummaryResponse
    chart_data: ChartDataResponse
    categories: List[CategoryDataResponse]
    recipients: List[RecipientDataResponse]
