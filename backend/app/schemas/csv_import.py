"""
CSV Import Schemas - Advanced CSV import with flexible mapping
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Optional, List, Any
from datetime import datetime


class FieldMapping(BaseModel):
    """Mapping configuration for a single field"""
    csv_header: str = Field(..., description="CSV column header name")
    field_name: str = Field(..., description="Standard field name (date, amount, recipient, purpose)")
    
    @field_validator('field_name')
    @classmethod
    def validate_field_name(cls, v):
        """Validate that field_name is one of the allowed values"""
        allowed_fields = ['date', 'amount', 'recipient', 'purpose']
        if v not in allowed_fields:
            raise ValueError(f"field_name must be one of: {', '.join(allowed_fields)}")
        return v


class CsvImportMapping(BaseModel):
    """Complete mapping configuration for CSV import (4 fields: 3 required + 1 optional)"""
    date: str = Field(..., description="CSV header for date field")
    amount: str = Field(..., description="CSV header for amount field")
    recipient: str = Field(..., description="CSV header for recipient/sender field")
    purpose: Optional[str] = Field(None, description="CSV header for purpose/description field (optional)")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.model_dump().items() if v is not None}
    
    def get_csv_headers(self) -> List[str]:
        """Get list of all mapped CSV headers"""
        return [v for v in self.model_dump().values() if v is not None]


class CsvImportRequest(BaseModel):
    """Request model for advanced CSV import"""
    account_id: int = Field(..., description="Target account ID")
    mapping: CsvImportMapping = Field(..., description="Field mapping configuration")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": 1,
                "mapping": {
                    "date": "Buchungstag",
                    "amount": "Betrag",
                    "recipient": "Empfänger/Sender",
                    "purpose": "Verwendungszweck"
                }
            }
        }
    )


class CsvPreviewRow(BaseModel):
    """Single row in CSV preview"""
    row_number: int
    data: Dict[str, Any]


class CsvImportPreview(BaseModel):
    """Preview response for CSV import"""
    headers: List[str] = Field(..., description="List of CSV column headers")
    sample_rows: List[CsvPreviewRow] = Field(..., description="Sample rows from CSV")
    total_rows: int = Field(..., description="Total number of data rows in CSV")
    detected_delimiter: str = Field(default=",", description="Detected CSV delimiter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "headers": ["Buchungstag", "Betrag", "Empfänger/Sender", "Verwendungszweck"],
                "sample_rows": [
                    {
                        "row_number": 1,
                        "data": {
                            "Buchungstag": "01.01.2024",
                            "Betrag": "-50.00",
                            "Empfänger/Sender": "REWE Markt",
                            "Verwendungszweck": "Einkauf Lebensmittel"
                        }
                    }
                ],
                "total_rows": 120,
                "detected_delimiter": ","
            }
        }


class CsvImportResponse(BaseModel):
    """Response model for CSV import operation"""
    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Success/error message")
    imported_count: int = Field(default=0, description="Number of rows successfully imported")
    duplicate_count: int = Field(default=0, description="Number of duplicate rows skipped")
    error_count: int = Field(default=0, description="Number of rows with errors")
    total_rows: int = Field(..., description="Total number of rows processed")
    errors: Optional[List[str]] = Field(default=None, description="List of error messages")
    recurring_detected: Optional[int] = Field(default=None, description="Number of recurring transactions detected")
    import_id: Optional[int] = Field(default=None, description="Import history record ID")
    transfer_candidates: Optional[List[Dict[str, Any]]] = Field(default=None, description="Potential transfer matches detected during import")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully imported 115 transactions. Found 8 recurring contracts.",
                "imported_count": 115,
                "duplicate_count": 5,
                "error_count": 0,
                "total_rows": 120,
                "errors": None,
                "recurring_detected": 8,
                "import_id": 42,
                "transfer_candidates": []
            }
        }


class MappingSuggestion(BaseModel):
    """Suggested mapping based on CSV headers"""
    field_name: str = Field(..., description="Standard field name")
    suggested_header: Optional[str] = Field(None, description="Suggested CSV header")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    alternatives: List[str] = Field(default_factory=list, description="Alternative suggestions")


class CsvImportSuggestions(BaseModel):
    """Complete set of mapping suggestions"""
    suggestions: Dict[str, MappingSuggestion] = Field(..., description="Suggestions per field")
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": {
                    "date": {
                        "field_name": "date",
                        "suggested_header": "Buchungstag",
                        "confidence": 0.95,
                        "alternatives": ["Datum", "Valutadatum"]
                    },
                    "amount": {
                        "field_name": "amount",
                        "suggested_header": "Betrag",
                        "confidence": 0.98,
                        "alternatives": ["Betrag (EUR)", "Umsatz"]
                    },
                    "recipient": {
                        "field_name": "recipient",
                        "suggested_header": "Empfänger/Sender",
                        "confidence": 0.90,
                        "alternatives": ["Empfänger", "Kontoinhaber"]
                    },
                    "purpose": {
                        "field_name": "purpose",
                        "suggested_header": "Verwendungszweck",
                        "confidence": 0.88,
                        "alternatives": ["Beschreibung", "Buchungstext"]
                    }
                }
            }
        }


class BulkImportFileResult(BaseModel):
    """Result for a single file in bulk import"""
    filename: str = Field(..., description="Name of the imported file")
    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Success/error message")
    imported_count: int = Field(default=0, description="Number of rows successfully imported")
    duplicate_count: int = Field(default=0, description="Number of duplicate rows skipped")
    error_count: int = Field(default=0, description="Number of rows with errors")
    total_rows: int = Field(default=0, description="Total number of rows processed")
    errors: Optional[List[str]] = Field(default=None, description="List of error messages")
    import_id: Optional[int] = Field(default=None, description="Import history record ID")


class BulkImportResponse(BaseModel):
    """Response model for bulk CSV import operation"""
    success: bool = Field(..., description="Whether bulk import completed")
    message: str = Field(..., description="Summary message")
    total_files: int = Field(..., description="Total number of files processed")
    successful_files: int = Field(..., description="Number of files imported successfully")
    failed_files: int = Field(..., description="Number of files that failed")
    total_imported_count: int = Field(default=0, description="Total rows imported across all files")
    total_duplicate_count: int = Field(default=0, description="Total duplicates across all files")
    total_error_count: int = Field(default=0, description="Total errors across all files")
    file_results: List[BulkImportFileResult] = Field(..., description="Results for each file")
    recurring_detected: Optional[int] = Field(default=None, description="Total recurring transactions detected")
    transfer_candidates: Optional[List[Dict[str, Any]]] = Field(default=None, description="Potential transfer matches detected")
