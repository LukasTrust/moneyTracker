"""
Transfer Router - API endpoints for inter-account transfers
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional

from app.database import get_db
from app.models import Transfer, DataRow, Account
from app.schemas.transfer import (
    TransferCreate,
    TransferUpdate,
    TransferResponse,
    TransferWithDetails,
    TransferCandidate,
    TransferDetectionRequest,
    TransferDetectionResponse,
    TransferStats
)
from app.services.transfer_matcher import TransferMatcher
from app.config import settings
from app.utils import get_logger

logger = get_logger("app.routers.transfers")

router = APIRouter()


@router.get("/transfers", response_model=List[TransferResponse])
def get_all_transfers(
    account_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_details: bool = False,
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all transfers, optionally filtered by account and date range.
    
    Args:
        account_id: Filter by account (shows transfers involving this account)
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
        include_details: Include full transaction details
    """
    query = db.query(Transfer)
    
    # Filter by account
    if account_id:
        # Get transfers where either transaction belongs to the account
        from_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        to_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        
        query = query.filter(
            or_(
                Transfer.from_transaction_id.in_(from_tx_ids),
                Transfer.to_transaction_id.in_(to_tx_ids)
            )
        )
    
    # Filter by date range
    if date_from:
        query = query.filter(Transfer.transfer_date >= date_from)
    if date_to:
        query = query.filter(Transfer.transfer_date <= date_to)
    
    transfers = query.order_by(Transfer.transfer_date.desc()).offset(offset).limit(min(limit, settings.MAX_LIMIT)).all()
    
    if not include_details:
        return transfers
    
    # Add transaction details
    result = []
    for transfer in transfers:
        from_tx = db.query(DataRow).filter(DataRow.id == transfer.from_transaction_id).first()
        to_tx = db.query(DataRow).filter(DataRow.id == transfer.to_transaction_id).first()
        
        from_account = db.query(Account).filter(Account.id == from_tx.account_id).first()
        to_account = db.query(Account).filter(Account.id == to_tx.account_id).first()
        
        transfer_dict = TransferResponse.from_orm(transfer).dict()
        transfer_dict['from_transaction'] = {
            'id': from_tx.id,
            'date': from_tx.transaction_date.isoformat(),
            'amount': float(from_tx.amount),
            'recipient': from_tx.recipient,
            'purpose': from_tx.purpose
        }
        transfer_dict['to_transaction'] = {
            'id': to_tx.id,
            'date': to_tx.transaction_date.isoformat(),
            'amount': float(to_tx.amount),
            'recipient': to_tx.recipient,
            'purpose': to_tx.purpose
        }
        transfer_dict['from_account_name'] = from_account.name if from_account else None
        transfer_dict['to_account_name'] = to_account.name if to_account else None
        
        result.append(transfer_dict)
    
    return result


@router.get("/transfers/{transfer_id}", response_model=TransferWithDetails)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific transfer by ID with full details.
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer {transfer_id} not found"
        )
    
    # Add transaction details
    from_tx = db.query(DataRow).filter(DataRow.id == transfer.from_transaction_id).first()
    to_tx = db.query(DataRow).filter(DataRow.id == transfer.to_transaction_id).first()
    
    from_account = db.query(Account).filter(Account.id == from_tx.account_id).first()
    to_account = db.query(Account).filter(Account.id == to_tx.account_id).first()
    
    transfer_dict = TransferResponse.from_orm(transfer).dict()
    transfer_dict['from_transaction'] = {
        'id': from_tx.id,
        'date': from_tx.transaction_date.isoformat(),
        'amount': float(from_tx.amount),
        'recipient': from_tx.recipient,
        'purpose': from_tx.purpose
    }
    transfer_dict['to_transaction'] = {
        'id': to_tx.id,
        'date': to_tx.transaction_date.isoformat(),
        'amount': float(to_tx.amount),
        'recipient': to_tx.recipient,
        'purpose': to_tx.purpose
    }
    transfer_dict['from_account_name'] = from_account.name if from_account else None
    transfer_dict['to_account_name'] = to_account.name if to_account else None
    
    return transfer_dict


@router.post("/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    transfer: TransferCreate,
    db: Session = Depends(get_db)
):
    """
    Manually create a transfer link between two transactions.
    """
    matcher = TransferMatcher(db)
    
    try:
        new_transfer = matcher.create_transfer(
            from_transaction_id=transfer.from_transaction_id,
            to_transaction_id=transfer.to_transaction_id,
            is_auto_detected=False,
            notes=transfer.notes
        )
        logger.info(
            "Transfer created",
            extra={
                "transfer_id": getattr(new_transfer, "id", None),
                "from_transaction_id": getattr(new_transfer, "from_transaction_id", None),
                "to_transaction_id": getattr(new_transfer, "to_transaction_id", None),
                "is_auto_detected": getattr(new_transfer, "is_auto_detected", False),
            },
        )
        return new_transfer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/transfers/{transfer_id}", response_model=TransferResponse)
