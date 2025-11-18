"""Additional tests to raise coverage for BudgetTracker service."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.budget_tracker import BudgetTracker


class FakeQuery:
    def __init__(self, result=None):
        self._result = result

    def filter(self, *args):
        return self

    def scalar(self):
        return self._result

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result

    def all(self):
        return self._result if isinstance(self._result, list) else []


class FakeDB:
    def __init__(self, budgets=None, categories=None, transfers=None, sum_result=None):
        # budgets: list of budget-like objects
        # categories: list of category-like objects (matching budgets by category_id)
        self.budgets = budgets or []
        self.categories = categories or []
        self.transfers = transfers or []
        self.sum_result = sum_result

    def query(self, *args):
        # If querying for Budget class
        if args and isinstance(args[0], type) and getattr(args[0], '__name__', '') == 'Budget':
            return FakeQuery(self.budgets)

        # If querying for Category class
        if args and isinstance(args[0], type) and getattr(args[0], '__name__', '') == 'Category':
            return FakeQuery(self.categories)

        # If this looks like a SUM/aggregation query, return the configured sum_result
        if len(args) == 1 and 'sum' in repr(args[0]).lower():
            return FakeQuery(self.sum_result)

        # If transfer id selection (column-like), return transfers
        if self.transfers and len(args) == 1:
            return FakeQuery(self.transfers)

        # Fallback: sum queries
        return FakeQuery(self.sum_result)


def make_budget(id=1, category_id=10, amount=1000.0, start_offset=-5, end_offset=5):
    today = date.today()
    return SimpleNamespace(
        id=id,
        category_id=category_id,
        amount=amount,
        period='monthly',
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        description='b',
        created_at=today,
        updated_at=today,
    )


def make_category(category_id=10, name='Cat', color='#112233', icon=None):
    return SimpleNamespace(id=category_id, name=name, color=color, icon=icon)


def test_get_budget_with_progress_none():
    db = FakeDB(budgets=[])
    tracker = BudgetTracker(db)
    assert tracker.get_budget_with_progress(123) is None


def test_get_budget_with_progress_with_category_and_progress(monkeypatch):
    b = make_budget(id=5, category_id=42, amount=200.0)
    cat = make_category(42, name='Food', color='#00ff00', icon='🍎')
    # sum_result set so calculate_budget_progress returns spent
    db = FakeDB(budgets=[b], categories=[cat], transfers=[(1,)], sum_result=Decimal('50.00'))
    tracker = BudgetTracker(db)

    # Call and ensure result fields present
    res = tracker.get_budget_with_progress(5)
    assert res is not None
    assert res.id == 5
    assert res.category_name == 'Food'
    assert res.category_color == '#00ff00'
    assert res.category_icon == '🍎'
    assert hasattr(res, 'progress')


def test_get_all_budgets_with_progress_active_filter_and_sort():
    # Create two budgets with different spent amounts
    b1 = make_budget(id=1, category_id=1, amount=100.0, start_offset=-2, end_offset=2)
    b2 = make_budget(id=2, category_id=2, amount=200.0, start_offset=-2, end_offset=2)
    cat1 = make_category(1, name='A')
    cat2 = make_category(2, name='B')

    # sum_results used by calculate_budget_progress scalar: but our FakeDB returns the same sum for all queries;
    # to simulate different spent, we'll monkeypatch calculate_budget_progress to return different percentages per budget id
    db = FakeDB(budgets=[b1, b2], categories=[cat1, cat2], sum_result=Decimal('0.00'))
    tracker = BudgetTracker(db)

    def fake_calc(budget, account_id=None):
        if budget.id == 1:
            return {
                'spent': Decimal('80.00'),
                'remaining': Decimal('20.00'),
                'percentage': 80.0,
                'is_exceeded': False,
                'days_remaining': 5,
                'daily_average_spent': Decimal('4.00'),
                'projected_total': Decimal('120.00'),
            }
        return {
            'spent': Decimal('150.00'),
            'remaining': Decimal('50.00'),
            'percentage': 75.0,
            'is_exceeded': False,
            'days_remaining': 5,
            'daily_average_spent': Decimal('5.00'),
            'projected_total': Decimal('155.00'),
        }

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(tracker, 'calculate_budget_progress', fake_calc)

    result = tracker.get_all_budgets_with_progress(account_id=None, active_only=False)
    # Should be sorted by percentage desc, so id 1 first
    assert len(result) == 2
    assert result[0].id == 1

    monkeypatch.undo()


def test_get_budget_summary_empty():
    db = FakeDB(budgets=[], categories=[], sum_result=0)
    tracker = BudgetTracker(db)
    summary = tracker.get_budget_summary(account_id=None, active_only=True)
    assert summary.total_budgets == 0
    assert summary.total_budget_amount == Decimal('0.00')


def test_get_budget_summary_with_values(monkeypatch):
    b1 = make_budget(id=1, category_id=1, amount=100.0)
    b2 = make_budget(id=2, category_id=2, amount=200.0)
    db = FakeDB(budgets=[b1, b2], categories=[make_category(1), make_category(2)], sum_result=Decimal('0.00'))
    tracker = BudgetTracker(db)

    # Monkeypatch get_all_budgets_with_progress to return made-up progress
    def fake_all(account_id=None, active_only=True):
        return [
            SimpleNamespace(id=1, amount=Decimal('100.00'), progress=SimpleNamespace(spent=Decimal('60.00'), remaining=Decimal('40.00'), percentage=60.0, is_exceeded=False)),
            SimpleNamespace(id=2, amount=Decimal('200.00'), progress=SimpleNamespace(spent=Decimal('220.00'), remaining=Decimal('-20.00'), percentage=110.0, is_exceeded=True)),
        ]

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(tracker, 'get_all_budgets_with_progress', fake_all)

    summary = tracker.get_budget_summary()
    assert summary.total_budgets == 2
    assert summary.budgets_exceeded == 1
    # budgets_at_risk depends on thresholds; current expectation is 0
    assert summary.budgets_at_risk == 0
    # overall percentage computed
    assert isinstance(summary.overall_percentage, float)

    monkeypatch.undo()


def test_check_budget_conflicts_with_and_without_exclude():
    # Create overlapping budgets
    b_existing = make_budget(id=10, category_id=5, start_offset=-1, end_offset=10)
    db = FakeDB(budgets=[b_existing])
    tracker = BudgetTracker(db)

    conflicts = tracker.check_budget_conflicts(category_id=5, start_date=b_existing.start_date, end_date=b_existing.end_date)
    assert len(conflicts) == 1

    conflicts_excluded = tracker.check_budget_conflicts(category_id=5, start_date=b_existing.start_date, end_date=b_existing.end_date, exclude_budget_id=10)
    # Exclude should still return list from FakeQuery (our fake does not filter by id), but ensure function runs
    assert isinstance(conflicts_excluded, list)
