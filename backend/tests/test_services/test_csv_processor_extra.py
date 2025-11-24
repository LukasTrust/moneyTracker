import io
import pandas as pd
import pytest

from app.services import csv_processor


def test_detect_encoding_monkeypatched(monkeypatch):
    # Force chardet to return None to exercise default fallback
    monkeypatch.setattr(csv_processor.chardet, 'detect', lambda b: {'encoding': None})
    enc = csv_processor.CsvProcessor.detect_encoding(b'abc')
    assert enc == 'utf-8'


def test_parse_csv_various_separators():
    # Comma
    content = b"col1,col2\n1,2\n3,4"
    df = csv_processor.CsvProcessor.parse_csv(content, encoding='utf-8')
    assert list(df.columns) == ['col1', 'col2']

    # Semicolon
    content = b"a;b\n5;6\n7;8"
    df = csv_processor.CsvProcessor.parse_csv(content, encoding='utf-8')
    assert list(df.columns) == ['a', 'b']

    # Tab
    content = b"x\t y\n9\t10"
    # ensure there are two columns despite odd spacing
    df = csv_processor.CsvProcessor.parse_csv(content, encoding='utf-8')
    assert len(df.columns) >= 2


def test_parse_csv_fails():
    # Single column only -> should raise
    content = b"onlyone\nvalue1\nvalue2"
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.parse_csv(content, encoding='utf-8')


def test_get_headers_and_sample_rows():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
    headers = csv_processor.CsvProcessor.get_headers(df)
    assert headers == ['a', 'b']
    samples = csv_processor.CsvProcessor.get_sample_rows(df, n=2)
    assert samples == [[1, 'x'], [2, 'y']]


def test_apply_mappings_and_preview_rows():
    df = pd.DataFrame({'Date': ['2024-01-01', ''], 'Amount': ['1.234,56', None], 'Foo': ['bar', '']})
    mappings = {'Date': 'date', 'Amount': 'amount', 'Foo': 'foo'}
    mapped = csv_processor.CsvProcessor.apply_mappings(df, mappings)
    assert mapped[0]['date'] == '2024-01-01'
    assert mapped[0]['amount'] == '1.234,56'
    # empty and None become None in mapping
    assert mapped[1]['date'] is None
    preview = csv_processor.CsvProcessor.get_preview_rows(df, n=2)
    assert preview[0]['row_number'] == 1
    assert preview[1]['data']['Date'] is None


@pytest.mark.parametrize("s,expected", [
    ("", 0.0),
    ("-1.234,56", -1234.56),
    ("1,234.56", 1234.56),
    ("123,45", 123.45),
    ("1,234", 1234.0),
    ("notanumber", 0.0),
])
def test_normalize_amount_variants(s, expected):
    assert csv_processor.CsvProcessor.normalize_amount(s) == expected


def test_detect_delimiter_and_parse_csv_advanced():
    # semicolon in sample
    content = "h1;h2\n1;2\n3;4".encode('utf-8')
    delim = csv_processor.CsvProcessor.detect_delimiter(content, encoding='utf-8')
    assert delim == ';'
    df, det = csv_processor.CsvProcessor.parse_csv_advanced(content, encoding='utf-8')
    assert det == ';'
    assert list(df.columns) == ['h1', 'h2']


def test_parse_csv_advanced_errors():
    # less than 2 columns
    content = b"only\n1\n2"
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.parse_csv_advanced(content, encoding='utf-8')

    # empty file (header only) -> dataframe length 0
    content = b"a,b\n"
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.parse_csv_advanced(content, encoding='utf-8')


def test_apply_mappings_advanced_and_parse_date():
    df = pd.DataFrame({'Buchungstag': ['31.12.2024', '01.01.24', 'bad'], 'Betrag': ['1,00', '2,00', '3,00']})
    mapping = {'date': 'Buchungstag', 'amount': 'Betrag'}
    res = csv_processor.CsvProcessor.apply_mappings_advanced(df, mapping)
    # function does not validate date strings here; all three rows have both fields so are included
    assert len(res) == 3
    # parse date formats
    d1 = csv_processor.CsvProcessor.parse_date('31.12.2024')
    assert d1 is not None and d1.year == 2024
    assert csv_processor.CsvProcessor.parse_date('notadate') is None


def test_parse_csv_calls_detect_encoding(monkeypatch):
    # Ensure detect_encoding is invoked when encoding is None
    called = {}

    def fake_detect(b):
        called['yes'] = True
        return 'utf-8'

    monkeypatch.setattr(csv_processor.CsvProcessor, 'detect_encoding', staticmethod(fake_detect))
    content = b"c1,c2\n1,2"
    df = csv_processor.CsvProcessor.parse_csv(content, encoding=None)
    assert 'yes' in called
    assert list(df.columns) == ['c1', 'c2']


def test_parse_csv_read_csv_raises_then_succeeds(monkeypatch):
    # Simulate pandas.read_csv raising on first two separators then succeeding
    # use existing pandas imported as pd

    calls = {'count': 0}

    def fake_read_csv(buff, encoding, sep, decimal, thousands, dtype, keep_default_na):
        calls['count'] += 1
        if sep in [',', ';']:
            raise ValueError('simulated parse error')
        # return a simple dataframe for tab
        return pd.DataFrame({'t1': ['a'], 't2': ['b']})

    monkeypatch.setattr(csv_processor.pd, 'read_csv', fake_read_csv)
    content = b"t1\tt2\na\tb"
    df = csv_processor.CsvProcessor.parse_csv(content, encoding='utf-8')
    assert list(df.columns) == ['t1', 't2']
    assert calls['count'] >= 1


def test_detect_delimiter_decode_error_returns_comma():
    # Force a decoding error by using ascii with non-ascii bytes
    content = bytes([0xff, 0xfe, 0xfd]) + b"\n"
    delim = csv_processor.CsvProcessor.detect_delimiter(content, encoding='ascii')
    assert delim == ','


def test_apply_mappings_advanced_with_none_mapping():
    # mapping contains a None value which should be ignored
    df = pd.DataFrame({'A': ['1'], 'B': ['2']})
    mapping = {'date': 'A', 'amount': None}
    res = csv_processor.CsvProcessor.apply_mappings_advanced(df, mapping)
    # since 'amount' mapping is None the reverse map won't include it -> rows missing amount so excluded
    assert res == []


def test_normalize_transaction_data_ok_and_errors():
    # valid
    row = {'date': '31.12.2024', 'amount': '-1.234,56', 'recipient': ' Alice ', 'purpose': 'fee'}
    norm = csv_processor.CsvProcessor.normalize_transaction_data(row)
    assert norm['date'].startswith('2024-12-31')
    assert norm['amount'] == -1234.56
    assert norm['recipient'] == 'Alice'
    assert norm['purpose'] == 'fee'

    # missing date
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.normalize_transaction_data({'amount': '1,00', 'recipient': 'Bob'})

    # invalid date
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.normalize_transaction_data({'date': 'bad', 'amount': '1,00', 'recipient': 'Bob'})

    # missing amount
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.normalize_transaction_data({'date': '31.12.2024', 'recipient': 'Bob'})

    # missing recipient
    with pytest.raises(ValueError):
        csv_processor.CsvProcessor.normalize_transaction_data({'date': '31.12.2024', 'amount': '1,00'})
