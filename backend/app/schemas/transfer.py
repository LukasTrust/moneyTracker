"""
Transfer Schemas - Pydantic models for API requests/responses
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class TransferBase(BaseModel):
    """Base schema for transfer data"""
    amount: Decimal = Field(..., gt=0, description="Transfer amount (always positive)")
    transfer_date: date = Field(..., description="Date of the transfer")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about this transfer")


class TransferCreate(TransferBase):
    """Schema for creating a new transfer (manual linking)"""
    from_transaction_id: int = Field(..., description="Transaction ID with negative amount (money leaving)")
    to_transaction_id: int = Field(..., description="Transaction ID with positive amount (money entering)")
    
    @field_validator('from_transaction_id', 'to_transaction_id')
    @classmethod
    def validate_transaction_ids(cls, v):
        if v <= 0:
            raise ValueError('Transaction ID must be positive')
        return v


class TransferUpdate(BaseModel):
    """Schema for updating a transfer"""
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about this transfer")


class TransferResponse(TransferBase):
    """Schema for transfer response"""
    id: int
    from_transaction_id: int
    to_transaction_id: int
    is_auto_detected: bool = Field(..., description="Whether this transfer was automatically detected")
    confidence_score: Optional[Decimal] = Field(None, description="Confidence score for auto-detection (0.00 to 1.00)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransferWithDetails(TransferResponse):
    """Schema for transfer with full transaction details"""
    from_transaction: Optional[dict] = Field(None, description="Full details of the source transaction")
    to_transaction: Optional[dict] = Field(None, description="Full details of the destination transaction")
    from_account_name: Optional[str] = Field(None, description="Name of the source account")
    to_account_name: Optional[str] = Field(None, description="Name of the destination account")


class TransferCandidate(BaseModel):
    """Schema for potential transfer matches found by auto-detection"""
    from_transaction_id: int
    to_transaction_id: int
    from_transaction: dict = Field(..., description="Details of the source transaction")
    to_transaction: dict = Field(..., description="Details of the destination transaction")
    amount: Decimal = Field(..., description="Transfer amount")
    transfer_date: date = Field(..., description="Date of the transfer")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Confidence score (0.00 to 1.00)")
    match_reason: str = Field(..., description="Explanation of why these transactions match")


class TransferDetectionRequest(BaseModel):
    """Schema for requesting transfer auto-detection"""
    account_ids: Optional[list[int]] = Field(None, description="Limit detection to specific accounts (optional)")
    date_from: Optional[date] = Field(None, description="Start date for detection range")
    date_to: Optional[date] = Field(None, description="End date for detection range")
    min_confidence: Optional[Decimal] = Field(0.7, ge=0, le=1, description="Minimum confidence score")
    auto_create: bool = Field(False, description="Automatically create transfers for high-confidence matches")


class TransferDetectionResponse(BaseModel):
    """Schema for transfer detection results"""
    candidates: list[TransferCandidate] = Field(..., description="List of potential transfer matches")
    total_found: int = Field(..., description="Total number of candidates found")
    auto_created: int = Field(0, description="Number of transfers automatically created")


class TransferStats(BaseModel):
    """Schema for transfer statistics"""
    total_transfers: int = Field(..., description="Total number of transfers")
    auto_detected: int = Field(..., description="Number of auto-detected transfers")
    manual: int = Field(..., description="Number of manually created transfers")
    total_amount: Decimal = Field(..., description="Total amount transferred")
    date_range: Optional[dict] = Field(None, description="Date range of transfers")
