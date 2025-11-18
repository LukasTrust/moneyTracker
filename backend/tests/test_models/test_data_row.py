"""
Tests for DataRow Model
"""
import pytest


def test_data_row_model_exists():
    """Test that DataRow model can be imported"""
    from app.models.data_row import DataRow
    
    assert DataRow is not None
    assert hasattr(DataRow, '__tablename__')


def test_data_row_tablename():
    """Test that DataRow has correct table name"""
    from app.models.data_row import DataRow
    
    assert DataRow.__tablename__ == "data_rows"


def test_data_row_has_required_columns():
    """Test that DataRow has all required columns"""
    from app.models.data_row import DataRow
    
    assert hasattr(DataRow, 'id')
    assert hasattr(DataRow, 'account_id')
    assert hasattr(DataRow, 'transaction_date')
    assert hasattr(DataRow, 'amount')
    assert hasattr(DataRow, 'recipient')
    assert hasattr(DataRow, 'purpose')
    assert hasattr(DataRow, 'category_id')
    assert hasattr(DataRow, 'created_at')


def test_data_row_has_relationships():
    """Test that DataRow has relationship definitions"""
    from app.models.data_row import DataRow
    
    assert hasattr(DataRow, 'account')
    assert hasattr(DataRow, 'category')


def test_data_row_data_property():
    """Test data property returns dict with transaction data"""
    from app.models.data_row import DataRow
    from datetime import date
    from decimal import Decimal
    from types import SimpleNamespace
    
    # Create mock data_row
    data_row = SimpleNamespace(
        transaction_date=date(2023, 10, 15),
        amount=Decimal('-50.00'),
        recipient='Supermarket',
        purpose='Groceries',
        valuta_date=date(2023, 10, 16),
        currency='EUR',
        raw_data={'bank_field': 'value'}
    )
    
    # Call the property
    result = DataRow.data.__get__(data_row)
    
    expected = {
        'date': '2023-10-15',
        'amount': '-50.00',
        'recipient': 'Supermarket',
        'purpose': 'Groceries',
        'valuta_date': '2023-10-16',
        'currency': 'EUR',
        'bank_field': 'value'
    }
    
    assert result == expected


def test_data_row_data_property_with_none_values():
    """Test data property handles None values correctly"""
    from app.models.data_row import DataRow
    from types import SimpleNamespace
    
    # Create mock data_row with None values
    data_row = SimpleNamespace(
        transaction_date=None,
        amount=None,
        recipient=None,
        purpose=None,
        valuta_date=None,
        currency='EUR',
        raw_data=None
    )
    
    # Call the property
    result = DataRow.data.__get__(data_row)
    
    expected = {
        'date': None,
        'amount': None,
        'recipient': None,
        'purpose': None,
        'valuta_date': None,
        'currency': 'EUR'
    }
    
    assert result == expected


def test_data_row_data_property_without_raw_data():
    """Test data property works without raw_data"""
    from app.models.data_row import DataRow
    from datetime import date
    from decimal import Decimal
    from types import SimpleNamespace
    
    # Create mock data_row without raw_data
    data_row = SimpleNamespace(
        transaction_date=date(2023, 10, 15),
        amount=Decimal('100.00'),
        recipient='Salary',
        purpose='Monthly salary',
        valuta_date=date(2023, 10, 15),
        currency='EUR',
        raw_data=None
    )
    
    # Call the property
    result = DataRow.data.__get__(data_row)
    
    expected = {
        'date': '2023-10-15',
        'amount': '100.00',
        'recipient': 'Salary',
        'purpose': 'Monthly salary',
        'valuta_date': '2023-10-15',
        'currency': 'EUR'
    }
    
    assert result == expected


def test_data_row_repr():
    """Test DataRow __repr__ method"""
    from app.models.data_row import DataRow
    from datetime import date
    from decimal import Decimal
    from types import SimpleNamespace
    
    # Create mock data_row
    data_row = SimpleNamespace(
        id=1,
        transaction_date=date(2023, 10, 15),
        amount=Decimal('-50.00'),
        recipient='Supermarket'
    )
    
    # Call the actual __repr__ method
    repr_str = DataRow.__repr__(data_row)
    
    assert 'DataRow' in repr_str
    assert '1' in repr_str
    assert '2023-10-15' in repr_str
    assert '-50.00' in repr_str
    assert 'Supermarket' in repr_str
