"""
Tests for Category Model
"""
import pytest


def test_category_model_exists():
    """Test that Category model can be imported"""
    from app.models.category import Category
    
    assert Category is not None
    assert hasattr(Category, '__tablename__')


def test_category_tablename():
    """Test that Category has correct table name"""
    from app.models.category import Category
    
    assert Category.__tablename__ == "categories"


def test_category_has_required_columns():
    """Test that Category has all required columns"""
    from app.models.category import Category
    
    assert hasattr(Category, 'id')
    assert hasattr(Category, 'name')
    assert hasattr(Category, 'color')
    assert hasattr(Category, 'icon')
    assert hasattr(Category, 'mappings')
    assert hasattr(Category, 'created_at')
    assert hasattr(Category, 'updated_at')


def test_category_name_is_unique():
    """Test that category name column is unique"""
    from app.models.category import Category
    
    name_col = Category.__table__.columns['name']
    assert name_col.unique is True


def test_category_default_color():
    """Test that Category has default color"""
    from app.models.category import Category
    
    color_col = Category.__table__.columns['color']
    assert color_col.default is not None
    assert color_col.default.arg.startswith('#')


def test_category_default_mappings():
    """Test that Category has default empty patterns in mappings"""
    from app.models.category import Category
    
    mappings_col = Category.__table__.columns['mappings']
    assert mappings_col.default is not None
    default_value = mappings_col.default.arg
    assert isinstance(default_value, dict)
    assert 'patterns' in default_value
    assert default_value['patterns'] == []


def test_category_repr():
    """Test Category __repr__ method"""
    from app.models.category import Category
    from types import SimpleNamespace
    
    category = SimpleNamespace(id=1, name='Groceries', color='#ff0000')
    repr_str = Category.__repr__(category)
    
    assert 'Category' in repr_str
    assert 'Groceries' in repr_str
    assert '#ff0000' in repr_str


def test_category_mappings_is_json():
    """Test that mappings column is JSON type"""
    from app.models.category import Category
    from sqlalchemy import JSON
    
    mappings_col = Category.__table__.columns['mappings']
    assert isinstance(mappings_col.type, JSON)
