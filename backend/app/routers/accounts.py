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
    # Delete dependent data in correct order to avoid foreign key constraint violations
    # Some relationships are handled by CASCADE delete in the database, but we need
    # to explicitly handle those without CASCADE or with complex dependencies.
    
    try:
        # 1. Delete recurring_transaction_links (via recurring_transactions)
        db.execute(text("""
            DELETE FROM recurring_transaction_links
            WHERE recurring_transaction_id IN (
                SELECT id FROM recurring_transactions WHERE account_id = :aid
            )
        """), {"aid": account.id})

        # 2. Delete recurring_transactions for this account
        db.execute(text("DELETE FROM recurring_transactions WHERE account_id = :aid"), {"aid": account.id})
        
        # 3. Delete transfers that involve data_rows from this account
        #    Transfers link two data_rows, so we need to delete transfers where
        #    either from_transaction or to_transaction belongs to this account
        db.execute(text("""
            DELETE FROM transfers
            WHERE from_transaction_id IN (
                SELECT id FROM data_rows WHERE account_id = :aid
            )
            OR to_transaction_id IN (
                SELECT id FROM data_rows WHERE account_id = :aid
            )
        """), {"aid": account.id})
        
        # 4. Delete background_jobs for this account
        db.execute(text("DELETE FROM background_jobs WHERE account_id = :aid"), {"aid": account.id})
        
    except Exception:
        logger.exception("Failed to delete dependent data for account %s", account.id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account due to database constraint violations"
        )

    # Finally delete the account itself
    # The following will be CASCADE deleted by the database:
    # - mappings (ON DELETE CASCADE)
    # - data_rows (ON DELETE CASCADE)
    # - import_history (ON DELETE CASCADE)
    # - insights (ON DELETE CASCADE)
    # - insight_generation_logs (ON DELETE CASCADE)
    db.delete(account)
    db.commit()
    logger.info("Account deleted successfully", extra={"account_id": account.id})

    return None
