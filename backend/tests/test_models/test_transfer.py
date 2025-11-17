"""
Tests for Transfer Model
"""
import pytest


def test_transfer_model_exists():
    """Test that Transfer model can be imported"""
    from app.models.transfer import Transfer
    
    assert Transfer is not None
    assert hasattr(Transfer, '__tablename__')


def test_transfer_tablename():
    """Test that Transfer has correct table name"""
    from app.models.transfer import Transfer
    
    assert Transfer.__tablename__ == "transfers"


def test_transfer_has_required_columns():
    """Test that Transfer has all required columns"""
    from app.models.transfer import Transfer
    
    assert hasattr(Transfer, 'id')
    assert hasattr(Transfer, 'from_transaction_id')
    assert hasattr(Transfer, 'to_transaction_id')
    assert hasattr(Transfer, 'amount')  # 'amount' exists, not 'confidence'
    assert hasattr(Transfer, 'transfer_date')
    assert hasattr(Transfer, 'is_auto_detected')


def test_transfer_has_transaction_relationships():
    """Test that Transfer has relationships to DataRow transactions"""
    from app.models.transfer import Transfer
    
    assert hasattr(Transfer, 'from_transaction')
    assert hasattr(Transfer, 'to_transaction')


def test_transfer_amount_is_numeric():
    """Test that amount is a numeric field"""
    from app.models.transfer import Transfer
    from sqlalchemy import Numeric
    
    amount_col = Transfer.__table__.columns['amount']
    assert isinstance(amount_col.type, Numeric)
