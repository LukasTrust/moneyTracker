"""DataRow Schemas
Audit reference: 05_backend_schemas.md - Pydantic v2 config
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataRowResponse(BaseModel):
    """Schema for data row response"""
    id: int
    account_id: int
    row_hash: str
    data: Dict[str, Any] = Field(..., description="Transaction data")
    category_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DataRowListResponse(BaseModel):
    """Schema for paginated data row list"""
    data: List[DataRowResponse]
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    limit: int = Field(..., description="Items per page")
