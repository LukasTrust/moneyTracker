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
