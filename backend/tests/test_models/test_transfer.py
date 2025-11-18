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


def test_transfer_repr():
    """Test Transfer __repr__ method"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.id = 1
    mock_transfer.amount = 100.50
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the __repr__ method to our mock
    repr_method = Transfer.__repr__
    result = repr_method(mock_transfer)
    
    assert result == "<Transfer(id=1, amount=100.5, from=10, to=20)>"


def test_transfer_get_direction_for_transaction_outgoing():
    """Test get_direction_for_transaction returns 'outgoing' for from_transaction"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    direction_method = Transfer.get_direction_for_transaction
    result = direction_method(mock_transfer, 10)  # from_transaction_id
    
    assert result == 'outgoing'


def test_transfer_get_direction_for_transaction_incoming():
    """Test get_direction_for_transaction returns 'incoming' for to_transaction"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    direction_method = Transfer.get_direction_for_transaction
    result = direction_method(mock_transfer, 20)  # to_transaction_id
    
    assert result == 'incoming'


def test_transfer_get_direction_for_transaction_invalid():
    """Test get_direction_for_transaction raises ValueError for invalid transaction_id"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    direction_method = Transfer.get_direction_for_transaction
    
    with pytest.raises(ValueError, match="Transaction 99 is not part of this transfer"):
        direction_method(mock_transfer, 99)  # invalid transaction_id


def test_transfer_get_counterpart_transaction_id_from():
    """Test get_counterpart_transaction_id returns to_transaction_id when given from_transaction_id"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    counterpart_method = Transfer.get_counterpart_transaction_id
    result = counterpart_method(mock_transfer, 10)  # from_transaction_id
    
    assert result == 20


def test_transfer_get_counterpart_transaction_id_to():
    """Test get_counterpart_transaction_id returns from_transaction_id when given to_transaction_id"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    counterpart_method = Transfer.get_counterpart_transaction_id
    result = counterpart_method(mock_transfer, 20)  # to_transaction_id
    
    assert result == 10


def test_transfer_get_counterpart_transaction_id_invalid():
    """Test get_counterpart_transaction_id raises ValueError for invalid transaction_id"""
    from app.models.transfer import Transfer
    from types import SimpleNamespace
    
    # Create a mock transfer object
    mock_transfer = SimpleNamespace()
    mock_transfer.from_transaction_id = 10
    mock_transfer.to_transaction_id = 20
    
    # Bind the method to our mock
    counterpart_method = Transfer.get_counterpart_transaction_id
    
    with pytest.raises(ValueError, match="Transaction 99 is not part of this transfer"):
        counterpart_method(mock_transfer, 99)  # invalid transaction_id
