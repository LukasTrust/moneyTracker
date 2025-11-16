"""
Recipients Router - Manage recipients/senders
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional

from app.database import get_db
from app.models.recipient import Recipient
from app.models.data_row import DataRow
from app.services.recipient_matcher import RecipientMatcher
from pydantic import BaseModel

router = APIRouter()


# Schemas
class RecipientBase(BaseModel):
    name: str
    aliases: Optional[List[str]] = []


class RecipientResponse(BaseModel):
    id: int
    name: str
    normalized_name: str
    aliases: List[str]
    transaction_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class RecipientUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None


class MergeRequest(BaseModel):
    keep_id: int
    merge_id: int


class RecipientSuggestion(BaseModel):
    recipient: RecipientResponse
    similarity: float


@router.get("/", response_model=List[RecipientResponse])
async def get_recipients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    sort_by: str = Query("transaction_count", regex="^(name|transaction_count|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all recipients with pagination and search
    
    Args:
        limit: Max results (default 100)
        offset: Pagination offset (default 0)
        search: Search by name (optional)
        sort_by: Sort field (name, transaction_count, created_at)
        sort_order: Sort order (asc, desc)
    
    Returns:
        List of recipients
    """
    query = db.query(Recipient)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Recipient.name.ilike(search_term)) |
            (Recipient.normalized_name.ilike(search_term)) |
            (Recipient.aliases.ilike(search_term))
        )
    
    # Sorting
    sort_column = getattr(Recipient, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    recipients = query.offset(offset).limit(limit).all()
    
    return [recipient.to_dict() for recipient in recipients]


@router.get("/top", response_model=List[RecipientResponse])
async def get_top_recipients(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get top recipients by transaction count
    
    Args:
        limit: Max results (default 10)
        
    Returns:
        List of top recipients
    """
    recipients = db.query(Recipient).order_by(
        desc(Recipient.transaction_count)
    ).limit(limit).all()
    
    return [recipient.to_dict() for recipient in recipients]


@router.get("/{recipient_id}", response_model=RecipientResponse)
async def get_recipient(
    recipient_id: int,
    db: Session = Depends(get_db)
):
    """
    Get recipient by ID
    
    Args:
        recipient_id: Recipient ID
        
    Returns:
        Recipient details
        
    Raises:
        404: Recipient not found
    """
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID {recipient_id} not found"
        )
    
    return recipient.to_dict()


@router.put("/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    recipient_id: int,
    update: RecipientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update recipient (name and/or aliases)
    
    Args:
        recipient_id: Recipient ID
        update: Update data
        
    Returns:
        Updated recipient
        
    Raises:
        404: Recipient not found
    """
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID {recipient_id} not found"
        )
    
    # Update name
    if update.name:
        recipient.name = update.name.strip()
        recipient.normalized_name = Recipient.normalize_name(update.name)
    
    # Update aliases
    if update.aliases is not None:
        recipient.aliases = ','.join([a.strip() for a in update.aliases if a.strip()])
    
    db.commit()
    db.refresh(recipient)
    
    return recipient.to_dict()


@router.delete("/{recipient_id}")
async def delete_recipient(
    recipient_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete recipient (sets recipient_id to NULL in data_rows)
    
    Args:
        recipient_id: Recipient ID
        
    Returns:
        Success message
        
    Raises:
        404: Recipient not found
    """
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID {recipient_id} not found"
        )
    
    # Unlink from data_rows
    db.query(DataRow).filter(DataRow.recipient_id == recipient_id).update(
        {"recipient_id": None}
    )
    
    # Delete recipient
    db.delete(recipient)
    db.commit()
    
    return {"message": f"Recipient '{recipient.name}' deleted successfully"}


@router.post("/merge")
async def merge_recipients(
    merge_request: MergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merge two recipients (combine transactions and aliases)
    
    Args:
        merge_request: IDs of recipients to merge
        
    Returns:
        Updated recipient
        
    Raises:
        400: Invalid merge request
        404: Recipient not found
    """
    matcher = RecipientMatcher(db)
    success = matcher.merge_recipients(
        keep_id=merge_request.keep_id,
        merge_id=merge_request.merge_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to merge recipients. Check that both IDs exist and are different."
        )
    
    # Get updated recipient
    recipient = db.query(Recipient).filter(Recipient.id == merge_request.keep_id).first()
    
    return {
        "message": "Recipients merged successfully",
        "recipient": recipient.to_dict()
    }


@router.get("/{recipient_id}/suggestions", response_model=List[RecipientSuggestion])
async def get_merge_suggestions(
    recipient_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get similar recipients for potential merging
    
    Args:
        recipient_id: Recipient ID
        limit: Max suggestions (default 5)
        
    Returns:
        List of similar recipients with similarity scores
        
    Raises:
        404: Recipient not found
    """
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID {recipient_id} not found"
        )
    
    matcher = RecipientMatcher(db)
    suggestions = matcher.get_recipient_suggestions(recipient.name, limit=limit + 1)
    
    # Filter out the recipient itself
    suggestions = [
        {
            "recipient": r.to_dict(),
            "similarity": score
        }
        for r, score in suggestions
        if r.id != recipient_id
    ][:limit]
    
    return suggestions


@router.post("/update-counts")
async def update_all_transaction_counts(db: Session = Depends(get_db)):
    """
    Recalculate transaction counts for all recipients
    
    Returns:
        Number of recipients updated
    """
    recipients = db.query(Recipient).all()
    
    for recipient in recipients:
        count = db.query(DataRow).filter(
            DataRow.recipient_id == recipient.id
        ).count()
        recipient.transaction_count = count
    
    db.commit()
    
    return {
        "message": "Transaction counts updated",
        "updated_count": len(recipients)
    }
