"""
Tests for CSV Import Router endpoints
"""
import pytest


def test_csv_import_router_imports():
    """Test that csv_import router can be imported"""
    from app.routers import csv_import
    
    assert hasattr(csv_import, 'router')
    assert csv_import.router is not None


def test_csv_import_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.csv_import import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_router_uses_csv_processor_service():
    """Test that CSV import router has csv processing functionality"""
    from app.routers import csv_import
    
    # Router should exist and handle CSV imports
    assert csv_import.router is not None


@pytest.mark.asyncio
async def test_get_available_banks():
    """Test get_available_banks endpoint"""
    from app.routers.csv_import import get_available_banks
    from unittest.mock import patch, MagicMock
    
    # Mock BankPresetMatcher
    mock_preset1 = MagicMock()
    mock_preset1.id = "sparkasse"
    mock_preset1.name = "Sparkasse"
    mock_preset1.description = "Sparkasse Bank"
    
    mock_preset2 = MagicMock()
    mock_preset2.id = "dkb"
    mock_preset2.name = "DKB"
    mock_preset2.description = "Deutsche Kreditbank"
    
    with patch('app.routers.csv_import.BankPresetMatcher') as mock_matcher_class:
        mock_matcher_class.get_all_presets.return_value = [mock_preset1, mock_preset2]
        
        result = await get_available_banks()
        
        # Verify result structure
        assert "banks" in result
        assert len(result["banks"]) == 2
        
        # Verify first bank
        assert result["banks"][0]["id"] == "sparkasse"
        assert result["banks"][0]["name"] == "Sparkasse"
        assert result["banks"][0]["description"] == "Sparkasse Bank"
        
        # Verify second bank
        assert result["banks"][1]["id"] == "dkb"
        assert result["banks"][1]["name"] == "DKB"
        assert result["banks"][1]["description"] == "Deutsche Kreditbank"


@pytest.mark.asyncio
async def test_detect_bank_from_csv_success():
    """Test detect_bank_from_csv endpoint with successful detection"""
    from app.routers.csv_import import detect_bank_from_csv
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"header1,header2,header3\nvalue1,value2,value3"
    
    # Mock CSV processor
    mock_df = MagicMock()
    mock_headers = ["header1", "header2", "header3"]
    
    # Mock bank preset
    mock_preset = MagicMock()
    mock_preset.name = "Test Bank"
    mock_preset.description = "Test Bank Description"
    mock_preset.mapping = {"field1": "value1"}
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.BankPresetMatcher') as mock_matcher_class:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = mock_headers
        mock_matcher_class.detect_bank.return_value = "test_bank"
        mock_matcher_class.get_preset.return_value = mock_preset
        
        result = await detect_bank_from_csv(mock_file)
        
        # Verify result
        assert result["detected"] is True
        assert result["bank_id"] == "test_bank"
        assert result["bank_name"] == "Test Bank"
        assert result["bank_description"] == "Test Bank Description"
        assert result["mapping"] == {"field1": "value1"}


@pytest.mark.asyncio
async def test_detect_bank_from_csv_no_detection():
    """Test detect_bank_from_csv endpoint with no bank detected"""
    from app.routers.csv_import import detect_bank_from_csv
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"header1,header2,header3\nvalue1,value2,value3"
    
    # Mock CSV processor
    mock_df = MagicMock()
    mock_headers = ["header1", "header2", "header3"]
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.BankPresetMatcher') as mock_matcher_class:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = mock_headers
        mock_matcher_class.detect_bank.return_value = None
        
        result = await detect_bank_from_csv(mock_file)
        
        # Verify result
        assert result["detected"] is False
        assert result["bank_id"] is None
        assert result["bank_name"] is None
        assert "message" in result


