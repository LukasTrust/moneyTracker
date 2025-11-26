"""
CSV row validation schemas
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class TransactionRow(BaseModel):
    """Simple transaction row schema used before persisting.

    Note: date is accepted as string here to avoid pydantic import-time
    complexities; parsing/validation is performed in the import logic.
    """
    date: str = Field(..., description="Transaction date (string)")
    amount: float = Field(..., description="Transaction amount")
    recipient: str = Field(..., min_length=1, max_length=200, description="Recipient or sender")
    purpose: Optional[str] = Field(None, max_length=1000, description="Purpose / booking text")
