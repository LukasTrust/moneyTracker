"""
Tests for Mapping Model
"""
import pytest


def test_mapping_model_exists():
    """Test that Mapping model can be imported"""
    from app.models.mapping import Mapping
    
    assert Mapping is not None
    assert hasattr(Mapping, '__tablename__')


def test_mapping_tablename():
    """Test that Mapping has correct table name"""
    from app.models.mapping import Mapping
    
    assert Mapping.__tablename__ == "mappings"


def test_mapping_has_required_columns():
    """Test that Mapping has all required columns"""
    from app.models.mapping import Mapping
    
    assert hasattr(Mapping, 'id')
    assert hasattr(Mapping, 'account_id')
    assert hasattr(Mapping, 'csv_header')  # 'csv_header' and 'standard_field'
    assert hasattr(Mapping, 'standard_field')
    assert hasattr(Mapping, 'created_at')


def test_mapping_has_account_relationship():
    """Test that Mapping has relationship to Account"""
    from app.models.mapping import Mapping
    
    assert hasattr(Mapping, 'account')


def test_mapping_repr():
    """Test Mapping __repr__ method"""
    from app.models.mapping import Mapping
    from types import SimpleNamespace
    
    # Create mock mapping
    mapping = SimpleNamespace(
        id=1,
        account_id=1,
        csv_header='Buchungsdatum',
        standard_field='date'
    )
    
    # Call the actual __repr__ method
    repr_str = Mapping.__repr__(mapping)
    
    assert 'Mapping' in repr_str
    assert '1' in repr_str
    assert 'Buchungsdatum' in repr_str
    assert 'date' in repr_str