@pytest.mark.asyncio
async def test_detect_bank_from_csv_error():
    """Test detect_bank_from_csv endpoint with parsing error"""
    from app.routers.csv_import import detect_bank_from_csv
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"invalid,csv,data"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = Exception("Parse error")
        
        with pytest.raises(HTTPException) as exc_info:
            await detect_bank_from_csv(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Fehler beim Analysieren der CSV" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_bank_preset_success():
    """Test get_bank_preset endpoint with valid bank"""
    from app.routers.csv_import import get_bank_preset
    from unittest.mock import patch, MagicMock
    
    # Mock bank preset
    mock_preset = MagicMock()
    mock_preset.id = "sparkasse"
    mock_preset.name = "Sparkasse"
    mock_preset.description = "Sparkasse Bank"
    mock_preset.mapping = {"date": "Buchungstag", "amount": "Betrag"}
    mock_preset.delimiter = ";"
    mock_preset.decimal = ","
    mock_preset.date_format = "DD.MM.YYYY"
    
    with patch('app.routers.csv_import.BankPresetMatcher') as mock_matcher_class:
        mock_matcher_class.get_preset.return_value = mock_preset
        
        result = await get_bank_preset("sparkasse")
        
        # Verify result
        assert result["id"] == "sparkasse"
        assert result["name"] == "Sparkasse"
        assert result["description"] == "Sparkasse Bank"
        assert result["mapping"] == {"date": "Buchungstag", "amount": "Betrag"}
        assert result["delimiter"] == ";"
        assert result["decimal"] == ","
        assert result["date_format"] == "DD.MM.YYYY"


@pytest.mark.asyncio
async def test_get_bank_preset_not_found():
    """Test get_bank_preset endpoint with invalid bank"""
    from app.routers.csv_import import get_bank_preset
    from unittest.mock import patch
    from fastapi import HTTPException
    import pytest
    
    with patch('app.routers.csv_import.BankPresetMatcher') as mock_matcher_class:
        mock_matcher_class.get_preset.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_bank_preset("invalid_bank")
        
        assert exc_info.value.status_code == 404
        assert "Bank 'invalid_bank' nicht gefunden" in exc_info.value.detail


@pytest.mark.asyncio
async def test_preview_csv_file_success():
    """Test preview_csv_file endpoint with valid CSV"""
    from app.routers.csv_import import preview_csv_file
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"header1,header2\nvalue1,value2\nvalue3,value4"
    
    # Mock DataFrame
    mock_df = MagicMock()
    mock_df.__len__ = lambda self: 2
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, ";")
        mock_csv_processor.get_headers.return_value = ["header1", "header2"]
        mock_csv_processor.get_preview_rows.return_value = [["value1", "value2"], ["value3", "value4"]]
        
        result = await preview_csv_file(mock_file)
        
        # Verify result
        assert result["headers"] == ["header1", "header2"]
        assert result["sample_rows"] == [["value1", "value2"], ["value3", "value4"]]
        assert result["total_rows"] == 2
        assert result["detected_delimiter"] == ";"


