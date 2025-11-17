"""
Import History Service - Business logic for import tracking and rollback
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Tuple
from datetime import datetime
import hashlib

from app.models.import_history import ImportHistory
from app.models.data_row import DataRow
from app.models.account import Account
from app.schemas.import_history import (
    ImportHistoryStats,
    ImportRollbackResponse
)
from app.utils import get_logger


# Module logger
logger = get_logger("app.services.import_history")


class ImportHistoryService:
    """Service for managing import history and rollbacks"""
    
    @staticmethod
    def create_import_record(
        db: Session,
        account_id: int,
        filename: str,
        file_content: Optional[bytes] = None
    ) -> ImportHistory:
        """
        Create a new import history record
        
        Args:
            db: Database session
            account_id: Target account ID
            filename: Original filename
            file_content: Optional file content for hash generation
            
        Returns:
            Created ImportHistory instance
        """
        file_hash = None
        if file_content:
            file_hash = hashlib.sha256(file_content).hexdigest()
        
        import_record = ImportHistory(
            account_id=account_id,
            filename=filename,
            file_hash=file_hash,
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='success'
        )
        
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        logger.info("Created import record %s for account %s (file=%s)", import_record.id, account_id, filename)

        return import_record
    
    @staticmethod
    def update_import_stats(
        db: Session,
        import_id: int,
        row_count: int,
        rows_inserted: int,
        rows_duplicated: int,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> ImportHistory:
        """
        Update import statistics after processing
        
        Args:
            db: Database session
            import_id: Import record ID
            row_count: Total rows in CSV
            rows_inserted: Number of rows successfully inserted
            rows_duplicated: Number of duplicate rows skipped
            status: Import status (success, partial, failed)
            error_message: Optional error details
            
        Returns:
            Updated ImportHistory instance
        """
        import_record = db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
        
        if not import_record:
            raise ValueError(f"Import record {import_id} not found")
        
        import_record.row_count = row_count
        import_record.rows_inserted = rows_inserted
        import_record.rows_duplicated = rows_duplicated
        import_record.status = status
        import_record.error_message = error_message
        
        db.commit()
        db.refresh(import_record)
        logger.info("Updated import record %s: rows=%s inserted=%s duplicated=%s status=%s", import_id, row_count, rows_inserted, rows_duplicated, status)

        return import_record
    
    @staticmethod
    def get_import_history_with_stats(
        db: Session,
        account_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ImportHistoryStats], int]:
        """
        Get import history with statistics
        
        Args:
            db: Database session
            account_id: Optional filter by account
            limit: Maximum number of records
            offset: Pagination offset
            
        Returns:
            Tuple of (import history list with stats, total count)
        """
        # Build base query
        base_query = db.query(ImportHistory)
        
        # Apply account filter if provided
        if account_id:
            base_query = base_query.filter(ImportHistory.account_id == account_id)
        
        # Get total count
        total = base_query.count()
        
        # Order by uploaded_at descending (newest first) and apply pagination
        imports = base_query.order_by(
            ImportHistory.uploaded_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Build stats list
        stats_list = []
        for import_record in imports:
            # Get account name
            account = db.query(Account).filter(Account.id == import_record.account_id).first()
            account_name = account.name if account else None
            
            # Count current rows
            current_row_count = db.query(func.count(DataRow.id)).filter(
                DataRow.import_id == import_record.id
            ).scalar() or 0
            
            # Calculate totals
            expenses_result = db.query(
                func.sum(DataRow.amount)
            ).filter(
                and_(DataRow.import_id == import_record.id, DataRow.amount < 0)
            ).scalar()
            
            income_result = db.query(
                func.sum(DataRow.amount)
            ).filter(
                and_(DataRow.import_id == import_record.id, DataRow.amount > 0)
            ).scalar()
            
            total_expenses = expenses_result if expenses_result else 0
            total_income = income_result if income_result else 0
            
            stats = ImportHistoryStats(
                id=import_record.id,
                account_id=import_record.account_id,
                account_name=account_name,
                filename=import_record.filename,
                uploaded_at=import_record.uploaded_at,
                row_count=import_record.row_count,
                rows_inserted=import_record.rows_inserted,
                rows_duplicated=import_record.rows_duplicated,
                status=import_record.status,
                current_row_count=current_row_count,
                total_expenses=total_expenses,
                total_income=total_income,
                can_rollback=current_row_count > 0  # Can rollback if rows exist
            )
            stats_list.append(stats)
        
        return stats_list, total
    
    @staticmethod
    def get_import_by_id(db: Session, import_id: int) -> Optional[ImportHistory]:
        """Get import history record by ID"""
        return db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
    
    @staticmethod
    def rollback_import(
        db: Session,
        import_id: int,
        account_id: Optional[int] = None
    ) -> ImportRollbackResponse:
        """
        Rollback an import by deleting all associated data rows
        
        Args:
            db: Database session
            import_id: Import record ID to rollback
            account_id: Optional account ID for authorization check
            
        Returns:
            Rollback response with deletion count
            
        Raises:
            ValueError: If import not found or belongs to different account
        """
        # Get import record
        import_record = db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
        
        if not import_record:
            raise ValueError(f"Import record {import_id} not found")
        
        # Check account ownership if provided
        if account_id and import_record.account_id != account_id:
            raise ValueError(f"Import {import_id} does not belong to account {account_id}")
        
        # Count rows before deletion
        rows_to_delete = db.query(DataRow).filter(DataRow.import_id == import_id).count()
        
        if rows_to_delete == 0:
            return ImportRollbackResponse(
                success=True,
                import_id=import_id,
                rows_deleted=0,
                message="No rows to delete (already rolled back or empty import)"
            )
        
        # Delete all data rows with this import_id
        # Note: This will cascade to related tables if configured
        db.query(DataRow).filter(DataRow.import_id == import_id).delete()
        
        # Update import status
        import_record.status = 'failed'
        import_record.error_message = f"Rolled back by user on {datetime.now().isoformat()}"
        
        db.commit()
        logger.info("Rolled back import %s, deleted %s rows", import_id, rows_to_delete)

        return ImportRollbackResponse(
            success=True,
            import_id=import_id,
            rows_deleted=rows_to_delete,
            message=f"Successfully deleted {rows_to_delete} rows from import '{import_record.filename}'"
        )
    
    @staticmethod
    def check_duplicate_file(
        db: Session,
        account_id: int,
        file_hash: str
    ) -> Optional[ImportHistory]:
        """
        Check if file has been imported before (based on hash)
        
        Args:
            db: Database session
            account_id: Account ID
            file_hash: SHA256 hash of file content
            
        Returns:
            Previous import record if duplicate found, None otherwise
        """
        return db.query(ImportHistory).filter(
            and_(
                ImportHistory.account_id == account_id,
                ImportHistory.file_hash == file_hash,
                ImportHistory.status == 'success'
            )
        ).first()
