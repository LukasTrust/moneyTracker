"""
Quick tests for response/auxiliary schema classes that were lightly covered.

These are small, focused checks to ensure constructors/validators and
`from_attributes` behavior work as expected for a few important models.
"""
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest


def test_csv_import_response_and_suggestions():
    from app.schemas.csv_import import (
        CsvImportRequest,
        CsvImportMapping,
        CsvImportPreview,
        CsvPreviewRow,
        CsvImportResponse,
        MappingSuggestion,
        CsvImportSuggestions,
    )

    mapping = CsvImportMapping(date="A", amount="B", recipient="C", purpose="D")
    req = CsvImportRequest(account_id=1, mapping=mapping)
    assert req.mapping.date == "A"

    row = CsvPreviewRow(row_number=1, data={"A": "01.01.2024", "B": "10.00"})
    preview = CsvImportPreview(headers=["A", "B"], sample_rows=[row], total_rows=2)
    assert preview.total_rows == 2
    assert preview.detected_delimiter == ","

    resp = CsvImportResponse(success=True, message="ok", imported_count=2, duplicate_count=0, error_count=0, total_rows=2)
    assert resp.success is True

    ms = MappingSuggestion(field_name="date", suggested_header="A", confidence=0.9, alternatives=["Datum"])
    suggestions = CsvImportSuggestions(suggestions={"date": ms})
    assert "date" in suggestions.suggestions


def test_insight_response_from_attributes():
    from app.schemas.insight import InsightResponse

    now = datetime.now()
    # create an object with attributes instead of a dict to exercise from_attributes
    obj = SimpleNamespace(
        id=1,
        account_id=None,
        insight_type="mom_increase",
        severity="info",
        title="T",
        description="D",
        insight_data=None,
        priority=5,
        cooldown_hours=24,
        valid_until=None,
        is_dismissed=False,
        dismissed_at=None,
        last_shown_at=None,
        show_count=0,
        created_at=now,
    )

    ir = InsightResponse.model_validate(obj)
    assert ir.id == 1
    assert ir.created_at == now


def test_transfer_response_and_with_details():
    from app.schemas.transfer import TransferResponse, TransferWithDetails

    now = datetime.now()
    tr = TransferResponse(
        id=1,
        amount=Decimal("10.00"),
        transfer_date=date.today(),
        from_transaction_id=1,
        to_transaction_id=2,
        is_auto_detected=False,
        confidence_score=Decimal("0.5"),
        created_at=now,
        updated_at=now,
    )
    assert tr.id == 1

    twd = TransferWithDetails(**tr.model_dump(), from_transaction={"id": 1}, to_transaction={"id": 2}, from_account_name="A", to_account_name="B")
    assert twd.from_account_name == "A"


def test_recurring_transaction_response_construction():
    from app.schemas.recurring_transaction import RecurringTransactionResponse

    rr = RecurringTransactionResponse(
        id=1,
        account_id=1,
        recipient="X",
        average_amount=10.0,
        average_interval_days=30,
        first_occurrence=date(2024, 1, 1),
        last_occurrence=date(2024, 3, 1),
        occurrence_count=3,
        is_active=True,
        is_manually_overridden=False,
        next_expected_date=date(2024, 4, 1),
        confidence_score=0.9,
        created_at=date(2024, 1, 1),
        updated_at=date(2024, 3, 1),
    )

    assert rr.occurrence_count == 3
