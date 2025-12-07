"""
CSV Import Router - Advanced CSV import with flexible mapping
Audit reference: 06_backend_routers.md - CSV import scaling & file size limits
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal
import json
import pandas as pd

from app.database import get_db
from app.config import settings
from app.models.account import Account
from app.models.data_row import DataRow
from app.models.mapping import Mapping
from app.routers.deps import verify_account_exists
from app.schemas.csv_import import (
    CsvImportPreview,
    CsvImportRequest,
    CsvImportResponse,
    CsvImportMapping,
    CsvImportSuggestions,
    MappingSuggestion,
    BulkImportResponse,
    BulkImportFileResult
)
from app.schemas.mapping import MappingValidationResponse, MappingValidationResult
from app.services.csv_processor import CsvProcessor
from app.services.hash_service import HashService
from app.services.category_matcher import CategoryMatcher
from app.services.mapping_suggester import MappingSuggester
from app.services.bank_presets import BankPresetMatcher
from app.services.recipient_matcher import RecipientMatcher
from app.services.recurring_transaction_detector import RecurringTransactionDetector, run_update_recurring_transactions
from app.utils import get_logger
from app.services.transfer_matcher import TransferMatcher
from app.services.errors import ValidationError as ServiceValidationError, DuplicateError
from pydantic import ValidationError
from app.schemas.csv import TransactionRow

logger = get_logger(__name__)
from app.services.import_history_service import ImportHistoryService

router = APIRouter()


def _parse_and_validate_csv(content: bytes, filename: str) -> Tuple[pd.DataFrame, str, List[str]]:
    """
    Parse and validate CSV file.
    
    Args:
        content: File content bytes
        filename: Original filename
        
    Returns:
        Tuple of (DataFrame, delimiter, headers)
        
    Raises:
        HTTPException: On validation errors
    """
    validate_file_size(content, filename)
    
    try:
        df, delimiter = CsvProcessor.parse_csv_advanced(content)
        validate_row_count(len(df), filename)
        headers = CsvProcessor.get_headers(df)
        return df, delimiter, headers
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {str(e)}"
        )


def _validate_and_apply_mapping(
    df: pd.DataFrame,
    headers: List[str],
    mapping: CsvImportMapping
) -> List[Dict[str, Any]]:
    """
    Validate mapping and apply to DataFrame.
    
    Args:
        df: Pandas DataFrame
        headers: CSV headers
        mapping: Mapping configuration
        
    Returns:
        List of mapped data dictionaries
        
    Raises:
        HTTPException: On validation errors
    """
    is_valid, errors = MappingSuggester.validate_mapping(
        mapping.to_dict(),
        headers
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mapping: {'; '.join(errors)}"
        )
    
    mapped_data = CsvProcessor.apply_mappings_advanced(df, mapping.to_dict())
    
    if not mapped_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid data rows found in CSV after mapping"
        )
    
    return mapped_data


def _process_transaction_row(
    idx: int,
    row_data: Dict[str, Any],
    account_id: int,
    import_id: int,
    existing_hashes: set,
    category_matcher: CategoryMatcher,
    recipient_matcher: RecipientMatcher,
    db: Session
) -> Tuple[Optional[DataRow], bool, Optional[str]]:
    """
    Process a single transaction row.
    
    Args:
        idx: Row index (for error messages)
        row_data: Raw row data from CSV
        account_id: Target account ID
        import_id: Import history ID
        existing_hashes: Set of existing row hashes
        category_matcher: CategoryMatcher instance
        recipient_matcher: RecipientMatcher instance
        db: Database session
        
    Returns:
        Tuple of (DataRow or None, is_duplicate, error_message or None)
    """
    try:
        # Normalize transaction data
        normalized_data = CsvProcessor.normalize_transaction_data(row_data)

        # Validate with Pydantic schema
        try:
            validated = TransactionRow.model_validate(normalized_data)
            validated_data = validated.model_dump()

            # Validate amount is finite
            import math
            from decimal import Decimal, InvalidOperation
            amt = validated_data.get('amount')
            if amt is None:
                return None, False, "Amount is required"
            
            try:
                amt_float = float(amt)
                if not math.isfinite(amt_float):
                    return None, False, f"Invalid amount value: {amt} (not finite)"
            except (ValueError, InvalidOperation, TypeError):
                return None, False, f"Invalid amount value: {amt} (cannot convert to number)"
        except ValidationError as ve:
            return None, False, f"Validation error - {ve.errors()}"

        # Generate hash
        date_val = validated_data.get('date')
        if hasattr(date_val, 'isoformat'):
            date_str_for_hash = date_val.isoformat()
        else:
            date_str_for_hash = str(date_val) if date_val is not None else None

        row_hash = HashService.generate_hash({
            'date': date_str_for_hash,
            'amount': validated_data.get('amount'),
            'recipient': validated_data.get('recipient')
        })
        
        # Check for duplicates
        if HashService.is_duplicate(row_hash, existing_hashes):
            return None, True, None
        
        # Match category
        category_id = category_matcher.match_category(validated_data)

        # Find or create recipient
        recipient = None
        recipient_name = validated_data.get('recipient')
        if recipient_name:
            recipient = recipient_matcher.find_or_create_recipient(recipient_name)

        # Parse date
        date_val = validated_data.get('date')
        transaction_date = None
        if date_val:
            if isinstance(date_val, str):
                parsed_dt = CsvProcessor.parse_date(date_val)
                if parsed_dt:
                    transaction_date = parsed_dt.date()
                else:
                    try:
                        from datetime import datetime as _dt
                        parsed_dt = _dt.fromisoformat(date_val)
                        transaction_date = parsed_dt.date()
                    except Exception:
                        transaction_date = None
            else:
                try:
                    transaction_date = date_val.date()
                except Exception:
                    transaction_date = None

        # Keep amount as Decimal for precise storage
        amount = validated_data.get('amount', Decimal('0.0'))

        # Get recipient and purpose
        recipient_str = validated_data.get('recipient', '')
        purpose = validated_data.get('purpose', '')
        currency = row_data.get('currency', 'EUR')
        
        # Saldo (optional - keep as Decimal)
        saldo = validated_data.get('saldo', None)
        
        # Create data row
        new_row = DataRow(
            account_id=account_id,
            row_hash=row_hash,
            transaction_date=transaction_date,
            amount=amount,
            recipient=recipient_str[:200] if recipient_str else None,
            purpose=purpose,
            currency=currency,
            saldo=saldo,
            raw_data=row_data,
            category_id=category_id,
            recipient_id=recipient.id if recipient else None,
            import_id=import_id
        )
        
        existing_hashes.add(row_hash)
        return new_row, False, None
        
    except ValueError as e:
        return None, False, str(e)
    except Exception as e:
        return None, False, f"Unexpected error - {str(e)}"


def _update_account_initial_balance(
    db: Session,
    account_id: int,
    import_id: int
) -> None:
    """
    Update account initial_balance based on earliest transaction with saldo.
    
    Args:
        db: Database session
        account_id: Account ID
        import_id: Import ID
    """
    try:
        earliest_with_saldo = db.query(DataRow).filter(
            DataRow.import_id == import_id,
            DataRow.saldo.isnot(None)
        ).order_by(DataRow.transaction_date.asc()).first()
        
        if earliest_with_saldo:
            calculated_initial_balance = earliest_with_saldo.saldo - earliest_with_saldo.amount
            
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                account.initial_balance = calculated_initial_balance
                db.commit()
                
                logger.info(
                    f"Updated account {account_id} initial_balance to {calculated_initial_balance} "
                    f"based on earliest transaction (date={earliest_with_saldo.transaction_date}, "
                    f"saldo={earliest_with_saldo.saldo}, amount={earliest_with_saldo.amount})"
                )
    except Exception as e:
        logger.exception(
            f"Could not update initial_balance for account {account_id}",
            exc_info=True,
            extra={"account_id": account_id, "import_id": import_id}
        )


def _trigger_recurring_detection(
    db: Session,
    account_id: int,
    import_id: int,
    background_tasks: Optional[BackgroundTasks] = None
) -> int:
    """
    Trigger recurring transaction detection.
    
    Args:
        db: Database session
        account_id: Account ID
        import_id: Import ID
        background_tasks: Optional background tasks instance
        
    Returns:
        Number of recurring transactions detected (0 if async)
    """
    try:
        if background_tasks is not None:
            from app.services.job_service import JobService
            job = JobService.create_job(db, task_type="recurring_detection", account_id=account_id, import_id=import_id)
            background_tasks.add_task(run_update_recurring_transactions, account_id)
            logger.info("Enqueued recurring detection for account", extra={"account_id": account_id, "job_id": getattr(job, 'id', None), "import_id": import_id})
            return 0
        else:
            detector = RecurringTransactionDetector(db)
            stats = detector.update_recurring_transactions(account_id)
            from app.models.recurring_transaction import RecurringTransaction
            recurring_count = db.query(RecurringTransaction).filter(
                RecurringTransaction.account_id == account_id,
                RecurringTransaction.is_active == True
            ).count()
            logger.info("Recurring detection (sync)", extra={"created": stats.get('created'), "updated": stats.get('updated'), "total_active": recurring_count, "account_id": account_id})
            return recurring_count
    except Exception as e:
        logger.exception("Could not detect recurring transactions", exc_info=True, extra={"account_id": account_id, "import_id": import_id})
        return 0


def _find_transfer_candidates(
    db: Session,
    account_id: int,
    import_id: int,
    mapped_data: List[Dict[str, Any]] = None,
    max_candidates: int = 200
) -> List[Dict[str, Any]]:
    """
    Find transfer candidates for imported transactions.
    
    Args:
        db: Database session
        account_id: Account ID
        import_id: Import ID
        mapped_data: Optional mapped data (fallback for date range)
        max_candidates: Maximum number of candidates to return
        
    Returns:
        List of transfer candidates
    """
    try:
        matcher = TransferMatcher(db)

        # Determine date range for imported rows
        from sqlalchemy import func
        from datetime import date
        date_min, date_max = db.query(
            func.min(DataRow.transaction_date),
            func.max(DataRow.transaction_date)
        ).filter(DataRow.import_id == import_id).one()

        # Fallback to mapped data if no transactions imported
        if not date_min or not date_max:
            if mapped_data:
                dates = [row.get('date') for row in mapped_data if row.get('date')]
                if dates:
                    parsed_dates = []
                    for d in dates:
                        if isinstance(d, date):
                            parsed_dates.append(d)
                        elif isinstance(d, str):
                            parsed_dt = CsvProcessor.parse_date(d)
                            if parsed_dt:
                                parsed_dates.append(parsed_dt.date())
                    
                    if parsed_dates:
                        date_min = min(parsed_dates)
                        date_max = max(parsed_dates)

        if date_min and date_max:
            candidates = matcher.find_transfer_candidates(
                account_ids=[account_id],
                date_from=date_min,
                date_to=date_max,
                min_confidence=0.7,
                exclude_existing=True
            )
            return candidates[:max_candidates]
        
        return []
    except Exception:
        logger.exception("Transfer detection failed", exc_info=True, extra={"import_id": import_id, "account_id": account_id})
        return []


def validate_file_size(content: bytes, filename: str) -> None:
    """
    Validate file size against configured limits.
    Audit reference: 01_backend_action_plan.md - P0 CSV file size limits
    
    Args:
        content: File content bytes
        filename: Original filename
        
    Raises:
        HTTPException: 413 if file too large
    """
    file_size = len(content)
    max_bytes = settings.MAX_IMPORT_BYTES
    
    if file_size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{filename}' is too large ({actual_mb:.1f} MB). Maximum allowed: {max_mb:.1f} MB"
        )


def validate_row_count(row_count: int, filename: str) -> None:
    """
    Validate row count against configured limits.
    
    Args:
        row_count: Number of rows in CSV
        filename: Original filename
        
    Raises:
        HTTPException: 413 if too many rows
    """
    max_rows = settings.MAX_IMPORT_ROWS
    
    if row_count > max_rows:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{filename}' has too many rows ({row_count:,}). Maximum allowed: {max_rows:,} rows"
        )


@router.get("/banks")
async def get_available_banks():
    """
    Get list of available bank presets
    
    Returns:
        List of banks with ID, name, and description
    """
    presets = BankPresetMatcher.get_all_presets()
    
    return {
        "banks": [
            {
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
            }
            for preset in presets
        ]
    }


@router.post("/detect-bank")
async def detect_bank_from_csv(
    file: UploadFile = File(...)
):
    """
    Detect bank from CSV headers
    
    Args:
        file: CSV file to analyze
        
    Returns:
        Detected bank ID and confidence, or null if not detected
    """
    content = await file.read()
    
    # Validate file size (Audit: 01_backend_action_plan.md - P0)
    validate_file_size(content, file.filename)
    
    try:
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
        
        # Validate row count
        validate_row_count(len(df), file.filename)
        
        headers = CsvProcessor.get_headers(df)
        
        # Detect bank
        bank_id = BankPresetMatcher.detect_bank(headers)
        
        if bank_id:
            preset = BankPresetMatcher.get_preset(bank_id)
            return {
                "detected": True,
                "bank_id": bank_id,
                "bank_name": preset.name,
                "bank_description": preset.description,
                "mapping": preset.mapping,
            }
        else:
            return {
                "detected": False,
                "bank_id": None,
                "bank_name": None,
                "message": "Bank konnte nicht automatisch erkannt werden. Bitte wählen Sie manuell."
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Analysieren der CSV: {str(e)}"
        )


@router.get("/banks/{bank_id}/preset")
async def get_bank_preset(bank_id: str):
    """
    Get mapping preset for a specific bank
    
    Args:
        bank_id: Bank identifier (e.g., 'sparkasse', 'dkb')
        
    Returns:
        Bank preset with mapping configuration
        
    Raises:
        404: Bank not found
    """
    preset = BankPresetMatcher.get_preset(bank_id)
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_id}' nicht gefunden"
        )
    
    return {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "mapping": preset.mapping,
        "delimiter": preset.delimiter,
        "decimal": preset.decimal,
        "date_format": preset.date_format,
    }


@router.post("/preview", response_model=CsvImportPreview)
async def preview_csv_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Preview CSV file without importing
    
    Returns headers, sample rows, and detected delimiter.
    Does not require account_id - can be called before mapping.
    
    Args:
        file: CSV file to preview
        
    Returns:
        Preview with headers, sample rows, total rows, delimiter
        
    Raises:
        400: Invalid CSV file
        413: File too large
    """
    # Read file content
    content = await file.read()
    
    # Validate file size (Audit: 01_backend_action_plan.md - P0)
    validate_file_size(content, file.filename)
    
    try:
        # Parse CSV with auto-detection
        df, delimiter = CsvProcessor.parse_csv_advanced(content)
        
        # Validate row count
        validate_row_count(len(df), file.filename)
        
        # Get headers
        headers = CsvProcessor.get_headers(df)
        
        # Get preview rows
        sample_rows = CsvProcessor.get_preview_rows(df, n=20)
        
        return {
            "headers": headers,
            "sample_rows": sample_rows,
            "total_rows": len(df),
            "detected_delimiter": delimiter
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.post("/suggest-mapping", response_model=CsvImportSuggestions)
async def suggest_mapping(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyze CSV headers and suggest field mappings
    
    Args:
        file: CSV file to analyze
        
    Returns:
        Suggested mappings for standard fields (date, amount, recipient, purpose)
        
    Raises:
        400: Invalid CSV file
        413: File too large
    """
    content = await file.read()
    
    # Validate file size
    validate_file_size(content, file.filename)
    
    try:
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
        
        # Validate row count
        validate_row_count(len(df), file.filename)
        
        headers = CsvProcessor.get_headers(df)
        
        # Get suggestions
        suggestions_dict = MappingSuggester.suggest_mappings(headers)
        
        # Convert to response format
        suggestions = {}
        for field_name, (suggested_header, confidence, alternatives) in suggestions_dict.items():
            suggestions[field_name] = MappingSuggestion(
                field_name=field_name,
                suggested_header=suggested_header,
                confidence=confidence,
                alternatives=alternatives
            )
        
        return {"suggestions": suggestions}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing CSV: {str(e)}"
        )


@router.post("/validate-mapping/{account_id}", response_model=MappingValidationResponse)
async def validate_saved_mapping(
    account_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Validate saved mappings against uploaded CSV file
    
    This endpoint checks if the saved mappings for an account are compatible
    with the uploaded CSV file. It identifies missing headers and suggests
    alternatives if available.
    
    Args:
        account_id: Account ID with saved mappings
        file: CSV file to validate against
        
    Returns:
        Validation result with details about missing/valid headers
        
    Raises:
        400: Invalid CSV file
        404: Account not found
        413: File too large
    """
    # Verify account exists
    account = verify_account_exists(account_id, db)
    
    # Read and validate file
    content = await file.read()
    validate_file_size(content, file.filename)
    
    try:
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
        validate_row_count(len(df), file.filename)
        headers = CsvProcessor.get_headers(df)
        
        # Get saved mappings
        saved_mappings = db.query(Mapping).filter(
            Mapping.account_id == account_id
        ).all()
        
        if not saved_mappings:
            # No saved mappings - suggest new ones
            suggestions_dict = MappingSuggester.suggest_mappings(headers)
            
            return MappingValidationResponse(
                is_valid=False,
                has_saved_mapping=False,
                validation_results=[],
                missing_headers=[],
                available_headers=headers
            )
        
        # Validate each saved mapping
        validation_results = []
        missing_headers = []
        all_valid = True
        
        for mapping in saved_mappings:
            is_valid = mapping.csv_header in headers
            
            if not is_valid:
                all_valid = False
                missing_headers.append(mapping.csv_header)
                
                # Try to suggest alternative
                suggestions_dict = MappingSuggester.suggest_mappings(headers)
                suggested = None
                
                if mapping.standard_field in suggestions_dict:
                    suggested_header, confidence, alternatives = suggestions_dict[mapping.standard_field]
                    if confidence > 0.5:
                        suggested = suggested_header
            else:
                suggested = None
            
            validation_results.append(
                MappingValidationResult(
                    field=mapping.standard_field,
                    csv_header=mapping.csv_header,
                    is_valid=is_valid,
                    suggested_header=suggested
                )
            )
        
        return MappingValidationResponse(
            is_valid=all_valid,
            has_saved_mapping=True,
            validation_results=validation_results,
            missing_headers=missing_headers,
            available_headers=headers
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating mapping: {str(e)}"
        )


@router.post("/import", response_model=CsvImportResponse)
async def import_csv_advanced(
    account_id: int = Form(...),
    mapping_json: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Import CSV file with custom mapping configuration
    
    This is the main import endpoint that processes CSV data according
    to the user-defined mapping and imports transactions into the database.
    
    Args:
        account_id: Target account ID
        mapping_json: JSON string of mapping configuration
        file: CSV file to import
        
    Returns:
        Import statistics (imported, duplicates, errors)
        
    Raises:
        400: Invalid data or mapping
        404: Account not found
        500: Server error during processing
    """
    # Check if account exists
    account = verify_account_exists(account_id, db)
    
    # Parse mapping JSON
    try:
        mapping_dict = json.loads(mapping_json)
        mapping = CsvImportMapping(**mapping_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mapping JSON format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mapping configuration: {str(e)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Create import history record
    import_record = ImportHistoryService.create_import_record(
        db=db,
        account_id=account_id,
        filename=file.filename,
        file_content=content
    )
    import_id = import_record.id
    
    try:
        # Parse and validate CSV
        df, _, headers = _parse_and_validate_csv(content, file.filename)
        
        # Validate and apply mapping
        mapped_data = _validate_and_apply_mapping(df, headers, mapping)
        
        # Get existing hashes for duplicate detection
        existing_hashes = {
            row.row_hash
            for row in db.query(DataRow.row_hash).filter(
                DataRow.account_id == account_id
            ).all()
        }
        
        # Initialize category matcher and recipient matcher
        category_matcher = CategoryMatcher(db)
        recipient_matcher = RecipientMatcher(db)
        
        # Process each row
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        error_messages = []
        
        for idx, row_data in enumerate(mapped_data, start=1):
            new_row, is_duplicate, error = _process_transaction_row(
                idx, row_data, account_id, import_id,
                existing_hashes, category_matcher, recipient_matcher, db
            )
            
            if error:
                error_count += 1
                error_messages.append(f"Row {idx}: {error}")
            elif is_duplicate:
                duplicate_count += 1
            elif new_row:
                db.add(new_row)
                imported_count += 1
        
        # Commit all changes
        db.commit()
        
        # Update account initial_balance if needed
        if imported_count > 0:
            _update_account_initial_balance(db, account_id, import_id)
        
        # Update import history with final statistics
        status_value = 'success' if error_count == 0 else ('partial' if imported_count > 0 else 'failed')
        error_summary = '; '.join(error_messages[:5]) if error_messages else None  # First 5 errors
        
        ImportHistoryService.update_import_stats(
            db=db,
            import_id=import_id,
            row_count=len(mapped_data),
            rows_inserted=imported_count,
            rows_duplicated=duplicate_count,
            status=status_value,
            error_message=error_summary
        )
        
        # Save mapping configuration for future use
        # This should happen regardless of imported_count to enable reuse even when all rows are duplicates
        if len(mapped_data) > 0:  # Only save if CSV had valid data (regardless of duplicates)
            try:
                # Delete existing mappings for this account
                db.query(Mapping).filter(Mapping.account_id == account_id).delete()
                
                # Save new mappings
                for field_name, csv_header in mapping.to_dict().items():
                    new_mapping = Mapping(
                        account_id=account_id,
                        csv_header=csv_header,
                        standard_field=field_name
                    )
                    db.add(new_mapping)
                
                db.commit()
                logger.info("Saved mappings for account", extra={
                    "account_id": account_id, 
                    "import_id": import_id,
                    "mapping_count": len(mapping.to_dict())
                })
            except Exception as e:
                # Log error but don't fail the import
                logger.exception("Could not save mappings", exc_info=True, extra={"account_id": account_id, "import_id": import_id})
        
        # Trigger recurring transaction detection after successful import
        recurring_count = 0
        if imported_count > 0 or duplicate_count > 0:
            recurring_count = _trigger_recurring_detection(db, account_id, import_id, background_tasks)

        # Run transfer detection for the imported rows
        transfer_candidates = _find_transfer_candidates(db, account_id, import_id, mapped_data)
        
        success = error_count == 0 or imported_count > 0
        
        # Build success message with recurring info
        message = f"Successfully imported {imported_count} transactions"
        if recurring_count > 0:
            message += f". Found {recurring_count} recurring contracts."
        
        return {
            "success": success,
            "message": message,
            "imported_count": imported_count,
            "duplicate_count": duplicate_count,
            "error_count": error_count,
            "total_rows": len(mapped_data),
            "errors": error_messages if error_messages else None,
            "recurring_detected": recurring_count if recurring_count > 0 else None,
            "import_id": import_id,  # Return import ID for frontend
            "transfer_candidates": transfer_candidates
        }
        
    except HTTPException:
        # Update import status to failed
        ImportHistoryService.update_import_stats(
            db=db,
            import_id=import_id,
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message="HTTP Exception during import"
        )
        raise
    except ValueError as e:
        # Update import status to failed
        ImportHistoryService.update_import_stats(
            db=db,
            import_id=import_id,
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        # Update import status to failed
        ImportHistoryService.update_import_stats(
            db=db,
            import_id=import_id,
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )



@router.get("/import/{import_id}/status")
async def get_import_status(import_id: int, db: Session = Depends(get_db)):
    """Return minimal status for a given import ID (for frontend polling)."""
    record = ImportHistoryService.get_import_by_id(db, import_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Import {import_id} not found")

    return {
        "id": record.id,
        "account_id": record.account_id,
        "filename": record.filename,
        "uploaded_at": record.uploaded_at,
        "status": record.status,
        "row_count": record.row_count,
        "rows_inserted": record.rows_inserted,
        "rows_duplicated": record.rows_duplicated,
        "error_message": record.error_message,
    }


@router.get("/import/{import_id}/transfer-candidates")
def get_transfer_candidates_for_import(import_id: int, db: Session = Depends(get_db)):
    """Run transfer detection limited to transactions from a specific import and return candidates."""
    import_record = ImportHistoryService.get_import_by_id(db, import_id)
    if not import_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Import {import_id} not found")

    # Determine date range for this import's rows
    from sqlalchemy import func
    date_min, date_max = db.query(func.min(DataRow.transaction_date), func.max(DataRow.transaction_date)).filter(
        DataRow.import_id == import_id
    ).one()

    matcher = TransferMatcher(db)
    candidates = []
    try:
        if date_min and date_max:
            candidates = matcher.find_transfer_candidates(
                account_ids=[import_record.account_id],
                date_from=date_min,
                date_to=date_max,
                min_confidence=0.7,
                exclude_existing=True
            )
    except Exception:
        logger.exception("Transfer detection failed for import", exc_info=True, extra={"import_id": import_id})

    return {
        "import_id": import_id,
        "account_id": import_record.account_id,
        "candidates": candidates,
        "total_found": len(candidates)
    }


@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_csv(
    account_id: int = Form(...),
    mapping_json: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Import multiple CSV files with the same mapping configuration
    
    Uses the first file to define the schema/mapping, then applies it to all files.
    If a file fails, it's logged as an error but processing continues with the next file.
    
    Args:
        account_id: Target account ID
        mapping_json: JSON string of mapping configuration (derived from first file)
        files: List of CSV files to import
        
    Returns:
        Bulk import statistics with results for each file
        
    Raises:
        400: Invalid data or mapping
        404: Account not found
        413: File too large
    """
    # Check if account exists
    account = verify_account_exists(account_id, db)
    
    # Parse mapping JSON
    try:
        mapping_dict = json.loads(mapping_json)
        mapping = CsvImportMapping(**mapping_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mapping JSON format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mapping configuration: {str(e)}"
        )
    
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for bulk import"
        )
    
    # Process each file
    file_results = []
    total_imported = 0
    total_duplicates = 0
    total_errors = 0
    successful_files = 0
    failed_files = 0
    all_transfer_candidates = []
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            
            # Validate file size
            try:
                validate_file_size(content, file.filename)
            except HTTPException as e:
                # File too large - skip and continue
                file_results.append(BulkImportFileResult(
                    filename=file.filename,
                    success=False,
                    message=f"Datei zu groß: {e.detail}",
                    imported_count=0,
                    duplicate_count=0,
                    error_count=0,
                    total_rows=0,
                    errors=[e.detail]
                ))
                failed_files += 1
                continue
            
            # Create import history record
            import_record = ImportHistoryService.create_import_record(
                db=db,
                account_id=account_id,
                filename=file.filename,
                file_content=content
            )
            import_id = import_record.id
            
            try:
                # Parse and validate CSV
                df, _, headers = _parse_and_validate_csv(content, file.filename)
                
                # Validate and apply mapping
                mapped_data = _validate_and_apply_mapping(df, headers, mapping)
                
                # Get existing hashes for duplicate detection
                existing_hashes = {
                    row.row_hash
                    for row in db.query(DataRow.row_hash).filter(
                        DataRow.account_id == account_id
                    ).all()
                }
                
                # Initialize matchers
                category_matcher = CategoryMatcher(db)
                recipient_matcher = RecipientMatcher(db)
                
                # Process each row
                imported_count = 0
                duplicate_count = 0
                error_count = 0
                error_messages = []
                
                for idx, row_data in enumerate(mapped_data, start=1):
                    new_row, is_duplicate, error = _process_transaction_row(
                        idx, row_data, account_id, import_id,
                        existing_hashes, category_matcher, recipient_matcher, db
                    )
                    
                    if error:
                        error_count += 1
                        error_messages.append(f"Row {idx}: {error}")
                    elif is_duplicate:
                        duplicate_count += 1
                    elif new_row:
                        db.add(new_row)
                        imported_count += 1
                
                # Commit changes for this file
                db.commit()
                
                # Update account initial_balance if needed
                if imported_count > 0:
                    _update_account_initial_balance(db, account_id, import_id)
                
                # Update import history
                status_value = 'success' if error_count == 0 else ('partial' if imported_count > 0 else 'failed')
                error_summary = '; '.join(error_messages[:5]) if error_messages else None
                
                ImportHistoryService.update_import_stats(
                    db=db,
                    import_id=import_id,
                    row_count=len(mapped_data),
                    rows_inserted=imported_count,
                    rows_duplicated=duplicate_count,
                    status=status_value,
                    error_message=error_summary
                )
                
                # Detect transfers for this file
                candidates = _find_transfer_candidates(db, account_id, import_id, None, max_candidates=50)
                all_transfer_candidates.extend(candidates)
                
                # Create file result
                success = error_count == 0 or imported_count > 0
                message = f"{imported_count} Transaktionen importiert"
                if duplicate_count > 0:
                    message += f", {duplicate_count} Duplikate"
                if error_count > 0:
                    message += f", {error_count} Fehler"
                
                file_results.append(BulkImportFileResult(
                    filename=file.filename,
                    success=success,
                    message=message,
                    imported_count=imported_count,
                    duplicate_count=duplicate_count,
                    error_count=error_count,
                    total_rows=len(mapped_data),
                    errors=error_messages[:10] if error_messages else None,  # First 10 errors
                    import_id=import_id
                ))
                
                # Update counters
                total_imported += imported_count
                total_duplicates += duplicate_count
                total_errors += error_count
                if success:
                    successful_files += 1
                else:
                    failed_files += 1
                    
            except Exception as e:
                # File-specific error
                db.rollback()
                
                # Update import status to failed
                ImportHistoryService.update_import_stats(
                    db=db,
                    import_id=import_id,
                    row_count=0,
                    rows_inserted=0,
                    rows_duplicated=0,
                    status='failed',
                    error_message=str(e)
                )
                
                file_results.append(BulkImportFileResult(
                    filename=file.filename,
                    success=False,
                    message=f"Fehler: {str(e)}",
                    imported_count=0,
                    duplicate_count=0,
                    error_count=0,
                    total_rows=0,
                    errors=[str(e)],
                    import_id=import_id
                ))
                failed_files += 1
                continue
                
        except Exception as e:
            # Unexpected error for this file
            file_results.append(BulkImportFileResult(
                filename=file.filename,
                success=False,
                message=f"Unerwarteter Fehler: {str(e)}",
                imported_count=0,
                duplicate_count=0,
                error_count=0,
                total_rows=0,
                errors=[str(e)]
            ))
            failed_files += 1
            continue
    
    # Save mapping configuration after successful imports
    if successful_files > 0:
        try:
            db.query(Mapping).filter(Mapping.account_id == account_id).delete()
            for field_name, csv_header in mapping.to_dict().items():
                new_mapping = Mapping(
                    account_id=account_id,
                    csv_header=csv_header,
                    standard_field=field_name
                )
                db.add(new_mapping)
            db.commit()
        except Exception as e:
            logger.exception("Could not save mappings", exc_info=True)
    
    # Trigger recurring transaction detection if any files were imported
    recurring_count = 0
    if total_imported > 0:
        recurring_count = _trigger_recurring_detection(db, account_id, None, background_tasks)
    
    # Build response message
    message = f"{successful_files}/{len(files)} Dateien erfolgreich importiert. "
    message += f"Insgesamt {total_imported} Transaktionen importiert"
    if total_duplicates > 0:
        message += f", {total_duplicates} Duplikate"
    if total_errors > 0:
        message += f", {total_errors} Fehler"
    
    return BulkImportResponse(
        success=successful_files > 0,
        message=message,
        total_files=len(files),
        successful_files=successful_files,
        failed_files=failed_files,
        total_imported_count=total_imported,
        total_duplicate_count=total_duplicates,
        total_error_count=total_errors,
        file_results=file_results,
        recurring_detected=recurring_count if recurring_count > 0 else None,
        transfer_candidates=all_transfer_candidates[:200] if all_transfer_candidates else None
    )

