"""
Account Router - CRUD operations for accounts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.account import Account
from app.routers.deps import get_account_by_id
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse
)

router = APIRouter()


@router.get("", response_model=AccountListResponse)
def get_accounts(db: Session = Depends(get_db)):
    """
    Get all accounts
    
    Returns:
        List of all accounts
    """
    accounts = db.query(Account).all()
    return {"accounts": accounts}


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account: Account = Depends(get_account_by_id)):
    """
    Get a specific account by ID
    
    Args:
        account_id: Account ID
        
    Returns:
        Account details
        
    Raises:
        404: Account not found
    """
    return account


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account_data: AccountCreate, db: Session = Depends(get_db)):
    """
    Create a new account
    
    Args:
        account_data: Account creation data
        
    Returns:
        Created account
    """
    # Create new account
    new_account = Account(**account_data.model_dump())
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_data: AccountUpdate,
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Update an existing account
    
    Args:
        account_id: Account ID
        account_data: Updated account data
        
    Returns:
        Updated account
        
    Raises:
        404: Account not found
    """
    # Update fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Delete an account
    
    Args:
        account_id: Account ID
        
    Raises:
        404: Account not found
        
    Note:
        This will also delete all associated mappings and data rows
        due to CASCADE delete configuration
    """
    db.delete(account)
    db.commit()
    
    return None
