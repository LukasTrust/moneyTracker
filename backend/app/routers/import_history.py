"""
Import History Router - API endpoints for import tracking and rollback
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.account import Account
from app.schemas.import_history import (
    ImportHistoryListResponse,
    ImportHistoryStats,
    ImportRollbackRequest,
    ImportRollbackResponse
)
from app.services.import_history_service import ImportHistoryService

router = APIRouter()


@router.get("/history", response_model=ImportHistoryListResponse)
async def get_import_history(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get import history with statistics
    
    Returns list of all imports with current statistics (row counts, totals).
    Can be filtered by account_id.
    
    Args:
        account_id: Optional account filter
        limit: Maximum records to return
        offset: Pagination offset
        db: Database session
        
    Returns:
        List of import history records with statistics
    """
    try:
        imports, total = ImportHistoryService.get_import_history_with_stats(
            db=db,
            account_id=account_id,
            limit=limit,
            offset=offset
        )
        
        return ImportHistoryListResponse(
            imports=imports,
            total=total
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching import history: {str(e)}"
        )


@router.get("/history/{import_id}", response_model=ImportHistoryStats)
async def get_import_details(
    import_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific import
    
    Args:
        import_id: Import record ID
        db: Database session
        
    Returns:
        Import statistics with current data
        
    Raises:
        404: Import not found
    """
    try:
        # Use the stats function to get detailed info
        imports, _ = ImportHistoryService.get_import_history_with_stats(
            db=db,
            account_id=None,
            limit=1,
            offset=0
        )
        
        # Filter by ID (since we can't filter in the service directly)
        import_stats = next((imp for imp in imports if imp.id == import_id), None)
        
        if not import_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import {import_id} not found"
            )
        
        return import_stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching import details: {str(e)}"
        )


@router.post("/rollback", response_model=ImportRollbackResponse)
async def rollback_import(
    request: ImportRollbackRequest,
    db: Session = Depends(get_db)
):
    """
    Rollback an import by deleting all associated data rows
    
    This will permanently delete all transactions imported in this session.
    Use with caution!
    
    Args:
        request: Rollback request with import_id and confirmation
        db: Database session
        
    Returns:
        Rollback result with deletion count
        
    Raises:
        400: Invalid request or import not found
        404: Import not found
    """
    # Check confirmation
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rollback must be confirmed (set confirm=true)"
        )
    
    try:
        result = ImportHistoryService.rollback_import(
            db=db,
            import_id=request.import_id
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during rollback: {str(e)}"
        )


@router.delete("/history/{import_id}")
async def delete_import_history(
    import_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an import history record
    
    Note: This only deletes the import record metadata, not the actual data rows.
    Use rollback endpoint to delete data rows.
    
    Args:
        import_id: Import record ID to delete
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        404: Import not found
    """
    import_record = ImportHistoryService.get_import_by_id(db, import_id)
    
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {import_id} not found"
        )
    
    try:
        db.delete(import_record)
        db.commit()
        
        return {
            "success": True,
            "message": f"Import history record {import_id} deleted"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting import record: {str(e)}"
        )
