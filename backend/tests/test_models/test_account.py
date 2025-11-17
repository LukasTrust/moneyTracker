"""
Tests for Account Model
"""
import pytest


def test_account_model_exists():
    """Test that Account model can be imported"""
    from app.models.account import Account
    
    assert Account is not None
    assert hasattr(Account, '__tablename__')


def test_account_tablename():
    """Test that Account has correct table name"""
    from app.models.account import Account
    
    assert Account.__tablename__ == "accounts"


def test_account_has_required_columns():
    """Test that Account has all required columns"""
    from app.models.account import Account
    
    # Check for column attributes
    assert hasattr(Account, 'id')
    assert hasattr(Account, 'name')
    assert hasattr(Account, 'bank_name')
    assert hasattr(Account, 'account_number')
    assert hasattr(Account, 'currency')
    assert hasattr(Account, 'description')
    assert hasattr(Account, 'initial_balance')
    assert hasattr(Account, 'created_at')
    assert hasattr(Account, 'updated_at')


def test_account_has_relationships():
    """Test that Account has relationship definitions"""
    from app.models.account import Account
    
    # Check for relationship attributes
    assert hasattr(Account, 'mappings')
    assert hasattr(Account, 'data_rows')
    assert hasattr(Account, 'import_history')
    assert hasattr(Account, 'insights')


def test_account_repr():
    """Test Account __repr__ method"""
    from app.models.account import Account
    
    # Create mock account
    from types import SimpleNamespace
    account = SimpleNamespace(id=1, name='Test Account', bank_name='Test Bank')
    
    # Call the actual __repr__ method
    repr_str = Account.__repr__(account)
    
    assert 'Account' in repr_str
    assert 'Test Account' in repr_str
    assert 'Test Bank' in repr_str


def test_account_default_currency():
    """Test that Account has default currency EUR"""
    from app.models.account import Account
    
    # Check column default
    currency_col = Account.__table__.columns['currency']
    assert currency_col.default is not None
    assert currency_col.default.arg == 'EUR'


def test_account_default_initial_balance():
    """Test that Account has default initial balance of 0"""
    from app.models.account import Account
    
    initial_balance_col = Account.__table__.columns['initial_balance']
    assert initial_balance_col.default is not None
    assert float(initial_balance_col.default.arg) == 0.0
