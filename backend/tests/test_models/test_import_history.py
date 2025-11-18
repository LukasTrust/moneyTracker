"""
Tests for ImportHistory Model
"""
import pytest


def test_import_history_model_exists():
    """Test that ImportHistory model can be imported"""
    from app.models.import_history import ImportHistory
    
    assert ImportHistory is not None
    assert hasattr(ImportHistory, '__tablename__')


def test_import_history_tablename():
    """Test that ImportHistory has correct table name"""
    from app.models.import_history import ImportHistory
    
    assert ImportHistory.__tablename__ == "import_history"


def test_import_history_has_required_columns():
    """Test that ImportHistory has all required columns"""
    from app.models.import_history import ImportHistory
    
    assert hasattr(ImportHistory, 'id')
    assert hasattr(ImportHistory, 'account_id')
    assert hasattr(ImportHistory, 'filename')
    assert hasattr(ImportHistory, 'uploaded_at')  # 'uploaded_at' not 'imported_at'
    assert hasattr(ImportHistory, 'row_count')


def test_import_history_has_account_relationship():
    """Test that ImportHistory has relationship to Account"""
    from app.models.import_history import ImportHistory
    
    assert hasattr(ImportHistory, 'account')


def test_import_history_repr():
    """Test that ImportHistory __repr__ method works correctly"""
    from app.models.import_history import ImportHistory
    from types import SimpleNamespace
    from types import MethodType
    
    # Create a mock instance using SimpleNamespace
    mock_instance = SimpleNamespace()
    
    # Set attributes that __repr__ uses
    mock_instance.id = 1
    mock_instance.account_id = 123
    mock_instance.filename = "test.csv"
    mock_instance.status = "success"
    mock_instance.rows_inserted = 100
    mock_instance.row_count = 105
    
    # Bind the __repr__ method to our mock instance
    mock_instance.__repr__ = MethodType(ImportHistory.__repr__, mock_instance)
    
    # Test the __repr__ method
    result = mock_instance.__repr__()
    expected = "<ImportHistory(id=1, account_id=123, filename='test.csv', status='success', rows=100/105)>"
    assert result == expected
