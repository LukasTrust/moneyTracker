"""
Import History Schemas - Pydantic models for Import History
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ImportHistoryBase(BaseModel):
    """Base schema for ImportHistory"""
    account_id: int = Field(..., description="Account ID this import belongs to")
    filename: str = Field(..., max_length=255, description="Original filename")
    row_count: int = Field(default=0, ge=0, description="Total rows in CSV")
    rows_inserted: int = Field(default=0, ge=0, description="Rows successfully inserted")
    rows_duplicated: int = Field(default=0, ge=0, description="Duplicate rows skipped")
    status: str = Field(default="success", pattern="^(success|partial|failed)$", description="Import status")
    error_message: Optional[str] = Field(None, description="Error details if failed")


class ImportHistoryCreate(ImportHistoryBase):
    """Schema for creating a new import history record"""
    file_hash: Optional[str] = Field(None, max_length=64, description="SHA256 hash of file content")


class ImportHistoryUpdate(BaseModel):
    """Schema for updating an import history record"""
    status: Optional[str] = Field(None, pattern="^(success|partial|failed)$")
    error_message: Optional[str] = None
    rows_inserted: Optional[int] = Field(None, ge=0)
    rows_duplicated: Optional[int] = Field(None, ge=0)


class ImportHistoryResponse(ImportHistoryBase):
    """Schema for import history response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_hash: Optional[str] = None
    uploaded_at: datetime
    created_at: datetime
    
    # Optional account name (from join)
    account_name: Optional[str] = None


class ImportHistoryStats(BaseModel):
    """Extended statistics for an import"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    account_name: Optional[str] = None
    filename: str
    uploaded_at: datetime
    row_count: int
    rows_inserted: int
    rows_duplicated: int
    status: str
    current_row_count: int = Field(..., description="Current number of rows (after potential deletions)")
    total_expenses: Decimal = Field(default=Decimal("0"), description="Sum of negative amounts")
    total_income: Decimal = Field(default=Decimal("0"), description="Sum of positive amounts")
    can_rollback: bool = Field(..., description="Whether rollback is possible")


class ImportHistoryListResponse(BaseModel):
    """Response for listing import history"""
    imports: list[ImportHistoryStats]
    total: int


class ImportRollbackRequest(BaseModel):
    """Request to rollback an import"""
    import_id: int = Field(..., description="Import ID to rollback")
    confirm: bool = Field(default=False, description="Confirmation flag")


class ImportRollbackResponse(BaseModel):
    """Response after rollback"""
    success: bool
    import_id: int
    rows_deleted: int
    message: str
