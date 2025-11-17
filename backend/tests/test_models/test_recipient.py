"""
Tests for Recipient Model
"""
import pytest


def test_recipient_model_exists():
    """Test that Recipient model can be imported"""
    from app.models.recipient import Recipient
    
    assert Recipient is not None
    assert hasattr(Recipient, '__tablename__')


def test_recipient_tablename():
    """Test that Recipient has correct table name"""
    from app.models.recipient import Recipient
    
    assert Recipient.__tablename__ == "recipients"


def test_recipient_has_required_columns():
    """Test that Recipient has all required columns"""
    from app.models.recipient import Recipient
    
    assert hasattr(Recipient, 'id')
    assert hasattr(Recipient, 'name')
    assert hasattr(Recipient, 'normalized_name')
    assert hasattr(Recipient, 'transaction_count')
    assert hasattr(Recipient, 'created_at')


def test_recipient_has_normalize_name_method():
    """Test that Recipient has normalize_name static method"""
    from app.models.recipient import Recipient
    
    assert hasattr(Recipient, 'normalize_name')
    assert callable(Recipient.normalize_name)
