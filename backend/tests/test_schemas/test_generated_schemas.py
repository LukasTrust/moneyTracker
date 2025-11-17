"""
Auto-generated tests for the Pydantic schema modules not yet covered by
`backend/tests/test_schemas/test_schemas.py`.

These focus on validation boundaries and simple helpers.
"""
from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_account_validations():
    from app.schemas.account import AccountCreate, AccountUpdate

    # valid
    a = AccountCreate(name="Checking", currency="USD", initial_balance=Decimal("10.00"))
    assert a.name == "Checking"
    assert a.currency == "USD"

    # invalid: empty name
    with pytest.raises(ValidationError):
        AccountCreate(name="", currency="EUR")

    # invalid: currency length != 3
    with pytest.raises(ValidationError):
        AccountCreate(name="A", currency="EURO")

    # update accepts partial fields
    upd = AccountUpdate(name=None)
    assert upd.name is None


def test_budget_validations():
    from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetPeriodEnum

    start = date(2024, 1, 1)
    end = date(2024, 1, 31)

    ok = BudgetCreate(category_id=1, period=BudgetPeriodEnum.MONTHLY, amount=Decimal("100.00"), start_date=start, end_date=end)
    assert ok.amount == Decimal("100.00")

    # invalid: amount <= 0
    with pytest.raises(ValidationError):
        BudgetCreate(category_id=1, period=BudgetPeriodEnum.MONTHLY, amount=Decimal("0"), start_date=start, end_date=end)

    # invalid: end_date before start_date
    with pytest.raises(ValidationError):
        BudgetCreate(category_id=1, period=BudgetPeriodEnum.MONTHLY, amount=Decimal("10"), start_date=end, end_date=start)

    # BudgetUpdate should validate end_date if both provided
    with pytest.raises(ValidationError):
        BudgetUpdate(start_date=end, end_date=start)


def test_category_validations_and_defaults():
    from app.schemas.category import CategoryBase, CategoryUpdate

    cb = CategoryBase(name="Food", color="#00FF00")
    assert cb.mappings is not None

    # invalid color
    with pytest.raises(ValidationError):
        CategoryBase(name="X", color="green")

    # update allows optional fields
    cu = CategoryUpdate(name=None)
    assert cu.name is None


def test_data_row_models():
    from app.schemas.data_row import DataRowResponse, DataRowListResponse

    now = datetime.utcnow()
    dr = DataRowResponse(id=1, account_id=2, row_hash="abc", data={"a": 1}, created_at=now)
    assert dr.id == 1
    assert dr.data["a"] == 1

    dr_list = DataRowListResponse(data=[dr], total=1, page=1, pages=1, limit=10)
    assert dr_list.total == 1


def test_import_history_validations_and_structs():
    from app.schemas.import_history import ImportHistoryBase, ImportRollbackRequest, ImportRollbackResponse

    # valid default
    ih = ImportHistoryBase(account_id=1, filename="x.csv")
    assert ih.row_count == 0

    # invalid status
    with pytest.raises(ValidationError):
        ImportHistoryBase(account_id=1, filename="f", status="bad")

    rb = ImportRollbackRequest(import_id=1, confirm=True)
    assert rb.confirm is True

    resp = ImportRollbackResponse(success=True, import_id=1, rows_deleted=5, message="ok")
    assert resp.success is True


def test_mapping_models():
    from app.schemas.mapping import MappingBase, MappingsUpdate

    m = MappingBase(csv_header="A", standard_field="amount")
    assert m.csv_header == "A"

    # invalid csv_header too short
    with pytest.raises(ValidationError):
        MappingBase(csv_header="", standard_field="f")

    mu = MappingsUpdate(mappings=[m])
    assert len(mu.mappings) == 1


def test_statistics_and_nested_models():
    from app.schemas.statistics import (
        SummaryResponse,
        ChartDataResponse,
        CategoryDataResponse,
        RecipientDataResponse,
        StatisticsResponse,
    )

    summary = SummaryResponse(total_income=100.0, total_expenses=-50.0, net_balance=50.0, transaction_count=5)
    chart = ChartDataResponse(labels=["Jan"], income=[100.0], expenses=[-50.0], balance=[50.0])
    cat = CategoryDataResponse(category_id=1, category_name="Food", color="#ffffff", total_amount=30.0, transaction_count=2, percentage=60.0)
    rec = RecipientDataResponse(recipient="X", total_amount=20.0, transaction_count=1, percentage=40.0)

    stats = StatisticsResponse(summary=summary, chart_data=chart, categories=[cat], recipients=[rec])
    assert stats.summary.net_balance == 50.0
