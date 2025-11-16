"""
Insight Schemas - Pydantic models for Insight API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class InsightBase(BaseModel):
    """Base schema for Insight"""
    account_id: Optional[int] = Field(None, description="Account ID (NULL for global insights)")
    insight_type: str = Field(..., description="Type of insight: mom_increase, yoy_decrease, etc.")
    severity: str = Field("info", description="Severity: info, success, warning, alert")
    title: str = Field(..., max_length=200, description="Short insight title")
    description: str = Field(..., description="Detailed insight description")
    insight_data: Optional[Dict[str, Any]] = Field(None, description="Additional data as JSON")
    priority: int = Field(5, ge=1, le=10, description="Display priority (1-10, higher = more important)")
    cooldown_hours: int = Field(24, ge=1, le=168, description="Hours before insight can be shown again")
    valid_until: Optional[datetime] = Field(None, description="Expiration date for time-sensitive insights")


class InsightCreate(InsightBase):
    """Schema for creating a new insight"""
    pass


class InsightResponse(InsightBase):
    """Schema for insight response"""
    id: int
    is_dismissed: bool
    dismissed_at: Optional[datetime]
    last_shown_at: Optional[datetime]
    show_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Schema for list of insights"""
    insights: List[InsightResponse]
    total: int
    active_count: int = Field(..., description="Number of non-dismissed insights")
    dismissed_count: int = Field(..., description="Number of dismissed insights")


class InsightDismiss(BaseModel):
    """Schema for dismissing an insight"""
    insight_id: int = Field(..., description="ID of insight to dismiss")


class InsightGenerationRequest(BaseModel):
    """Schema for requesting insight generation"""
    account_id: Optional[int] = Field(None, description="Account ID (NULL for global insights)")
    generation_types: Optional[List[str]] = Field(
        None,
        description="Types to generate: mom, yoy, savings_potential, full_analysis. NULL = all types"
    )
    force_regenerate: bool = Field(False, description="Force regeneration even if recently generated")


class InsightGenerationResponse(BaseModel):
    """Schema for insight generation response"""
    success: bool
    insights_generated: int
    insights_removed: int = Field(0, description="Number of expired insights removed")
    generation_type: str
    message: str


class InsightGenerationLogResponse(BaseModel):
    """Schema for insight generation log"""
    id: int
    account_id: Optional[int]
    generation_type: str
    insights_generated: int
    generated_at: datetime
    generation_params: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class InsightStatistics(BaseModel):
    """Schema for insight statistics"""
    total_insights: int
    active_insights: int
    dismissed_insights: int
    insights_by_type: Dict[str, int]
    insights_by_severity: Dict[str, int]
    insights_by_account: Dict[int, int] = Field(..., description="Count of insights per account_id")
    last_generation: Optional[datetime] = Field(None, description="Timestamp of last generation")
