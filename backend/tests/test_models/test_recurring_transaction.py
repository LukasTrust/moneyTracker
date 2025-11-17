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
