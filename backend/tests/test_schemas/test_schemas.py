"""
Tests for Pydantic schema models in `app.schemas`.

These tests exercise basic validation rules and convenience helpers
so we quickly catch regressions in the schemas.
"""
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_transfer_create_valid_and_invalid():
    from app.schemas.transfer import TransferCreate

    # valid instance
    valid = TransferCreate(
        amount=Decimal("100.00"),
        transfer_date=date.today(),
        from_transaction_id=1,
        to_transaction_id=2,
        notes="ok",
    )

    assert valid.amount == Decimal("100.00")
    assert valid.from_transaction_id == 1

    # invalid: non-positive amount
    with pytest.raises(ValidationError):
        TransferCreate(
            amount=Decimal("0"),
            transfer_date=date.today(),
            from_transaction_id=1,
            to_transaction_id=2,
        )

    # invalid: non-positive transaction id
    with pytest.raises(ValidationError):
        TransferCreate(
            amount=Decimal("10.00"),
            transfer_date=date.today(),
            from_transaction_id=0,
            to_transaction_id=2,
        )


def test_transfer_candidate_confidence_bounds():
    from app.schemas.transfer import TransferCandidate

    # valid confidence
    valid = TransferCandidate(
        from_transaction_id=1,
        to_transaction_id=2,
        from_transaction={"id": 1},
        to_transaction={"id": 2},
        amount=Decimal("10.00"),
        transfer_date=date.today(),
        confidence_score=Decimal("0.5"),
        match_reason="match",
    )

    assert valid.confidence_score == Decimal("0.5")

    # out of range confidence (>1)
    with pytest.raises(ValidationError):
        TransferCandidate(
            from_transaction_id=1,
            to_transaction_id=2,
            from_transaction={"id": 1},
            to_transaction={"id": 2},
            amount=Decimal("10.00"),
            transfer_date=date.today(),
            confidence_score=Decimal("1.1"),
            match_reason="match",
        )


def test_transfer_detection_request_defaults():
    from app.schemas.transfer import TransferDetectionRequest

    req = TransferDetectionRequest()
    # default min_confidence should be 0.7
    # pydantic will coerce to Decimal for the field type if declared so in the model
    assert float(req.min_confidence) == pytest.approx(0.7)
    assert req.auto_create is False


def test_csv_field_mapping_and_helpers():
    from app.schemas.csv_import import FieldMapping, CsvImportMapping

    # valid field mapping
    fm = FieldMapping(csv_header="Buchungstag", field_name="date")
    assert fm.field_name == "date"

    # invalid field_name
    with pytest.raises(ValidationError):
        FieldMapping(csv_header="X", field_name="not_a_field")

    # CsvImportMapping helpers
    cim = CsvImportMapping(date="A", amount="B", recipient="C", purpose=None)
    d = cim.to_dict()
    assert "purpose" not in d
    headers = cim.get_csv_headers()
    assert set(headers) == {"A", "B", "C"}


def test_recurring_transaction_validations():
    from app.schemas.recurring_transaction import RecurringTransactionCreate

    # valid occurrence_count >= 3
    ok = RecurringTransactionCreate(
        recipient="Test",
        average_amount=10.0,
        average_interval_days=30,
        account_id=1,
        first_occurrence=date.today(),
        last_occurrence=date.today(),
        occurrence_count=3,
    )
    assert ok.occurrence_count == 3

    # invalid occurrence_count < 3
    with pytest.raises(ValidationError):
        RecurringTransactionCreate(
            recipient="Test",
            average_amount=10.0,
            average_interval_days=30,
            account_id=1,
            first_occurrence=date.today(),
            last_occurrence=date.today(),
            occurrence_count=2,
        )


def test_insight_priority_and_cooldown_bounds():
    from app.schemas.insight import InsightBase

    # valid
    ok = InsightBase(
        insight_type="mom_increase",
        title="t",
        description="d",
        priority=5,
        cooldown_hours=24,
    )
    assert ok.priority == 5

    # invalid priority
    with pytest.raises(ValidationError):
        InsightBase(
            insight_type="x",
            title="t",
            description="d",
            priority=11,
            cooldown_hours=24,
        )

    # invalid cooldown
    with pytest.raises(ValidationError):
        InsightBase(
            insight_type="x",
            title="t",
            description="d",
            priority=5,
            cooldown_hours=0,
        )
