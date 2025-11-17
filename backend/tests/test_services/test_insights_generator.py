"""
Tests for InsightsGenerator service
"""
from datetime import date, timedelta
from app.services.insights_generator import InsightsGenerator


class FakeQuery:
    def __init__(self, result=None):
        self._result = result
    
    def filter(self, *args):
        return self
    
    def scalar(self):
        return self._result
    
    def all(self):
        return self._result if isinstance(self._result, list) else []


class FakeDB:
    def __init__(self, transfers=None, expenses=None):
        self._transfers = transfers or []
        self._expenses = expenses
    
    def query(self, *args):
        # If querying for transfers
        if self._transfers and len(args) == 1:
            return FakeQuery(self._transfers)
        # If querying for expenses sum
        return FakeQuery(self._expenses)


def test_insights_generator_initialization():
    """Test InsightsGenerator initializes correctly"""
    db = FakeDB()
    generator = InsightsGenerator(db)
    
    assert generator.db is db
    assert hasattr(generator, '_get_transfer_transaction_ids')
    assert hasattr(generator, '_get_expenses_for_period')


def test_threshold_constants():
    """Test that thresholds are defined and reasonable"""
    assert hasattr(InsightsGenerator, 'MOM_THRESHOLD')
    assert hasattr(InsightsGenerator, 'YOY_THRESHOLD')
    assert hasattr(InsightsGenerator, 'CATEGORY_GROWTH_THRESHOLD')
    assert hasattr(InsightsGenerator, 'CATEGORY_GROWTH_MIN_AMOUNT')
    assert hasattr(InsightsGenerator, 'UNUSUAL_EXPENSE_MULTIPLIER')
    
    # Check values are reasonable
    assert 0.0 < InsightsGenerator.MOM_THRESHOLD < 1.0
    assert 0.0 < InsightsGenerator.YOY_THRESHOLD < 1.0
    assert InsightsGenerator.CATEGORY_GROWTH_MIN_AMOUNT > 0
    assert InsightsGenerator.UNUSUAL_EXPENSE_MULTIPLIER > 1.0


def test_cooldown_settings():
    """Test that cooldown settings are defined"""
    assert hasattr(InsightsGenerator, 'DEFAULT_COOLDOWN_HOURS')
    assert hasattr(InsightsGenerator, 'HIGH_PRIORITY_COOLDOWN_HOURS')
    assert hasattr(InsightsGenerator, 'LOW_PRIORITY_COOLDOWN_HOURS')
    
    # Check reasonable values
    assert InsightsGenerator.HIGH_PRIORITY_COOLDOWN_HOURS > 0
    assert InsightsGenerator.DEFAULT_COOLDOWN_HOURS >= InsightsGenerator.HIGH_PRIORITY_COOLDOWN_HOURS
    assert InsightsGenerator.LOW_PRIORITY_COOLDOWN_HOURS >= InsightsGenerator.DEFAULT_COOLDOWN_HOURS


def test_subscription_keywords():
    """Test that subscription keywords are defined"""
    assert hasattr(InsightsGenerator, 'SUBSCRIPTION_KEYWORDS')
    keywords = InsightsGenerator.SUBSCRIPTION_KEYWORDS
    
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    
    # Check for common subscriptions
    keywords_lower = [k.lower() for k in keywords]
    assert 'netflix' in keywords_lower or any('netflix' in k for k in keywords_lower)
    assert 'spotify' in keywords_lower or any('spotify' in k for k in keywords_lower)


def test_get_transfer_transaction_ids():
    """Test getting transfer transaction IDs"""
    db = FakeDB(transfers=[])
    generator = InsightsGenerator(db)
    
    transfer_ids = generator._get_transfer_transaction_ids()
    assert isinstance(transfer_ids, set)


def test_get_expenses_for_period_zero():
    """Test getting expenses when none exist"""
    db = FakeDB(expenses=0.0)
    generator = InsightsGenerator(db)
    
    today = date.today()
    start = today - timedelta(days=30)
    
    expenses = generator._get_expenses_for_period(
        account_id=None,
        start_date=start,
        end_date=today
    )
    
    assert expenses == 0.0


def test_get_expenses_for_period_with_amount():
    """Test getting expenses with actual spending"""
    db = FakeDB(expenses=-500.0)  # 500 EUR spent
    generator = InsightsGenerator(db)
    
    today = date.today()
    start = today - timedelta(days=30)
    
    expenses = generator._get_expenses_for_period(
        account_id=None,
        start_date=start,
        end_date=today,
        exclude_transfers=True
    )
    
    # The method returns absolute value for expenses
    assert abs(expenses) == 500.0


def test_mom_threshold_is_percentage():
    """Test that MoM threshold is a reasonable percentage"""
    threshold = InsightsGenerator.MOM_THRESHOLD
    assert 0.1 <= threshold <= 0.5  # Between 10% and 50%


def test_yoy_threshold_is_percentage():
    """Test that YoY threshold is a reasonable percentage"""
    threshold = InsightsGenerator.YOY_THRESHOLD
    assert 0.1 <= threshold <= 0.5  # Between 10% and 50%


def test_unusual_expense_multiplier():
    """Test that unusual expense multiplier is reasonable"""
    multiplier = InsightsGenerator.UNUSUAL_EXPENSE_MULTIPLIER
    assert 2.0 <= multiplier <= 5.0  # Between 2x and 5x average


def test_generator_has_required_methods():
    """Test that generator has all expected methods"""
    db = FakeDB()
    generator = InsightsGenerator(db)
    
    # Core methods
    assert hasattr(generator, '_get_transfer_transaction_ids')
    assert hasattr(generator, '_get_expenses_for_period')
    
    # All should be callable
    assert callable(generator._get_transfer_transaction_ids)
    assert callable(generator._get_expenses_for_period)
