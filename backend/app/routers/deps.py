"""
Dependencies for FastAPI routes.

This module provides reusable dependencies for route handlers,
reducing code duplication and ensuring consistent behavior.
"""

from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models.account import Account


def get_account_by_id(
    account_id: Annotated[int, Path(description="The ID of the account")],
    db: Session = Depends(get_db)
) -> Account:
    """
    Get an account by ID and verify it exists.
    
    This dependency can be used in route handlers to automatically
    validate that an account exists before processing the request.
    
    Args:
        account_id: The ID of the account to retrieve
        db: Database session
        
    Returns:
        The Account object if found
        
    Raises:
        HTTPException: 404 error if account not found
        
    Example:
        @router.get("/accounts/{account_id}/data")
        def get_data(
            account: Account = Depends(get_account_by_id),
            db: Session = Depends(get_db)
        ):
            # account is guaranteed to exist here
            return account.data
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    return account


def verify_account_exists(account_id: int, db: Session) -> Account:
    """
    Helper function to verify an account exists.
    
    Use this when you can't use the Depends() mechanism,
    such as with Form parameters.
    
    Args:
        account_id: The ID of the account to verify
        db: Database session
        
    Returns:
        The Account object if found
        
    Raises:
        HTTPException: 404 error if account not found
        
    Example:
        account = verify_account_exists(account_id, db)
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    return account
