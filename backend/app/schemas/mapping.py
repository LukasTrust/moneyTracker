"""
Mapping Schemas
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class MappingBase(BaseModel):
    """Base schema for Mapping"""
    csv_header: str = Field(..., min_length=1, max_length=100, description="CSV column name")
    standard_field: str = Field(..., min_length=1, max_length=50, description="Standard field name")


class MappingCreate(MappingBase):
    """Schema for creating a new mapping"""
    pass


class MappingResponse(MappingBase):
    """Schema for mapping response"""
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MappingsUpdate(BaseModel):
    """Schema for bulk updating mappings"""
    mappings: List[MappingBase] = Field(..., description="List of mappings to save")
