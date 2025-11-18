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


def test_recipient_normalize_name():
    """Test normalize_name static method"""
    from app.models.recipient import Recipient
    
    # Test basic normalization
    assert Recipient.normalize_name("  AMAZON PAYMENTS  ") == "amazon payments"
    assert Recipient.normalize_name("Amazon.DE") == "amazon.de"
    assert Recipient.normalize_name("") == ""
    assert Recipient.normalize_name(None) == ""
    assert Recipient.normalize_name("  multiple   spaces  ") == "multiple spaces"


def test_recipient_add_alias():
    """Test add_alias method"""
    from app.models.recipient import Recipient
    from types import SimpleNamespace
    
    # Create mock recipient
    recipient = SimpleNamespace(
        aliases=None,
        normalize_name=Recipient.normalize_name
    )
    # Bind the add_alias method to the mock object
    recipient.add_alias = Recipient.add_alias.__get__(recipient, Recipient)
    
    # Add first alias
    recipient.add_alias("Amazon DE")
    assert recipient.aliases == "amazon de"
    
    # Add second alias
    recipient.add_alias("Amazon.de")
    assert recipient.aliases == "amazon de,amazon.de"
    
    # Add duplicate (should not add)
    recipient.add_alias("Amazon DE")
    assert recipient.aliases == "amazon de,amazon.de"
    
    # Add empty (should not add)
    recipient.add_alias("")
    assert recipient.aliases == "amazon de,amazon.de"


def test_recipient_matches():
    """Test matches method"""
    from app.models.recipient import Recipient
    from types import SimpleNamespace
    
    # Create mock recipient
    recipient = SimpleNamespace(
        normalized_name="amazon payments",
        aliases="amazon.de,amazon payments eu",
        normalize_name=Recipient.normalize_name
    )
    # Bind the matches method to the mock object
    recipient.matches = Recipient.matches.__get__(recipient, Recipient)
    
    # Test exact match
    assert recipient.matches("AMAZON PAYMENTS") == True
    assert recipient.matches("amazon payments") == True
    
    # Test alias match
    assert recipient.matches("Amazon.DE") == True
    assert recipient.matches("amazon payments eu") == True
    
    # Test no match
    assert recipient.matches("PayPal") == False
    assert recipient.matches("") == False


def test_recipient_repr():
    """Test __repr__ method"""
    from app.models.recipient import Recipient
    from types import SimpleNamespace
    
    # Create mock recipient
    recipient = SimpleNamespace(
        id=1,
        name="Amazon Payments",
        normalized_name="amazon payments"
    )
    # Bind the __repr__ method to the mock object
    recipient.__repr__ = Recipient.__repr__.__get__(recipient, Recipient)
    
    # Test __repr__
    assert recipient.__repr__() == "<Recipient(id=1, name='Amazon Payments', normalized='amazon payments')>"


def test_recipient_to_dict():
    """Test to_dict method"""
    from app.models.recipient import Recipient
    from types import SimpleNamespace
    from datetime import datetime
    
    # Create mock recipient
    recipient = SimpleNamespace(
        id=1,
        name="Amazon Payments",
        normalized_name="amazon payments",
        aliases="amazon.de,amazon payments eu",
        transaction_count=42,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 2, 12, 0, 0)
    )
    # Bind the to_dict method to the mock object
    recipient.to_dict = Recipient.to_dict.__get__(recipient, Recipient)
    
    # Test to_dict
    result = recipient.to_dict()
    expected = {
        "id": 1,
        "name": "Amazon Payments",
        "normalized_name": "amazon payments",
        "aliases": ["amazon.de", "amazon payments eu"],
        "transaction_count": 42,
        "created_at": "2023-01-01T12:00:00",
        "updated_at": "2023-01-02T12:00:00"
    }
    assert result == expected