def update_transfer(
    transfer_id: int,
    transfer_update: TransferUpdate,
    db: Session = Depends(get_db)
):
    """
    Update transfer notes.
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer {transfer_id} not found"
        )
    
    if transfer_update.notes is not None:
        transfer.notes = transfer_update.notes
    
    db.commit()
    db.refresh(transfer)
    logger.info("Transfer updated", extra={"transfer_id": transfer.id, "notes": transfer.notes})

    return transfer


@router.delete("/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a transfer link (unlinking the two transactions).
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer {transfer_id} not found"
        )
    
    db.delete(transfer)
    db.commit()
    logger.info("Transfer deleted", extra={"transfer_id": transfer_id})

    return None


@router.post("/transfers/detect", response_model=TransferDetectionResponse)
def detect_transfers(
    request: TransferDetectionRequest,
    db: Session = Depends(get_db)
):
    """
    Auto-detect potential transfers based on matching criteria.
    
    Args:
        request: Detection parameters (account filters, date range, confidence threshold)
    """
    matcher = TransferMatcher(db)
    
    # Find candidates
    candidates = matcher.find_transfer_candidates(
        account_ids=request.account_ids,
        date_from=request.date_from,
        date_to=request.date_to,
        min_confidence=float(request.min_confidence) if request.min_confidence else 0.7,
        exclude_existing=True
    )
    
    auto_created = 0
    
    # Auto-create if requested
    if request.auto_create:
        for candidate in candidates:
            try:
                matcher.create_transfer(
                    from_transaction_id=candidate['from_transaction_id'],
                    to_transaction_id=candidate['to_transaction_id'],
                    is_auto_detected=True,
                    confidence_score=candidate['confidence_score'],
                    notes=candidate['match_reason']
                )
                auto_created += 1
            except ValueError:
                # Skip if validation fails
                continue

    logger.info("Transfer detection completed", extra={"total_found": len(candidates), "auto_created": auto_created})

    return TransferDetectionResponse(
        candidates=candidates,
        total_found=len(candidates),
        auto_created=auto_created
    )


@router.get("/transfers/stats", response_model=TransferStats)
def get_transfer_stats(
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics about transfers.
    """
    query = db.query(Transfer)
    
    # Filter by account if specified
    if account_id:
        from_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        to_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        
        query = query.filter(
            or_(
                Transfer.from_transaction_id.in_(from_tx_ids),
                Transfer.to_transaction_id.in_(to_tx_ids)
            )
        )
    
    from sqlalchemy import func

    total_transfers = query.count()
    auto_detected = query.filter(Transfer.is_auto_detected == True).count()
    manual = total_transfers - auto_detected

    total_amount = db.query(func.sum(Transfer.amount)).select_from(Transfer)
    # Reapply same filters for amount and date range
    if account_id:
        from_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        to_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        total_amount = total_amount.filter(
            or_(
                Transfer.from_transaction_id.in_(from_tx_ids),
                Transfer.to_transaction_id.in_(to_tx_ids),
            )
        )
    total_amount = total_amount.scalar() or 0

    # Date range via aggregates
    min_max = db.query(func.min(Transfer.transfer_date), func.max(Transfer.transfer_date))
    if account_id:
        from_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        to_tx_ids = db.query(DataRow.id).filter(DataRow.account_id == account_id).subquery()
        min_max = min_max.filter(
            or_(
                Transfer.from_transaction_id.in_(from_tx_ids),
                Transfer.to_transaction_id.in_(to_tx_ids),
            )
        )
    min_date, max_date = min_max.one()
    date_range = None
    if min_date and max_date:
        date_range = {'from': min_date.isoformat(), 'to': max_date.isoformat()}
    
    return TransferStats(
        total_transfers=total_transfers,
        auto_detected=auto_detected,
        manual=manual,
        total_amount=total_amount,
        date_range=date_range
    )


@router.get("/transactions/{transaction_id}/transfer", response_model=Optional[TransferResponse])
def get_transfer_for_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a transaction is part of a transfer.
    """
    matcher = TransferMatcher(db)
    transfer = matcher.get_transfer_for_transaction(transaction_id)
    
    if not transfer:
        return None
    
    return transfer
