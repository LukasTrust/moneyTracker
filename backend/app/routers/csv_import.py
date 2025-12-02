"""
CSV Import Router - Advanced CSV import with flexible mapping
Audit reference: 06_backend_routers.md - CSV import scaling & file size limits
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import json

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
    MappingSuggestion
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
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
        headers = CsvProcessor.get_headers(df)
        
        # Validate mapping
        is_valid, errors = MappingSuggester.validate_mapping(
            mapping.to_dict(),
            headers
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mapping: {'; '.join(errors)}"
            )
        
        # Apply mappings
        mapped_data = CsvProcessor.apply_mappings_advanced(df, mapping.to_dict())
        
        if not mapped_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid data rows found in CSV after mapping"
            )
        
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
            try:
                # Normalize transaction data (simplified to 3-4 fields)
                normalized_data = CsvProcessor.normalize_transaction_data(row_data)

                # Validate normalized data with Pydantic schema before persisting
                try:
                    validated = TransactionRow.model_validate(normalized_data)
                    # Use the validated Python dict (date as date, amount as Decimal, etc.)
                    validated_data = validated.model_dump()

                    # Validate amount is a finite number (reject NaN/inf)
                    # Accept Decimal, int, or float
                    import math
                    from decimal import Decimal, InvalidOperation
                    amt = validated_data.get('amount')
                    if amt is None:
                        error_count += 1
                        error_messages.append(f"Row {idx}: Amount is required")
                        continue
                    # Check if it's a valid number (Decimal, int, or float) and finite
                    try:
                        amt_float = float(amt)
                        if not math.isfinite(amt_float):
                            error_count += 1
                            error_messages.append(f"Row {idx}: Invalid amount value: {amt} (not finite)")
                            continue
                    except (ValueError, InvalidOperation, TypeError):
                        error_count += 1
                        error_messages.append(f"Row {idx}: Invalid amount value: {amt} (cannot convert to number)")
                        continue
                except ValidationError as ve:
                    error_count += 1
                    error_messages.append(f"Row {idx}: Validation error - {ve.errors()}")
                    continue

                # Generate hash (use validated data to ensure canonicalization)
                # Date may be a string or date object depending on schema
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
                    duplicate_count += 1
                    continue
                
                # Match category using rules (only CategoryMatcher, no CSV category)
                category_id = category_matcher.match_category(validated_data)

                # Find or create recipient
                recipient = None
                recipient_name = validated_data.get('recipient')
                if recipient_name:
                    recipient = recipient_matcher.find_or_create_recipient(recipient_name)

                # Parse structured fields from validated_data
                # Ensure transaction_date is a date object (DB expects Date)
                date_val = validated_data.get('date')
                transaction_date = None
                if date_val:
                    # If Pydantic returned a string, try multiple parse strategies
                    if isinstance(date_val, str):
                        parsed_dt = CsvProcessor.parse_date(date_val)
                        if parsed_dt:
                            transaction_date = parsed_dt.date()
                        else:
                            # Fallback: try ISO format parsing
                            try:
                                from datetime import datetime as _dt
                                parsed_dt = _dt.fromisoformat(date_val)
                                transaction_date = parsed_dt.date()
                            except Exception:
                                transaction_date = None
                    else:
                        # If it's already a date/datetime-like object, try to get date()
                        try:
                            transaction_date = date_val.date()
                        except Exception:
                            transaction_date = None

                # Amount: convert Decimal to float for DB storage
                amount = float(validated_data.get('amount', 0.0))

                # Recipient and Purpose
                recipient_str = validated_data.get('recipient', '')
                purpose = validated_data.get('purpose', '')
                
                # Currency (from raw data or default)
                currency = row_data.get('currency', 'EUR')
                
                # Create data row with structured fields
                new_row = DataRow(
                    account_id=account_id,
                    row_hash=row_hash,
                    # NEW: Structured fields
                    transaction_date=transaction_date,
                    amount=amount,
                    recipient=recipient_str[:200] if recipient_str else None,  # Truncate to 200 chars
                    purpose=purpose,
                    currency=currency,
                    raw_data=row_data,  # Keep original CSV data for audit
                    # Relations
                    category_id=category_id,
                    recipient_id=recipient.id if recipient else None,
                    import_id=import_id  # Link to import history
                )
                
                db.add(new_row)
                existing_hashes.add(row_hash)
                imported_count += 1
                
            except ValueError as e:
                error_count += 1
                error_messages.append(f"Row {idx}: {str(e)}")
                continue
            except Exception as e:
                error_count += 1
                error_messages.append(f"Row {idx}: Unexpected error - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
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
        # IMPORTANT: Always analyze ALL transactions for the account, not just newly imported ones
        recurring_count = 0
        if imported_count > 0 or duplicate_count > 0:  # Run even if only duplicates (might detect new patterns)
            try:
                # If a BackgroundTasks instance is provided by FastAPI, enqueue the detection
                if background_tasks is not None:
                    # Create job record first
                    from app.services.job_service import JobService
                    job = JobService.create_job(db, task_type="recurring_detection", account_id=account_id, import_id=import_id)
                    background_tasks.add_task(run_update_recurring_transactions, account_id)
                    logger.info("Enqueued recurring detection for account", extra={"account_id": account_id, "job_id": getattr(job, 'id', None), "import_id": import_id})
                else:
                    # Fallback to synchronous run (useful for tests or CLI)
                    detector = RecurringTransactionDetector(db)
                    stats = detector.update_recurring_transactions(account_id)
                    from app.models.recurring_transaction import RecurringTransaction
                    recurring_count = db.query(RecurringTransaction).filter(
                        RecurringTransaction.account_id == account_id,
                        RecurringTransaction.is_active == True
                    ).count()
                    logger.info("Recurring detection (sync)", extra={"created": stats.get('created'), "updated": stats.get('updated'), "total_active": recurring_count, "account_id": account_id})
            except Exception as e:
                # Log error but don't fail the import
                logger.exception("Could not detect recurring transactions", exc_info=True, extra={"account_id": account_id, "import_id": import_id})

        # Run transfer detection for the imported rows and include candidates in response
        # Run this even if no new rows were imported (e.g., all duplicates) to detect transfers
        # between existing transactions
        transfer_candidates = None
        try:
            matcher = TransferMatcher(db)

            # Determine date range for imported rows - limit detection to imported date span
            from sqlalchemy import func
            date_min, date_max = db.query(func.min(DataRow.transaction_date), func.max(DataRow.transaction_date)).filter(
                DataRow.import_id == import_id
            ).one()

            # If no new transactions were imported (all duplicates), check date range of all transactions in account
            if not date_min or not date_max:
                # Use date range from the CSV data that was attempted to be imported
                if mapped_data:
                    # Get date range from the mapped data
                    dates = [row.get('date') for row in mapped_data if row.get('date')]
                    if dates:
                        from datetime import datetime as _dt
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

            # Call matcher to find candidates involving this account within the date range
            candidates = matcher.find_transfer_candidates(
                account_ids=[account_id],
                date_from=date_min,
                date_to=date_max,
                min_confidence=0.7,
                exclude_existing=True
            ) if date_min and date_max else []

            # Limit number returned to avoid huge payloads
            MAX_CANDIDATES_RETURN = 200
            transfer_candidates = candidates[:MAX_CANDIDATES_RETURN]

            # If background tasks are provided and we prefer async detection, we could enqueue here.
        except Exception:
            # Non-fatal: log and continue
            logger.exception("Transfer detection failed during import", exc_info=True, extra={"import_id": import_id, "account_id": account_id})
        
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
