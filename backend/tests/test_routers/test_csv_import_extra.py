import json
import pytest

from fastapi import HTTPException

from app.routers import csv_import


class FakeUpload:
    def __init__(self, content: bytes, filename: str = "test.csv"):
        self._content = content
        self.filename = filename

    async def read(self):
        return self._content


class FakeDBQuery:
    def __init__(self, count_val=0):
        self._count = count_val

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []

    def delete(self):
        return None

    def first(self):
        return None

    def count(self):
        return self._count


class FakeDB:
    def __init__(self, count_val=0):
        self._q = FakeDBQuery(count_val=count_val)

    def query(self, *args, **kwargs):
        return self._q

    def add(self, obj):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


@pytest.mark.asyncio
async def test_detect_bank_not_found(monkeypatch):
    # Make parse return headers that don't match any bank
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: ([], ',')))
    monkeypatch.setattr(csv_import.CsvProcessor, 'get_headers', staticmethod(lambda df: ['A', 'B']))
    monkeypatch.setattr(csv_import.BankPresetMatcher, 'detect_bank', staticmethod(lambda headers: None))

    upload = FakeUpload(b"a,b\n1,2")
    res = await csv_import.detect_bank_from_csv(file=upload)
    assert res['detected'] is False
    assert 'nicht automatisch erkannt' in res['message']


@pytest.mark.asyncio
async def test_get_bank_preset_not_found(monkeypatch):
    monkeypatch.setattr(csv_import.BankPresetMatcher, 'get_preset', staticmethod(lambda bid: None))
    with pytest.raises(HTTPException):
        await csv_import.get_bank_preset('nope')


@pytest.mark.asyncio
async def test_preview_csv_value_and_general_error(monkeypatch):
    upload = FakeUpload(b"a,b\n1,2")

    # ValueError path
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (_ for _ in ()).throw(ValueError('bad csv'))))
    with pytest.raises(HTTPException) as exc:
        await csv_import.preview_csv_file(file=upload, db=None)
    assert exc.value.status_code == 400

    # Generic exception path
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (_ for _ in ()).throw(Exception('boom'))))
    with pytest.raises(HTTPException) as exc2:
        await csv_import.preview_csv_file(file=upload, db=None)
    assert exc2.value.status_code == 500


@pytest.mark.asyncio
async def test_suggest_mapping_value_error(monkeypatch):
    upload = FakeUpload(b"a,b\n1,2")
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (_ for _ in ()).throw(ValueError('bad'))))
    with pytest.raises(HTTPException) as exc:
        await csv_import.suggest_mapping(file=upload, db=None)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_import_invalid_mapping_json(monkeypatch):
    # invalid JSON should raise HTTPException
    upload = FakeUpload(b"a,b\n1,2", filename='in.csv')
    monkeypatch.setattr(csv_import, 'verify_account_exists', lambda aid, db: object())
    with pytest.raises(HTTPException) as exc:
        await csv_import.import_csv_advanced(account_id=1, mapping_json='notjson', file=upload, db=FakeDB())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_import_mapping_validation_fails_updates_import_history(monkeypatch):
    # Prepare good JSON but mapping validation fails
    upload = FakeUpload(b"h1,h2\n1,2", filename='f.csv')
    monkeypatch.setattr(csv_import, 'verify_account_exists', lambda aid, db: object())
    # Create import record
    monkeypatch.setattr(csv_import.ImportHistoryService, 'create_import_record', staticmethod(lambda **kwargs: type('R', (), {'id': 99})()))
    # parse returns df with headers
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (['dummy_df'], ',')))
    monkeypatch.setattr(csv_import.CsvProcessor, 'get_headers', staticmethod(lambda df: ['h1', 'h2']))
    # mapping validation returns false
    monkeypatch.setattr(csv_import.MappingSuggester, 'validate_mapping', staticmethod(lambda m, h: (False, ['error'])))

    monkeypatch.setattr(csv_import.ImportHistoryService, 'update_import_stats', staticmethod(lambda **kwargs: None))

    with pytest.raises(HTTPException):
        await csv_import.import_csv_advanced(account_id=1, mapping_json=json.dumps({'a': 'b'}), file=upload, db=FakeDB())


@pytest.mark.asyncio
async def test_import_no_mapped_data_updates_import_history(monkeypatch):
    upload = FakeUpload(b"h1,h2\n1,2", filename='f.csv')
    monkeypatch.setattr(csv_import, 'verify_account_exists', lambda aid, db: object())
    monkeypatch.setattr(csv_import.ImportHistoryService, 'create_import_record', staticmethod(lambda **kwargs: type('R', (), {'id': 100})()))
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (['dummy_df'], ',')))
    monkeypatch.setattr(csv_import.CsvProcessor, 'get_headers', staticmethod(lambda df: ['h1', 'h2']))
    # mapping valid
    monkeypatch.setattr(csv_import.MappingSuggester, 'validate_mapping', staticmethod(lambda m, h: (True, [])))
    # but apply_mappings_advanced returns empty
    monkeypatch.setattr(csv_import.CsvProcessor, 'apply_mappings_advanced', staticmethod(lambda df, m: []))

    monkeypatch.setattr(csv_import.ImportHistoryService, 'update_import_stats', staticmethod(lambda **kwargs: None))

    with pytest.raises(HTTPException):
        await csv_import.import_csv_advanced(account_id=1, mapping_json=json.dumps({'a': 'b'}), file=upload, db=FakeDB())


@pytest.mark.asyncio
async def test_import_parse_raises_generic_updates_import_history(monkeypatch):
    upload = FakeUpload(b"badcontent", filename='f.csv')
    monkeypatch.setattr(csv_import, 'verify_account_exists', lambda aid, db: object())
    monkeypatch.setattr(csv_import.ImportHistoryService, 'create_import_record', staticmethod(lambda **kwargs: type('R', (), {'id': 101})()))
    # make parse raise generic exception
    monkeypatch.setattr(csv_import.CsvProcessor, 'parse_csv_advanced', staticmethod(lambda c: (_ for _ in ()).throw(Exception('boom'))))

    monkeypatch.setattr(csv_import.ImportHistoryService, 'update_import_stats', staticmethod(lambda **kwargs: None))

    with pytest.raises(HTTPException):
        await csv_import.import_csv_advanced(account_id=1, mapping_json=json.dumps({'a': 'b'}), file=upload, db=FakeDB())
