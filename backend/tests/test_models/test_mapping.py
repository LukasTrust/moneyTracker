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
