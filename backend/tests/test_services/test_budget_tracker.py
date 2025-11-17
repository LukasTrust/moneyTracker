"""
Tests for BudgetTracker service
"""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from app.services.budget_tracker import BudgetTracker


class FakeQuery:
    def __init__(self, result=None):
        self._result = result
        self._filters = []
    
    def filter(self, *args):
        self._filters.extend(args)
        return self
    
    def scalar(self):
        return self._result
    
    def all(self):
        return self._result if isinstance(self._result, list) else []


class FakeDB:
    def __init__(self, transfers=None, sum_result=None):
        self._transfers = transfers or []
        self._sum_result = sum_result
    
    def query(self, *args):
        # If querying for transfer IDs
        if len(args) == 1 and hasattr(args[0], '__name__'):
            return FakeQuery(self._transfers)
        # If querying for sum
        return FakeQuery(self._sum_result)


def test_budget_tracker_initialization():
    """Test BudgetTracker initializes with db"""
    db = FakeDB()
    tracker = BudgetTracker(db)
    
    assert tracker.db is db
    assert hasattr(tracker, 'calculate_budget_progress')
    assert hasattr(tracker, '_get_transfer_transaction_ids')


def test_get_transfer_transaction_ids_empty():
    """Test getting transfer IDs when none exist"""
    db = FakeDB(transfers=[])
    tracker = BudgetTracker(db)
    
    transfer_ids = tracker._get_transfer_transaction_ids()
    assert isinstance(transfer_ids, set)
    assert len(transfer_ids) == 0


def test_get_transfer_transaction_ids():
    """Test getting transfer IDs"""
    # Mock transfer results - tuples of IDs
    transfers = [(1,), (2,), (3,)]
    db = FakeDB(transfers=transfers)
    tracker = BudgetTracker(db)
    
    transfer_ids = tracker._get_transfer_transaction_ids()
    assert isinstance(transfer_ids, set)


def test_calculate_budget_progress_zero_spent():
    """Test budget progress with no spending"""
    today = date.today()
    budget = SimpleNamespace(
        category_id=1,
        amount=1000.0,
        start_date=today - timedelta(days=15),
        end_date=today + timedelta(days=15)
    )
    
    db = FakeDB(transfers=[], sum_result=0)  # No spending
    tracker = BudgetTracker(db)
    
    progress = tracker.calculate_budget_progress(budget)
    
    assert progress.spent == Decimal('0.00')
    assert progress.remaining == Decimal('1000.00')
    assert progress.percentage == 0.0
    assert progress.is_exceeded is False


def test_calculate_budget_progress_with_spending():
    """Test budget progress with some spending"""
    today = date.today()
    budget = SimpleNamespace(
        category_id=1,
        amount=1000.0,
        start_date=today - timedelta(days=15),
        end_date=today + timedelta(days=15)
    )
    
    # 500 EUR spent
    db = FakeDB(transfers=[], sum_result=500.0)
    tracker = BudgetTracker(db)
    
    progress = tracker.calculate_budget_progress(budget)
    
    assert progress.spent == Decimal('500.00')
    assert progress.remaining == Decimal('500.00')
    assert progress.percentage == 50.0
    assert progress.is_exceeded is False


def test_calculate_budget_progress_exceeded():
    """Test budget progress when exceeded"""
    today = date.today()
    budget = SimpleNamespace(
        category_id=1,
        amount=1000.0,
        start_date=today - timedelta(days=15),
        end_date=today + timedelta(days=15)
    )
    
    # 1200 EUR spent (over budget)
    db = FakeDB(transfers=[], sum_result=1200.0)
    tracker = BudgetTracker(db)
    
    progress = tracker.calculate_budget_progress(budget)
    
    assert progress.spent == Decimal('1200.00')
    assert progress.remaining == Decimal('-200.00')
    assert progress.percentage == 120.0
    assert progress.is_exceeded is True


def test_budget_tracker_has_required_methods():
    """Test that BudgetTracker has all required methods"""
    db = FakeDB()
    tracker = BudgetTracker(db)
    
    # Check method existence
    assert hasattr(tracker, 'calculate_budget_progress')
    assert hasattr(tracker, '_get_transfer_transaction_ids')
    assert callable(tracker.calculate_budget_progress)
    assert callable(tracker._get_transfer_transaction_ids)
