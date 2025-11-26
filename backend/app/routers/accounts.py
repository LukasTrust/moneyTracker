"""
Account Router - CRUD operations for accounts
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from app.utils.pagination import paginate_query
from app.config import settings
from app.utils import get_logger
from app.models.recurring_transaction import RecurringTransaction
from sqlalchemy import text

logger = get_logger("app.routers.accounts")

router = APIRouter()


@router.get("", response_model=AccountListResponse)
def get_accounts(
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get all accounts
    
    Returns:
        List of all accounts
    """
    # Support direct calls in unit tests where `db` may be passed positionally
    # (e.g. get_accounts(mock_db)). If `limit` is actually a DB session, shift values.
    if hasattr(limit, 'query'):
        db = limit
        limit = settings.DEFAULT_LIMIT
        offset = 0

    # Coerce Query defaults (FastAPI's Query objects) to ints when called directly
    if not isinstance(limit, int):
        limit = settings.DEFAULT_LIMIT
    if not isinstance(offset, int):
        offset = 0

    # If called directly in unit tests (positional db) shift values and keep compatibility
    if hasattr(limit, 'query'):
        db = limit
        limit = settings.DEFAULT_LIMIT
        offset = 0

    # Coerce Query defaults (FastAPI's Query objects) to ints when called directly
    if not isinstance(limit, int):
        limit = settings.DEFAULT_LIMIT
    if not isinstance(offset, int):
        offset = 0

    # Build base query and always use paginate_query to produce a consistent
    # response shape that matches `AccountListResponse` (includes pagination fields).
    query = db.query(Account).order_by(Account.id)

    items, total, eff_limit, eff_offset, pages = paginate_query(query, limit, offset)
    page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1
    return {"accounts": items, "total": total, "limit": eff_limit, "offset": eff_offset, "pages": pages, "page": page}


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
    logger.info("Account created", extra={"account_id": new_account.id, "account_name": new_account.name})

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
    logger.info("Account updated", extra={"account_id": account.id, "updated_fields": list(update_data.keys())})

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
    # Delete dependent recurring_transaction_links and recurring_transactions
    # using direct SQL to avoid ORM flush/update behaviour that can attempt
    # to set NOT NULL FKs to NULL and cause IntegrityError. The database
    # FK constraints already declare ON DELETE CASCADE for these relations,
    # but using explicit SQL here ensures a safe, ordered cleanup across
    # different DB backends and avoids ORM-generated UPDATE statements.
    try:
        # Remove links first (safe even if none exist)
        db.execute(text("""
            DELETE FROM recurring_transaction_links
            WHERE recurring_transaction_id IN (
                SELECT id FROM recurring_transactions WHERE account_id = :aid
            )
        """), {"aid": account.id})

        # Remove recurring transactions for this account
        db.execute(text("DELETE FROM recurring_transactions WHERE account_id = :aid"), {"aid": account.id})
    except Exception:
        logger.exception("Failed to delete recurring transactions/links for account %s", account.id)

    # Finally delete the account itself and commit
    db.delete(account)
    db.commit()
    logger.info("Account deleted", extra={"account_id": account.id})

    return None
