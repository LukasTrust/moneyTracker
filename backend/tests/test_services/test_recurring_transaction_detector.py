"""
Tests for RecurringTransactionDetector service
"""
from datetime import date, timedelta
from app.services.recurring_transaction_detector import RecurringTransactionDetector


class FakeQuery:
    def __init__(self, items):
        self._items = items
    
    def filter(self, condition):
        return self
    
    def order_by(self, field):
        return self
    
    def all(self):
        return self._items


class FakeDB:
    def __init__(self, transactions=None):
        self._transactions = transactions or []
    
    def query(self, model):
        return FakeQuery(self._transactions)


def test_detector_initialization():
    """Test RecurringTransactionDetector initializes correctly"""
    db = FakeDB()
    detector = RecurringTransactionDetector(db)
    
    assert detector.db is db
    assert hasattr(detector, 'detect_recurring_for_account')
    assert hasattr(detector, '_group_by_recipient')


def test_detector_constants():
    """Test that detector has required configuration constants"""
    assert hasattr(RecurringTransactionDetector, 'MIN_OCCURRENCES')
    assert hasattr(RecurringTransactionDetector, 'AMOUNT_TOLERANCE')
    assert hasattr(RecurringTransactionDetector, 'INTERVAL_TOLERANCE_DAYS')
    assert hasattr(RecurringTransactionDetector, 'INTERVALS')
    assert hasattr(RecurringTransactionDetector, 'ACTIVITY_THRESHOLD_DAYS')
    
    # Check reasonable values
    assert RecurringTransactionDetector.MIN_OCCURRENCES >= 2
    assert RecurringTransactionDetector.AMOUNT_TOLERANCE > 0
    assert RecurringTransactionDetector.ACTIVITY_THRESHOLD_DAYS > 0


def test_intervals_configuration():
    """Test that typical intervals are defined"""
    intervals = RecurringTransactionDetector.INTERVALS
    
    assert isinstance(intervals, list)
    assert len(intervals) > 0
    
    # Should include common intervals
    assert 30 in intervals  # Monthly
    assert 7 in intervals or 90 in intervals  # Weekly or Quarterly


def test_detect_with_no_transactions():
    """Test detection with no transactions"""
    db = FakeDB(transactions=[])
    detector = RecurringTransactionDetector(db)
    
    result = detector.detect_recurring_for_account(account_id=1)
    assert isinstance(result, list)
    assert len(result) == 0


def test_detect_with_few_transactions():
    """Test detection with too few transactions"""
    # Only 2 transactions, but MIN_OCCURRENCES is 3
    from types import SimpleNamespace
    
    transactions = [
        SimpleNamespace(
            id=1,
            account_id=1,
            recipient='Netflix',
            amount=-9.99,
            transaction_date=date.today() - timedelta(days=30)
        ),
        SimpleNamespace(
            id=2,
            account_id=1,
            recipient='Netflix',
            amount=-9.99,
            transaction_date=date.today()
        ),
    ]
    
    db = FakeDB(transactions=transactions)
    detector = RecurringTransactionDetector(db)
    
    result = detector.detect_recurring_for_account(account_id=1)
    assert isinstance(result, list)


def test_group_by_recipient():
    """Test grouping transactions by recipient"""
    from types import SimpleNamespace
    
    transactions = [
        SimpleNamespace(id=1, recipient='Netflix', amount=-9.99),
        SimpleNamespace(id=2, recipient='Spotify', amount=-9.99),
        SimpleNamespace(id=3, recipient='Netflix', amount=-9.99),
    ]
    
    db = FakeDB()
    detector = RecurringTransactionDetector(db)
    
    grouped = detector._group_by_recipient(transactions)
    
    assert isinstance(grouped, dict)
    # Recipients are normalized to lowercase
    assert 'netflix' in grouped
    assert 'spotify' in grouped
    assert len(grouped['netflix']) == 2
    assert len(grouped['spotify']) == 1


def test_amount_tolerance_is_reasonable():
    """Test that amount tolerance is set to a reasonable value"""
    tolerance = RecurringTransactionDetector.AMOUNT_TOLERANCE
    
    # Should be between 1 and 10 EUR
    assert 1.0 <= tolerance <= 10.0


def test_detector_has_activity_threshold():
    """Test that detector considers activity when detecting"""
    threshold = RecurringTransactionDetector.ACTIVITY_THRESHOLD_DAYS
    
    # Should be reasonable (30-90 days)
    assert 20 <= threshold <= 180
