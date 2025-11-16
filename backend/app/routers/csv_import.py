"""
CSV Import Router - Advanced CSV import with flexible mapping
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.models.account import Account
from app.models.data_row import DataRow
from app.models.mapping import Mapping
from app.schemas.csv_import import (
    CsvImportPreview,
    CsvImportRequest,
    CsvImportResponse,
    CsvImportMapping,
    CsvImportSuggestions,
    MappingSuggestion
)
from app.services.csv_processor import CsvProcessor
from app.services.hash_service import HashService
from app.services.category_matcher import CategoryMatcher
from app.services.mapping_suggester import MappingSuggester
from app.services.bank_presets import BankPresetMatcher
from app.services.recipient_matcher import RecipientMatcher
from app.services.recurring_transaction_detector import RecurringTransactionDetector
from app.services.import_history_service import ImportHistoryService

router = APIRouter()


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
    
    try:
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
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
    """
    # Read file content
    content = await file.read()
    
    try:
        # Parse CSV with auto-detection
        df, delimiter = CsvProcessor.parse_csv_advanced(content)
        
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
    
    Uses intelligent pattern matching to suggest which CSV columns
    should map to which standard fields (date, amount, sender, recipient).
    
    Args:
        file: CSV file to analyze
        
    Returns:
        Mapping suggestions with confidence scores
        
    Raises:
        400: Invalid CSV file
    """
    # Read file content
    content = await file.read()
    
    try:
        # Parse CSV
        df, _ = CsvProcessor.parse_csv_advanced(content)
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


@router.post("/import", response_model=CsvImportResponse)
async def import_csv_advanced(
    account_id: int = Form(...),
    mapping_json: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
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
                
                # Generate hash
                row_hash = HashService.generate_hash(normalized_data)
                
                # Check for duplicates
                if HashService.is_duplicate(row_hash, existing_hashes):
                    duplicate_count += 1
                    continue
                
                # Match category using rules (only CategoryMatcher, no CSV category)
                category_id = category_matcher.match_category(normalized_data)
                
                # Find or create recipient
                recipient = None
                recipient_name = normalized_data.get('recipient')
                if recipient_name:
                    recipient = recipient_matcher.find_or_create_recipient(recipient_name)
                
                # Parse structured fields from normalized_data
                # Date: normalized_data['date'] is already ISO format (YYYY-MM-DD) from normalize_transaction_data
                transaction_date_str = normalized_data.get('date')
                from datetime import datetime
                transaction_date = datetime.fromisoformat(transaction_date_str).date() if transaction_date_str else None
                
                # Amount: already parsed as float/decimal
                amount = normalized_data.get('amount', 0.0)
                
                # Recipient and Purpose
                recipient_str = normalized_data.get('recipient', '')
                purpose = normalized_data.get('purpose', '')
                
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
        
        # Trigger recurring transaction detection after successful import
        # IMPORTANT: Always analyze ALL transactions for the account, not just newly imported ones
        recurring_count = 0
        if imported_count > 0 or duplicate_count > 0:  # Run even if only duplicates (might detect new patterns)
            try:
                detector = RecurringTransactionDetector(db)
                stats = detector.update_recurring_transactions(account_id)
                
                # Get total count of active recurring transactions
                from app.models.recurring_transaction import RecurringTransaction
                recurring_count = db.query(RecurringTransaction).filter(
                    RecurringTransaction.account_id == account_id,
                    RecurringTransaction.is_active == True
                ).count()
                
                print(f"✅ Recurring detection: {stats['created']} new, {stats['updated']} updated, {recurring_count} total active")
            except Exception as e:
                # Log error but don't fail the import
                print(f"⚠️  Warning: Could not detect recurring transactions: {str(e)}")
        
        # Save mapping configuration for future use
        if imported_count > 0:
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
            except Exception as e:
                # Log error but don't fail the import
                print(f"Warning: Could not save mappings: {str(e)}")
        
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
            "import_id": import_id  # Return import ID for frontend
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
