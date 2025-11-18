"""
Tests for RecurringTransaction Model
"""
import pytest


def test_recurring_transaction_model_exists():
    """Test that RecurringTransaction model can be imported"""
    from app.models.recurring_transaction import RecurringTransaction
    
    assert RecurringTransaction is not None
    assert hasattr(RecurringTransaction, '__tablename__')


def test_recurring_tablename():
    """Test that RecurringTransaction has correct table name"""
    from app.models.recurring_transaction import RecurringTransaction
    
    assert RecurringTransaction.__tablename__ == "recurring_transactions"


def test_recurring_has_required_columns():
    """Test that RecurringTransaction has all required columns"""
    from app.models.recurring_transaction import RecurringTransaction
    
    assert hasattr(RecurringTransaction, 'id')
    assert hasattr(RecurringTransaction, 'account_id')
    assert hasattr(RecurringTransaction, 'recipient')
    assert hasattr(RecurringTransaction, 'average_amount')  # 'average_amount' not 'amount'
    assert hasattr(RecurringTransaction, 'average_interval_days')  # 'average_interval_days' not 'interval_days'
    assert hasattr(RecurringTransaction, 'next_expected_date')
    assert hasattr(RecurringTransaction, 'is_active')
    assert hasattr(RecurringTransaction, 'created_at')
    assert hasattr(RecurringTransaction, 'updated_at')


def test_recurring_has_account_relationship():
    """Test that RecurringTransaction has relationship to Account"""
    from app.models.recurring_transaction import RecurringTransaction
    
    assert hasattr(RecurringTransaction, 'account')


def test_recurring_default_is_active():
    """Test that is_active defaults to True"""
    from app.models.recurring_transaction import RecurringTransaction
    
    is_active_col = RecurringTransaction.__table__.columns['is_active']
    assert is_active_col.default is not None
    assert is_active_col.default.arg is True


def test_recurring_link_model_exists():
    """Test that RecurringTransactionLink model exists"""
    from app.models.recurring_transaction import RecurringTransactionLink
    
    assert RecurringTransactionLink is not None
    assert hasattr(RecurringTransactionLink, '__tablename__')


def test_recurring_transaction_repr():
    """Test __repr__ method for RecurringTransaction"""
    from app.models.recurring_transaction import RecurringTransaction
    from types import SimpleNamespace
    
    # Create mock recurring transaction
    recurring = SimpleNamespace(
        id=1,
        recipient="Netflix",
        average_amount=15.99,
        average_interval_days=30
    )
    # Bind the __repr__ method to the mock object
    recurring.__repr__ = RecurringTransaction.__repr__.__get__(recurring, RecurringTransaction)
    
    # Test __repr__
    expected = "<RecurringTransaction(id=1, recipient='Netflix', amount=15.99, interval=30d)>"
    assert recurring.__repr__() == expected


def test_recurring_transaction_link_repr():
    """Test __repr__ method for RecurringTransactionLink"""
    from app.models.recurring_transaction import RecurringTransactionLink
    from types import SimpleNamespace
    
    # Create mock recurring transaction link
    link = SimpleNamespace(
        recurring_transaction_id=5,
        data_row_id=123
    )
    # Bind the __repr__ method to the mock object
    link.__repr__ = RecurringTransactionLink.__repr__.__get__(link, RecurringTransactionLink)
    
    # Test __repr__
    expected = "<RecurringTransactionLink(recurring_id=5, data_row_id=123)>"
    assert link.__repr__() == expected
