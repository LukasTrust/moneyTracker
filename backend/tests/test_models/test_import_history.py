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
