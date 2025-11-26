"""
Mapping Router - Manage CSV header mappings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.mapping import Mapping
from app.models.account import Account
from app.routers.deps import get_account_by_id
from app.schemas.mapping import (
    MappingResponse,
    MappingsUpdate
)
from app.utils.pagination import paginate_query
from app.config import settings

router = APIRouter()


@router.get("/{account_id}/mappings", response_model=List[MappingResponse])
def get_mappings(
    account: Account = Depends(get_account_by_id),
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all mappings for an account
    
    Args:
        account_id: Account ID
        
    Returns:
        List of mappings
        
    Raises:
        404: Account not found
    """
    query = db.query(Mapping).filter(Mapping.account_id == account.id).order_by(Mapping.id)
    items, total, eff_limit, eff_offset, pages = paginate_query(query, limit, offset)
    return items


@router.post("/{account_id}/mappings", response_model=List[MappingResponse])
def save_mappings(
    mappings_data: MappingsUpdate,
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Save/update mappings for an account (replaces existing mappings)
    
    Args:
        account_id: Account ID
        mappings_data: List of mappings to save
        
    Returns:
        Saved mappings
        
    Raises:
        404: Account not found
    """
    # Delete existing mappings
    db.query(Mapping).filter(Mapping.account_id == account.id).delete()
    
    # Create new mappings
    new_mappings = []
    for mapping_data in mappings_data.mappings:
        new_mapping = Mapping(
            account_id=account.id,
            csv_header=mapping_data.csv_header,
            standard_field=mapping_data.standard_field
        )
        db.add(new_mapping)
        new_mappings.append(new_mapping)
    
    db.commit()
    
    # Refresh all new mappings
    for mapping in new_mappings:
        db.refresh(mapping)
    
    return new_mappings


@router.delete("/{account_id}/mappings", status_code=status.HTTP_204_NO_CONTENT)
def delete_mappings(
    account: Account = Depends(get_account_by_id),
    db: Session = Depends(get_db)
):
    """
    Delete all mappings for an account
    
    Args:
        account_id: Account ID
        
    Raises:
        404: Account not found
    """
    # Delete all mappings
    db.query(Mapping).filter(Mapping.account_id == account.id).delete()
    db.commit()
    
    return None
