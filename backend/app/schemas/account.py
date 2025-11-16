"""
Account Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class AccountBase(BaseModel):
    """Base schema for Account"""
    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    bank_name: Optional[str] = Field(None, max_length=100, description="Bank name")
    account_number: Optional[str] = Field(None, max_length=50, description="Account number")
    currency: str = Field(default='EUR', min_length=3, max_length=3, description="Account currency (ISO 4217 code)")
    description: Optional[str] = Field(None, description="Account description")
    initial_balance: Decimal = Field(default=Decimal("0.0"), description="Starting balance of the account")


class AccountCreate(AccountBase):
    """Schema for creating a new account"""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = None
    initial_balance: Optional[Decimal] = None


class AccountResponse(AccountBase):
    """Schema for account response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """Schema for list of accounts"""
    accounts: List[AccountResponse]