@pytest.mark.asyncio
async def test_preview_csv_file_invalid():
    """Test preview_csv_file endpoint with invalid CSV"""
    from app.routers.csv_import import preview_csv_file
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"invalid,csv"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = ValueError("Invalid CSV")
        
        with pytest.raises(HTTPException) as exc_info:
            await preview_csv_file(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Invalid CSV file" in exc_info.value.detail


@pytest.mark.asyncio
async def test_suggest_mapping_success():
    """Test suggest_mapping endpoint with valid CSV"""
    from app.routers.csv_import import suggest_mapping
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"Buchungstag,Betrag,Empfaenger\n01.01.2023,100.50,Test"
    
    # Mock DataFrame
    mock_df = MagicMock()
    
    # Mock suggestions
    mock_suggestions = {
        "date": ("Buchungstag", 0.95, ["Datum"]),
        "amount": ("Betrag", 0.90, ["Summe"]),
        "recipient": ("Empfaenger", 0.85, ["Sender"])
    }
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester_class:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["Buchungstag", "Betrag", "Empfaenger"]
        mock_suggester_class.suggest_mappings.return_value = mock_suggestions
        
        result = await suggest_mapping(mock_file)
        
        # Verify result structure
        assert "suggestions" in result
        assert "date" in result["suggestions"]
        assert "amount" in result["suggestions"]
        assert "recipient" in result["suggestions"]
        
        # Verify date suggestion
        date_suggestion = result["suggestions"]["date"]
        assert date_suggestion.suggested_header == "Buchungstag"
        assert date_suggestion.confidence == 0.95
        assert date_suggestion.alternatives == ["Datum"]


@pytest.mark.asyncio
async def test_suggest_mapping_invalid_csv():
    """Test suggest_mapping endpoint with invalid CSV"""
    from app.routers.csv_import import suggest_mapping
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"invalid"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = ValueError("Invalid CSV")
        
        with pytest.raises(HTTPException) as exc_info:
            await suggest_mapping(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Invalid CSV file" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_advanced_success():
    """Test import_csv_advanced endpoint with successful import"""
    from app.routers.csv_import import import_csv_advanced
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test Recipient"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    mock_account.id = 1
    
    # Mock DataFrame and processed data
    mock_df = MagicMock()
    mock_mapped_data = [{
        'date': '2023-01-01',
        'amount': 100.50,
        'recipient': 'Test Recipient',
        'purpose': 'Test transaction',
        'currency': 'EUR'
    }]
    
    # Mock normalized data
    mock_normalized_data = {
        'date': '2023-01-01',
        'amount': 100.50,
        'recipient': 'Test Recipient',
        'purpose': 'Test transaction'
    }
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.id = 1
    
    # Mock import record
    mock_import_record = MagicMock()
    mock_import_record.id = 1
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.HashService') as mock_hash_service, \
         patch('app.routers.csv_import.CategoryMatcher') as mock_category_matcher_class, \
         patch('app.routers.csv_import.RecipientMatcher') as mock_recipient_matcher_class, \
         patch('app.routers.csv_import.ImportHistoryService') as mock_import_service, \
         patch('app.routers.csv_import.RecurringTransactionDetector') as mock_detector_class:
        
        # Setup mocks
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["date", "amount", "recipient"]
        mock_csv_processor.apply_mappings_advanced.return_value = mock_mapped_data
        mock_csv_processor.normalize_transaction_data.return_value = mock_normalized_data
        
        mock_suggester.validate_mapping.return_value = (True, [])
        
        mock_hash_service.generate_hash.return_value = "test_hash_123"
        mock_hash_service.is_duplicate.return_value = False
        
        mock_category_matcher = MagicMock()
        mock_category_matcher.match_category.return_value = 1
        mock_category_matcher_class.return_value = mock_category_matcher
        
        mock_recipient_matcher = MagicMock()
        mock_recipient_matcher.find_or_create_recipient.return_value = mock_recipient
        mock_recipient_matcher_class.return_value = mock_recipient_matcher
        
        mock_import_service.create_import_record.return_value = mock_import_record
        
        mock_detector = MagicMock()
        mock_detector.update_recurring_transactions.return_value = {"created": 0, "updated": 0}
        mock_detector_class.return_value = mock_detector
        
        # Mock DB query for existing hashes
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock recurring transaction count
        mock_recurring_query = MagicMock()
        mock_recurring_query.filter.return_value.count.return_value = 0
        mock_db.query.side_effect = lambda *args: mock_recurring_query if args and hasattr(args[0], '__name__') and 'RecurringTransaction' in str(args[0]) else mock_db.query.return_value
        
        # Test mapping JSON
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        result = await import_csv_advanced(1, mapping_json, mock_file, mock_db)
        
        # Verify result
        assert result["success"] is True
        assert result["imported_count"] == 1
        assert result["duplicate_count"] == 0
        assert result["error_count"] == 0
        assert "import_id" in result


@pytest.mark.asyncio
async def test_import_csv_advanced_invalid_mapping_json():
    """Test import_csv_advanced endpoint with invalid mapping JSON"""
    from app.routers.csv_import import import_csv_advanced
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount\n2023-01-01,100.50"
    
    with patch('app.routers.csv_import.verify_account_exists'):
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, "invalid json", mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "Invalid mapping JSON format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_advanced_invalid_mapping():
    """Test import_csv_advanced endpoint with invalid mapping configuration"""
    from app.routers.csv_import import import_csv_advanced
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount\n2023-01-01,100.50"
    
    # Mock account
    mock_account = MagicMock()
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester:
        
        mock_csv_processor.parse_csv_advanced.return_value = (MagicMock(), None)
        mock_csv_processor.get_headers.return_value = ["date", "amount"]
        mock_suggester.validate_mapping.return_value = (False, ["Missing required field: recipient"])
        
        mapping_json = '{"date": "date", "amount": "amount"}'
        
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "Invalid mapping" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_advanced_no_valid_data():
    """Test import_csv_advanced endpoint with no valid data after mapping"""
    from app.routers.csv_import import import_csv_advanced
    from unittest.mock import patch, MagicMock
    from fastapi import UploadFile, HTTPException
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount\n2023-01-01,100.50"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService'):
        
        mock_csv_processor.parse_csv_advanced.return_value = (MagicMock(), None)
        mock_csv_processor.get_headers.return_value = ["date", "amount"]
        mock_csv_processor.apply_mappings_advanced.return_value = []  # No valid data
        mock_suggester.validate_mapping.return_value = (True, [])
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "No valid data rows found in CSV after mapping" in exc_info.value.detail


@pytest.mark.asyncio
async def test_detect_bank_from_csv_value_error():
    """Test detect_bank_from_csv endpoint with ValueError"""
    from app.routers.csv_import import detect_bank_from_csv
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"invalid,csv,data"
    mock_file.filename = "test.csv"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = ValueError("Invalid CSV format")
        
        with pytest.raises(HTTPException) as exc_info:
            await detect_bank_from_csv(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Fehler beim Analysieren der CSV: Invalid CSV format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_detect_bank_from_csv_general_exception():
    """Test detect_bank_from_csv endpoint with general Exception"""
    from app.routers.csv_import import detect_bank_from_csv
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount\n2023-01-01,100.50"
    mock_file.filename = "test.csv"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            await detect_bank_from_csv(mock_file)
        
        assert exc_info.value.status_code == 400  # The code catches Exception and raises 400
        assert "Fehler beim Analysieren der CSV: Unexpected error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_suggest_mapping_value_error():
    """Test suggest_mapping endpoint with ValueError"""
    from app.routers.csv_import import suggest_mapping
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"invalid,csv,data"
    mock_file.filename = "test.csv"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = ValueError("Invalid CSV format")
        
        with pytest.raises(HTTPException) as exc_info:
            await suggest_mapping(mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "Invalid CSV file: Invalid CSV format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_suggest_mapping_general_exception():
    """Test suggest_mapping endpoint with general Exception"""
    from app.routers.csv_import import suggest_mapping
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount\n2023-01-01,100.50"
    mock_file.filename = "test.csv"
    
    with patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor:
        mock_csv_processor.parse_csv_advanced.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            await suggest_mapping(mock_file, MagicMock())
        
        assert exc_info.value.status_code == 500
        assert "Error analyzing CSV: Unexpected error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_advanced_datetime_parsing_error():
    """Test import_csv_advanced with datetime parsing error"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\ninvalid-date,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    # Mock data structures
    mock_df = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.to_dict.return_value = {"date": "date", "amount": "amount", "recipient": "recipient"}
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService'), \
         patch('app.routers.csv_import.CategoryMatcher'), \
         patch('app.routers.csv_import.RecipientMatcher'), \
         patch('app.routers.csv_import.HashService'), \
         patch('app.routers.csv_import.RecurringTransactionDetector'):
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["date", "amount", "recipient"]
        mock_csv_processor.apply_mappings_advanced.return_value = [
            {"date": "invalid-date", "amount": "100.50", "recipient": "Test"}
        ]
        mock_csv_processor.normalize_transaction_data.return_value = {
            "date": "invalid-date", "amount": 100.50, "recipient": "Test"
        }
        mock_suggester.validate_mapping.return_value = (True, [])
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        # This should trigger the datetime parsing error in the row processing loop
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        # Should fail due to datetime parsing error
        assert exc_info.value.status_code in [400, 500]


@pytest.mark.asyncio
async def test_import_csv_advanced_recurring_detection_error():
    """Test import_csv_advanced with recurring detection error"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile
    from unittest.mock import patch, MagicMock
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    # Mock data structures
    mock_df = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.to_dict.return_value = {"date": "date", "amount": "amount", "recipient": "recipient"}
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService'), \
         patch('app.routers.csv_import.CategoryMatcher') as mock_category_matcher, \
         patch('app.routers.csv_import.RecipientMatcher') as mock_recipient_matcher, \
         patch('app.routers.csv_import.HashService') as mock_hash_service, \
         patch('app.routers.csv_import.RecurringTransactionDetector') as mock_recurring_detector, \
         patch('app.routers.csv_import.Mapping') as mock_mapping_model:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["date", "amount", "recipient"]
        mock_csv_processor.apply_mappings_advanced.return_value = [
            {"date": "2023-01-01", "amount": "100.50", "recipient": "Test"}
        ]
        mock_csv_processor.normalize_transaction_data.return_value = {
            "date": "2023-01-01", "amount": 100.50, "recipient": "Test"
        }
        mock_suggester.validate_mapping.return_value = (True, [])
        mock_hash_service.generate_hash.return_value = "testhash"
        mock_hash_service.is_duplicate.return_value = False
        mock_category_matcher.return_value.match_category.return_value = 1
        mock_recipient_matcher.return_value.find_or_create_recipient.return_value = MagicMock(id=1)
        
        # Mock DB query for existing hashes
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock recurring transaction count
        mock_recurring_query = MagicMock()
        mock_recurring_query.filter.return_value.count.return_value = 0
        mock_db.query.side_effect = lambda *args: mock_recurring_query if args and hasattr(args[0], '__name__') and 'RecurringTransaction' in str(args[0]) else mock_db.query.return_value
        
        # Make recurring detection fail
        mock_recurring_detector.return_value.detect_and_create.side_effect = Exception("Recurring detection failed")
        
        # Mock the update_recurring_transactions to return stats
        mock_recurring_detector.return_value.update_recurring_transactions.return_value = {'created': 0, 'updated': 0}
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        # Should succeed despite recurring detection error (error is logged but not raised)
        result = await import_csv_advanced(1, mapping_json, mock_file, mock_db)
        
        assert result["success"] is True
        assert result["imported_count"] == 1


@pytest.mark.asyncio
async def test_import_csv_advanced_mapping_save_error():
    """Test import_csv_advanced with mapping save error"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile
    from unittest.mock import patch, MagicMock
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    # Mock data structures
    mock_df = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.to_dict.return_value = {"date": "date", "amount": "amount", "recipient": "recipient"}
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService'), \
         patch('app.routers.csv_import.CategoryMatcher') as mock_category_matcher, \
         patch('app.routers.csv_import.RecipientMatcher') as mock_recipient_matcher, \
         patch('app.routers.csv_import.HashService') as mock_hash_service, \
         patch('app.routers.csv_import.RecurringTransactionDetector') as mock_recurring_detector, \
         patch('app.routers.csv_import.Mapping') as mock_mapping_model:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["date", "amount", "recipient"]
        mock_csv_processor.apply_mappings_advanced.return_value = [
            {"date": "2023-01-01", "amount": "100.50", "recipient": "Test"}
        ]
        mock_csv_processor.normalize_transaction_data.return_value = {
            "date": "2023-01-01", "amount": 100.50, "recipient": "Test"
        }
        mock_suggester.validate_mapping.return_value = (True, [])
        mock_hash_service.generate_hash.return_value = "testhash"
        mock_hash_service.is_duplicate.return_value = False
        mock_category_matcher.return_value.match_category.return_value = 1
        mock_recipient_matcher.return_value.find_or_create_recipient.return_value = MagicMock(id=1)
        
        # Mock the query for recurring count to return 0
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 0
        mock_mapping_model.query = mock_query
        
        # Mock DB query for existing hashes
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock recurring transaction count
        mock_recurring_query = MagicMock()
        mock_recurring_query.filter.return_value.count.return_value = 0
        mock_db.query.side_effect = lambda *args: mock_recurring_query if args and hasattr(args[0], '__name__') and 'RecurringTransaction' in str(args[0]) else mock_db.query.return_value
        
        # Make mapping save fail
        mock_mapping_model.query.filter.return_value.delete.side_effect = Exception("DB save failed")
        
        # Mock the update_recurring_transactions to return stats
        mock_recurring_detector.return_value.update_recurring_transactions.return_value = {'created': 0, 'updated': 0}
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        # Should succeed despite mapping save error (error is logged but not raised)
        result = await import_csv_advanced(1, mapping_json, mock_file, mock_db)
        
        assert result["success"] is True
        assert result["imported_count"] == 1


@pytest.mark.asyncio
async def test_import_csv_advanced_partial_success():
    """Test import_csv_advanced with partial success (some errors)"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile
    from unittest.mock import patch, MagicMock
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test\n2023-01-02,invalid-amount,Test2"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    # Mock data structures
    mock_df = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.to_dict.return_value = {"date": "date", "amount": "amount", "recipient": "recipient"}
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService'), \
         patch('app.routers.csv_import.CategoryMatcher') as mock_category_matcher, \
         patch('app.routers.csv_import.RecipientMatcher') as mock_recipient_matcher, \
         patch('app.routers.csv_import.HashService') as mock_hash_service, \
         patch('app.routers.csv_import.RecurringTransactionDetector') as mock_recurring_detector, \
         patch('app.routers.csv_import.Mapping') as mock_mapping_model:
        
        mock_csv_processor.parse_csv_advanced.return_value = (mock_df, None)
        mock_csv_processor.get_headers.return_value = ["date", "amount", "recipient"]
        mock_csv_processor.apply_mappings_advanced.return_value = [
            {"date": "2023-01-01", "amount": "100.50", "recipient": "Test"},
            {"date": "2023-01-02", "amount": "invalid-amount", "recipient": "Test2"}
        ]
        
        # First call succeeds, second fails
        mock_csv_processor.normalize_transaction_data.side_effect = [
            {"date": "2023-01-01", "amount": 100.50, "recipient": "Test"},
            ValueError("Invalid amount")
        ]
        
        mock_suggester.validate_mapping.return_value = (True, [])
        mock_hash_service.generate_hash.return_value = "testhash"
        mock_hash_service.is_duplicate.return_value = False
        mock_category_matcher.return_value.match_category.return_value = 1
        mock_recipient_matcher.return_value.find_or_create_recipient.return_value = MagicMock(id=1)
        
        # Mock DB query for existing hashes
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock recurring transaction count
        mock_recurring_query = MagicMock()
        mock_recurring_query.filter.return_value.count.return_value = 0
        mock_db.query.side_effect = lambda *args: mock_recurring_query if args and hasattr(args[0], '__name__') and 'RecurringTransaction' in str(args[0]) else mock_db.query.return_value
        
        # Mock the query for recurring count to return 0
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 0
        mock_mapping_model.query = mock_query
        
        # Mock the update_recurring_transactions to return stats
        mock_recurring_detector.return_value.update_recurring_transactions.return_value = {'created': 0, 'updated': 0}
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        result = await import_csv_advanced(1, mapping_json, mock_file, mock_db)
        
        # Should have partial success
        assert result["success"] is True  # success = error_count == 0 or imported_count > 0
        assert result["imported_count"] == 1
        assert result["error_count"] == 1


@pytest.mark.asyncio
async def test_import_csv_advanced_httpexception_error():
    """Test import_csv_advanced with HTTPException during processing"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService') as mock_import_service:
        
        # Make HTTPException occur during CSV parsing (before mapping validation)
        mock_csv_processor.parse_csv_advanced.side_effect = HTTPException(status_code=400, detail="Test HTTP error")
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "Test HTTP error" in exc_info.value.detail
        
        # Verify import status was updated to failed
        mock_import_service.update_import_stats.assert_called_with(
            db=mock_import_service.update_import_stats.call_args[1]['db'],
            import_id=mock_import_service.update_import_stats.call_args[1]['import_id'],
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message="HTTP Exception during import"
        )


@pytest.mark.asyncio
async def test_import_csv_advanced_value_error():
    """Test import_csv_advanced with ValueError during processing"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService') as mock_import_service:
        
        # Make ValueError occur during CSV parsing (before mapping validation)
        mock_csv_processor.parse_csv_advanced.side_effect = ValueError("Invalid CSV data")
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        assert exc_info.value.status_code == 400
        assert "Invalid CSV file: Invalid CSV data" in exc_info.value.detail
        
        # Verify import status was updated to failed
        mock_import_service.update_import_stats.assert_called_with(
            db=mock_import_service.update_import_stats.call_args[1]['db'],
            import_id=mock_import_service.update_import_stats.call_args[1]['import_id'],
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message="Invalid CSV data"
        )


@pytest.mark.asyncio
async def test_import_csv_advanced_general_exception():
    """Test import_csv_advanced with general Exception during processing"""
    from app.routers.csv_import import import_csv_advanced
    from fastapi import UploadFile, HTTPException
    from unittest.mock import patch, MagicMock
    import pytest
    
    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.read.return_value = b"date,amount,recipient\n2023-01-01,100.50,Test"
    mock_file.filename = "test.csv"
    
    # Mock account
    mock_account = MagicMock()
    
    with patch('app.routers.csv_import.verify_account_exists', return_value=mock_account), \
         patch('app.routers.csv_import.CsvProcessor') as mock_csv_processor, \
         patch('app.routers.csv_import.MappingSuggester') as mock_suggester, \
         patch('app.routers.csv_import.ImportHistoryService') as mock_import_service:
        
        # Make general Exception occur during CSV parsing (before mapping validation)
        mock_csv_processor.parse_csv_advanced.side_effect = Exception("Unexpected processing error")
        
        mapping_json = '{"date": "date", "amount": "amount", "recipient": "recipient"}'
        
        with pytest.raises(HTTPException) as exc_info:
            await import_csv_advanced(1, mapping_json, mock_file, MagicMock())
        
        assert exc_info.value.status_code == 500
        assert "Error processing CSV: Unexpected processing error" in exc_info.value.detail
        
        # Verify import status was updated to failed
        mock_import_service.update_import_stats.assert_called_with(
            db=mock_import_service.update_import_stats.call_args[1]['db'],
            import_id=mock_import_service.update_import_stats.call_args[1]['import_id'],
            row_count=0,
            rows_inserted=0,
            rows_duplicated=0,
            status='failed',
            error_message="Unexpected processing error"
        )
