"""
Mapping Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
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
    
    model_config = ConfigDict(from_attributes=True)


class MappingsUpdate(BaseModel):
    """Schema for bulk updating mappings"""
    mappings: List[MappingBase] = Field(..., description="List of mappings to save")


class MappingValidationResult(BaseModel):
    """Result of validating a single mapping field"""
    field: str = Field(..., description="Standard field name (date, amount, etc.)")
    csv_header: str = Field(..., description="Expected CSV header from saved mapping")
    is_valid: bool = Field(..., description="Whether the CSV header exists in uploaded file")
    suggested_header: str | None = Field(None, description="Suggested alternative if original not found")


class MappingValidationResponse(BaseModel):
    """Response for mapping validation"""
    is_valid: bool = Field(..., description="Whether all mappings are valid")
    has_saved_mapping: bool = Field(..., description="Whether account has saved mappings")
    validation_results: List[MappingValidationResult] = Field(default_factory=list, description="Validation details per field")
    missing_headers: List[str] = Field(default_factory=list, description="CSV headers from mapping that are missing in file")
    available_headers: List[str] = Field(default_factory=list, description="Available headers in uploaded CSV")
