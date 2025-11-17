import pandas as pd
from app.services.csv_processor import CsvProcessor
from io import BytesIO


def test_normalize_amount_variants():
    assert CsvProcessor.normalize_amount("-1.234,56") == -1234.56
    assert CsvProcessor.normalize_amount("1,234.56") == 1234.56
    assert CsvProcessor.normalize_amount("") == 0.0
    assert CsvProcessor.normalize_amount("abc") == 0.0


def test_detect_delimiter_semicolon():
    content = "col1;col2;col3\nval1;val2;val3\n".encode('utf-8')
    delim = CsvProcessor.detect_delimiter(content, encoding='utf-8')
    assert delim == ';'


def test_parse_date_various():
    assert CsvProcessor.parse_date('31.12.2024') is not None
    assert CsvProcessor.parse_date('2024-12-31') is not None
    assert CsvProcessor.parse_date('') is None


def test_apply_mappings_advanced_and_preview():
    df = pd.DataFrame({
        'Buchungstag': ['2024-11-15', '2024-11-14'],
        'Betrag': ['-42.50', '100.00'],
        'Empfänger': ['REWE', 'Gehalt']
    })

    mapping = {'date': 'Buchungstag', 'amount': 'Betrag', 'recipient': 'Empfänger'}
    result = CsvProcessor.apply_mappings_advanced(df, mapping)
    # Both rows have date and amount -> included
    assert len(result) == 2

    preview = CsvProcessor.get_preview_rows(df, n=2)
    assert isinstance(preview, list) and len(preview) == 2
