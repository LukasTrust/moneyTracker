"""CSV row validation schemas
Audit reference: 05_backend_schemas.md - Use Decimal for money
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class TransactionRow(BaseModel):
    """Simple transaction row schema used before persisting.

    Note: date is accepted as string here to avoid pydantic import-time
    complexities; parsing/validation is performed in the import logic.
    Amount uses Decimal for precision.
    """
    date: str = Field(..., description="Transaction date (string)")
    amount: Decimal = Field(..., description="Transaction amount (Decimal for precision)")
    recipient: str = Field(..., min_length=1, max_length=200, description="Recipient or sender")
    purpose: Optional[str] = Field(None, max_length=1000, description="Purpose / booking text")
    saldo: Optional[Decimal] = Field(None, description="Account balance at transaction time (optional)")
